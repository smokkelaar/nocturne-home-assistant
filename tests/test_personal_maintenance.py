import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'nocturne_personal/rootfs/opt/nocturne-ha'


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, file)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


cli = load('maintenance_cli', BASE / 'maintenance_cli.py')
entry = load('personal_entry', BASE / 'personal_entry.py')
settings = load('personal_maintenance_settings', BASE / 'settings.py')


class MaintenanceTests(unittest.TestCase):
    def test_disabled_requires_no_new_password_and_preserves_old_configuration(self):
        self.assertEqual((False, ''), entry.enabled_options({}))
        config = json.loads((ROOT / 'nocturne_personal/config.json').read_text())
        self.assertFalse(config['options']['maintenance_enabled'])
        self.assertEqual('', config['options']['maintenance_password'])
        self.assertEqual({'8448/tcp': 8450}, config['ports'])
        self.assertNotIn('docker_api', config)
        self.assertNotIn('host_pid', config)

    def test_password_validation_rejects_missing_short_and_control_characters(self):
        for password in ('', 'short', 'long-password-with\nnewline', 'x' * 257, None):
            with self.subTest(password_type=type(password).__name__):
                with self.assertRaises(ValueError):
                    entry.enabled_options({'maintenance_enabled': True, 'maintenance_password': password})
        self.assertEqual((True, 'a-valid-test-password'), entry.enabled_options(
            {'maintenance_enabled': True, 'maintenance_password': 'a-valid-test-password'}))
        with self.assertRaises(ValueError):
            entry.enabled_options({'maintenance_enabled': 'true'})

    def test_recovery_plan_keeps_settings_unchanged_and_requires_valid_https_host(self):
        original = {'public_url': 'https://old.example.net:8450'}
        with patch.object(cli, 'checked_options', settings.validate_options):
            plan = cli.recovery_plan(original, 'https://new.example.net:8450')
            self.assertEqual('https://new.example.net:8450/auth/recovery', plan['recovery_url'])
            self.assertEqual('https://old.example.net:8450', original['public_url'])
            for url in ('http://new.example.net', 'https://127.0.0.1', 'https://new.example.net/auth',
                        'https://name:password@new.example.net'):
                with self.subTest(url=url), self.assertRaises(ValueError):
                    cli.recovery_plan(original, url)

    def test_invalid_domain_diagnosis_never_returns_options_or_secrets(self):
        with patch.object(cli, 'checked_options', settings.validate_options):
            report = cli.doctor({'public_url': 'bad', 'maintenance_password': 'secret-value'})
        self.assertEqual('invalid', report['configuration'])
        self.assertNotIn('secret-value', json.dumps(report))

    def test_generic_api_rejects_nonlocal_paths_before_loading_credentials(self):
        for path in ('https://evil.example/api/v4/status', '//evil.example/api/',
                     '/other', '/api/../secret', '/api/status\r\nAuthorization: leak'):
            with self.subTest(path=path), patch.object(cli, 'options') as options:
                with self.assertRaises(ValueError):
                    cli.api_request(path, service=True)
                options.assert_not_called()

    def test_mutation_requires_explicit_write_before_any_http_request(self):
        with patch.object(cli, 'api_request') as api:
            with self.assertRaises(SystemExit):
                cli.main(['api', '/api/v4/test', '--method', 'DELETE'])
            api.assert_not_called()

    def test_proxy_enforces_network_and_password_for_terminal_including_websocket(self):
        config = entry.nginx_configuration('/maintenance/terminal/test-nonce')
        self.assertIn('allow 172.30.32.2;', config)
        self.assertIn('deny all;', config)
        self.assertEqual(2, config.count('auth_basic_user_file'))
        self.assertIn('proxy_pass http://127.0.0.1:8101;', config)
        self.assertIn('proxy_set_header Upgrade $http_upgrade;', config)
        self.assertNotIn('X-Forwarded-For', config)
        command = entry.terminal_command('/maintenance/terminal/test-nonce')
        self.assertIn('127.0.0.1', command)
        self.assertNotIn('-a', command)  # no client-supplied shell command arguments
        self.assertNotIn('-c', command)  # no password in process arguments

    def test_wizard_escapes_input_does_not_show_secret_and_uses_relative_ingress_links(self):
        raw = {'public_url': 'https://example.net', 'maintenance_password': 'hidden-test-secret'}
        with patch.object(entry, 'doctor', return_value={'api': 'stopped'}), \
             patch.object(entry, 'recovery_plan', return_value={'steps': ['Keep data'],
                         'recovery_url': 'https://example.net/auth/recovery'}):
            page = entry.wizard_page(raw, '/maintenance/terminal/test-nonce', lambda: 'stopped', '"><script>bad</script>')
        self.assertNotIn('hidden-test-secret', page)
        self.assertNotIn('<script>bad</script>', page)
        self.assertIn('href="terminal/test-nonce/"', page)
        self.assertIn('Nocturne-proces: stopped', page)


if __name__ == '__main__':
    unittest.main()
