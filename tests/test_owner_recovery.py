import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import uuid

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'tools/personal-maintenance/rootfs/opt/nocturne-ha/owner_recovery.py'
spec = importlib.util.spec_from_file_location('owner_recovery', SOURCE)
recovery = importlib.util.module_from_spec(spec)
sys.modules['owner_recovery'] = recovery
spec.loader.exec_module(recovery)
TENANT, SUBJECT = str(uuid.uuid4()), str(uuid.uuid4())
OWNER = {'tenant_id': TENANT, 'subject_id': SUBJECT, 'username': 'forgotten-owner'}


class OwnerRecoveryTests(unittest.TestCase):
    def test_reviewed_source_matches_personal_pin_and_packaged_guard(self):
        lock = json.loads((ROOT / 'upstream-personal.json').read_text())
        self.assertEqual(lock['commit'], recovery.SUPPORTED_COMMIT)
        packaged = ROOT / 'nocturne_personal/rootfs/opt/nocturne-ha'
        self.assertEqual(SOURCE.read_bytes(), (packaged / 'owner_recovery.py').read_bytes())
        with patch.object(recovery, 'BASE', packaged), \
             patch.object(recovery.os, 'geteuid', return_value=0, create=True):
            recovery.guard()

    def test_native_pbkdf2_format_and_code_normalization(self):
        code, stored = recovery.fresh_code()
        self.assertRegex(code, r'^[ABCDEFGHJKLMNPQRSTUVWXYZ23456789]{5}-[ABCDEFGHJKLMNPQRSTUVWXYZ23456789]{5}$')
        algorithm, iterations, salt, hashed = stored.split('$')
        self.assertEqual(('pbkdf2-sha256', '100000'), (algorithm, iterations))
        salt = base64.b64decode(salt)
        self.assertEqual(16, len(salt))
        self.assertEqual(hashlib.pbkdf2_hmac('sha256', code.lower().upper().replace('-', '').encode(),
                                          salt, 100_000, 32), base64.b64decode(hashed))

    def test_missing_write_or_backup_never_accesses_database(self):
        for write, backup in ((False, False), (True, False), (False, True)):
            with patch.object(recovery, 'owners') as owners, self.assertRaises(ValueError):
                recovery.issue(TENANT, SUBJECT, write, backup)
            owners.assert_not_called()

    def test_non_owner_or_wrong_tenant_never_gets_code(self):
        with patch.object(recovery, 'owners', return_value=[OWNER]), patch.object(recovery, 'database') as db:
            with self.assertRaises(ValueError):
                recovery.issue(str(uuid.uuid4()), SUBJECT, True, True)
            db.assert_not_called()

    def test_issuance_keeps_passkeys_roles_and_existing_codes_and_receipt_has_no_secret(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(recovery, 'RECEIPTS', Path(directory)), \
             patch.object(recovery, 'owners', return_value=[OWNER]), \
             patch.object(recovery, 'database', side_effect=lambda sql: next(Path(directory).glob('*.json')).stem.rsplit('owner-recovery-', 1)[1]) as db:
            result = recovery.issue(TENANT, SUBJECT, True, True)
            receipt = Path(result['receipt']).read_text()
            self.assertNotIn(result['code'], receipt)
            self.assertEqual(SUBJECT, json.loads(receipt)['subject_id'])
            sql = db.call_args.args[0]
            self.assertIn('BEGIN;', sql)
            self.assertIn('INSERT INTO recovery_codes', sql)
            self.assertNotIn('DELETE', sql)
            self.assertNotRegex(sql, r'(INSERT INTO|UPDATE|DELETE FROM) passkey_credentials')
            self.assertNotIn(result['code'], sql)

    def test_receipt_failure_prevents_database_mutation(self):
        with patch.object(recovery, 'owners', return_value=[OWNER]), \
             patch.object(recovery, 'write_receipt', side_effect=OSError('disk full')), \
             patch.object(recovery, 'database') as db, self.assertRaises(OSError):
            recovery.issue(TENANT, SUBJECT, True, True)
        db.assert_not_called()

    def test_totp_reset_is_explicit_and_limited_to_selected_account(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(recovery, 'RECEIPTS', Path(directory)), \
             patch.object(recovery, 'owners', return_value=[OWNER]), \
             patch.object(recovery, 'database', side_effect=lambda sql: next(Path(directory).glob('*.json')).stem.rsplit('owner-recovery-', 1)[1]) as db:
            result = recovery.issue(TENANT, SUBJECT, True, True, reset_totp=True)
            sql = db.call_args.args[0]
            self.assertIn("DELETE FROM totp_credentials WHERE subject_id = '" + SUBJECT + "'", sql)
            self.assertIn("WHERE id = '" + result['code_id'] + "'", sql)
            self.assertTrue(json.loads(Path(result['receipt']).read_text())['reset_totp'])

    def test_oidc_owner_without_username_requires_explicit_safe_name(self):
        owner = {**OWNER, 'username': None}
        with patch.object(recovery, 'owners', return_value=[owner]), patch.object(recovery, 'database') as db:
            for username in (None, "injected'; SELECT 1;", 'ab'):
                with self.assertRaises(ValueError):
                    recovery.issue(TENANT, SUBJECT, True, True, username)
            db.assert_not_called()

    def test_guard_rejects_unreviewed_source_and_nonroot(self):
        with patch.object(recovery.os, 'geteuid', return_value=1, create=True), self.assertRaises(ValueError):
            recovery.guard()
        with tempfile.TemporaryDirectory() as directory, patch.object(recovery, 'BASE', Path(directory)), \
             patch.object(recovery.os, 'geteuid', return_value=0, create=True):
            (Path(directory) / 'version.json').write_text('{"source_commit":"unreviewed"}')
            with self.assertRaises(ValueError):
                recovery.guard()

    def test_invalid_uuid_rejected_before_owner_lookup(self):
        with patch.object(recovery, 'owners') as owners, self.assertRaises(ValueError):
            recovery.issue("'; SELECT 1;", SUBJECT, True, True)
        owners.assert_not_called()


if __name__ == '__main__':
    unittest.main()
