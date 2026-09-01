"""Opt-in removal of HTTP Basic must preserve Nocturne's own authentication."""
import ast
import http.client
import importlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / 'nocturne_local/rootfs/opt/nocturne-ha'
sys.path.insert(0, str(CODE))
settings = importlib.import_module('settings')
runtime = importlib.import_module('run')


class NativeGatewayTests(unittest.TestCase):
    def setUp(self):
        self.options = settings.validate_options({
            'public_url': 'https://nocturne.example.net:8448',
            'certificate': 'fullchain.pem', 'private_key': 'privkey.pem', 'gateway_auth': False,
        })
        self.status = {'status': 'ok', 'anonymousReadAccess': False, 'isDemo': False,
                       'settings': {'requireAuthentication': False}, 'runtimeState': 'loaded'}

    def test_old_options_keep_basic_auth_by_default(self):
        options = settings.validate_options({})
        self.assertIs(True, options['gateway_auth'])
        self.assertIn('auth_basic_user_file', settings.nginx_config(options, 'cert', 'key'))
        manifest = json.loads((ROOT / 'nocturne_local/config.json').read_text())
        self.assertIs(True, manifest['options']['gateway_auth'])
        self.assertEqual('bool', manifest['schema']['gateway_auth'])

    def test_boolean_must_be_explicit_and_certificates_configured(self):
        for value in ('false', 0, 1, None, [], {}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                settings.validate_options({**self.options, 'gateway_auth': value})
        with self.assertRaisesRegex(ValueError, 'GATEWAY_TLS'):
            settings.validate_options({'gateway_auth': False})

    def test_both_modes_use_native_upstream_authorization_in_production(self):
        passwords = {key: '0' * 64 for key in settings.SECRET_FIELDS}
        api, web = settings.service_environments(self.options, passwords)
        self.assertNotIn('Security__RequireAuthentication', api)
        self.assertEqual('Production', api['ASPNETCORE_ENVIRONMENT'])
        self.assertEqual('production', web['NODE_ENV'])
        normal_api, _ = settings.service_environments(settings.validate_options({}), passwords)
        self.assertNotIn('Security__RequireAuthentication', normal_api)

    def test_native_nginx_removes_only_basic_and_restricts_hostname(self):
        config = settings.nginx_config(self.options, 'cert', 'key')
        self.assertIn('auth_basic off;', config)
        self.assertNotIn('auth_basic_user_file', config)
        self.assertIn('if ($host != "nocturne.example.net") { return 421; }', config)
        for header in ('Authorization', 'X-Instance-Key', 'X-Instance-Service'):
            self.assertIn(f'proxy_set_header {header} "";', config)
        self.assertIn('listen 8448 ssl;', config)
        self.assertIn('ssl_protocols TLSv1.2 TLSv1.3;', config)
        self.assertIn('location ^~ /api/v4/dev-only { return 404; }', config)
        self.assertNotIn('satisfy any', config)

    def test_status_does_not_display_unused_gateway_secret(self):
        page = settings.status_page(self.options, {}, 'fictional-gateway-secret', False)
        self.assertNotIn('fictional-gateway-secret', page)
        self.assertNotIn('Toegangscode voor deze lokale test tonen', page)
        self.assertIn('Geen extra gatewaycode nodig', page)
        self.assertIn('Nocturne-aanmelding blijft verplicht', page)
        self.assertIn('href="https://nocturne.example.net:8448/auth/login"', page)

    def connections(self, payload=None, status_code=200, protected_code=401):
        status, protected = MagicMock(), MagicMock()
        response = status.getresponse.return_value
        response.status = status_code
        response.read.return_value = json.dumps(self.status).encode() if payload is None else payload
        protected.getresponse.return_value.status = protected_code
        return status, protected

    def test_native_guard_accepts_private_instance_despite_false_legacy_flag(self):
        status, protected = self.connections()
        with patch.object(runtime.http.client, 'HTTPConnection', side_effect=[status, protected]) as factory:
            runtime.verify_native_auth(self.options)
            self.assertEqual(2, factory.call_count)
            for call in factory.call_args_list:
                self.assertEqual(('127.0.0.1', 8080), call.args)
                self.assertEqual({'timeout': 3}, call.kwargs)
            self.assertEqual('/api/v4/status', status.request.call_args.args[1])
            self.assertEqual('/api/v4/ChartData/dashboard', protected.request.call_args.args[1])
            for connection in (status, protected):
                self.assertEqual({'Host', 'X-Forwarded-Host', 'X-Forwarded-Proto'},
                                 set(connection.request.call_args.kwargs['headers']))
                connection.close.assert_called_once()
            status.getresponse.return_value.read.assert_called_once_with(65537)
            protected.getresponse.return_value.read.assert_not_called()

    def test_unavailable_status_stays_closed_with_http_code(self):
        for code in (301, 401, 404, 500, 503):
            with self.subTest(code=code):
                status, protected = self.connections(status_code=code)
                with patch.object(runtime.http.client, 'HTTPConnection', return_value=status) as factory:
                    with self.assertRaisesRegex(ValueError, f'GATEWAY_STATUS:.*HTTP {code}'):
                        runtime.verify_native_auth(self.options)
                    factory.assert_called_once()
                    status.close.assert_called_once()
                    status.getresponse.return_value.read.assert_called_once_with(65537)

    def test_setup_and_recovery_have_actionable_errors_without_raw_data(self):
        for code, payload, error in (
            (200, {'status': 'setup_required'}, 'GATEWAY_SETUP'),
            (503, {'setupRequired': True}, 'GATEWAY_SETUP'),
            (503, {'error': 'setup_required'}, 'GATEWAY_SETUP'),
            (503, {'recoveryMode': True}, 'GATEWAY_RECOVERY'),
            (503, {'error': 'recovery_mode_active'}, 'GATEWAY_RECOVERY'),
        ):
            with self.subTest(code=code, payload=payload):
                status, _ = self.connections(status_code=code, payload=json.dumps(payload).encode())
                with patch.object(runtime.http.client, 'HTTPConnection', return_value=status):
                    with self.assertRaisesRegex(ValueError, error + ':.*gateway_auth: true'):
                        runtime.verify_native_auth(self.options)

    def test_non_json_error_keeps_http_code_without_body(self):
        for code in (301, 500, 503):
            for payload in (b'<html>private backend error</html>', b'', b'\xff', b'[]', b'x' * 65537):
                with self.subTest(code=code, payload=payload[:20]):
                    status, _ = self.connections(status_code=code, payload=payload)
                    with patch.object(runtime.http.client, 'HTTPConnection', return_value=status):
                        with self.assertRaisesRegex(ValueError, f'GATEWAY_STATUS:.*HTTP {code}') as caught:
                            runtime.verify_native_auth(self.options)
                        self.assertNotIn('private', str(caught.exception))

    def test_unknown_unlocked_demo_or_malformed_status_stays_closed(self):
        payloads = [b'not json', b'\xff', b'{}', b'[]', b'x' * 65537]
        for status in ({'settings': []}, {**self.status, 'status': 'unknown'},
                       {**self.status, 'anonymousReadAccess': True},
                       {**self.status, 'anonymousReadAccess': 'false'},
                       {**self.status, 'anonymousReadAccess': None},
                       {**self.status, 'anonymousReadAccess': 0},
                       {**self.status, 'runtimeState': 'demo'}, {**self.status, 'isDemo': True},
                       {**self.status, 'isDemo': 'false'}, {**self.status, 'isDemo': 0}):
            payloads.append(json.dumps(status).encode())
        for payload in payloads:
            with self.subTest(payload=payload[:60]):
                status, protected = self.connections(payload=payload)
                with patch.object(runtime.http.client, 'HTTPConnection', return_value=status) as factory:
                    with self.assertRaisesRegex(ValueError, 'GATEWAY_AUTH'):
                        runtime.verify_native_auth(self.options)
                    factory.assert_called_once()
                    status.close.assert_called_once()

    def test_legacy_settings_and_nullable_demo_flag_do_not_override_real_checks(self):
        for legacy in (True, False, None):
            payload = {**self.status, 'settings': {'requireAuthentication': legacy}, 'isDemo': None}
            status, protected = self.connections(payload=json.dumps(payload).encode())
            with patch.object(runtime.http.client, 'HTTPConnection', side_effect=[status, protected]):
                runtime.verify_native_auth(self.options)

    def test_protected_route_must_deny_instead_of_succeed_redirect_or_disappear(self):
        for code in (200, 204, 301, 302, 403, 404, 500, 503):
            with self.subTest(code=code):
                status, protected = self.connections(protected_code=code)
                with patch.object(runtime.http.client, 'HTTPConnection', side_effect=[status, protected]):
                    with self.assertRaisesRegex(ValueError, 'GATEWAY_AUTH'):
                        runtime.verify_native_auth(self.options)
                    status.close.assert_called_once()
                    protected.close.assert_called_once()
                    protected.getresponse.return_value.read.assert_not_called()

    def test_transport_failures_stay_closed_without_logging_response_data(self):
        for stage in ('status', 'protected'):
            for error in (OSError('private'), TimeoutError('private'), http.client.HTTPException('private')):
                with self.subTest(stage=stage, error=type(error).__name__):
                    status, protected = self.connections()
                    target = status if stage == 'status' else protected
                    target.request.side_effect = error
                    with patch.object(runtime.http.client, 'HTTPConnection', side_effect=[status, protected]):
                        with self.assertRaisesRegex(ValueError, 'GATEWAY_AUTH') as caught:
                            runtime.verify_native_auth(self.options)
                        self.assertNotIn('private', str(caught.exception))
                        target.close.assert_called_once()

    def test_boot_guard_precedes_public_listener(self):
        tree = ast.parse((CODE / 'run.py').read_text())
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
        native_if = next(node for node in ast.walk(main)
                         if isinstance(node, ast.If)
                         and ast.unparse(node.test) == "not options['gateway_auth']")
        guard = next(node for node in ast.walk(native_if)
                     if isinstance(node, ast.Call)
                     and isinstance(node.func, ast.Name)
                     and node.func.id == 'verify_native_auth')
        https_start = next(node for node in ast.walk(main)
                           if isinstance(node, ast.Call)
                           and isinstance(node.func, ast.Attribute)
                           and node.func.attr == 'start'
                           and node.args and isinstance(node.args[0], ast.Constant)
                           and node.args[0].value == 'HTTPS')
        self.assertLess(guard.lineno, https_start.lineno)


if __name__ == '__main__':
    unittest.main()
