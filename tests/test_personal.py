"""Personal must not change existing HA app identities or silently use stock code."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import update_personal as updater


class PersonalTests(unittest.TestCase):
    def setUp(self):
        self.lock = json.loads((ROOT / 'upstream-personal.json').read_text())
        self.directory = ROOT / 'nocturne_personal'
        self.config = json.loads((self.directory / 'config.json').read_text())

    def test_generated_package_matches_exact_source_and_recipe(self):
        updater.check()

    def test_three_distinct_data_and_network_identities(self):
        all_configs = [json.loads((ROOT / package / 'config.json').read_text())
                       for package in ('nocturne_local', 'nocturne_latest', 'nocturne_personal')]
        self.assertEqual(3, len({entry['slug'] for entry in all_configs}))
        self.assertEqual([8448, 8449, 8450], [entry['ports']['8448/tcp'] for entry in all_configs])
        self.assertEqual('Nocturne Personal Release', self.config['name'])
        self.assertEqual('nocturne_personal', self.config['slug'])
        self.assertTrue(self.config['options']['gateway_auth'])
        self.assertEqual('cold', self.config['backup'])
        self.assertNotIn('host_network', self.config)

    def test_personal_source_replaces_both_api_and_web(self):
        recipe = (self.directory / 'Dockerfile').read_text()
        self.assertIn('dotnet publish', recipe)
        self.assertIn('pnpm --filter @nocturne/app run build', recipe)
        self.assertIn('COPY --from=source /out/api/ /app/', recipe)
        self.assertIn('COPY --from=source /out/web/ /opt/nocturne-web/', recipe)
        self.assertIn(self.lock['commit'], recipe)
        self.assertIn('--checksum=sha256:' + self.lock['archive_sha256'], recipe)
        self.assertNotIn(':latest', recipe)
        for line in recipe.splitlines():
            if line.startswith('FROM '):
                self.assertIn('@sha256:', line)

    def test_settings_use_only_the_fixed_personal_namespace(self):
        path = self.directory / 'rootfs/opt/nocturne-ha/settings.py'
        spec = importlib.util.spec_from_file_location('personal_settings_test', path)
        settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(settings)
        options = settings.validate_options({'cookie_namespace': 'NocturneOfficial_'})
        self.assertEqual('NocturnePersonal_', options['cookie_namespace'])
        self.assertEqual('https://homeassistant.local:8450', options['public_url'])
        page = settings.status_page(options, {}, '', True)
        self.assertIn('Nocturne Personal Release', page)
        self.assertIn('Personal ' + self.lock['version'], page)
        self.assertIn(self.lock['commit'][:12], page)
        options['cookie_namespace'] = 'NocturneLatest_'
        with self.assertRaises(ValueError):
            settings.nginx_config(options, '/cert', '/key')

    def test_lock_rejects_mutable_refs_and_foreign_sources(self):
        for field, value in [('repository', 'someone/else'), ('commit', 'personal'),
                             ('archive_sha256', 'wrong'), ('version', 'latest')]:
            lock = {**self.lock, field: value}
            with self.assertRaises(ValueError):
                updater.validate(lock)

    def test_updater_does_not_write_existing_packages(self):
        source = (ROOT / 'tools/update_personal.py').read_text()
        self.assertNotIn("ROOT / 'nocturne_local'", source)
        self.assertIn("directory = ROOT / 'nocturne_personal'", source)
        workflow = (ROOT / '.github/workflows/personal.yml').read_text()
        allowlist = workflow.split('add-paths:', 1)[1].split('body:', 1)[0]
        self.assertNotIn('nocturne_latest', allowlist)
        self.assertNotIn('nocturne_local', allowlist)
        self.assertIn('upstream-personal.json', allowlist)


if __name__ == '__main__':
    unittest.main()
