import http.client
import http.server
import importlib.util
import json
from pathlib import Path
import re
import sys
import threading
import unittest
from unittest.mock import patch
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / 'tools/personal-maintenance/rootfs/opt/nocturne-ha'
sys.path.insert(0, str(TEMPLATES))
import owner_recovery
spec = importlib.util.spec_from_file_location('totp_entry', TEMPLATES / 'personal_entry.py')
entry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entry)
entry.BASE = ROOT / 'nocturne_personal/rootfs/opt/nocturne-ha'
OWNER = {'tenant_id': '11111111-1111-4111-8111-111111111111',
         'subject_id': '22222222-2222-4222-8222-222222222222',
         'username': 'synthetic-owner', 'tenant_name': 'Synthetic tenant', 'totp_count': 1}


class TotpResetSqlTests(unittest.TestCase):
    def setUp(self):
        for mocked in (patch.object(owner_recovery, 'owners', return_value=[OWNER]),
                       patch.object(owner_recovery, 'profile', return_value='pbkdf2'),
                       patch.object(owner_recovery, 'write_receipt', return_value=Path('/synthetic/receipt.json'))):
            mocked.start()
            self.addCleanup(mocked.stop)

    def reset(self, **options):
        return owner_recovery.reset_totp(OWNER['tenant_id'], OWNER['subject_id'],
            expected_username=OWNER['username'], **options)

    def test_both_confirmations_are_required_before_reading_accounts(self):
        with patch.object(owner_recovery, 'owners') as owners, patch.object(owner_recovery, 'database') as db:
            for write, backup in ((False, False), (True, False), (False, True)):
                with self.assertRaises(ValueError):
                    self.reset(write=write, backup_confirmed=backup)
            owners.assert_not_called()
            db.assert_not_called()

    def test_reset_removes_only_selected_totp_without_touching_other_credentials(self):
        with patch.object(owner_recovery, 'database', return_value='BEGIN\n{"eligible":1,"removed":1}\nCOMMIT') as db:
            result = self.reset(write=True, backup_confirmed=True)
        self.assertEqual(1, result['removed'])
        sql = db.call_args.args[0]
        self.assertIn("DELETE FROM totp_credentials WHERE subject_id = '" + OWNER['subject_id'] + "'", sql)
        self.assertIn('AND EXISTS (SELECT 1 FROM eligible)', sql)
        self.assertIn("s.username = 'synthetic-owner'", sql)
        self.assertNotRegex(sql, r'(INSERT INTO|UPDATE|DELETE FROM) (subjects|passkey_credentials|recovery_codes|tenant_roles)')
        self.assertNotIn('secret_key', sql)

    def test_changed_username_or_wrong_owner_prevents_any_reset(self):
        with patch.object(owner_recovery, 'database') as db:
            with self.assertRaises(ValueError):
                owner_recovery.reset_totp(OWNER['tenant_id'], OWNER['subject_id'], True, True, 'different-owner')
            with self.assertRaises(ValueError):
                owner_recovery.reset_totp('33333333-3333-4333-8333-333333333333', OWNER['subject_id'], True, True, OWNER['username'])
            db.assert_not_called()

    def test_full_disk_prevents_reset_and_zero_removed_is_idempotent(self):
        with patch.object(owner_recovery, 'write_receipt', side_effect=OSError('disk full')), \
             patch.object(owner_recovery, 'database') as db:
            with self.assertRaises(OSError):
                self.reset(write=True, backup_confirmed=True)
            db.assert_not_called()
        with patch.object(owner_recovery, 'database', return_value='{"eligible":1,"removed":0}'):
            self.assertEqual(0, self.reset(write=True, backup_confirmed=True)['removed'])


class TotpResetRequestTests(unittest.TestCase):
    def test_request_is_bound_to_owner_one_use_expiring_and_confirmation_required(self):
        now = [10]
        requests = entry.TotpResetRequests(lambda: now[0])
        token = requests.issue(OWNER)
        valid = {'token': [token], 'backup': ['yes'], 'confirm': ['yes']}
        for invalid in ({'token': [token]}, {**valid, 'subject': ['attacker-selected']},
                        {**valid, 'confirm': ['no']}, {**valid, 'backup': ['yes', 'yes']}):
            with self.assertRaises(ValueError):
                requests.take(invalid)
        self.assertEqual({'tenant': OWNER['tenant_id'], 'subject': OWNER['subject_id'],
                          'expected_username': OWNER['username']}, requests.take(valid))
        with self.assertRaises(ValueError):
            requests.take(valid)
        expired = requests.issue(OWNER)
        now[0] += 1801
        with self.assertRaises(ValueError):
            requests.take({**valid, 'token': [expired]})

    def test_result_cannot_be_displayed_as_success_for_a_different_account(self):
        requests = entry.TotpResetRequests()
        token = requests.completed('selected-account', 'Synthetic success')
        self.assertIsNone(requests.notice(token, 'different-account'))
        token = requests.completed('selected-account', 'Synthetic success')
        self.assertEqual('Synthetic success', requests.notice(token, 'selected-account'))
        self.assertIsNone(requests.notice(token, 'selected-account'))


class TotpResetHttpTests(unittest.TestCase):
    def setUp(self):
        self.owner = dict(OWNER)
        self.key = 'a' * 64
        self.raw = {'maintenance_enabled': True, 'maintenance_password': 'synthetic-only-password'}
        mocks = (patch.object(owner_recovery, 'readiness', return_value={'compatible': True, 'message': 'Ready'}),
                 patch.object(owner_recovery, 'owners', side_effect=lambda: [self.owner]),
                 patch.object(entry, 'doctor', return_value={'api': 'ready'}),
                 patch.object(entry, 'recovery_plan', return_value={'steps': [], 'recovery_url': 'https://example.net/auth/recovery'}))
        for mocked in mocks:
            mocked.start()
            self.addCleanup(mocked.stop)
        handler = entry.wizard_handler(self.raw, '/maintenance/terminal/synthetic', lambda: 'actief', self.key)
        self.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.close_server)

    def close_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def request(self, method, path, body=None, authenticated=True, content_type='application/x-www-form-urlencoded'):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        headers = {'Content-Type': content_type}
        if authenticated:
            headers['X-Nocturne-Maintenance-Key'] = self.key
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        self.last_location = response.getheader('Location')
        status, data = response.status, response.read().decode()
        connection.close()
        return status, data

    def form(self):
        selection = self.owner['tenant_id'] + ':' + self.owner['subject_id']
        status, page = self.request('GET', '/maintenance/?' + urlencode({'owner': selection}))
        self.assertEqual(200, status)
        self.assertNotIn(self.key, page)
        self.assertIn('action="totp-reset"', page)
        return {'token': re.search(r'name="token" value="([^"]+)"', page)[1], 'backup': 'yes', 'confirm': 'yes'}

    def test_authenticated_confirmed_post_resets_once_and_shows_reenrollment_guidance(self):
        form = self.form()
        def reset(**arguments):
            self.owner['totp_count'] = 0
            return {'removed': 1}
        with patch.object(owner_recovery, 'reset_totp', side_effect=reset) as action:
            status, page = self.request('POST', '/maintenance/totp-reset', urlencode(form))
            self.assertEqual(303, status)
            self.assertTrue(self.last_location.startswith('./?'))
            status, page = self.request('GET', '/maintenance/' + self.last_location[2:])
            self.assertEqual(200, status)
            self.assertIn('TOTP is uitgeschakeld', page)
            self.assertIn('Stel je authenticator na aanmelden opnieuw in', page)
            self.assertNotIn('action="totp-reset"', page)
            self.assertEqual(400, self.request('POST', '/maintenance/totp-reset', urlencode(form))[0])
            action.assert_called_once_with(tenant=self.owner['tenant_id'], subject=self.owner['subject_id'],
                expected_username=self.owner['username'], write=True, backup_confirmed=True)

    def test_missing_backend_auth_nonce_confirmation_and_get_cannot_reset(self):
        form = self.form()
        with patch.object(owner_recovery, 'reset_totp') as action:
            self.assertEqual(403, self.request('GET', '/maintenance/', authenticated=False)[0])
            self.assertEqual(403, self.request('POST', '/maintenance/totp-reset', urlencode(form), authenticated=False)[0])
            self.assertEqual(404, self.request('GET', '/maintenance/totp-reset')[0])
            for invalid in ({**form, 'token': 'guessed'}, {'token': form['token'], 'confirm': 'yes'},
                            {**form, 'subject': 'different-account'}):
                self.assertEqual(400, self.request('POST', '/maintenance/totp-reset', urlencode(invalid))[0])
            self.assertEqual(415, self.request('POST', '/maintenance/totp-reset', '{}', content_type='application/json')[0])
            self.assertEqual(413, self.request('POST', '/maintenance/totp-reset', 'x' * 4097)[0])
            self.raw['maintenance_enabled'] = False
            self.assertEqual(403, self.request('POST', '/maintenance/totp-reset', urlencode(form))[0])
            action.assert_not_called()

    def test_failure_does_not_expose_private_error_and_request_cannot_be_replayed(self):
        form = self.form()
        with patch.object(owner_recovery, 'reset_totp', side_effect=ValueError('private-error-detail')) as action:
            status, page = self.request('POST', '/maintenance/totp-reset', urlencode(form))
            self.assertEqual(409, status)
            self.assertNotIn('private-error-detail', page)
            self.assertEqual(400, self.request('POST', '/maintenance/totp-reset', urlencode(form))[0])
            action.assert_called_once()


if __name__ == '__main__':
    unittest.main()
