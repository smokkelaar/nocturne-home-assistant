"""Publication must preserve identities and fail closed before advertising images."""
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
from awesomeversion import AwesomeVersion

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import prebuilt_publish as publisher
from versioning import next_package


def inspected(repository, reference, arch, revision=None, labels=None):
    return {'digest': 'sha256:' + ('a' if arch == 'amd64' else 'b') * 64,
            'index': 'sha256:' + 'c' * 64, 'revision': revision, 'labels': labels or {}}


class PrebuiltTests(unittest.TestCase):
    def test_large_plain_version_upgrades_every_legacy_variant_and_handles_retries(self):
        previous = [json.loads((ROOT / package / 'config.json').read_text())['version']
                    for package in publisher.CHANNELS.values()]
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
        for name in ('publication.json', 'build-platforms.json', 'LICENSE'):
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
                self.assertEqual('1.0.101', config['version'])
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


if __name__ == '__main__':
    unittest.main()
