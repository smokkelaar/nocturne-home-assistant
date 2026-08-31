import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { spawnSync } from 'node:child_process';
import { checkModules } from '../nocturne_local/build/check_web.mjs';

function fixture(context) {
  const root = mkdtempSync(join(tmpdir(), 'nocturne-web-check-'));
  context.after(() => rmSync(root, { recursive: true }));
  mkdirSync(join(root, 'app'));
  writeFileSync(join(root, 'package.json'), JSON.stringify({ type: 'module' }));
  return root;
}

test('loads ESM from the application context', (context) => {
  const root = fixture(context);
  writeFileSync(join(root, 'app/healthy.mjs'), 'export const ready = true;');
  assert.match(checkModules(root, 'app', ['./healthy.mjs']), /OK: .\/healthy.mjs/);
});

test('missing modules cause a build failure', (context) => {
  const root = fixture(context);
  assert.throws(() => checkModules(root, 'app', ['nocturne-missing-module']), /Web dependency check failed/);
});

test('external dependency paths are rejected even when readable', (context) => {
  const root = fixture(context);
  const external = fixture(context);
  writeFileSync(join(external, 'outside.mjs'), 'export const value = 1;');
  const filename = join(external, 'outside.mjs');
  // A file URL also exercises Windows path handling; realpath protects symlinks too.
  const { href } = pathToFileURL(filename);
  assert.throws(() => checkModules(root, 'app', [href]), /Dependency outside application directory/);
});

test('module evaluation errors cannot produce a passing check', (context) => {
  const root = fixture(context);
  writeFileSync(join(root, 'app/broken.mjs'), 'throw Error("fixture import failed");');
  assert.throws(() => checkModules(root, 'app', ['./broken.mjs']), /fixture import failed/);
});

test('unhandled import rejection cannot produce a passing check', (context) => {
  const root = fixture(context);
  writeFileSync(join(root, 'app/rejection.mjs'), 'void Promise.reject(Error("fixture rejection"));');
  assert.throws(() => checkModules(root, 'app', ['./rejection.mjs']), /fixture rejection/);
});

test('build entrypoint rejects any user other than UID 1655', () => {
  if (process.getuid?.() === 1655) return;
  const checker = fileURLToPath(new URL('../nocturne_local/build/check_web.mjs', import.meta.url));
  const result = spawnSync(process.execPath, [resolve(checker)], { encoding: 'utf8', timeout: 10000 });
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /UID 1655/);
});
