"""Land automation pull requests and confirm what the HA store really offers.

`land` drives one automation PR to a merge without a human: it brings the branch up
to date with main (branch protection is strict), dispatches the required Validate
checks for the exact head commit, waits for them and squash-merges that commit.
Merges and pushes made with the Actions GITHUB_TOKEN start no workflows, so a source
PR names `--publish-after` to dispatch the store publication itself.

`status` is the one answer to "is it in HA yet": a version counts as ready only when
main's config.json advertises it and both architectures pull anonymously from GHCR.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.request

import registry

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = 'smokkelaar/nocturne-home-assistant'
REQUIRED_CHECKS = ('Unit tests', 'Container smoke test')
PACKAGES = {'official': 'nocturne_local', 'latest': 'nocturne_latest',
            'personal': 'nocturne_personal', 'test-a': 'nocturne_test_a',
            'test-b': 'nocturne_test_b', 'test-c': 'nocturne_test_c'}
ARCHITECTURES = {'amd64': 'amd64', 'aarch64': 'arm64'}
FAILED = {'failure', 'timed_out', 'action_required', 'startup_failure'}
RESTART_AFTER = 10 * 60
REFRESH_HINT = ('HA leest de store zelf maar eens per 3 uur. Direct zien: Instellingen > Apps > '
                'App store > menu rechtsboven > Controleren op updates.')


class LandingError(RuntimeError):
    pass


def github(path, method='GET', body=None):
    """GitHub REST call through `gh`, which carries GH_TOKEN; returns (status, json)."""
    command = ['gh', 'api', '--method', method, '-i', path]
    if body is not None:
        command += ['--input', '-']
    result = subprocess.run(command, input=json.dumps(body) if body is not None else None,
                            capture_output=True, text=True, timeout=120, check=False)
    head, _, payload = result.stdout.partition('\r\n\r\n')
    if not payload and '\n\n' in result.stdout:
        head, _, payload = result.stdout.partition('\n\n')
    try:
        status = int(head.split(None, 2)[1])
    except (IndexError, ValueError):
        raise LandingError('GitHub call failed: ' + path + ': ' + result.stderr.strip()[:300])
    return status, json.loads(payload) if payload.strip() else {}


def required_checks(api, repository, sha):
    """Latest state per required check on sha: 'missing', 'running' or its conclusion."""
    status, data = api(f'repos/{repository}/commits/{sha}/check-runs?per_page=100')
    if status != 200:
        raise LandingError(f'Cannot read checks for {sha}: HTTP {status}')
    runs = {}
    for run in sorted(data.get('check_runs', []), key=lambda run: run.get('started_at') or ''):
        if run.get('name') in REQUIRED_CHECKS:
            runs[run['name']] = run.get('conclusion') if run.get('status') == 'completed' else 'running'
    return {name: runs.get(name, 'missing') for name in REQUIRED_CHECKS}


def dispatch(api, repository, ref, inputs=None):
    status, _ = api(f'repos/{repository}/actions/workflows/validate.yml/dispatches', 'POST',
                    {'ref': ref, 'inputs': inputs or {}})
    if status != 204:
        raise LandingError(f'Could not start Validate on {ref}: HTTP {status}')


def publish(api, repository):
    dispatch(api, repository, 'main', {'publish': 'true', 'force': 'false', 'channels': 'changed'})


def land(api, repository, number, wait_minutes, publish_after=False, sleep=time.sleep, clock=time.monotonic):
    deadline = clock() + wait_minutes * 60
    dispatched = {}
    updated = set()
    while True:
        status, pr = api(f'repos/{repository}/pulls/{number}')
        if status != 200:
            raise LandingError(f'Cannot read PR #{number}: HTTP {status}')
        if pr.get('merged'):
            print(f'PR #{number} is merged as {pr.get("merge_commit_sha")}.')
            break
        if pr.get('state') != 'open':
            raise LandingError(f'PR #{number} was closed without merging.')
        sha, branch, state = pr['head']['sha'], pr['head']['ref'], pr.get('mergeable_state')
        if state == 'dirty':
            raise LandingError(f'PR #{number} conflicts with main; regenerate it.')
        if state == 'behind' and sha not in updated:
            updated.add(sha)
            code, _ = api(f'repos/{repository}/pulls/{number}/update-branch', 'PUT', {'expected_head_sha': sha})
            if code not in (202, 422):
                raise LandingError(f'Could not bring PR #{number} up to date: HTTP {code}')
            print(f'PR #{number} was behind main; merged main into {branch}.')
        elif state != 'behind':
            checks = required_checks(api, repository, sha)
            failed = sorted(name for name, result in checks.items() if result in FAILED)
            if failed:
                raise LandingError(f'Required checks failed on {sha[:12]}: {", ".join(failed)}')
            if all(result == 'success' for result in checks.values()):
                code, merged = api(f'repos/{repository}/pulls/{number}/merge', 'PUT',
                                   {'merge_method': 'squash', 'sha': sha})
                if code == 200 and merged.get('merged'):
                    print(f'PR #{number} merged at {sha[:12]}.')
                    break
                print(f'Merge of PR #{number} not accepted yet (HTTP {code}); retrying.')
            elif 'running' not in checks.values():
                # Nothing runs for this commit: never started, superseded, or the dispatch was lost.
                started = dispatched.get(sha)
                if (started is None or clock() - started > RESTART_AFTER
                        or ('cancelled' in checks.values() and clock() - started > 120)):
                    dispatch(api, repository, branch)
                    dispatched[sha] = clock()
                    print(f'Started Validate for {branch} at {sha[:12]}.')
        if clock() > deadline:
            raise LandingError(f'PR #{number} did not land within {wait_minutes} minutes.')
        sleep(30)
    if publish_after:
        publish(api, repository)
        print('Dispatched store publication on main.')


def fetch_json(url):
    headers = {'User-Agent': 'nocturne-ha-store-status', 'Accept': 'application/vnd.github.raw+json'}
    token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if token:
        headers['Authorization'] = 'Bearer ' + token
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as response:
        return json.loads(response.read(2_000_000))


def channel_status(repository, channel, ref='main', fetch=fetch_json, inspect=registry.image):
    package = PACKAGES[channel]
    config = fetch(f'https://api.github.com/repos/{repository}/contents/{package}/config.json?ref={ref}')
    version, image = config['version'], config.get('image', '')
    pulls = {}
    for hass, arch in ARCHITECTURES.items():
        try:
            inspect(image.replace('{arch}', hass).removeprefix('ghcr.io/'), version, arch,
                    labels={'io.hass.version': version, 'io.hass.arch': hass})
            pulls[hass] = True
        except (OSError, ValueError, KeyError) as error:
            pulls[hass] = str(error)[:120] or type(error).__name__
    return {'channel': channel, 'package': package, 'version': version, 'pulls': pulls,
            'ready': bool(image) and all(value is True for value in pulls.values())}


def pending_work(repository, fetch=fetch_json):
    """Open automation PRs and running publication runs that are not in the store yet."""
    notes = []
    owner = repository.split('/')[0]
    for branch in ('automation/prebuilt-store', 'automation/nocturne-personal', 'automation/nocturne-latest'):
        for pr in fetch(f'https://api.github.com/repos/{repository}/pulls?state=open&head={owner}:{branch}'):
            notes.append(f'Open PR #{pr["number"]} ({branch}) is not merged yet: {pr["html_url"]}')
    for status in ('in_progress', 'queued'):
        runs = fetch(f'https://api.github.com/repos/{repository}/actions/workflows/validate.yml/runs'
                     f'?branch=main&event=workflow_dispatch&status={status}&per_page=10')
        for run in runs.get('workflow_runs', []):
            notes.append(f'Publication run {status}: {run["html_url"]}')
    return notes


def status(repository, channels, expect, wait_minutes=0, sleep=time.sleep, clock=time.monotonic,
           fetch=fetch_json, inspect=registry.image, out=print):
    deadline = clock() + wait_minutes * 60
    while True:
        rows = [channel_status(repository, channel, fetch=fetch, inspect=inspect) for channel in channels]
        missing = [row for row in rows if not row['ready'] or
                   (row['channel'] in expect and row['version'] != expect[row['channel']])]
        if not missing or clock() >= deadline:
            break
        sleep(60)
    lines = []
    for row in rows:
        wanted = expect.get(row['channel'])
        if row['ready'] and (not wanted or row['version'] == wanted):
            state = 'IN STORE'
        elif wanted and row['version'] != wanted:
            state = f'NOT YET (store has {row["version"]}, expected {wanted})'
        else:
            state = 'NOT PULLABLE ' + ', '.join(f'{arch}: {value}' for arch, value in row['pulls'].items() if value is not True)
        lines.append(f'{row["channel"]:<8} {row["version"]:<12} {state}')
    out('\n'.join(lines))
    if missing:
        for note in pending_work(repository, fetch):
            out(note)
    else:
        out(REFRESH_HINT)
    return not missing


def parse_expect(values):
    expect = {}
    for value in values:
        channel, _, version = value.partition('=')
        channel = channel.replace('nocturne_', '').replace('_', '-')
        if channel == 'local':
            channel = 'official'
        if channel not in PACKAGES or not version:
            raise SystemExit('Use --expect CHANNEL=VERSION, e.g. test-b=1.0.102701')
        expect[channel] = version
    return expect


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--repository', default=os.environ.get('GITHUB_REPOSITORY', REPOSITORY))
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('land', help='bring an automation PR up to date, validate and merge it')
    p.add_argument('--pr', type=int, required=True)
    p.add_argument('--wait-minutes', type=int, default=60)
    p.add_argument('--publish-after', action='store_true')
    p = sub.add_parser('status', help='show which versions HA can install right now')
    p.add_argument('--channel', action='append', choices=sorted(PACKAGES))
    p.add_argument('--expect', action='append', default=[], metavar='CHANNEL=VERSION')
    p.add_argument('--candidates', type=Path, help='expect every version in a candidates.json')
    p.add_argument('--wait-minutes', type=int, default=0)
    args = parser.parse_args(argv)
    if args.command == 'land':
        try:
            land(github, args.repository, args.pr, args.wait_minutes, args.publish_after)
        except LandingError as error:
            print('::error::' + str(error))
            return 1
        return 0
    expect = parse_expect(args.expect)
    if args.candidates:
        expect.update({channel: proof['version'] for channel, proof in json.loads(args.candidates.read_text()).items()})
    channels = args.channel or sorted(expect) or sorted(PACKAGES)
    report = []
    ready = status(args.repository, channels, expect, args.wait_minutes, out=lambda line: (print(line), report.append(line)))
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a', encoding='utf-8') as handle:
            handle.write('## HA store\n\n```\n' + '\n'.join(report) + '\n```\n')
    return 0 if ready else 1


if __name__ == '__main__':
    sys.exit(main())
