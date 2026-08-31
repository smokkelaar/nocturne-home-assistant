"""Real OpenSSL fixtures plus fail-safe watcher/reload regression tests."""
import importlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'nocturne_local/rootfs/opt/nocturne-ha'))
tls = importlib.import_module('tls')
settings = importlib.import_module('settings')
runtime = importlib.import_module('run')


def certificate(root, name, hostname='homeassistant.local', san=True):
    cert, key = root / (name + '.crt'), root / (name + '.key')
    command = ['openssl', 'req', '-x509', '-newkey', 'ec', '-pkeyopt', 'ec_paramgen_curve:prime256v1',
               '-nodes', '-days', '30', '-keyout', str(key), '-out', str(cert), '-subj', '/CN=' + hostname]
    if san:
        command += ['-addext', 'subjectAltName=DNS:' + hostname]
    subprocess.run(command, capture_output=True, check=True, timeout=15)
    return cert, key


@unittest.skipUnless(shutil.which('openssl'), 'OpenSSL required (installed in Linux CI/runtime)')
class CertificateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.good = certificate(cls.root, 'good')
        cls.other = certificate(cls.root, 'other')
        cls.wrong = certificate(cls.root, 'wrong', 'other.example.net')
        cls.no_san = certificate(cls.root, 'nosan', san=False)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_valid_pair_and_expiry_summary(self):
        info = tls.inspect_pair(*self.good, 'homeassistant.local')
        self.assertGreater(info.not_after, time.time())
        self.assertIn('UTC', info.summary())
        self.assertEqual(64, len(info.leaf_sha256))

    def test_wrong_hostname_rejected(self):
        with self.assertRaisesRegex(tls.CertificateError, 'CERT_HOSTNAME'):
            tls.inspect_pair(*self.wrong, 'homeassistant.local')

    def test_common_name_without_san_rejected(self):
        with self.assertRaisesRegex(tls.CertificateError, 'CERT_SAN'):
            tls.inspect_pair(*self.no_san, 'homeassistant.local')

    def test_mismatched_private_key_rejected(self):
        with self.assertRaisesRegex(tls.CertificateError, 'CERT_KEY_MISMATCH'):
            tls.inspect_pair(self.good[0], self.other[1], 'homeassistant.local')

    def test_expired_and_future_dates_rejected(self):
        info = tls.inspect_pair(*self.good, 'homeassistant.local')
        for now, code in [(info.not_before - 1, 'CERT_NOT_YET_VALID'), (info.not_after, 'CERT_EXPIRED')]:
            with self.subTest(code=code), self.assertRaisesRegex(tls.CertificateError, code):
                tls.inspect_pair(*self.good, 'homeassistant.local', now=now)

    def test_malformed_cert_rejected_without_content_in_error(self):
        with tempfile.TemporaryDirectory() as directory:
            cert = Path(directory) / 'bad.crt'
            cert.write_text('private-content-not-for-logs')
            with self.assertRaisesRegex(tls.CertificateError, '^CERT_PARSE:') as caught:
                tls.inspect_pair(cert, self.good[1], 'homeassistant.local')
            self.assertNotIn('private-content', str(caught.exception))

    def test_watcher_keeps_snapshot_until_stable_valid_pair_is_loaded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cert, key = root / 'source.crt', root / 'source.key'
            cert.write_bytes(self.good[0].read_bytes())
            key.write_bytes(self.good[1].read_bytes())
            watcher = tls.CertificateWatcher(cert, key, 'homeassistant.local', root / 'private')
            original = watcher.active
            callback = MagicMock(return_value=True)
            try:
                cert.write_bytes(self.other[0].read_bytes())
                watcher.poll(callback, now=0)
                watcher.poll(callback, now=11)
                callback.assert_not_called()
                self.assertIn('CERT_KEY_MISMATCH', watcher.message)
                self.assertIs(watcher.active, original)
                self.assertEqual(self.good[0].read_bytes(), original.cert.read_bytes())
                key.write_bytes(self.other[1].read_bytes())
                watcher.poll(callback, now=12)
                watcher.poll(callback, now=15)
                callback.assert_not_called()
                watcher.poll(callback, now=23)
                callback.assert_called_once()
                self.assertNotEqual(watcher.active.info.leaf_sha256, original.info.leaf_sha256)
                self.assertFalse(original.cert.exists())
                # The source is never replaced or rewritten by the watcher.
                self.assertEqual(self.other[1].read_bytes(), key.read_bytes())
            finally:
                watcher.active.close()

    def test_failed_reload_retains_old_snapshot_and_retries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cert, key = root / 'source.crt', root / 'source.key'
            cert.write_bytes(self.good[0].read_bytes())
            key.write_bytes(self.good[1].read_bytes())
            watcher = tls.CertificateWatcher(cert, key, 'homeassistant.local', root / 'private')
            original = watcher.active
            try:
                cert.write_bytes(self.other[0].read_bytes())
                key.write_bytes(self.other[1].read_bytes())
                watcher.poll(lambda _: False, now=0)
                watcher.poll(lambda _: False, now=11)
                self.assertIs(watcher.active, original)
                self.assertTrue(original.cert.exists())
                self.assertEqual(1, len(list((root / 'private').iterdir())))
                self.assertIn('CERT_RELOAD', watcher.message)
                watcher.poll(lambda _: True, now=30)
                self.assertIsNot(watcher.active, original)
            finally:
                watcher.active.close()

    def test_missing_source_does_not_stop_existing_certificate(self):
        with tempfile.TemporaryDirectory() as directory:
            cert, key = certificate(Path(directory), 'source')
            watcher = tls.CertificateWatcher(cert, key, 'homeassistant.local', Path(directory) / 'private')
            try:
                key.unlink()
                callback = MagicMock()
                watcher.poll(callback)
                callback.assert_not_called()
                self.assertIn('CERT_FILES', watcher.message)
                self.assertTrue(watcher.active.key.exists())
            finally:
                watcher.active.close()


class ReloadTests(unittest.TestCase):
    def setUp(self):
        # The product runs on Linux; Windows unit tests simulate its HUP signal.
        self.hup = patch.object(tls.signal, 'SIGHUP', 1, create=True)
        self.hup.start()
        self.addCleanup(self.hup.stop)

    def test_nginx_test_failure_does_not_signal_or_replace(self):
        with tempfile.TemporaryDirectory() as directory:
            conf = Path(directory) / 'nginx.conf'
            conf.write_bytes(b'old')
            process = MagicMock()
            with patch.object(tls.subprocess, 'run', return_value=MagicMock(returncode=1)):
                self.assertFalse(tls.reload_nginx(process, conf, 'new', 'fingerprint', 'host.local'))
            process.send_signal.assert_not_called()
            self.assertEqual(b'old', conf.read_bytes())

    def test_failed_peer_confirmation_restores_old_config(self):
        with tempfile.TemporaryDirectory() as directory:
            conf = Path(directory) / 'nginx.conf'
            conf.write_bytes(b'old')
            process = MagicMock()
            process.poll.return_value = None
            with patch.object(tls.subprocess, 'run', return_value=MagicMock(returncode=0)), \
                    patch.object(tls.time, 'monotonic', side_effect=[0, 9]):
                self.assertFalse(tls.reload_nginx(process, conf, 'new', 'fingerprint', 'host.local'))
            self.assertEqual(2, process.send_signal.call_count)
            self.assertEqual(b'old', conf.read_bytes())

    def test_success_only_signals_nginx_and_keeps_new_config(self):
        with tempfile.TemporaryDirectory() as directory:
            conf = Path(directory) / 'nginx.conf'
            conf.write_bytes(b'old')
            process = MagicMock()
            process.poll.return_value = None
            with patch.object(tls.subprocess, 'run', return_value=MagicMock(returncode=0)), \
                    patch.object(tls.time, 'sleep'), patch.object(tls, 'peer_fingerprint', return_value='fingerprint'):
                self.assertTrue(tls.reload_nginx(process, conf, 'new', 'fingerprint', 'host.local'))
            process.send_signal.assert_called_once()
            self.assertEqual(b'new', conf.read_bytes())

    def test_browser_checks_remain_explicitly_unverified_and_escaped(self):
        page = settings.status_page(settings.validate_options({}), {}, '', False, {'Certificate': '<script>bad</script>'})
        self.assertIn('niet automatisch uitgevoerd', page)
        self.assertIn('DNS-route', page)
        self.assertNotIn('<script>', page)
        self.assertIn('&lt;script&gt;', page)

    def test_web_http_failure_not_reported_as_ready(self):
        for status, location, expected in [(200, '', True), (500, '', False),
                (303, '/setup', True), (302, '//elsewhere.example/', False),
                (302, 'https://evil.example/', False)]:
            with self.subTest(status=status, location=location), patch.object(runtime.http.client, 'HTTPConnection') as factory:
                response = factory.return_value.getresponse.return_value
                response.status = status
                response.getheader.return_value = location
                self.assertEqual(expected, runtime.web_response_reachable(settings.validate_options({})))


if __name__ == '__main__':
    unittest.main()
