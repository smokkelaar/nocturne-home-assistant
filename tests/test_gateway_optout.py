"""All installable packages keep the same explicit, default-off wrapper opt-out."""
import ast
import http.client
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

from test_channels import load_settings

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import update_upstream
import update_latest
import update_personal
import update_test_channels

PACKAGES = ('nocturne_local', 'nocturne_latest', 'nocturne_personal',
            'nocturne_test_a', 'nocturne_test_b', 'nocturne_test_c')


def load_guard(package):
    tree = ast.parse((ROOT / package / 'rootfs/opt/nocturne-ha/run.py').read_text(encoding='utf-8'))
    guard = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and node.name == 'verify_native_auth')
    namespace = {'http': type('Http', (), {'client': http.client}), 'json': json}
    exec(compile(ast.Module(body=[guard], type_ignores=[]), '<gateway-guard>', 'exec'), namespace)
    return namespace['verify_native_auth']


class GatewayOptOutTests(unittest.TestCase):
    def options(self, settings, **extra):
        return settings.validate_options({'certificate': 'fullchain.pem', 'private_key': 'privkey.pem',
                                          'gateway_auth': False, **extra})

    def test_all_packages_default_to_protection_and_have_complete_labels(self):
        for package in PACKAGES:
            with self.subTest(package=package):
                settings = load_settings(package)
                self.assertFalse(settings.validate_options({})['skip_gateway_check'])
                config = json.loads((ROOT / package / 'config.json').read_text(encoding='utf-8'))
                self.assertFalse(config['options']['skip_gateway_check'])
                self.assertEqual('bool', config['schema']['skip_gateway_check'])
                common = json.loads((ROOT / 'nocturne_latest/config.json').read_text(encoding='utf-8'))
                shared_schema = {key: value for key, value in config['schema'].items()
                                 if package != 'nocturne_personal' or not key.startswith('maintenance_')}
                self.assertEqual(common['schema'], shared_schema)
                self.assertNotIn('verify_native_auth', config['options'])
                for locale in ('en', 'nl'):
                    labels = json.loads((ROOT / package / 'translations' / (locale + '.json')).read_text(encoding='utf-8'))
                    self.assertEqual(set(config['schema']), set(labels['configuration']))
                    self.assertTrue(labels['configuration']['skip_gateway_check']['description'])

    def test_each_package_rejects_anonymous_access_unless_explicitly_skipped(self):
        for package in PACKAGES:
            with self.subTest(package=package):
                settings = load_settings(package)
                guard = load_guard(package)
                connection = MagicMock()
                connection.getresponse.return_value.status = 200
                connection.getresponse.return_value.read.return_value = json.dumps({
                    'status': 'ok', 'runtimeState': 'loaded', 'anonymousReadAccess': True,
                }).encode()
                with patch.object(http.client, 'HTTPConnection', return_value=connection) as factory:
                    with self.assertRaisesRegex(ValueError, 'GATEWAY_AUTH'):
                        guard(self.options(settings))
                    factory.assert_called_once()
                with patch.object(http.client, 'HTTPConnection') as factory:
                    guard(self.options(settings, skip_gateway_check=True))
                    factory.assert_not_called()

    def test_skip_does_not_remove_enabled_gateway_or_change_nocturne_permissions(self):
        for package in PACKAGES:
            with self.subTest(package=package):
                settings = load_settings(package)
                options = self.options(settings, skip_gateway_check=True)
                default = self.options(settings)
                passwords = {field: 'synthetic-value' for field in settings.SECRET_FIELDS}
                self.assertEqual(settings.service_environments(default, passwords),
                                 settings.service_environments(options, passwords))
                self.assertEqual(settings.nginx_config(default, '/cert', '/key'),
                                 settings.nginx_config(options, '/cert', '/key'))
                enabled = self.options(settings, gateway_auth=True, skip_gateway_check=True)
                self.assertIn('auth_basic_user_file', settings.nginx_config(enabled, '/cert', '/key'))
                self.assertNotIn('GATEWAY_SKIPPED', settings.status_page(enabled, {}, 'fixture-code', False))
                connection = MagicMock()
                connection.getresponse.return_value.status = 200
                connection.getresponse.return_value.read.return_value = b'{}'
                with patch.object(http.client, 'HTTPConnection', return_value=connection) as factory:
                    with self.assertRaisesRegex(ValueError, 'GATEWAY_AUTH'):
                        load_guard(package)(enabled)
                    factory.assert_called_once()

    def test_skipped_status_is_prominent_and_does_not_force_login_or_show_gateway_code(self):
        for package in PACKAGES:
            with self.subTest(package=package):
                settings = load_settings(package)
                options = self.options(settings, skip_gateway_check=True)
                page = settings.status_page(options, {}, 'fixture-code', False)
                self.assertIn('GATEWAY_SKIPPED', page)
                self.assertIn('role="alert"', page)
                self.assertIn('Nocturne bepaalt de toegang', page)
                self.assertNotIn('Nocturne-aanmelding blijft verplicht', page)
                self.assertNotIn('fixture-code', page)
                self.assertIn(f'href="{options["public_url"]}"', page)
                self.assertNotIn(options['public_url'] + '/auth/login', page)

    def test_skip_requires_real_boolean_and_does_not_relax_tls_or_hostname_validation(self):
        for package in PACKAGES:
            settings = load_settings(package)
            for value in ('true', 'false', 0, 1, None, [], {}):
                with self.subTest(package=package, value=value), self.assertRaisesRegex(ValueError, 'skip_gateway_check'):
                    settings.validate_options({'skip_gateway_check': value})
            with self.subTest(package=package), self.assertRaisesRegex(ValueError, 'GATEWAY_TLS'):
                settings.validate_options({'gateway_auth': False, 'skip_gateway_check': True})
            with self.subTest(package=package), self.assertRaises(ValueError):
                self.options(settings, skip_gateway_check=True, public_url='https://127.0.0.1:8448')

    def test_test_a_migrates_raw_legacy_options_only_if_canonical_option_is_absent(self):
        settings = load_settings('nocturne_test_a')
        guard = load_guard('nocturne_test_a')
        for extra in ({'verify_native_auth': False},
                      {'skip_gateway_check': True, 'verify_native_auth': True},
                      {'skip_gateway_check': True, 'verify_native_auth': False}):
            with self.subTest(extra=extra):
                options = self.options(settings, **extra)
                self.assertNotIn('verify_native_auth', options)
                with patch.object(http.client, 'HTTPConnection') as connection:
                    guard(options)
                    connection.assert_not_called()
                self.assertIn('GATEWAY_SKIPPED', settings.status_page(options, {}, '', False))
        with patch.object(http.client, 'HTTPConnection') as connection:
            connection.return_value.getresponse.return_value.status = 200
            connection.return_value.getresponse.return_value.read.return_value = b'{}'
            with self.assertRaisesRegex(ValueError, 'GATEWAY_AUTH'):
                guard(self.options(settings, verify_native_auth=False, skip_gateway_check=False))
            connection.assert_called_once()

    def test_future_generated_package_configs_keep_the_canonical_default_off_option(self):
        generated = {}
        for tool, lock_name, package in (
            (update_upstream, 'upstream.json', 'nocturne_local'),
            (update_latest, 'upstream-latest.json', 'nocturne_latest'),
        ):
            lock = json.loads((ROOT / lock_name).read_text(encoding='utf-8'))
            version = json.loads((ROOT / package / 'config.json').read_text(encoding='utf-8'))['version']
            generated.update(tool.render(ROOT, lock, version))
        lock = json.loads((ROOT / 'upstream-personal.json').read_text(encoding='utf-8'))
        version = json.loads((ROOT / 'nocturne_personal/config.json').read_text(encoding='utf-8'))['version']
        generated['nocturne_personal/config.json'] = update_personal.files(lock, version)['config.json']
        generated.update(update_test_channels.files())
        for package in PACKAGES:
            with self.subTest(package=package):
                config = json.loads(generated[package + '/config.json'])
                self.assertFalse(config['options']['skip_gateway_check'])
                self.assertEqual('bool', config['schema']['skip_gateway_check'])


if __name__ == '__main__':
    unittest.main()
