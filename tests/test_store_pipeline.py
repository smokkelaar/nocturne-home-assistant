"""Automation PRs land without a human, and only an installable version counts as ready."""
from pathlib import Path
import sys
import unittest
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import registry
import store_pipeline as pipeline

REPO = 'smokkelaar/nocturne-home-assistant'


class FakeGitHub:
    """Scripted PR states; records every write the lander makes."""

    def __init__(self, states, checks):
        self.states, self.checks, self.calls = list(states), dict(checks), []

    def __call__(self, path, method='GET', body=None):
        self.calls.append((method, path, body))
        if path.endswith('/check-runs?per_page=100'):
            sha = path.split('/commits/')[1].split('/')[0]
            sequence = self.checks.get(sha, [[]])
            return 200, {'check_runs': sequence[0] if len(sequence) == 1 else sequence.pop(0)}
        if method == 'GET' and '/pulls/' in path:
            return 200, self.states[0] if len(self.states) == 1 else self.states.pop(0)
        if path.endswith('/merge'):
            return 200, {'merged': True}
        if path.endswith('/update-branch'):
            return 202, {}
        if path.endswith('/dispatches'):
            return 204, {}
        raise AssertionError(path)

    def writes(self):
        return [(method, path.rsplit('/', 1)[-1], body) for method, path, body in self.calls
                if method != 'GET']


def pr(sha, state='blocked', merged=False):
    return {'merged': merged, 'state': 'open', 'mergeable_state': state, 'merge_commit_sha': 'm',
            'head': {'sha': sha, 'ref': 'automation/prebuilt-store'}}


def run(name, status='completed', conclusion='success', started='2026-10-28T20:00:00Z'):
    return {'name': name, 'status': status, 'conclusion': conclusion, 'started_at': started}


def green():
    return [run('Unit tests'), run('Container smoke test')]


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class LandTests(unittest.TestCase):
    def land(self, api, minutes=60, publish_after=False):
        clock = Clock()
        pipeline.land(api, REPO, 7, minutes, publish_after, sleep=clock.sleep, clock=clock)
        return api.writes()

    def test_behind_branch_is_updated_validated_and_merged_at_the_tested_commit(self):
        running = [run('Unit tests', 'in_progress', None), run('Container smoke test', 'queued', None)]
        api = FakeGitHub([pr('old', 'behind'), pr('new'), pr('new'), pr('new', 'clean')],
                         {'new': [[], running, green()]})
        writes = self.land(api)
        self.assertEqual(('PUT', 'update-branch', {'expected_head_sha': 'old'}), writes[0])
        self.assertEqual(('POST', 'dispatches', {'ref': 'automation/prebuilt-store', 'inputs': {}}), writes[1])
        self.assertEqual(('PUT', 'merge', {'merge_method': 'squash', 'sha': 'new'}), writes[-1])
        self.assertEqual(3, len(writes))

    def test_failed_required_check_stops_without_merging(self):
        api = FakeGitHub([pr('a')], {'a': [[run('Unit tests'), run('Container smoke test', conclusion='failure')]]})
        with self.assertRaises(pipeline.LandingError):
            self.land(api)
        self.assertNotIn('merge', [path for _, path, _ in api.writes()])

    def test_newest_check_run_decides(self):
        api = FakeGitHub([pr('a')], {'a': [[run('Unit tests'), run('Container smoke test', conclusion='failure'),
                                            run('Container smoke test', started='2026-10-28T21:00:00Z')]]})
        self.assertEqual('merge', self.land(api)[-1][1])

    def test_lost_dispatch_is_restarted_but_not_repeated_every_poll(self):
        api = FakeGitHub([pr('a')], {'a': [[]]})
        with self.assertRaises(pipeline.LandingError):
            self.land(api, minutes=25)
        dispatches = [w for w in api.writes() if w[1] == 'dispatches']
        self.assertEqual(3, len(dispatches))

    def test_conflict_is_reported(self):
        with self.assertRaises(pipeline.LandingError):
            self.land(FakeGitHub([pr('a', 'dirty')], {}))

    def test_source_promotion_dispatches_the_store_publication_after_merge(self):
        api = FakeGitHub([pr('a', merged=True)], {})
        writes = self.land(api, publish_after=True)
        self.assertEqual([('POST', 'dispatches', {'ref': 'main', 'inputs': {
            'publish': 'true', 'force': 'false', 'channels': 'changed'}})], writes)


class StatusTests(unittest.TestCase):
    def fetch(self, url):
        if 'contents/' in url:
            return {'version': '1.0.5', 'image': 'ghcr.io/smokkelaar/nocturne-home-assistant/nocturne-test-b-{arch}'}
        if '/pulls?' in url:
            return [{'number': 9, 'html_url': 'https://example.invalid/9'}] if 'prebuilt-store' in url else []
        return {'workflow_runs': []}

    def status(self, expect, inspect=lambda *args, **kwargs: {}):
        lines = []
        clock = Clock()
        ready = pipeline.status(REPO, ['test-b'], expect, 0, clock.sleep, clock, self.fetch, inspect, lines.append)
        return ready, '\n'.join(lines)

    def test_expected_version_in_main_and_pullable_is_ready(self):
        ready, report = self.status({'test-b': '1.0.5'})
        self.assertTrue(ready)
        self.assertIn('IN STORE', report)
        self.assertIn('Controleren op updates', report)

    def test_unmerged_publication_is_not_ready_and_names_the_open_pr(self):
        ready, report = self.status({'test-b': '1.0.6'})
        self.assertFalse(ready)
        self.assertIn('expected 1.0.6', report)
        self.assertIn('Open PR #9', report)

    def test_private_or_missing_image_is_not_ready(self):
        def inspect(repository, version, arch, **kwargs):
            if arch == 'arm64':
                raise urllib.error.HTTPError('u', 401, 'unauthorized', {}, None)
            return {}
        ready, report = self.status({}, inspect)
        self.assertFalse(ready)
        self.assertIn('aarch64', report)

    def test_expect_accepts_package_names(self):
        self.assertEqual({'test-b': '1', 'official': '2'},
                         pipeline.parse_expect(['nocturne_test_b=1', 'nocturne_local=2']))


class RegistryRetryTests(unittest.TestCase):
    def test_transient_errors_retry_and_absence_does_not(self):
        calls = []

        def flaky(url, headers=None, expected=None):
            calls.append(url)
            if len(calls) < 3:
                raise urllib.error.HTTPError(url, 503, 'busy', {}, None)
            return {'ok': True}, 'sha256:x'
        original = registry._fetch
        registry._fetch = flaky
        try:
            self.assertEqual(({'ok': True}, 'sha256:x'), registry.fetch('u', sleep=lambda _: None))
            calls.clear()
            registry._fetch = lambda *a, **k: (_ for _ in ()).throw(urllib.error.HTTPError('u', 404, 'gone', {}, None))
            with self.assertRaises(urllib.error.HTTPError):
                registry.fetch('u', sleep=lambda _: calls.append('slept'))
            self.assertEqual([], calls)
        finally:
            registry._fetch = original


class WorkflowTests(unittest.TestCase):
    def test_every_automation_pr_is_landed_by_its_own_run(self):
        validate = (ROOT / '.github/workflows/validate.yml').read_text()
        self.assertIn('store_pipeline.py land --pr "$PR"', validate)
        self.assertIn('store_pipeline.py status --candidates', validate)
        for name in ('personal.yml', 'latest.yml'):
            workflow = (ROOT / '.github/workflows' / name).read_text()
            self.assertIn('--publish-after', workflow)
            self.assertIn('group: source-promotion', workflow)
        self.assertNotIn('store_pipeline', (ROOT / '.github/workflows/upstream.yml').read_text())

    def test_image_push_retries(self):
        native = (ROOT / '.github/workflows/native-prebuilt.yml').read_text()
        self.assertIn('docker push "$IMAGE" && exit 0', native)


if __name__ == '__main__':
    unittest.main()
