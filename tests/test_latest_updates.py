"""Offline tests for the daily, digest-pinned Latest promotion."""
import copy
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('update_latest', ROOT / 'tools/update_latest.py')
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)


class LatestUpdateTests(unittest.TestCase):
    def setUp(self):
        self.lock = json.loads((ROOT / 'upstream-latest.json').read_text())

    def candidate(self):
        value = copy.deepcopy(self.lock)
        value['commit'] = 'b' * 40
        value['workflow_run'] += 1
        value['published_at'] = '2026-09-01T06:53:00Z'
        value['api']['digest'] = 'sha256:' + 'c' * 64
        value['web']['digest'] = 'sha256:' + 'd' * 64
        return value

    def fixture(self, directory):
        root = Path(directory)
        for name in ['config.json', 'Dockerfile', 'CHANGELOG.md']:
            target = root / 'nocturne_latest' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / 'nocturne_latest' / name, target)
        version = root / 'nocturne_latest/rootfs/opt/nocturne-ha/version.json'
        version.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / 'nocturne_latest/rootfs/opt/nocturne-ha/version.json', version)
        (root / 'upstream-latest.json').write_text(json.dumps(self.lock))
        return root

    def test_lock_rejects_floating_or_malformed_provenance(self):
        mutations = [('channel', 'dev'), ('commit', 'short'), ('workflow_run', 0),
                     ('published_at', 'yesterday')]
        for field, value in mutations:
            lock = copy.deepcopy(self.lock)
            lock[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                updater.validate_lock(lock)
        lock = copy.deepcopy(self.lock)
        lock['api']['tag'] = 'main'
        with self.assertRaises(ValueError):
            updater.validate_lock(lock)

    def test_generated_metadata_matches_both_digests_and_commit(self):
        version = json.loads((ROOT / 'nocturne_latest/config.json').read_text())['version']
        for name, expected in updater.render(ROOT, self.lock, version).items():
            actual = (ROOT / name).read_text()
            self.assertEqual(json.loads(expected), json.loads(actual)) if name.endswith('.json') else self.assertEqual(expected, actual)

    def test_update_bumps_only_latest_wrapper_and_preserves_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.fixture(directory)
            original = json.loads((root / 'nocturne_latest/config.json').read_text())
            version = updater.apply_update(root, self.lock, self.candidate())
            config = json.loads((root / 'nocturne_latest/config.json').read_text())
            self.assertEqual(version, config['version'])
            self.assertEqual('nocturne_latest', config['slug'])
            self.assertEqual(original['options'], config['options'])
            self.assertIn(self.candidate()['commit'][:7], (root / 'nocturne_latest/CHANGELOG.md').read_text())

    def test_unchanged_commit_and_invalid_dockerfile_write_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.fixture(directory)
            before = (root / 'upstream-latest.json').read_bytes()
            with self.assertRaises(ValueError):
                updater.apply_update(root, self.lock, self.lock)
            (root / 'nocturne_latest/Dockerfile').write_text('FROM latest\n')
            with self.assertRaises(ValueError):
                updater.apply_update(root, self.lock, self.candidate())
            self.assertEqual(before, (root / 'upstream-latest.json').read_bytes())

    def test_digest_mismatch_is_rejected(self):
        class Response(io.BytesIO):
            headers = {'Docker-Content-Digest': 'sha256:' + 'f' * 64}
        with patch.object(updater.urllib.request, 'urlopen', return_value=Response(b'{}')):
            with self.assertRaisesRegex(ValueError, 'digest mismatch'):
                updater.fetch('https://ghcr.io/example')

    def test_build_job_must_succeed_for_the_exact_commit(self):
        commit = 'a' * 40
        runs = {'workflow_runs': [{'id': 7, 'head_sha': commit, 'status': 'completed'}]}
        with patch.object(updater, 'github', side_effect=[runs, {'jobs': [
                {'name': 'build-and-push', 'conclusion': 'failure'}]}]):
            with self.assertRaises(updater.NotReady):
                updater.successful_build(commit)
        with patch.object(updater, 'github', side_effect=[runs, {'jobs': [
                {'name': 'build-and-push', 'conclusion': 'success'}]}]):
            self.assertEqual(7, updater.successful_build(commit)['id'])

    def test_resolver_pins_the_inspected_amd64_manifest_not_parent_index(self):
        commit = 'a' * 40
        selected = 'sha256:' + '1' * 64
        parent = 'sha256:' + '2' * 64
        config_digest = 'sha256:' + '3' * 64
        responses = [
            ({'token': 'test'}, 'unused'),
            ({'manifests': [{'digest': selected, 'platform': {
                'os': 'linux', 'architecture': 'amd64'}}]}, parent),
            ({'config': {'digest': config_digest}}, selected),
            ({'os': 'linux', 'architecture': 'amd64', 'config': {
                'Env': ['GIT_COMMIT=' + commit]}}, config_digest),
        ]
        with patch.object(updater, 'fetch', side_effect=responses):
            self.assertEqual(selected, updater.resolve_image('api', commit)['digest'])


if __name__ == '__main__':
    unittest.main()
