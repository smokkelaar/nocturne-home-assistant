"""Read-only OCI verification, adapted from the AGPL upstream HA publisher.

Source: smokkelaar/nocturne-home-assistant-upstream,
deploy/home-assistant/tools/candidate.py. Tokens stay in memory and are never logged.
"""
import hashlib
import json
import re
import urllib.request

ACCEPT = ', '.join(('application/vnd.oci.image.index.v1+json',
                   'application/vnd.docker.distribution.manifest.list.v2+json',
                   'application/vnd.oci.image.manifest.v1+json',
                   'application/vnd.docker.distribution.manifest.v2+json'))


def fetch(url, headers=None, expected=None):
    request = urllib.request.Request(url, headers={'User-Agent': 'nocturne-ha-prebuilt', **(headers or {})})
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read(10_000_001)
        if len(raw) > 10_000_000:
            raise ValueError('Registry metadata exceeds limit')
        digest = 'sha256:' + hashlib.sha256(raw).hexdigest()
        advertised = response.headers.get('Docker-Content-Digest')
        if (expected and digest != expected) or (advertised and digest != advertised):
            raise ValueError('Registry content digest mismatch')
        return json.loads(raw), digest


def image(repository, reference, arch, revision=None, labels=None):
    if not re.fullmatch(r'[a-z0-9][a-z0-9._/-]+', repository) or arch not in ('amd64', 'arm64'):
        raise ValueError('Invalid registry repository/platform')
    token = fetch('https://ghcr.io/token?service=ghcr.io&scope=repository:' + repository + ':pull')[0]['token']
    headers = {'Authorization': 'Bearer ' + token, 'Accept': ACCEPT}
    expected = reference if reference.startswith('sha256:') else None
    manifest, digest = fetch(f'https://ghcr.io/v2/{repository}/manifests/{reference}', headers, expected)
    parent = digest
    if 'manifests' in manifest:
        entries = [entry for entry in manifest['manifests']
                   if entry.get('platform', {}).get('os') == 'linux'
                   and entry['platform'].get('architecture') == arch]
        if len(entries) != 1:
            raise ValueError('Expected one native image for ' + arch)
        digest = entries[0]['digest']
        manifest, _ = fetch(f'https://ghcr.io/v2/{repository}/manifests/{digest}', headers, digest)
    config, _ = fetch(f'https://ghcr.io/v2/{repository}/blobs/' + manifest['config']['digest'], headers, manifest['config']['digest'])
    if config.get('architecture') != arch or config.get('os') != 'linux':
        raise ValueError('Registry image platform mismatch')
    actual_labels = config.get('config', {}).get('Labels', {})
    env = dict(value.split('=', 1) for value in config.get('config', {}).get('Env', []) if '=' in value)
    actual_revision = actual_labels.get('org.opencontainers.image.revision') or env.get('GIT_COMMIT')
    if revision and actual_revision != revision:
        raise ValueError('Registry source revision mismatch')
    if any(actual_labels.get(key) != value for key, value in (labels or {}).items()):
        raise ValueError('Registry HA image labels mismatch')
    return {'digest': digest, 'index': parent, 'revision': actual_revision, 'labels': actual_labels}
