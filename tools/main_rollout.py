"""Let the existing Official installation follow the approved upstream main pair."""
import json
import re


def load(root, channel):
    path = root / 'main-rollout.json'
    if not path.exists():
        return None
    policy = json.loads(path.read_text(encoding='utf-8'))
    if policy != {'repository': 'nightscout/nocturne', 'source': 'approved-latest',
                  'channels': ['official']}:
        raise ValueError('Official main policy must use the approved Nightscout image pair')
    if channel not in policy['channels']:
        return None
    lock = json.loads((root / 'upstream-latest.json').read_text(encoding='utf-8'))
    if lock.get('channel') != 'main' or not re.fullmatch('[0-9a-f]{40}', lock.get('commit', '')):
        raise ValueError('Official main needs an exact approved main commit')
    return {**lock, 'repository': policy['repository']}


def metadata(original, rollout):
    link = f"https://github.com/{rollout['repository']}/tree/{rollout['commit']}"
    return {**original, 'repository': rollout['repository'],
            'source_commit': rollout['commit'], 'commit_at': rollout['commit_at'],
            'base_commit': rollout['commit'],
            'nocturne': 'main@' + rollout['commit'][:7],
            'base': 'Nocturne main', 'release': 'Official main ' + rollout['commit'][:7],
            'release_url': link,
            'purpose': 'Use the verified official Nightscout main build without Personal changes.',
            'purpose_url': link,
            'test_url': f"https://github.com/nightscout/nocturne/actions/runs/{rollout['workflow_run']}",
            'source_rollout': rollout}
