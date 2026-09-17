// Build-time dependency checks, in the real ESM import contexts and runtime UID.
// Does not start the web server, connect to a database, or load patient data.
import { spawnSync } from 'node:child_process';
import { resolve, join } from 'node:path';
import { pathToFileURL } from 'node:url';

export function checkModules(root, relativeDirectory, modules, resolveOnly = []) {
  const check = `
    import { realpathSync } from 'node:fs';
    import { relative, isAbsolute } from 'node:path';
    import { fileURLToPath } from 'node:url';
    const root = realpathSync(process.argv[1]);
    const modules = JSON.parse(process.argv[2]);
    const resolveOnly = JSON.parse(process.argv[3]);
    for (const name of [...modules, ...resolveOnly]) {
      const target = realpathSync(fileURLToPath(import.meta.resolve(name)));
      const offset = relative(root, target);
      if (offset === '..' || offset.startsWith('../') || offset.startsWith('..\\\\') || isAbsolute(offset)) {
        throw Error('Dependency outside application directory: ' + name);
      }
      if (!resolveOnly.includes(name)) await import(name);
      console.log('[web-build-check] OK: ' + name);
    }
  `;
  const result = spawnSync(process.execPath, [
    '--unhandled-rejections=strict', '--input-type=module', '--eval', check,
    resolve(root), JSON.stringify(modules), JSON.stringify(resolveOnly),
  ], {
    cwd: join(root, relativeDirectory), encoding: 'utf8', timeout: 45000,
    env: { ...process.env, NODE_ENV: 'production', OTEL_SDK_DISABLED: 'true',
      OTEL_EXPORTER_OTLP_ENDPOINT: '' },
  });
  if (result.error || result.status !== 0) {
    throw Error(`Web dependency check failed in ${relativeDirectory}:\n${result.stderr || result.error}`);
  }
  return result.stdout;
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  if (process.getuid?.() !== 1655) {
    throw Error('Run the build check as nocturne-web (UID 1655), not as root');
  }
  const root = '/opt/nocturne-web';
  process.stdout.write(checkModules(root, 'packages/app', [
    'zod', 'import-in-the-middle', '@opentelemetry/api', '@nocturne/bridge',
  ], ['import-in-the-middle/hook.mjs']));
  process.stdout.write(checkModules(root, 'packages/bridge', [
    'socket.io', '@microsoft/signalr', 'tough-cookie', 'winston',
  ]));
}
