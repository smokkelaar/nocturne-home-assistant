"""External public origins must survive packaging without changing listener hosts."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ('nocturne_local', 'nocturne_latest', 'nocturne_personal',
            'nocturne_test_a', 'nocturne_test_b', 'nocturne_test_c')


def settings_for(package):
    path = ROOT / package / 'rootfs/opt/nocturne-ha/settings.py'
    spec = importlib.util.spec_from_file_location('origin_' + package, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PublicOriginTests(unittest.TestCase):
    def test_api_and_web_keep_external_authority_in_every_package(self):
        for package in PACKAGES:
            settings = settings_for(package)
            cases = [('https://mynocturne.duckdns.org:8451', 'mynocturne.duckdns.org:8451'),
                     ('https://mynocturne.duckdns.org:443', 'mynocturne.duckdns.org:443'),
                     ('https://mynocturne.duckdns.org', 'mynocturne.duckdns.org')]
            default = json.loads((ROOT / package / 'config.json').read_text())['options']['public_url']
            cases.append((default, default.removeprefix('https://')))
            for url, authority in cases:
                with self.subTest(package=package, url=url):
                    options = settings.validate_options({'public_url': url})
                    passwords = {key: 'synthetic-value' for key in settings.SECRET_FIELDS}
                    api, web = settings.service_environments(options, passwords)
                    self.assertEqual(authority, api['BASE_DOMAIN'])
                    self.assertEqual(authority, web['BASE_DOMAIN'])
                    self.assertEqual(url, options['public_url'])
                    self.assertEqual('http://127.0.0.1:8080', api['ASPNETCORE_URLS'])
                    self.assertEqual('http://127.0.0.1:8000', api['WEB_URL'])
                    self.assertEqual('8000', web['PORT'])
                    for key in ('NOCTURNE_API_HTTP', 'NOCTURNE_API_URL', 'PUBLIC_API_URL'):
                        self.assertEqual('http://127.0.0.1:8080', web[key])

    def test_native_host_guard_stays_hostname_only(self):
        for package in PACKAGES:
            settings = settings_for(package)
            options = settings.validate_options({
                'public_url': 'https://mynocturne.duckdns.org:8451',
                'certificate': 'fullchain.pem', 'private_key': 'privkey.pem',
                'gateway_auth': False})
            config = settings.nginx_config(options, 'cert', 'key')
            with self.subTest(package=package):
                self.assertEqual('mynocturne.duckdns.org', options['hostname'])
                self.assertIn('server_name mynocturne.duckdns.org;', config)
                self.assertNotIn('server_name mynocturne.duckdns.org:8451;', config)
                self.assertIn('if ($host != "mynocturne.duckdns.org") { return 421; }', config)
                self.assertIn('listen 8448 ssl;', config)
                self.assertIn('X-Forwarded-Host $http_host', config)

