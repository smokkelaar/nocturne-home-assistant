"""The Official and Latest apps must remain selectable and isolated."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_settings(package):
    path = ROOT / package / 'rootfs/opt/nocturne-ha/settings.py'
    spec = importlib.util.spec_from_file_location('settings_' + package, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ChannelTests(unittest.TestCase):
    def setUp(self):
        self.official = json.loads((ROOT / 'nocturne_local/config.json').read_text())
        self.latest = json.loads((ROOT / 'nocturne_latest/config.json').read_text())

    def test_two_distinct_store_entries_and_data_identities(self):
        self.assertEqual('Nocturne Official Release', self.official['name'])
        self.assertEqual('Nocturne Latest Release', self.latest['name'])
        self.assertEqual('nocturne_local', self.official['slug'])  # Existing data/update identity.
        self.assertEqual('nocturne_latest', self.latest['slug'])
        self.assertNotEqual(self.official['slug'], self.latest['slug'])
        self.assertEqual({'8448/tcp': 8448}, self.official['ports'])
        self.assertEqual({'8448/tcp': 8449}, self.latest['ports'])
        self.assertNotEqual(self.official['options']['public_url'], self.latest['options']['public_url'])

    def test_both_channels_have_one_shared_functional_wrapper_version(self):
        wrapper = json.loads((ROOT / 'wrapper.json').read_text())['version']
        for package, manifest in (('nocturne_local', self.official), ('nocturne_latest', self.latest)):
            runtime = json.loads((ROOT / package / 'rootfs/opt/nocturne-ha/version.json').read_text())
            self.assertEqual(wrapper, runtime['app'])
            self.assertEqual(manifest['version'], runtime['package'])
            self.assertRegex(runtime['package'], '^' + wrapper.replace('.', r'\.') + r'-[1-9]\d*$')
            self.assertIn('HA wrapper ' + wrapper, manifest['description'])

    def test_latest_uses_only_immutable_image_references(self):
        dockerfile = (ROOT / 'nocturne_latest/Dockerfile').read_text()
        images = [line for line in dockerfile.splitlines() if line.startswith('FROM ')]
        self.assertEqual(3, len(images))
        for image in images:
            self.assertIn('@sha256:', image)
            self.assertNotRegex(image, r':latest(?:\s|$)')
        lock = json.loads((ROOT / 'upstream-latest.json').read_text())
        self.assertEqual({'latest'}, {lock[kind]['tag'] for kind in ('api', 'web')})
        for kind in ('api', 'web'):
            self.assertIn('@' + lock[kind]['digest'], dockerfile)

    def test_shared_wrapper_security_code_stays_identical(self):
        common = [
            'build/check_web.mjs', 'build/prepare_web.py',
            'rootfs/opt/nocturne-ha/bootstrap.sql', 'rootfs/opt/nocturne-ha/run.py',
            'rootfs/opt/nocturne-ha/settings.py', 'rootfs/opt/nocturne-ha/tls.py',
            'translations/nl.json', 'translations/en.json',
        ]
        for relative in common:
            with self.subTest(file=relative):
                self.assertEqual((ROOT / 'nocturne_local' / relative).read_bytes(),
                                 (ROOT / 'nocturne_latest' / relative).read_bytes())

    def test_each_status_page_names_its_channel(self):
        for package, name, port in [('nocturne_local', 'Nocturne Official Release', 8448),
                                    ('nocturne_latest', 'Nocturne Latest Release', 8449)]:
            settings = load_settings(package)
            options = settings.validate_options({})
            self.assertEqual(f'https://homeassistant.local:{port}', options['public_url'])
            page = settings.status_page(options, {}, '', True)
            self.assertIn('<h1>' + name + '</h1>', page)

    def test_latest_never_inherits_official_identity_or_default_port(self):
        serialized = json.dumps(self.latest)
        self.assertNotIn('"slug": "nocturne_local"', serialized)
        self.assertNotEqual(8448, self.latest['ports']['8448/tcp'])
        self.assertTrue(self.latest['options']['public_url'].endswith(':8449'))

    def test_automation_policies_are_channel_specific(self):
        official = (ROOT / '.github/workflows/upstream.yml').read_text()
        latest = (ROOT / '.github/workflows/latest.yml').read_text()
        self.assertNotIn('schedule:', official)
        self.assertNotIn('gh pr merge', official)
        self.assertIn('workflow_dispatch:', official)
        self.assertIn("cron: '53 6 * * *'", latest)
        self.assertIn('gh workflow run validate.yml', latest)
        self.assertIn('gh pr merge "$PROPOSAL_NUMBER" --auto --squash', latest)
        self.assertNotIn('nocturne_local/', latest.split('add-paths:', 1)[1])
        self.assertIn('nocturne_latest/config.json', latest)

    def test_channel_documentation_names_both_choices(self):
        install = (ROOT / 'docs/INSTALLATIE.md').read_text()
        channels = (ROOT / 'docs/CHANNELS.md').read_text()
        for name in ('Nocturne Official Release', 'Nocturne Latest Release'):
            self.assertIn(name, install)
            self.assertIn(name, channels)

    def test_ha_option_labels_cover_exactly_the_supported_schema(self):
        for package in ('nocturne_local', 'nocturne_latest'):
            schema = json.loads((ROOT / package / 'config.json').read_text())['schema']
            for language in ('nl', 'en'):
                translation = json.loads((ROOT / package / 'translations' / (language + '.json')).read_text(encoding='utf-8'))
                self.assertEqual(set(schema), set(translation['configuration']))
                for entry in translation['configuration'].values():
                    self.assertTrue(entry['name'])
                    self.assertTrue(entry['description'])


if __name__ == '__main__':
    unittest.main()
