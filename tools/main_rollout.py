"""Pinned fork-main rollout using the existing source compiler and app identities."""
import json
import re


def load(root, channel):
    path = root / 'main-rollout.json'
    if not path.exists():
        return None
    value = json.loads(path.read_text(encoding='utf-8'))
    if channel not in value['channels']:
        return None
    if value['repository'] != 'smokkelaar/nocturne-personal':
        raise ValueError('Unexpected main source repository')
    if not re.fullmatch('[0-9a-f]{40}', value['commit']):
        raise ValueError('Main rollout needs an exact source commit')
    if not re.fullmatch('[0-9a-f]{64}', value['archive_sha256']):
        raise ValueError('Main rollout needs an archive checksum')
    return value


def metadata(original, rollout):
    return {**original, 'repository': rollout['repository'],
            'source_commit': rollout['commit'], 'commit_at': rollout['commit_at'],
            'nocturne': 'fork-main@' + rollout['commit'][:7],
            'base': 'Pinned fork main with temporary basal serialization fix',
            'release': 'Main snapshot with temporary basal fix',
            'release_url': f"https://github.com/{rollout['repository']}/tree/{rollout['commit']}",
            'source_rollout': rollout}


def recipe(root, original_name, rollout):
    text = (root / 'nocturne_personal/Dockerfile').read_text(encoding='utf-8')
    pattern = r'ADD --checksum=sha256:[0-9a-f]{64} https://codeload.github.com/smokkelaar/nocturne-personal/tar.gz/[0-9a-f]{40}'
    replacement = (f"ADD --checksum=sha256:{rollout['archive_sha256']} "
                   f"https://codeload.github.com/{rollout['repository']}/tar.gz/{rollout['commit']}")
    text, count = re.subn(pattern, replacement, text)
    if count != 1:
        raise ValueError('Source compiler archive signature changed')
    return text.replace('checksum-verified Personal source', 'checksum-verified fork main source').replace(
        'Nocturne Personal Release - Home Assistant app', original_name + ' - Home Assistant app')
