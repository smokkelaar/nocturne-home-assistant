"""Generate only Personal, compiling its exact fork source instead of upstream binaries."""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
REPO = 'smokkelaar/nocturne-personal'
SDK = 'mcr.microsoft.com/dotnet/sdk@sha256:0e53453ccfc8ff2d51319fe80c678971c6d0f8008dff3565fa88e15840b69854'
RUST = 'rust@sha256:4673f78db88b71f09d5451bbc404734807918161241215ba0a50bbbe9b448117'
COMMON = ('build/check_web.mjs', 'build/prepare_web.py', 'build/check_cookies.conf',
          'rootfs/opt/nocturne-ha/bootstrap.sql', 'rootfs/opt/nocturne-ha/run.py',
          'rootfs/opt/nocturne-ha/tls.py', 'translations/nl.json', 'translations/en.json')


def github(path, raw=False):
    headers = {'User-Agent': 'nocturne-personal-updater',
               'Accept': 'application/vnd.github.raw+json' if raw else 'application/vnd.github+json'}
    token = os.environ.get('GH_TOKEN')
    if token:
        headers['Authorization'] = 'Bearer ' + token
    request = urllib.request.Request(f'https://api.github.com/repos/{REPO}/{path}', headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def validate(lock):
    if lock['channel'] != 'personal' or lock['repository'] != REPO:
        raise ValueError('Wrong Personal source identity')
    for value in (lock['commit'], lock['upstream']['commit']):
        if not re.fullmatch(r'[0-9a-f]{40}', value):
            raise ValueError('Invalid source commit')
    if not re.fullmatch(r'[0-9a-f]{64}', lock['archive_sha256']):
        raise ValueError('Invalid source archive checksum')
    if not re.fullmatch(r'\d+\.\d+\.\d+', lock['version']):
        raise ValueError('Invalid Personal extension version')
    for key in ('commit_at',):
        if datetime.fromisoformat(lock[key].replace('Z', '+00:00')).tzinfo is None:
            raise ValueError('Timestamp must include timezone')
    for kind in ('api', 'web'):
        if not re.fullmatch(r'sha256:[0-9a-f]{64}', lock['upstream'][kind]['digest']):
            raise ValueError('Invalid Daily image pin')


def source_url(lock):
    return f'https://codeload.github.com/{REPO}/tar.gz/{lock["commit"]}'


def resolve():
    approved = json.loads((ROOT / 'upstream-latest.json').read_text())
    head = github('commits/personal')
    commit = head['sha']
    meta = github(f'contents/.personal/version.json?ref={commit}', raw=True)
    if meta['base_commit'] != approved['commit']:
        raise ValueError('Personal has not yet merged the currently approved Daily base')
    comparison = github(f'compare/{approved["commit"]}...{commit}')
    if comparison['status'] not in ('ahead', 'identical') or comparison['merge_base_commit']['sha'] != approved['commit']:
        raise ValueError('Personal does not descend from the approved Daily commit')
    lock = dict(channel='personal', repository=REPO, version=meta['version'],
                commit=commit, commit_at=head['commit']['committer']['date'], upstream=approved)
    digest = hashlib.sha256()
    total = 0
    with urllib.request.urlopen(source_url(lock), timeout=120) as response:
        while block := response.read(1024 * 1024):
            total += len(block)
            if total > 250_000_000:
                raise ValueError('Source archive exceeds safety limit')
            digest.update(block)
    lock['archive_sha256'] = digest.hexdigest()
    validate(lock)
    return lock


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Personal wrapper compatibility signature changed')
    return text.replace(old, new)


def validate_transition(old, new):
    if tuple(map(int, new['version'].split('.'))) < tuple(map(int, old['version'].split('.'))):
        raise ValueError('Personal extension version cannot move backwards')
    if old['commit'] != new['commit']:
        comparison = github(f'compare/{old["commit"]}...{new["commit"]}')
        if comparison['status'] != 'ahead' or comparison['merge_base_commit']['sha'] != old['commit']:
            raise ValueError('Personal source must preserve the previously published source history')


def files(lock, delivery):
    validate(lock)
    latest = ROOT / 'nocturne_latest'
    wrapper = json.loads((ROOT / 'wrapper.json').read_text())['version']
    if not re.fullmatch(re.escape(lock['version']) + r'-[1-9]\d*', delivery):
        raise ValueError('Invalid Personal delivery version')
    generated = {path: (latest / path).read_bytes() for path in COMMON}
    config = json.loads((latest / 'config.json').read_text())
    config.update(name='Nocturne Personal Release', slug='nocturne_personal', version=delivery,
                  panel_title='Nocturne Personal', ports={'8448/tcp': 8450})
    config['options']['public_url'] = 'https://homeassistant.local:8450'
    stamp = datetime.fromisoformat(lock['upstream']['commit_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M UTC')
    config['description'] = f"HA wrapper {wrapper} · Personal {lock['version']} · Daily {lock['upstream']['commit'][:7]} - {stamp}. Experimental."
    generated['config.json'] = json.dumps(config, indent=2) + '\n'
    docs = (latest / 'DOCS.md').read_text(encoding='utf-8').replace('Nocturne Latest Release', 'Nocturne Personal Release').replace('8449', '8450')
    docs = docs.replace('the frequently updated upstream-`main` channel', 'the Personal source-fork channel following the approved Daily base')
    docs = docs.replace('Leave the Latest host port', 'Leave the Personal host port')
    docs = docs.replace('isolated from Official even', 'isolated from Official and Latest even')
    generated['DOCS.md'] = docs + '\nPersonal compiles API and web from its pinned fork source. Builds need more time and resources than Latest. Google Health is not implemented yet. [Personal versions, source and update behavior](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/PERSONAL.md).\n'
    generated['README.md'] = '# Nocturne Personal Release\n\nIndependent Personal fork on the tested Daily base. Default host port 8450, separate data and cookies.\n\n[Installation and updates](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/PERSONAL.md). Google Health is not implemented yet.\n'
    runtime = dict(app=wrapper, package=delivery, personal=lock['version'],
                   source_commit=lock['commit'], source_at=lock['commit_at'],
                   nocturne='main@' + lock['upstream']['commit'][:7],
                   commit_at=lock['upstream']['commit_at'], name=config['name'],
                   default_public_url=config['options']['public_url'], cookie_namespace='NocturnePersonal_')
    generated['rootfs/opt/nocturne-ha/version.json'] = json.dumps(runtime, indent=2) + '\n'
    settings = (latest / 'rootfs/opt/nocturne-ha/settings.py').read_text(encoding='utf-8')
    settings = settings.replace("('NocturneOfficial_', 'NocturneLatest_')",
                                "('NocturnePersonal_',)")
    settings = replace_once(settings, "    rows = ''.join(",
        "    snapshot += f'<p>Personal {esc(versions[\"personal\"])} · bron {esc(versions[\"source_commit\"][:12])}</p>'\n    rows = ''.join(")
    settings = replace_once(settings, "    return api, web", "    versions = json.loads(Path(__file__).with_name('version.json').read_text())\n    api.update(GIT_COMMIT=versions['source_commit'], BUILD_DATE=versions['source_at'])\n    return api, web")
    generated['rootfs/opt/nocturne-ha/settings.py'] = settings
    cookies = (latest / 'rootfs/opt/nocturne-ha/cookies.mjs').read_text(encoding='utf-8')
    generated['rootfs/opt/nocturne-ha/cookies.mjs'] = replace_once(cookies,
        "const PREFIXES = ['NocturneOfficial_', 'NocturneLatest_'];",
        "const PREFIXES = ['NocturneOfficial_', 'NocturneLatest_', 'NocturnePersonal_'];")
    original = (latest / 'Dockerfile').read_text(encoding='utf-8')
    node = next(line for line in original.splitlines() if line.startswith('FROM node:'))
    tail = original[original.index('USER root'):]
    tail = tail.replace('Nocturne Latest Release', 'Nocturne Personal Release')
    tail = re.sub(r'ARG BUILD_VERSION=\S+', 'ARG BUILD_VERSION=' + delivery, tail)
    tail = replace_once(tail, 'COPY --from=web /app/ /opt/nocturne-web/',
                        'COPY --from=source /out/web/ /opt/nocturne-web/')
    tail = replace_once(tail, 'USER root\nARG BUILD_VERSION=', 'USER root\nCOPY --from=source /out/api/ /app/\nCOPY --from=source /src/crates/target/release/libnocturne_alerts.so /app/libnocturne_alerts.so\nARG BUILD_VERSION=')
    generated['Dockerfile'] = f'''# Both API and web are compiled from the same checksum-verified Personal source.
{node}
FROM {RUST} AS rust
FROM {SDK} AS source
COPY --from=node /usr/local/ /usr/local/
COPY --from=rust /usr/local/cargo/ /usr/local/cargo/
COPY --from=rust /usr/local/rustup/ /usr/local/rustup/
ENV CARGO_HOME=/usr/local/cargo RUSTUP_HOME=/usr/local/rustup PATH=/usr/local/cargo/bin:$PATH
ENV DOTNET_CLI_TELEMETRY_OPTOUT=1 NODE_OPTIONS=--max-old-space-size=6144
RUN apt-get update && apt-get install -y --no-install-recommends build-essential pkg-config libssl-dev ca-certificates \\
    && npm install -g pnpm@10.13.1
ADD --checksum=sha256:{lock['archive_sha256']} {source_url(lock)} /tmp/source.tar.gz
RUN mkdir /src && tar -xzf /tmp/source.tar.gz --strip-components=1 -C /src
WORKDIR /src/src/Web
RUN pnpm install --frozen-lockfile && pnpm --filter @nocturne/bridge run build
WORKDIR /src
RUN dotnet build src/API/Nocturne.API/Nocturne.API.csproj -c Release -p:UseSharedCompilation=false
RUN cargo build --manifest-path crates/Cargo.toml --release --locked -p nocturne-alerts-ffi
RUN dotnet publish src/API/Nocturne.API/Nocturne.API.csproj -c Release -r linux-x64 --self-contained false \\
    -p:GenerateNSwagClient=false -p:UseSharedCompilation=false -o /out/api
WORKDIR /src/src/Web
ENV PUBLIC_API_URL=http://localhost:1612 PUBLIC_WEBSOCKET_RECONNECT_ATTEMPTS=5 PUBLIC_WEBSOCKET_RECONNECT_DELAY=1000
ENV PUBLIC_WEBSOCKET_MAX_RECONNECT_DELAY=30000 PUBLIC_WEBSOCKET_PING_TIMEOUT=15000 PUBLIC_WEBSOCKET_PING_INTERVAL=20000
RUN pnpm --filter @nocturne/bot run build && pnpm --filter @nocturne/app run build
RUN mkdir -p /out/web/packages/app /out/web/packages/bridge \\
    && cp package.json pnpm-lock.yaml pnpm-workspace.yaml /out/web/ \\
    && cp packages/app/package.json packages/app/server.js packages/app/server-origin-warning.js /out/web/packages/app/ \\
    && cp -r packages/app/build /out/web/packages/app/ \\
    && cp packages/bridge/package.json /out/web/packages/bridge/ \\
    && cp -r packages/bridge/dist /out/web/packages/bridge/
# Use the matching approved Daily runtime/OS; replace its application with our source build.
FROM ghcr.io/nightscout/nocturne/nocturne-api@{lock['upstream']['api']['digest']}
{tail}'''
    return {key: value if isinstance(value, bytes) else value.encode() for key, value in generated.items()}


def check(lock=None):
    lock = lock or json.loads((ROOT / 'upstream-personal.json').read_text())
    directory = ROOT / 'nocturne_personal'
    delivery = json.loads((directory / 'config.json').read_text())['version']
    for path, expected in files(lock, delivery).items():
        if (directory / path).read_bytes() != expected:
            raise ValueError('Generated Personal file differs: ' + path)
    print('Personal pins, source recipe, identity and wrapper compatibility verified.')


def update():
    lock_path = ROOT / 'upstream-personal.json'
    old = json.loads(lock_path.read_text()) if lock_path.exists() else None
    lock = resolve()
    if old == lock:
        check(lock)
        print('No new Personal source; no package change.')
        return
    if old:
        validate_transition(old, lock)
    directory = ROOT / 'nocturne_personal'
    delivery = lock['version'] + '-1'
    if old and old['version'] == lock['version']:
        previous = json.loads((directory / 'config.json').read_text())['version']
        delivery = lock['version'] + '-' + str(int(previous.rsplit('-', 1)[1]) + 1)
    for path, data in files(lock, delivery).items():
        target = directory / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    lock_path.write_text(json.dumps(lock, indent=2) + '\n')
    changelog = directory / 'CHANGELOG.md'
    prior = changelog.read_text(encoding='utf-8') if old else ''
    changelog.write_text(f"# {delivery}\n\nPersonal {lock['version']}; source `{lock['commit']}`; Daily base `{lock['upstream']['commit']}`.\n\n" + prior, encoding='utf-8')
    check(lock)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--update', action='store_true')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    update() if args.update else check()
