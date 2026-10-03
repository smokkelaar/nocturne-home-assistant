"""The Official and Latest apps must remain selectable and isolated."""
import importlib.util
import ast
import json
import html
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
        self.test_a = json.loads((ROOT / 'nocturne_test_a/config.json').read_text())
        self.test_b = json.loads((ROOT / 'nocturne_test_b/config.json').read_text())
        self.test_c = json.loads((ROOT / 'nocturne_test_c/config.json').read_text())

    def test_two_distinct_store_entries_and_data_identities(self):
        self.assertEqual('Nocturne Official Release', self.official['name'])
        self.assertEqual('Nocturne Latest Release', self.latest['name'])
        self.assertEqual('nocturne_local', self.official['slug'])  # Existing data/update identity.
        self.assertEqual('nocturne_latest', self.latest['slug'])
        self.assertNotEqual(self.official['slug'], self.latest['slug'])
        self.assertEqual({'8448/tcp': 8448}, self.official['ports'])
        self.assertEqual({'8448/tcp': 8449}, self.latest['ports'])
        self.assertNotEqual(self.official['options']['public_url'], self.latest['options']['public_url'])

    def test_test_a_is_a_distinct_pr_store_entry(self):
        self.assertEqual('Nocturne Test A', self.test_a['name'])
        self.assertEqual('nocturne_test_a', self.test_a['slug'])
        self.assertEqual({'8448/tcp': 8451}, self.test_a['ports'])
        self.assertTrue(self.test_a['options']['public_url'].endswith(':8451'))
        self.assertNotEqual(self.test_a['slug'], 'nocturne_personal')

    def test_test_a_api_logging_is_enabled_without_remote_telemetry(self):
        settings = load_settings('nocturne_test_a')
        passwords = {name: 'test-value' for name in settings.SECRET_FIELDS}
        api, web = settings.service_environments(settings.validate_options({}), passwords)
        self.assertEqual('false', api['OTEL_SDK_DISABLED'])
        self.assertEqual('', api['OTEL_EXPORTER_OTLP_ENDPOINT'])
        self.assertEqual('Warning', api['Logging__LogLevel__Default'])
        self.assertEqual('true', web['OTEL_SDK_DISABLED'])
        self.assertEqual('', web['OTEL_EXPORTER_OTLP_ENDPOINT'])

    def test_test_a_public_authority_keeps_the_share_link_port(self):
        settings = load_settings('nocturne_test_a')
        passwords = {name: 'test-value' for name in settings.SECRET_FIELDS}
        for url, authority in (
            ('https://example.test:8451', 'example.test:8451'),
            ('https://example.test', 'example.test'),
        ):
            with self.subTest(url=url):
                options = settings.validate_options({'public_url': url})
                api, web = settings.service_environments(options, passwords)
                self.assertEqual(authority, api['BASE_DOMAIN'])
                self.assertEqual(authority, web['BASE_DOMAIN'])
                self.assertEqual('example.test', options['hostname'])

    def test_test_a_uses_shared_gateway_schema_and_reads_legacy_options(self):
        settings = load_settings('nocturne_test_a')
        self.assertFalse(settings.validate_options({})['skip_gateway_check'])
        self.assertEqual(self.latest['schema'], self.test_a['schema'])
        self.assertNotIn('verify_native_auth', self.test_a['options'])
        self.assertNotIn('verify_native_auth', self.test_a['schema'])
        for language in ('nl', 'en'):
            translation = json.loads((ROOT / 'nocturne_test_a/translations' / (language + '.json')).read_text(encoding='utf-8'))
            self.assertEqual(set(self.test_a['schema']), set(translation['configuration']))
        options = settings.validate_options({
            'public_url': 'https://example.test:8451',
            'certificate': 'fullchain.pem', 'private_key': 'privkey.pem',
            'gateway_auth': False, 'verify_native_auth': False,
        })
        self.assertTrue(options['skip_gateway_check'])
        self.assertNotIn('verify_native_auth', options)
        nginx = settings.nginx_config(options, '/cert', '/key')
        self.assertIn('if ($ha_allowed_host = 0) { return 421; }', nginx)
        self.assertIn('~^[a-z0-9]+\\.share\\.example\\.test$ 1;', nginx)
        self.assertIn('server_name example.test *.share.example.test;', nginx)
        self.assertNotIn('auth_basic_user_file', nginx)
        self.assertIn('proxy_set_header X-Instance-Key "";', nginx)
        self.assertIn('proxy_set_header X-Instance-Service "";', nginx)
        status = settings.status_page(options, {}, 'synthetic-gateway-secret', False)
        self.assertIn('private-instantiecontrole uitgeschakeld', status)
        self.assertNotIn('Nocturne-aanmelding blijft verplicht', status)
        self.assertNotIn('synthetic-gateway-secret', status)
        for value in ('false', 0, 1, None, {}, []):
            with self.subTest(value=value), self.assertRaises(ValueError):
                settings.validate_options({'verify_native_auth': value})
        with self.assertRaisesRegex(ValueError, 'GATEWAY_TLS'):
            settings.validate_options({'gateway_auth': False, 'verify_native_auth': False})

    def test_test_a_explicit_verification_skip_does_not_call_the_api(self):
        import http.client
        from unittest.mock import MagicMock, patch
        tree = ast.parse((ROOT / 'nocturne_test_a/rootfs/opt/nocturne-ha/run.py').read_text())
        guard = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                     and node.name == 'verify_native_auth')
        namespace = {'http': type('Http', (), {'client': http.client}), 'json': json}
        exec(compile(ast.Module(body=[guard], type_ignores=[]), '<test-a-guard>', 'exec'), namespace)
        with patch.object(http.client, 'HTTPConnection') as connection:
            namespace['verify_native_auth']({'skip_gateway_check': True})
            connection.assert_not_called()
        response = MagicMock()
        response.status = 200
        response.read.return_value = json.dumps({
            'status': 'ok', 'runtimeState': 'loaded', 'anonymousReadAccess': True,
        }).encode()
        with patch.object(http.client, 'HTTPConnection') as connection:
            connection.return_value.getresponse.return_value = response
            with self.assertRaisesRegex(ValueError, 'GATEWAY_AUTH'):
                namespace['verify_native_auth']({'authority': 'example.test:8451'})
            connection.assert_called_once()

    def test_test_b_is_a_distinct_personal_store_entry(self):
        self.assertEqual('Nocturne Test B', self.test_b['name'])
        self.assertEqual('nocturne_test_b', self.test_b['slug'])
        self.assertEqual({'8448/tcp': 8452}, self.test_b['ports'])
        self.assertTrue(self.test_b['options']['public_url'].endswith(':8452'))
        self.assertNotEqual(self.test_b['slug'], 'nocturne_test_a')
        self.assertNotEqual(self.test_b['ports'], self.test_a['ports'])

    def test_test_c_is_a_distinct_personal_store_entry(self):
        self.assertEqual('Nocturne Test C', self.test_c['name'])
        self.assertEqual('nocturne_test_c', self.test_c['slug'])
        self.assertEqual({'8448/tcp': 8453}, self.test_c['ports'])
        self.assertTrue(self.test_c['options']['public_url'].endswith(':8453'))
        self.assertNotEqual(self.test_c['slug'], self.test_b['slug'])
        self.assertNotEqual(self.test_c['ports'], self.test_b['ports'])

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
            'build/check_web.mjs', 'build/prepare_web.py', 'build/check_cookies.conf',
            'rootfs/opt/nocturne-ha/bootstrap.sql', 'rootfs/opt/nocturne-ha/run.py',
            'rootfs/opt/nocturne-ha/settings.py', 'rootfs/opt/nocturne-ha/tls.py',
            'rootfs/opt/nocturne-ha/cookies.mjs',
            'translations/nl.json', 'translations/en.json',
        ]
        for relative in common:
            with self.subTest(file=relative):
                self.assertEqual((ROOT / 'nocturne_local' / relative).read_bytes(),
                                 (ROOT / 'nocturne_latest' / relative).read_bytes())

    def test_each_status_page_names_its_channel(self):
        for package, name, port in [('nocturne_local', 'Nocturne Official Release', 8448),
                                    ('nocturne_latest', 'Nocturne Latest Release', 8449),
                                    ('nocturne_test_a', 'Nocturne Test A', 8451),
                                    ('nocturne_test_b', 'Nocturne Test B', 8452),
                                    ('nocturne_test_c', 'Nocturne Test C', 8453)]:
            settings = load_settings(package)
            options = settings.validate_options({})
            self.assertEqual(f'https://homeassistant.local:{port}', options['public_url'])
            page = settings.status_page(options, {}, '', True)
            self.assertIn('<h1>' + name + '</h1>', page)

    def test_status_page_links_version_provenance(self):
        page = load_settings('nocturne_latest').status_page(
            load_settings('nocturne_latest').validate_options({}), {}, '', False)
        self.assertIn('<h2>Versie en herkomst</h2>', page)
        self.assertIn('Softwarebasis', page)
        self.assertIn('Exacte broncommit', page)
        self.assertIn('https://github.com/nightscout/nocturne', page)
        self.assertIn('Doel van deze versie', page)
        self.assertIn('Te controleren', page)

    def test_every_channel_exposes_complete_clickable_provenance(self):
        packages = ('nocturne_local', 'nocturne_latest', 'nocturne_personal',
                    'nocturne_test_a', 'nocturne_test_b', 'nocturne_test_c')
        for package in packages:
            with self.subTest(package=package):
                runtime_path = ROOT / package / 'rootfs/opt/nocturne-ha/version.json'
                versions = json.loads(runtime_path.read_text())
                for key in ('repository', 'source_commit', 'base', 'base_commit', 'release',
                            'release_url', 'purpose', 'purpose_url', 'test_plan', 'test_url'):
                    self.assertTrue(versions.get(key), f'{package} mist {key}')
                settings = load_settings(package)
                page = settings.status_page(settings.validate_options({}), {}, '', False)
                self.assertIn(f"https://github.com/{versions['repository']}/commit/{versions['source_commit']}", page)
                self.assertIn(versions['release_url'], page)
                self.assertIn(versions['purpose_url'], page)
                self.assertIn(versions['test_url'], page)
                self.assertIn(versions['purpose'], page)
                self.assertIn(html.escape(versions['test_plan']), page)
                self.assertIn('<h2>Systeemresources</h2>', page)

    def test_latest_never_inherits_official_identity_or_default_port(self):
        serialized = json.dumps(self.latest)
        self.assertNotIn('"slug": "nocturne_local"', serialized)
        self.assertNotEqual(8448, self.latest['ports']['8448/tcp'])
        self.assertTrue(self.latest['options']['public_url'].endswith(':8449'))

    def test_cookie_namespace_is_fixed_by_channel_not_user_url_or_option(self):
        for package, namespace in [('nocturne_local', 'NocturneOfficial_'),
                                    ('nocturne_latest', 'NocturneLatest_'),
                                    ('nocturne_test_a', 'NocturneTestA_'),
                                    ('nocturne_test_b', 'NocturneTestB_'),
                                    ('nocturne_test_c', 'NocturneTestC_')]:
            settings = load_settings(package)
            for port in (8448, 8449, 8451, 8452, 8453):
                options = settings.validate_options({
                    'public_url': f'https://example.net:{port}',
                    'cookie_namespace': 'attacker_',
                })
                self.assertEqual(namespace, options['cookie_namespace'])
                nginx = settings.nginx_config(options, '/cert', '/key')
                self.assertIn(f'set $ha_cookie_namespace "{namespace}";', nginx)
                self.assertIn('proxy_set_header Cookie $ha_upstream_cookie;', nginx)
                self.assertEqual(3, nginx.count('js_header_filter ha_cookies.responseCookies;'))
            options['cookie_namespace'] = 'invalid'
            with self.assertRaises(ValueError):
                settings.nginx_config(options, '/cert', '/key')

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
