"""Offline regression checks. These are NOT a Docker/HA runtime certification."""
import importlib
import io
import json
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / 'nocturne_local/rootfs/opt/nocturne-ha'
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(ROOT / 'nocturne_local/build'))
settings = importlib.import_module('settings')
runtime = importlib.import_module('run')
prepare = importlib.import_module('prepare_web')


class OptionsTests(unittest.TestCase):
    def test_default_address(self):
        self.assertEqual('homeassistant.local', settings.validate_options({})['hostname'])

    def test_valid_domain_and_certificates(self):
        value = settings.validate_options(dict(public_url='https://nocturne.example.net',
                                                certificate='fullchain.pem', private_key='privkey.pem'))
        self.assertEqual('nocturne.example.net', value['hostname'])

    def test_reject_unsafe_urls(self):
        for url in ['http://homeassistant.local:8448', 'https://192.0.2.10:8448',
                    'https://localhost', 'https://host.local/path', 'https://host.local/?x=1',
                    'https://user:password@host.local', 'https://host.local:65536',
                    'https://host.local:0', 'https://host.local\n', 'https://bad_.local',
                    'https://host.local/#x', 'https://host.local;nginx']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                settings.validate_options({'public_url': url})

    def test_certificates_are_paired_and_cannot_traverse(self):
        for cert, key in [('file.pem', ''), ('../file.pem', 'key'), ('/ssl/file', 'key'),
                          ('file.pem;value', 'key'), ('a.pem', 'sub/key.pem')]:
            with self.subTest(cert=cert), self.assertRaises(ValueError):
                settings.validate_options({'certificate': cert, 'private_key': key})


class PersistenceTests(unittest.TestCase):
    def test_secrets_are_unique_and_survive_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            first = settings.load_secrets(directory)
            self.assertEqual(first, settings.load_secrets(directory))
            self.assertEqual(6, len(set(first.values())))

    def test_corrupt_secrets_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'secrets.json'
            path.write_text('{}')
            with self.assertRaises(ValueError):
                settings.load_secrets(directory)
            self.assertEqual('{}', path.read_text())

    def test_missing_secrets_with_database_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / 'postgres'
            db.mkdir()
            (db / 'PG_VERSION').write_text('17')
            with self.assertRaises(ValueError):
                settings.load_secrets(directory)
            self.assertFalse((Path(directory) / 'secrets.json').exists())


class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.options = settings.validate_options({})
        self.passwords = {key: (str(i) * 64) for i, key in enumerate(settings.SECRET_FIELDS)}

    def test_no_superuser_or_gateway_password_in_application_environments(self):
        api, web = settings.service_environments(self.options, self.passwords)
        for env in (api, web):
            serialized = json.dumps(env)
            self.assertNotIn(self.passwords['postgres'], serialized)
            self.assertNotIn(self.passwords['gateway'], serialized)
            self.assertNotIn('SUPERVISOR_TOKEN', serialized)
        self.assertNotIn(self.passwords['migrator'], json.dumps(web))
        self.assertNotIn(self.passwords['web'], json.dumps(api))

    def test_no_demo_data_and_api_loopback_only(self):
        api, web = settings.service_environments(self.options, self.passwords)
        self.assertEqual('false', api['DemoService__Enabled'])
        self.assertEqual('http://127.0.0.1:8080', api['ASPNETCORE_URLS'])
        self.assertEqual('true', web['OTEL_SDK_DISABLED'])

    def test_proxy_has_auth_no_access_log_and_canonical_headers(self):
        text = settings.nginx_config(self.options, '/data/tls/test.crt', '/data/tls/test.key')
        for expected in ['auth_basic_user_file', 'access_log off;', 'user www-data;',
                         'X-Forwarded-Host $http_host', 'X-Forwarded-Proto https',
                         'Authorization ""', 'listen 8448 ssl;', 'hubs/']:
            self.assertIn(expected, text)
        self.assertNotIn('listen 80;', text)

    def test_status_page_escapes_text(self):
        page = settings.status_page(self.options, {'API': '<script>bad</script>'}, 'abc', True)
        self.assertNotIn('<script>', page)
        self.assertIn('&lt;script&gt;', page)
        self.assertIn('Zelfondertekend', page)

    def handler(self, peer):
        handler_type = runtime.make_handler(runtime.Supervisor(), self.options, self.passwords, True)
        handler = object.__new__(handler_type)
        handler.client_address = (peer, 1234)
        handler.path = '/'
        handler.wfile = io.BytesIO()
        for name in ('send_error', 'send_response', 'send_header', 'end_headers'):
            setattr(handler, name, MagicMock())
        return handler

    def test_ingress_rejects_untrusted_peers(self):
        for peer in ['127.0.0.1', '192.0.2.10', '172.30.33.1']:
            handler = self.handler(peer)
            handler.do_GET()
            handler.send_error.assert_called_with(403)
            self.assertEqual(b'', handler.wfile.getvalue())

    def test_ingress_ha_peer_receives_status_with_no_cache(self):
        handler = self.handler('172.30.32.2')
        handler.do_GET()
        handler.send_response.assert_called_with(200)
        handler.send_header.assert_any_call('Cache-Control', 'no-store')
        self.assertIn(self.passwords['gateway'].encode(), handler.wfile.getvalue())
        self.assertNotIn(self.passwords['instance'].encode(), handler.wfile.getvalue())

    def test_database_roles_cannot_bypass_row_security(self):
        sql = (CODE / 'bootstrap.sql').read_text()
        self.assertEqual(3, sql.count('NOBYPASSRLS'))
        self.assertIn('BEGIN;', sql)
        self.assertIn('COMMIT;', sql)
        self.assertNotIn('DROP ', sql)


class LifecycleTests(unittest.TestCase):
    def test_child_failure_is_not_reported_as_success(self):
        supervisor = runtime.Supervisor()
        child = MagicMock(returncode=9)
        child.poll.return_value = 9
        supervisor.children = [('Nocturne API', child)]
        with self.assertRaises(RuntimeError):
            supervisor.check_children()
        self.assertIn('gestopt', supervisor.status['Nocturne API'])

    def test_database_stops_after_clients(self):
        calls = []
        class Process:
            def __init__(self, name): self.name = name
            def poll(self): return None
            def send_signal(self, sig): calls.append((self.name, sig))
            def wait(self, timeout): pass
        supervisor = runtime.Supervisor()
        supervisor.children = [(name, Process(name)) for name in ['PostgreSQL', 'Nocturne API', 'Nocturne Web']]
        supervisor.shutdown()
        self.assertEqual(('PostgreSQL', signal.SIGINT), calls[-1])
        self.assertEqual(3, len(calls))

    def test_ready_probe_does_not_accept_arbitrary_503(self):
        for payload, expected in [(b'{"error":"setup_required"}', True),
                                  (b'{"error":"recovery_mode_active","recoveryMode":true}', True),
                                  (b'{"error":"database_failure"}', False), (b'bad gateway', False)]:
            error = urllib.error.HTTPError('http://local', 503, 'Unavailable', {}, io.BytesIO(payload))
            with patch.object(runtime.urllib.request, 'urlopen', side_effect=error):
                self.assertEqual(expected, runtime.api_reachable('homeassistant.local'))

    def test_bootstrap_does_not_recreate_existing_roles(self):
        with patch.object(runtime, 'psql', side_effect=['1', '3']) as query:
            runtime.bootstrap_database({})
            self.assertEqual(2, query.call_count)

    def test_partial_bootstrap_is_not_reset(self):
        with patch.object(runtime, 'psql', side_effect=['1', '2']):
            with self.assertRaises(RuntimeError):
                runtime.bootstrap_database({})


class WebPreparationTests(unittest.TestCase):
    def fixture(self, directory, workspace='enableGlobalVirtualStore: true\n'):
        root = Path(directory)
        (root / 'packages/app').mkdir(parents=True)
        (root / 'pnpm-workspace.yaml').write_text(workspace)
        (root / 'packages/app/server.js').write_text('server.listen(PORT, () => {\n});\n')
        return root

    def test_local_store_and_loopback_patches(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.fixture(directory)
            prepare.prepare_web(root)
            self.assertEqual('enableGlobalVirtualStore: false\n', (root / 'pnpm-workspace.yaml').read_text())
            self.assertIn("server.listen(PORT, '127.0.0.1'", (root / 'packages/app/server.js').read_text())

    def test_unexpected_store_signature_fails_without_changing_listener(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.fixture(directory, 'unknown: true\n')
            with self.assertRaises(ValueError):
                prepare.prepare_web(root)
            self.assertIn('server.listen(PORT, () => {', (root / 'packages/app/server.js').read_text())

    def test_unexpected_listener_leaves_store_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.fixture(directory)
            (root / 'packages/app/server.js').write_text('changed upstream')
            with self.assertRaises(ValueError):
                prepare.prepare_web(root)
            self.assertEqual('enableGlobalVirtualStore: true\n', (root / 'pnpm-workspace.yaml').read_text())


class PackagingTests(unittest.TestCase):
    def test_ha_manifest(self):
        config = json.loads((ROOT / 'nocturne_local/config.json').read_text())
        self.assertEqual(['amd64'], config['arch'])
        self.assertEqual('cold', config['backup'])
        self.assertFalse(config['init'])
        self.assertEqual({'8448/tcp': 8448}, config['ports'])
        self.assertEqual(8099, config['ingress_port'])
        for key in ('docker_api', 'host_network', 'full_access', 'hassio_api', 'homeassistant_api'):
            self.assertFalse(config.get(key, False))

    def test_images_are_pinned_and_web_bound_to_loopback(self):
        dockerfile = (ROOT / 'nocturne_local/Dockerfile').read_text()
        images = [line for line in dockerfile.splitlines() if line.startswith('FROM ')]
        self.assertEqual(3, len(images))
        for line in images:
            self.assertIn('@sha256:', line)
        self.assertIn('prepare_web.py /opt/nocturne-web', dockerfile)
        self.assertNotIn('docker.sock', dockerfile)

    def test_web_import_check_runs_as_runtime_user(self):
        dockerfile = (ROOT / 'nocturne_local/Dockerfile').read_text()
        check_at = dockerfile.index('RUN node /opt/nocturne-ha-build/check_web.mjs')
        self.assertEqual('USER nocturne-web', [line for line in dockerfile[:check_at].splitlines()
                                              if line.startswith('USER ')][-1])
        self.assertLess(dockerfile.index('prepare_web.py /opt/nocturne-web'),
                        dockerfile.index('pnpm install --prod --frozen-lockfile'))

    def test_visible_version_matches_manifest(self):
        version = json.loads((ROOT / 'nocturne_local/config.json').read_text())['version']
        page = settings.status_page(settings.validate_options({}), {}, '', True)
        wrapper = json.loads((ROOT / 'wrapper.json').read_text())['version']
        self.assertIn('HA-wrapper ' + wrapper, page)
        self.assertIn('HA-pakket ' + version, page)
        self.assertIn('Nocturne Official Release', page)
        self.assertIn('ARG BUILD_VERSION=' + version, (ROOT / 'nocturne_local/Dockerfile').read_text())

    def test_source_files_are_lf_without_bom(self):
        for package in ('nocturne_local', 'nocturne_latest'):
            for file in (ROOT / package).rglob('*'):
                if file.is_file() and file.suffix in ('.py', '.sql', '.json'):
                    self.assertNotIn(b'\r\n', file.read_bytes(), str(file))
                    self.assertFalse(file.read_bytes().startswith(b'\xef\xbb\xbf'), str(file))


if __name__ == '__main__':
    unittest.main(verbosity=2)
