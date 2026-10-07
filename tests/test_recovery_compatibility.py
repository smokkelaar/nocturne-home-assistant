import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'tools/personal-maintenance/rootfs/opt/nocturne-ha'
sys.path.insert(0, str(BASE))
import recovery_compatibility as compatibility


class RecoveryCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.rules = compatibility.contracts()
        self.rule = self.rules['profiles'][0]
        self.version = {'repository': 'smokkelaar/nocturne-personal', 'source_commit': 'a' * 40}
        self.binary = hashlib.sha256(b'synthetic-api-binary').hexdigest()

    def manifest(self):
        return compatibility.build_manifest(self.version, self.rules, self.rule['hashes'], self.binary)

    def test_new_unlisted_commit_with_unchanged_contract_is_accepted(self):
        manifest = self.manifest()
        self.assertTrue(manifest['compatible'])
        self.assertEqual(self.rule['kind'], compatibility.verify_manifest(self.version, manifest, self.rules, self.binary))
        self.assertNotIn('a' * 40, {rule['reviewed_commit'] for rule in self.rules['profiles']})

    def test_changed_critical_source_blocks_only_owner_recovery(self):
        hashes = {**self.rule['hashes'], self.rules['files'][0]: 'b' * 64}
        manifest = compatibility.build_manifest(self.version, self.rules, hashes, self.binary)
        self.assertFalse(manifest['compatible'])
        with self.assertRaises(ValueError):
            compatibility.verify_manifest(self.version, manifest, self.rules, self.binary)

    def test_copied_manifest_changed_api_or_forged_profile_is_rejected(self):
        for field, value in [('source_commit', 'b' * 40), ('repository', 'nightscout/nocturne'),
                             ('api_sha256', 'c' * 64), ('compatible', False), ('profile', 'unknown')]:
            manifest = {**self.manifest(), field: value}
            with self.subTest(field=field), self.assertRaises(ValueError):
                compatibility.verify_manifest(self.version, manifest, self.rules, self.binary)

    def test_missing_manifest_disables_recovery_without_runtime_network(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            (base / 'version.json').write_text(json.dumps(self.version))
            with patch.object(compatibility, 'BASE', base), \
                 patch.object(compatibility.urllib.request, 'urlopen') as network:
                self.assertFalse(compatibility.report()['compatible'])
                network.assert_not_called()

    def test_partial_contract_or_arbitrary_repository_cannot_enable_recovery(self):
        manifest = self.manifest()
        manifest['source_hashes'] = dict(list(self.rule['hashes'].items())[:-1])
        with self.assertRaises(ValueError):
            compatibility.verify_manifest(self.version, manifest, self.rules, self.binary)
        with self.assertRaises(ValueError):
            compatibility.identity({**self.version, 'repository': 'someone/else'})

    def test_actual_source_changes_are_detected_but_unrelated_files_do_not_matter(self):
        rules = {'files': ['auth/Recovery.cs'], 'profiles': []}
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source / 'auth').mkdir()
            (source / 'auth/Recovery.cs').write_bytes(b'reviewed native recovery')
            original = compatibility.source_hashes(self.version, rules, source)
            (source / 'new-ui-test.txt').write_bytes(b'unrelated experiment')
            self.assertEqual(original, compatibility.source_hashes(self.version, rules, source))
            (source / 'auth/Recovery.cs').write_bytes(b'changed native recovery')
            self.assertNotEqual(original, compatibility.source_hashes(self.version, rules, source))

    def test_native_dependency_change_invalidates_the_build_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            api = base / 'Nocturne.API.dll'
            api.write_bytes(b'api')
            data = base / 'Nocturne.Infrastructure.Data.dll'
            data.write_bytes(b'old schema assembly')
            with patch.object(compatibility, 'API', api):
                before = compatibility.binary_hash()
                data.write_bytes(b'new schema assembly')
                self.assertNotEqual(before, compatibility.binary_hash())

    def test_all_packages_build_the_manifest_after_copying_binary_and_metadata(self):
        for package in ('nocturne_local', 'nocturne_latest', 'nocturne_personal', 'nocturne_test_a', 'nocturne_test_b', 'nocturne_test_c'):
            with self.subTest(package=package):
                recipe = (ROOT / package / 'Dockerfile').read_text()
                self.assertLess(recipe.index('COPY rootfs/ /'), recipe.index('RUN python3 /opt/nocturne-ha/recovery_compatibility.py'))
                version = json.loads((ROOT / package / 'rootfs/opt/nocturne-ha/version.json').read_text())
                compatibility.identity(version)


if __name__ == '__main__':
    unittest.main()
