"""The shared command-line diagnostics stay read-only and local."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = ROOT / 'nocturne_latest/rootfs/opt/nocturne-ha/diagnostic_cli.py'
spec = importlib.util.spec_from_file_location('diagnostic_cli', CLI_PATH)
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


class DiagnosticCliTests(unittest.TestCase):
    def test_cli_is_packaged_and_invokable_for_every_channel(self):
        channels = ('nocturne_local', 'nocturne_latest', 'nocturne_personal',
                    'nocturne_test_a', 'nocturne_test_b', 'nocturne_test_c')
        script = CLI_PATH.read_bytes()
        for channel in channels:
            with self.subTest(channel=channel):
                root = ROOT / channel / 'rootfs'
                self.assertEqual(script, (root / 'opt/nocturne-ha/diagnostic_cli.py').read_bytes())
                self.assertTrue((root / 'usr/local/bin/nocturne-ha').is_file())
                dockerfile = (ROOT / channel / 'Dockerfile').read_text()
                self.assertIn('/usr/local/bin/nocturne-ha', dockerfile)

    def test_api_command_rejects_external_or_mutating_targets_before_connecting(self):
        for path in ('https://example.com/api/v3/version', '//example.com/api/v3/version',
                     '/api/../secrets', '/health', '/api/status\r\nHost: example.com'):
            with self.subTest(path=path), \
                    patch.object(cli, 'checked_options') as options, \
                    patch.object(cli.http.client, 'HTTPConnection') as connection:
                with self.assertRaises(ValueError):
                    cli.api_request(path)
                options.assert_not_called()
                connection.assert_not_called()

    def test_doctor_reports_invalid_configuration_without_exposing_its_values(self):
        with patch.object(cli, 'checked_options', side_effect=ValueError('secret-value')):
            result = cli.doctor()
        self.assertEqual('invalid', result['configuration'])
        self.assertNotIn('secret-value', str(result))


if __name__ == '__main__':
    unittest.main()
