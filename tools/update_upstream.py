"""Manually promote official Nocturne releases and update explicit pins.

No dependencies, no floating latest images, no auto-merge, no access to HA.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.request

from versioning import next_package, package_build, wrapper_version

ROOT = Path(__file__).resolve().parents[1]
PROJECT = 'nightscout/nocturne'
ACCEPT = ', '.join([
    'application/vnd.oci.image.index.v1+json',
    'application/vnd.docker.distribution.manifest.list.v2+json',
    'application/vnd.oci.image.manifest.v1+json',
    'application/vnd.docker.distribution.manifest.v2+json',
])


def semver(value):
    if not isinstance(value, str) or not re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', value):
        raise ValueError('Only stable three-part numeric versions are accepted')
    return tuple(map(int, value.split('.')))


def release_version(release):
    if release.get('draft') or release.get('prerelease'):
        raise ValueError('Draft/prerelease updates require manual review')
    tag = release['tag_name']
    version = tag.removeprefix('v')
    semver(version)
    return version


def fetch(url, headers=None, expected_digest=None):
    request = urllib.request.Request(url, headers={'User-Agent': 'nocturne-home-assistant-updater', **(headers or {})})
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read(10_000_001)
        if len(body) > 10_000_000:
            raise ValueError('Unexpectedly large upstream metadata')
        digest = 'sha256:' + hashlib.sha256(body).hexdigest()
        advertised = response.headers.get('Docker-Content-Digest')
        if (expected_digest and expected_digest != digest) or (advertised and advertised != digest):
            raise ValueError('OCI digest mismatch')
        return json.loads(body), digest


def github(path):
    token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    headers = {'Authorization': 'Bearer ' + token} if token else {}
    return fetch('https://api.github.com/repos/' + PROJECT + '/' + path, headers)[0]


def resolve_image(kind, version, commit):
    repository = f'{PROJECT}/nocturne-{kind}'
    auth, _ = fetch(f'https://ghcr.io/token?service=ghcr.io&scope=repository:{repository}:pull')
    headers = {'Authorization': 'Bearer ' + auth['token'], 'Accept': ACCEPT}
    for tag in (version, 'v' + version):
        try:
            manifest, digest = fetch(f'https://ghcr.io/v2/{repository}/manifests/{tag}', headers)
            break
        except urllib.error.HTTPError as error:
            if error.code != 404 or tag.startswith('v'):
                raise
    if 'manifests' in manifest:
        entries = [m for m in manifest['manifests'] if m.get('platform', {}).get('os') == 'linux'
                   and m['platform'].get('architecture') == 'amd64']
        if len(entries) != 1:
            raise ValueError('Expected exactly one linux/amd64 image')
        selected = entries[0]['digest']
        manifest, _ = fetch(f'https://ghcr.io/v2/{repository}/manifests/{selected}', headers, selected)
    config_digest = manifest['config']['digest']
    config, _ = fetch(f'https://ghcr.io/v2/{repository}/blobs/{config_digest}', headers, config_digest)
    if config.get('architecture') != 'amd64' or config.get('os') != 'linux':
        raise ValueError('Unsupported upstream image platform')
    env = dict(item.split('=', 1) for item in config['config'].get('Env', []) if '=' in item)
    revision = config['config'].get('Labels', {}).get('org.opencontainers.image.revision') or env.get('GIT_COMMIT')
    # 0.2.4 API includes GIT_COMMIT; its web image does not expose a revision.
    if (kind == 'api' and revision != commit) or (revision and revision != commit):
        raise ValueError('Upstream image/source revision mismatch or missing API revision')
    return {'tag': tag, 'digest': digest}


def validate_lock(lock):
    semver(lock['version'])
    if lock['tag'] not in (lock['version'], 'v' + lock['version']):
        raise ValueError('Release tag/version mismatch')
    if not re.fullmatch('[0-9a-f]{40}', lock['commit']):
        raise ValueError('Invalid source commit')
    for kind in ('api', 'web'):
        if lock[kind]['tag'] not in (lock['version'], 'v' + lock['version']):
            raise ValueError('API and web must come from the same release')
        if not re.fullmatch('sha256:[0-9a-f]{64}', lock[kind]['digest']):
            raise ValueError('Invalid image digest')


def dumps(value):
    return json.dumps(value, indent=2) + '\n'


def render(root, lock, app_version):
    validate_lock(lock)
    package_build(root, app_version)
    wrapper = wrapper_version(root)
    config = json.loads((root / 'nocturne_local/config.json').read_text(encoding='utf-8'))
    config['version'] = app_version
    config['description'] = (f"HA wrapper {wrapper} · Official Nocturne {lock['version']} with PostgreSQL. "
                             'Experimental; not for clinical use.')
    dockerfile = (root / 'nocturne_local/Dockerfile').read_text(encoding='utf-8')
    for kind in ('api', 'web'):
        pattern = rf'(?m)^FROM ghcr\.io/nightscout/nocturne/nocturne-{kind}@sha256:[0-9a-f]{{64}}'
        replacement = f"FROM ghcr.io/{PROJECT}/nocturne-{kind}@{lock[kind]['digest']}"
        dockerfile, count = re.subn(pattern, replacement, dockerfile)
        if count != 1:
            raise ValueError('Unexpected Dockerfile image signature')
    dockerfile, count = re.subn(r'(?m)^ARG BUILD_VERSION=\S+$', 'ARG BUILD_VERSION=' + app_version, dockerfile)
    if count != 1:
        raise ValueError('Unexpected Dockerfile version signature')
    return {
        'upstream.json': dumps(lock),
        'nocturne_local/config.json': dumps(config),
        'nocturne_local/Dockerfile': dockerfile,
        'nocturne_local/rootfs/opt/nocturne-ha/version.json': dumps({
            'app': wrapper, 'package': app_version,
            'nocturne': lock['version'], 'name': 'Nocturne Official Release',
            'default_public_url': 'https://homeassistant.local:8448',
            'cookie_namespace': 'NocturneOfficial_',
        }),
    }


def apply_update(root, current, candidate):
    validate_lock(current)
    validate_lock(candidate)
    if semver(candidate['version']) <= semver(current['version']):
        raise ValueError('Refusing an equal version, retag, or downgrade')
    version = json.loads((root / 'nocturne_local/config.json').read_text(encoding='utf-8'))['version']
    next_version = next_package(root, version)
    prepared = render(root, candidate, next_version)  # Validate ALL before writing ANY.
    changelog = root / 'nocturne_local/CHANGELOG.md'
    note = (f"## {next_version}\n\n- Update paired Nocturne API/web to {candidate['version']}.\n"
            f"- [Upstream release](https://github.com/{PROJECT}/releases/tag/{candidate['tag']}).\n"
            '- Maintainer review and backup required before installation; database migrations may occur.\n\n')
    prepared['nocturne_local/CHANGELOG.md'] = note + changelog.read_text(encoding='utf-8')
    for name, content in prepared.items():
        (root / name).write_text(content, encoding='utf-8', newline='\n')
    return next_version


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check', action='store_true', help='Offline: verify the lock and generated version fields')
    mode.add_argument('--check-upstream', action='store_true', help='Online read-only: compare latest stable release')
    mode.add_argument('--update', action='store_true', help='Online: prepare a newer stable release in this checkout')
    args = parser.parse_args()
    current = json.loads((ROOT / 'upstream.json').read_text(encoding='utf-8'))
    validate_lock(current)
    if args.check:
        version = json.loads((ROOT / 'nocturne_local/config.json').read_text(encoding='utf-8'))['version']
        for name, expected in render(ROOT, current, version).items():
            actual = (ROOT / name).read_text(encoding='utf-8')
            same = json.loads(actual) == json.loads(expected) if name.endswith('.json') else actual == expected
            if not same:
                raise ValueError('Inconsistent generated metadata: ' + name)
        print('Version and image pins are consistent.')
        return
    release = github('releases/latest')
    version = release_version(release)
    if semver(version) <= semver(current['version']):
        print('No newer stable Nocturne release: ' + current['version'])
        return
    print(f"New stable Nocturne release: {current['version']} -> {version}")
    if args.check_upstream:
        return
    commit = github('commits/' + release['tag_name'])['sha']
    candidate = {'version': version, 'tag': release['tag_name'], 'commit': commit}
    for kind in ('api', 'web'):
        candidate[kind] = resolve_image(kind, version, commit)
    next_version = apply_update(ROOT, current, candidate)
    print('Prepared HA app version ' + next_version + '; review and tests are still required.')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, urllib.error.URLError) as error:
        # Do not dump HTTP request headers or credentials.
        raise SystemExit(f'Update refused: {type(error).__name__}: {error}') from None
