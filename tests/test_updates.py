"""Offline updater tests; no GitHub writes or registry traffic."""
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
spec = importlib.util.spec_from_file_location('update_upstream', ROOT / 'tools/update_upstream.py')
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.lock = json.loads((ROOT / 'upstream.json').read_text())

    def candidate(self):
        value = copy.deepcopy(self.lock)
        major, minor, patch_version = updater.semver(value['version'])
        value['version'] = f'{major}.{minor}.{patch_version + 1}'
        value['tag'] = 'v' + value['version']
        for kind in ('api', 'web'):
            value[kind] = {'tag': value['version'], 'digest': 'sha256:' + ('a' if kind == 'api' else 'b') * 64}
        return value

    def test_numeric_semver_order_not_string_order(self):
        self.assertGreater(updater.semver('0.2.10'), updater.semver('0.2.9'))

    def test_reject_prerelease_draft_and_untrusted_tags(self):
        for release in [dict(tag_name='v0.3.0-rc1'), dict(tag_name='v0.3.0', prerelease=True),
                        dict(tag_name='v0.3.0', draft=True), dict(tag_name='v0.3.0;echo bad'),
                        dict(tag_name='v0.3'), dict(tag_name='v01.2.3')]:
            with self.subTest(release=release), self.assertRaises(ValueError):
                updater.release_version(release)

    def test_reject_mixed_image_versions_and_invalid_hashes(self):
        for kind, field, value in [('api', 'tag', 'latest'), ('web', 'tag', '0.0.1'),
                                   ('api', 'digest', 'sha256:not-a-hash')]:
            lock = copy.deepcopy(self.lock)
            lock[kind][field] = value
            with self.assertRaises(ValueError):
                updater.validate_lock(lock)

    def test_all_generated_metadata_agrees(self):
        version = json.loads((ROOT / 'nocturne_local/config.json').read_text())['version']
        for name, expected in updater.render(ROOT, self.lock, version).items():
            actual = (ROOT / name).read_text()
            self.assertEqual(json.loads(expected), json.loads(actual)) if name.endswith('.json') else self.assertEqual(expected, actual)

    def fixture(self, directory):
        root = Path(directory)
        for name in ['config.json', 'Dockerfile', 'CHANGELOG.md']:
            target = root / 'nocturne_local' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / 'nocturne_local' / name, target)
        (root / 'nocturne_local/rootfs/opt/nocturne-ha').mkdir(parents=True)
        (root / 'upstream.json').write_text(json.dumps(self.lock))
        return root

    def test_update_bumps_wrapper_and_preserves_options(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.fixture(directory)
            original = json.loads((root / 'nocturne_local/config.json').read_text())
            version = updater.apply_update(root, self.lock, self.candidate())
            config = json.loads((root / 'nocturne_local/config.json').read_text())
            self.assertEqual(version, config['version'])
            self.assertNotEqual(original['version'], config['version'])
            self.assertEqual(original['options'], config['options'])
            self.assertEqual(original['slug'], config['slug'])
            self.assertIn(version, (root / 'nocturne_local/CHANGELOG.md').read_text())

    def test_same_version_retag_and_downgrade_cannot_change_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.fixture(directory)
            before = (root / 'nocturne_local/config.json').read_bytes()
            with self.assertRaises(ValueError):
                updater.apply_update(root, self.lock, self.lock)
            older = self.candidate()
            older['version'], older['tag'] = '0.0.1', 'v0.0.1'
            for kind in ('api', 'web'):
                older[kind]['tag'] = '0.0.1'
            with self.assertRaises(ValueError):
                updater.apply_update(root, self.lock, older)
            self.assertEqual(before, (root / 'nocturne_local/config.json').read_bytes())

    def test_signature_failure_writes_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.fixture(directory)
            dockerfile = root / 'nocturne_local/Dockerfile'
            dockerfile.write_text('FROM unknown:latest\n')
            before = (root / 'upstream.json').read_bytes()
            with self.assertRaises(ValueError):
                updater.apply_update(root, self.lock, self.candidate())
            self.assertEqual(before, (root / 'upstream.json').read_bytes())

    def test_digest_mismatch_is_rejected(self):
        class Response(io.BytesIO):
            headers = {'Docker-Content-Digest': 'sha256:' + 'f' * 64}
        with patch.object(updater.urllib.request, 'urlopen', return_value=Response(b'{}')):
            with self.assertRaisesRegex(ValueError, 'digest mismatch'):
                updater.fetch('https://ghcr.io/example')

    def test_registry_requires_amd64_and_matching_api_source(self):
        manifest = {'config': {'digest': 'sha256:' + 'a' * 64}}
        config = {'architecture': 'amd64', 'os': 'linux', 'config': {'Env': ['GIT_COMMIT=' + self.lock['commit']]}}
        for invalid in ['architecture', 'revision', None]:
            candidate = copy.deepcopy(config)
            if invalid == 'architecture': candidate['architecture'] = 'arm64'
            if invalid == 'revision': candidate['config']['Env'] = []
            sequence = [({'token': 'temporary-fixture-token'}, ''), (manifest, 'sha256:' + 'b' * 64), (candidate, '')]
            with patch.object(updater, 'fetch', side_effect=sequence):
                if invalid:
                    with self.assertRaises(ValueError):
                        updater.resolve_image('api', self.lock['version'], self.lock['commit'])
                else:
                    self.assertEqual(self.lock['version'], updater.resolve_image('api', self.lock['version'], self.lock['commit'])['tag'])


if __name__ == '__main__':
    unittest.main()
