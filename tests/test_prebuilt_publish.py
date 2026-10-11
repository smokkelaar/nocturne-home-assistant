"""Publication must preserve identities and fail closed before advertising images."""
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import subprocess
import unittest
from unittest.mock import patch
from awesomeversion import AwesomeVersion

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import prebuilt_publish as publisher
import update_personal
import update_test_channels
import update_latest
import update_upstream
from versioning import next_package


def inspected(repository, reference, arch, revision=None, labels=None):
    return {'digest': 'sha256:' + ('a' if arch == 'amd64' else 'b') * 64,
            'index': 'sha256:' + 'c' * 64, 'revision': revision, 'labels': labels or {}}


class PrebuiltTests(unittest.TestCase):
    def test_ci_only_edits_preserve_legacy_fingerprints_but_runtime_changes_do_not(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.fixture(root)
            def git(*args):
                return subprocess.check_output(['git', *args], cwd=root).decode().strip()
            git('init', '-q')
            git('add', '.')
            git('-c', 'user.name=CI', '-c', 'user.email=ci@example.invalid', 'commit', '-qm', 'published fixture')
            revision = git('rev-parse', 'HEAD')
            builder = (root / 'tools/prebuilt_publish.py').read_bytes()
            proof = {'wrapper_commit': revision, 'recipe': publisher.recipe_hash(root, 'nocturne_personal', builder)}
            (root / 'tools/prebuilt_publish.py').write_bytes(b'Changed orchestration only')
            self.assertTrue(publisher.recipe_matches(root, 'nocturne_personal', proof))
            runtime = root / 'nocturne_personal/rootfs/opt/nocturne-ha/version.json'
            runtime.write_bytes(runtime.read_bytes() + b' ')
            # JSON normalization ignores whitespace; a real runtime input must invalidate it.
            value = publisher.read(runtime)
            value['personal'] = '0.3.99'
            publisher.write(runtime, value)
            self.assertFalse(publisher.recipe_matches(root, 'nocturne_personal', proof))

    def test_explicit_channel_selections_build_one_four_or_six_channels(self):
        for selection, expected in [('personal', {'personal'}), ('official,latest,personal,test-c', {'official', 'latest', 'personal', 'test-c'}), ('all', set(publisher.CHANNELS))]:
            with self.subTest(selection=selection), tempfile.TemporaryDirectory() as temporary, patch.object(publisher.registry, 'image', side_effect=inspected):
                matrix = publisher.prepare(ROOT, Path(temporary), 'd' * 40, 1, 1, 'e' * 40, channels=selection)
                self.assertEqual(expected, {item['channel'] for item in matrix['include']})
                self.assertEqual(len(expected) * 2, len(matrix['include']))

    def test_invalid_channels_fail_before_network_access_or_creating_output(self):
        for selection in ('', 'personal,', 'all,personal', 'personal;echo', 'unknown'):
            with self.subTest(selection=selection), tempfile.TemporaryDirectory() as temporary, patch.object(publisher.registry, 'image') as image:
                target = Path(temporary) / 'candidate'
                with self.assertRaises(ValueError):
                    publisher.prepare(ROOT, target, 'd' * 40, 1, 1, 'e' * 40, channels=selection)
                image.assert_not_called()
                self.assertFalse(target.exists())

    def test_automatic_selection_builds_only_a_changed_channel_and_skips_docs(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(publisher.registry, 'image', side_effect=inspected):
            root = Path(temporary)
            self.fixture(root)
            for name in ('upstream.json', 'upstream-latest.json', 'upstream-personal.json'):
                shutil.copyfile(ROOT / name, root / name)
            first = root / 'work/first'
            publisher.prepare(root, first, 'd' * 40, 1, 1, 'e' * 40, channels='all')
            publisher.promote(root, first / 'candidates.json')
            (root / 'README.md').write_text('Documentation only')
            self.assertEqual([], publisher.prepare(root, root / 'work/none', 'f' * 40, 2, 1, 'e' * 40)['include'])
            runtime = root / 'nocturne_personal/rootfs/opt/nocturne-ha/version.json'
            value = publisher.read(runtime)
            value['personal'] = '0.3.99'
            publisher.write(runtime, value)
            matrix = publisher.prepare(root, root / 'work/personal', 'f' * 40, 2, 1, 'e' * 40)
            self.assertEqual(['personal', 'personal'], [item['channel'] for item in matrix['include']])

    def test_license_is_a_build_input_and_fingerprint_is_platform_independent(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.fixture(root)
            before = publisher.recipe_hash(root, 'nocturne_personal')
            (root / 'LICENSE').write_bytes((root / 'LICENSE').read_bytes() + b'\nSynthetic license notice\n')
            self.assertNotEqual(before, publisher.recipe_hash(root, 'nocturne_personal'))

    def test_large_plain_version_upgrades_every_legacy_variant_and_handles_retries(self):
        previous = ['0.1.13-1', '0.3.27-p1', '0.3.26-9', '0.3.26-a16', '0.3.25-b33', '0.3.25-c32']
        version = publisher.next_version(previous, 1, 1)
        self.assertEqual('1.0.101', version)
        for old in previous:
            self.assertGreater(AwesomeVersion(version), AwesomeVersion(old))
        self.assertGreater(AwesomeVersion(publisher.next_version([version], 1, 2)), AwesomeVersion(version))
        self.assertGreater(AwesomeVersion(publisher.next_version(['1.0.9001'], 1, 1)), AwesomeVersion('1.0.9001'))
        for candidate in ('1.0.101', '1.0.100', '1.0.102-p1', '01.0.102'):
            with self.assertRaises(ValueError):
                publisher.require_upgrade(candidate, version)
        self.assertEqual('1.0.102', next_package(ROOT, '1.0.101'))

    def test_prepare_builds_twelve_native_contexts_without_changing_the_store(self):
        before = {package: (ROOT / package / 'config.json').read_bytes() for package in publisher.CHANNELS.values()}
        with tempfile.TemporaryDirectory() as temporary, patch.object(publisher.registry, 'image', side_effect=inspected):
            target = Path(temporary)
            matrix = publisher.prepare(ROOT, target, 'd' * 40, 1, 1, 'e' * 40, force=True)
            self.assertEqual(12, len(matrix['include']))
            self.assertEqual({(channel, arch) for channel in publisher.CHANNELS for arch in publisher.PLATFORMS},
                             {(item['channel'], item['arch']) for item in matrix['include']})
            for item in matrix['include']:
                context = Path(item['context'])
                config = publisher.read(context / 'config.json')
                old = json.loads(before[item['package']])
                self.assertEqual(old['slug'], config['slug'])
                self.assertEqual(old['options'], config['options'])
                self.assertEqual(old['ports'], config['ports'])
                self.assertEqual(['amd64', 'aarch64'], config['arch'])
                self.assertIn('nocturne-' + item['channel'] + '-{arch}', config['image'])
                recipe = (context / 'Dockerfile').read_text()
                self.assertIn('ARG BUILD_ARCH=' + item['hass_arch'], recipe)
                if item['channel'] not in ('official', 'latest'):
                    self.assertIn('ARG DOTNET_RID=' + publisher.PLATFORMS[item['arch']]['rid'], recipe)
                    self.assertIn(publisher.read(ROOT / 'build-platforms.json')['sdk'][item['arch']], recipe)
            self.assertEqual(before, {package: (ROOT / package / 'config.json').read_bytes() for package in publisher.CHANNELS.values()})

    def fixture(self, target):
        for name in ('publication.json', 'build-platforms.json', 'LICENSE', 'wrapper.json',
                     'upstream-test-a.json', 'upstream-test-b.json', 'upstream-test-c.json'):
            shutil.copyfile(ROOT / name, target / name)
        (target / 'tools').mkdir()
        shutil.copyfile(ROOT / 'tools/prebuilt_publish.py', target / 'tools/prebuilt_publish.py')
        for package in publisher.CHANNELS.values():
            shutil.copytree(ROOT / package, target / package, ignore=shutil.ignore_patterns('__pycache__'))

    def test_failed_public_pull_never_changes_any_store_configuration(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.fixture(root)
            # Prepare uses approved source locks; copy those read-only inputs too.
            for name in ('upstream.json', 'upstream-latest.json', 'upstream-personal.json'):
                shutil.copyfile(ROOT / name, root / name)
            output = root / 'work/candidates'
            with patch.object(publisher.registry, 'image', side_effect=inspected):
                publisher.prepare(root, output, 'd' * 40, 1, 1, 'e' * 40, force=True)
            before = {package: (root / package / 'config.json').read_bytes() for package in publisher.CHANNELS.values()}
            def public_image(repository, reference, arch, *args, **kwargs):
                if arch == 'arm64':
                    raise ValueError('Anonymous ARM64 pull failed')
                return inspected(repository, reference, arch, *args, **kwargs)
            with patch.object(publisher.registry, 'image', side_effect=public_image), self.assertRaises(ValueError):
                publisher.promote(root, output / 'candidates.json')
            self.assertEqual(before, {package: (root / package / 'config.json').read_bytes() for package in publisher.CHANNELS.values()})

    def test_only_complete_public_images_are_promoted_and_recipe_does_not_loop(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.fixture(root)
            for name in ('upstream.json', 'upstream-latest.json', 'upstream-personal.json'):
                shutil.copyfile(ROOT / name, root / name)
            output = root / 'work/candidates'
            with patch.object(publisher.registry, 'image', side_effect=inspected):
                publisher.prepare(root, output, 'd' * 40, 1, 1, 'e' * 40, force=True)
                publisher.promote(root, output / 'candidates.json')
                matrix = publisher.prepare(root, root / 'work/next', 'f' * 40, 2, 1, 'e' * 40)
            self.assertEqual([], matrix['include'])
            for channel, package in publisher.CHANNELS.items():
                config = publisher.read(root / package / 'config.json')
                self.assertEqual(publisher.read(output / 'candidates.json')[channel]['version'], config['version'])
                self.assertEqual(publisher.image_name('smokkelaar/nocturne-home-assistant', channel), config['image'])
                self.assertEqual(config['version'], publisher.read(root / package / 'rootfs/opt/nocturne-ha/version.json')['package'])

    def test_store_or_source_race_prevents_promotion(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.fixture(root)
            for name in ('upstream.json', 'upstream-latest.json', 'upstream-personal.json'):
                shutil.copyfile(ROOT / name, root / name)
            with patch.object(publisher.registry, 'image', side_effect=inspected):
                publisher.prepare(root, root / 'work/candidates', 'd' * 40, 1, 1, 'e' * 40, force=True)
                config = publisher.read(root / 'nocturne_local/config.json')
                config['version'] = '1.0.100'
                publisher.write(root / 'nocturne_local/config.json', config)
                with self.assertRaisesRegex(ValueError, 'changed'):
                    publisher.promote(root, root / 'work/candidates/candidates.json')

    def test_generators_keep_each_own_image_after_publication(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.fixture(root)
            for name in ('upstream.json', 'upstream-latest.json', 'upstream-personal.json'):
                shutil.copyfile(ROOT / name, root / name)
            with patch.object(publisher.registry, 'image', side_effect=inspected):
                publisher.prepare(root, root / 'work/candidates', 'd' * 40, 1, 1, 'e' * 40, force=True)
                publisher.promote(root, root / 'work/candidates/candidates.json')
            for updater, lockfile, package in ((update_upstream, 'upstream.json', 'nocturne_local'),
                                              (update_latest, 'upstream-latest.json', 'nocturne_latest')):
                rendered = updater.render(root, publisher.read(root / lockfile), '1.0.102')
                for name, value in rendered.items():
                    self.assertEqual((root / name).read_bytes(), value.encode('utf-8'), name)
            with patch.object(update_personal, 'ROOT', root), patch.object(update_test_channels, 'ROOT', root):
                delivery = publisher.read(root / 'nocturne_personal/config.json')['version']
                generated = update_personal.files(publisher.read(root / 'upstream-personal.json'), delivery)
                for name, value in generated.items():
                    self.assertEqual((root / 'nocturne_personal' / name).read_bytes(), value, name)
                for name, value in update_test_channels.files().items():
                    self.assertEqual((root / name).read_bytes(), value, name)

    def test_unreleased_source_notes_receive_only_the_published_version(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.fixture(root)
            for name in ('upstream.json', 'upstream-latest.json', 'upstream-personal.json'):
                shutil.copyfile(ROOT / name, root / name)
            notes = root / 'nocturne_personal/CHANGELOG.md'
            notes.write_bytes(('## Unreleased source candidate\n\n- Second candidate\n\n## Unreleased source candidate\n\n- First candidate\n\n' + notes.read_text()).encode())
            with patch.object(publisher.registry, 'image', side_effect=inspected):
                publisher.prepare(root, root / 'work/candidates', 'd' * 40, 1, 1, 'e' * 40, force=True)
                publisher.promote(root, root / 'work/candidates/candidates.json')
            content = notes.read_text()
            self.assertNotIn('## Unreleased', content)
            self.assertIn('Second candidate', content)
            self.assertIn('First candidate', content)


if __name__ == '__main__':
    unittest.main()
