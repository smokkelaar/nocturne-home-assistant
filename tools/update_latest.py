"""Promote a tested Nocturne main snapshot into the separate Latest HA app.

The upstream ``latest`` tags are used only for discovery. The generated HA
Dockerfile always uses immutable OCI digests and records the exact source
commit plus the successful upstream build job that produced the pair.
"""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
PROJECT = 'nightscout/nocturne'
ACCEPT = ', '.join([
    'application/vnd.oci.image.index.v1+json',
    'application/vnd.docker.distribution.manifest.list.v2+json',
    'application/vnd.oci.image.manifest.v1+json',
    'application/vnd.docker.distribution.manifest.v2+json',
])


class NotReady(ValueError):
    """The current upstream head has no complete paired image build yet."""


def semver(value):
    if not isinstance(value, str) or not re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', value):
        raise ValueError('HA app version must be stable three-part numeric semver')
    return tuple(map(int, value.split('.')))


def fetch(url, headers=None, expected_digest=None):
    request = urllib.request.Request(url, headers={'User-Agent': 'nocturne-home-assistant-latest-updater',
                                                   **(headers or {})})
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


def validate_lock(lock):
    if lock.get('channel') != 'main' or not re.fullmatch(r'[0-9a-f]{40}', lock.get('commit', '')):
        raise ValueError('Invalid Latest channel/source commit')
    if type(lock.get('workflow_run')) is not int or lock['workflow_run'] <= 0:
        raise ValueError('Invalid upstream workflow provenance')
    published = lock.get('published_at', '')
    try:
        datetime.fromisoformat(published.replace('Z', '+00:00'))
    except (TypeError, ValueError):
        raise ValueError('Invalid upstream publication timestamp') from None
    for kind in ('api', 'web'):
        if lock.get(kind, {}).get('tag') != 'latest':
            raise ValueError('Latest discovery tags must remain paired')
        if not re.fullmatch(r'sha256:[0-9a-f]{64}', lock[kind].get('digest', '')):
            raise ValueError('Invalid immutable image digest')


def resolve_image(kind, commit):
    repository = f'{PROJECT}/nocturne-{kind}'
    auth, _ = fetch(f'https://ghcr.io/token?service=ghcr.io&scope=repository:{repository}:pull')
    headers = {'Authorization': 'Bearer ' + auth['token'], 'Accept': ACCEPT}
    manifest, digest = fetch(f'https://ghcr.io/v2/{repository}/manifests/latest', headers)
    if 'manifests' in manifest:
        entries = [entry for entry in manifest['manifests']
                   if entry.get('platform', {}).get('os') == 'linux'
                   and entry['platform'].get('architecture') == 'amd64']
        if len(entries) != 1:
            raise ValueError('Expected exactly one linux/amd64 image')
        selected = entries[0]['digest']
        manifest, _ = fetch(f'https://ghcr.io/v2/{repository}/manifests/{selected}', headers, selected)
    config_digest = manifest['config']['digest']
    config, _ = fetch(f'https://ghcr.io/v2/{repository}/blobs/{config_digest}', headers, config_digest)
    if config.get('architecture') != 'amd64' or config.get('os') != 'linux':
        raise ValueError('Unsupported upstream image platform')
    environment = dict(item.split('=', 1) for item in config['config'].get('Env', []) if '=' in item)
    revision = config['config'].get('Labels', {}).get('org.opencontainers.image.revision')
    revision = revision or environment.get('GIT_COMMIT')
    # The API image exposes GIT_COMMIT and anchors the pair. The web image is
    # accepted only from the same completed build-and-push job below.
    if (kind == 'api' and revision != commit) or (revision and revision != commit):
        raise NotReady('Published latest image does not match current main')
    return {'tag': 'latest', 'digest': digest}


def successful_build(commit):
    runs = github('actions/workflows/docker-publish.yml/runs?branch=main&event=push&per_page=50')
    matches = [run for run in runs.get('workflow_runs', [])
               if run.get('head_sha') == commit and run.get('status') == 'completed']
    for run in matches:
        jobs = github(f"actions/runs/{run['id']}/jobs?per_page=100").get('jobs', [])
        build = [job for job in jobs if job.get('name') == 'build-and-push']
        if len(build) == 1 and build[0].get('conclusion') == 'success':
            return run
    raise NotReady('Current main has no successful build-and-push job yet')


def resolve_candidate(current):
    validate_lock(current)
    commit = github('commits/main')['sha']
    if commit == current['commit']:
        return current
    comparison = github(f"compare/{current['commit']}...{commit}")
    if comparison.get('status') != 'ahead' or comparison.get('behind_by') != 0:
        raise ValueError('Refusing rewritten, divergent or downgraded main history')
    run = successful_build(commit)
    candidate = {
        'channel': 'main', 'commit': commit, 'workflow_run': run['id'],
        'published_at': run['created_at'],
        'api': resolve_image('api', commit), 'web': resolve_image('web', commit),
    }
    # Close the race where main or the floating discovery tag changes while
    # manifests are being inspected. Nothing is written unless both stay put.
    if github('commits/main')['sha'] != commit or resolve_image('api', commit) != candidate['api']:
        raise NotReady('Upstream main/images changed during resolution; retry later')
    validate_lock(candidate)
    return candidate


def dumps(value):
    return json.dumps(value, indent=2) + '\n'


def render(root, lock, app_version):
    validate_lock(lock)
    semver(app_version)
    config = json.loads((root / 'nocturne_latest/config.json').read_text())
    config['version'] = app_version
    config['description'] = (f"Daily-tested Nocturne main snapshot {lock['commit'][:7]} with PostgreSQL. "
                             'Highly experimental; not for clinical use.')
    dockerfile = (root / 'nocturne_latest/Dockerfile').read_text()
    for kind in ('api', 'web'):
        pattern = rf'(?m)^FROM ghcr\.io/nightscout/nocturne/nocturne-{kind}@sha256:[0-9a-f]{{64}}'
        replacement = f"FROM ghcr.io/{PROJECT}/nocturne-{kind}@{lock[kind]['digest']}"
        dockerfile, count = re.subn(pattern, replacement, dockerfile)
        if count != 1:
            raise ValueError('Unexpected Latest Dockerfile image signature')
    dockerfile, count = re.subn(r'(?m)^ARG BUILD_VERSION=\S+$', 'ARG BUILD_VERSION=' + app_version, dockerfile)
    if count != 1:
        raise ValueError('Unexpected Latest Dockerfile version signature')
    return {
        'upstream-latest.json': dumps(lock),
        'nocturne_latest/config.json': dumps(config),
        'nocturne_latest/Dockerfile': dockerfile,
        'nocturne_latest/rootfs/opt/nocturne-ha/version.json': dumps({
            'app': app_version, 'nocturne': 'main@' + lock['commit'][:7],
            'name': 'Nocturne Latest Release',
        }),
    }


def apply_update(root, current, candidate):
    validate_lock(current)
    validate_lock(candidate)
    if candidate['commit'] == current['commit']:
        raise ValueError('Refusing an unchanged Latest snapshot')
    version = json.loads((root / 'nocturne_latest/config.json').read_text())['version']
    major, minor, patch = semver(version)
    next_version = f'{major}.{minor}.{patch + 1}'
    prepared = render(root, candidate, next_version)  # Validate all before writing any file.
    changelog = root / 'nocturne_latest/CHANGELOG.md'
    note = (f"## {next_version}\n\n- Update Nocturne Latest from `{current['commit'][:7]}` "
            f"to [`{candidate['commit'][:7]}`](https://github.com/{PROJECT}/compare/"
            f"{current['commit']}...{candidate['commit']}).\n"
            f"- Upstream paired-image build: https://github.com/{PROJECT}/actions/runs/"
            f"{candidate['workflow_run']}\n"
            '- Automated container and previous-Latest upgrade tests are required before merge. '
            'Keep a cold backup; rollback after a development schema migration is not guaranteed.\n\n')
    prepared['nocturne_latest/CHANGELOG.md'] = note + changelog.read_text()
    for name, content in prepared.items():
        (root / name).write_text(content, encoding='utf-8', newline='\n')
    return next_version


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check', action='store_true', help='Offline: verify Latest lock/generated files')
    mode.add_argument('--check-upstream', action='store_true', help='Online read-only: compare tested main')
    mode.add_argument('--update', action='store_true', help='Online: prepare a newer tested main snapshot')
    args = parser.parse_args()
    current = json.loads((ROOT / 'upstream-latest.json').read_text())
    validate_lock(current)
    if args.check:
        version = json.loads((ROOT / 'nocturne_latest/config.json').read_text())['version']
        for name, expected in render(ROOT, current, version).items():
            actual = (ROOT / name).read_text()
            same = json.loads(actual) == json.loads(expected) if name.endswith('.json') else actual == expected
            if not same:
                raise ValueError('Inconsistent generated Latest metadata: ' + name)
        print('Latest source and image pins are consistent.')
        return
    try:
        candidate = resolve_candidate(current)
    except NotReady as error:
        print('No promotable Latest snapshot: ' + str(error))
        return
    if candidate['commit'] == current['commit']:
        print('Latest already tracks tested main ' + current['commit'][:7])
        return
    print(f"New tested main snapshot: {current['commit'][:7]} -> {candidate['commit'][:7]}")
    if args.check_upstream:
        return
    next_version = apply_update(ROOT, current, candidate)
    print('Prepared Latest HA app version ' + next_version + '; automated tests are still required.')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, urllib.error.URLError) as error:
        raise SystemExit(f'Latest update refused: {type(error).__name__}: {error}') from None
