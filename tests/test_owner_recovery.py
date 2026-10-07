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
sys.path.insert(0, str(SOURCE.parent))
spec = importlib.util.spec_from_file_location('owner_recovery', SOURCE)
recovery = importlib.util.module_from_spec(spec)
sys.modules['owner_recovery'] = recovery
spec.loader.exec_module(recovery)
recovery.BASE = ROOT / 'nocturne_personal/rootfs/opt/nocturne-ha'
TENANT, SUBJECT = str(uuid.uuid4()), str(uuid.uuid4())
OWNER = {'tenant_id': TENANT, 'subject_id': SUBJECT, 'username': 'forgotten-owner'}


class OwnerRecoveryTests(unittest.TestCase):
    def setUp(self):
        # SQL and receipt tests isolate contract verification; its actual checks
        # are covered separately by test_recovery_compatibility.
        self.profile_patch = patch.object(recovery, 'profile', return_value='pbkdf2')
        self.profile_patch.start()
        self.addCleanup(self.profile_patch.stop)

    def test_every_pinned_channel_has_an_explicit_reviewed_profile(self):
        for package in ('nocturne_local', 'nocturne_latest', 'nocturne_personal',
                        'nocturne_test_a', 'nocturne_test_b', 'nocturne_test_c'):
            with self.subTest(package=package), \
                 patch.object(recovery, 'BASE', ROOT / package / 'rootfs/opt/nocturne-ha'), \
                 patch.object(recovery.os, 'geteuid', return_value=0, create=True), \
                 patch.object(recovery, 'profile', return_value='hmac' if package == 'nocturne_local' else 'pbkdf2'):
                recovery.guard()
                query = recovery.owner_query()
                self.assertEqual(package == 'nocturne_local', 'm.revoked_at IS NULL' in query)

    def test_official_hash_matches_native_hmac_and_never_returns_instance_key(self):
        import hmac
        with patch('pathlib.Path.read_text', return_value='{"instance":"synthetic-instance-key"}'):
            code, stored = recovery.fresh_code(legacy=True)
        expected = hmac.new(b'synthetic-instance-key', code.replace('-', '').encode(), hashlib.sha256).hexdigest()
        self.assertEqual(expected, stored)
        self.assertNotIn('synthetic-instance-key', code + stored)

    def test_official_issue_uses_legacy_columns_and_rechecks_unrevoked_owner(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(recovery, 'RECEIPTS', Path(directory)), \
             patch.object(recovery, 'profile', return_value='hmac'), \
             patch.object(recovery, 'owners', return_value=[OWNER]), \
             patch.object(recovery, 'fresh_code', return_value=('ABCDE-FGHJK', 'a' * 64)) as fresh, \
             patch.object(recovery, 'database', side_effect=lambda sql: next(Path(directory).glob('*.json')).stem.rsplit('owner-recovery-', 1)[1]) as db:
            recovery.issue(TENANT, SUBJECT, True, True)
        fresh.assert_called_once_with(True)
        sql = db.call_args.args[0]
        self.assertIn('AND m.revoked_at IS NULL', sql)
        self.assertIn('INSERT INTO recovery_codes (id, subject_id, code_hash, used_at, created_at)', sql)
        self.assertNotIn('invalidated_at', sql)

    def test_official_revoke_deletes_only_the_selected_unused_code(self):
        code_id = str(uuid.uuid4())
        receipt = {'code_id': code_id, 'subject_id': SUBJECT}
        with patch.object(recovery, 'guard'), \
             patch.object(recovery, 'check_schema'), \
             patch.object(recovery, 'profile', return_value='hmac'), \
             patch('pathlib.Path.read_text', return_value=json.dumps(receipt)), \
             patch.object(recovery, 'database') as db:
            recovery.revoke(code_id, write=True)
        self.assertEqual(f"DELETE FROM recovery_codes WHERE id = '{code_id}' AND subject_id = '{SUBJECT}' AND used_at IS NULL;", db.call_args.args[0])

    def test_packaged_recovery_matches_shared_runtime(self):
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
        with patch.object(recovery, 'profile', side_effect=ValueError('Unknown contract')), \
             patch.object(recovery.os, 'geteuid', return_value=0, create=True):
            with self.assertRaises(ValueError):
                recovery.guard()

    def test_invalid_uuid_rejected_before_owner_lookup(self):
        with patch.object(recovery, 'owners') as owners, self.assertRaises(ValueError):
            recovery.issue("'; SELECT 1;", SUBJECT, True, True)
        owners.assert_not_called()

    def test_schema_missing_or_wrong_columns_blocks_recovery(self):
        for rows in ([], [{'table_name': 'subjects', 'column_name': 'id', 'udt_name': 'text'}]):
            with patch.object(recovery, 'database', return_value=json.dumps(rows)):
                with self.assertRaises(ValueError):
                    recovery.check_schema('pbkdf2')

    def test_schema_failure_prevents_owner_query(self):
        with patch.object(recovery, 'guard'), \
             patch.object(recovery, 'check_schema', side_effect=ValueError('Schema mismatch')), \
             patch.object(recovery, 'database') as db:
            with self.assertRaises(ValueError):
                recovery.owners()
            db.assert_not_called()


if __name__ == '__main__':
    unittest.main()
