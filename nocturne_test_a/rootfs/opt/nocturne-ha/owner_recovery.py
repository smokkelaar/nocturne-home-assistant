"""Local HA-admin break-glass recovery for explicitly reviewed Nocturne builds.

Adds a native single-use recovery code, never changes owners, passkeys or roles.
Database access is by the existing local PostgreSQL OS account, not an HTTP API.
"""
import base64
from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import uuid
import recovery_compatibility

BASE = Path('/opt/nocturne-ha')
RECEIPTS = Path('/data/maintenance')

OWNER_QUERY = """
SELECT DISTINCT s.id AS subject_id, s.username, s.name,
       t.id AS tenant_id, t.slug AS tenant_slug, t.display_name AS tenant_name,
       (SELECT count(*) FROM totp_credentials c WHERE c.subject_id = s.id) AS totp_count,
       (SELECT count(*) FROM passkey_credentials c WHERE c.subject_id = s.id) AS passkey_count
FROM subjects s
JOIN tenant_members m ON m.subject_id = s.id
JOIN tenants t ON t.id = m.tenant_id
JOIN tenant_member_roles mr ON mr.tenant_member_id = m.id
JOIN tenant_roles r ON r.id = mr.tenant_role_id AND r.tenant_id = t.id
WHERE r.slug = 'owner' AND s.is_active AND NOT s.is_system_subject
  AND NOT s.is_demo_subject AND s.approval_status = 'Approved'
  AND t.is_active AND NOT t.is_demo
"""


def database(sql):
    from run import psql
    return psql(database='nocturne', stdin=sql)


def profile():
    return recovery_compatibility.current_profile()


def check_schema(kind):
    # Read-only inspection of the actual migrated database before any write.
    rows = json.loads(database("SELECT coalesce(json_agg(c), '[]'::json) FROM ("
        "SELECT table_name, column_name, udt_name, is_nullable, column_default "
        "FROM information_schema.columns WHERE table_schema = 'public' "
        "AND table_name IN ('subjects','tenants','tenant_members','tenant_roles',"
        "'tenant_member_roles','recovery_codes','totp_credentials','passkey_credentials')) c;"))
    columns = {(row['table_name'], row['column_name']): row for row in rows}
    required = {
        'subjects': {'id': 'uuid', 'username': 'string', 'name': 'string', 'is_active': 'bool',
                     'is_system_subject': 'bool', 'is_demo_subject': 'bool', 'approval_status': 'string', 'updated_at': 'date'},
        'tenants': {'id': 'uuid', 'slug': 'string', 'display_name': 'string', 'is_active': 'bool', 'is_demo': 'bool'},
        'tenant_members': {'id': 'uuid', 'subject_id': 'uuid', 'tenant_id': 'uuid'},
        'tenant_roles': {'id': 'uuid', 'tenant_id': 'uuid', 'slug': 'string'},
        'tenant_member_roles': {'tenant_member_id': 'uuid', 'tenant_role_id': 'uuid'},
        'recovery_codes': {'id': 'uuid', 'subject_id': 'uuid', 'code_hash': 'string', 'used_at': 'date', 'created_at': 'date'},
        'totp_credentials': {'subject_id': 'uuid'},
        'passkey_credentials': {'subject_id': 'uuid'},
    }
    required['tenant_members'].update({'revoked_at': 'date'} if kind == 'hmac' else {})
    required['recovery_codes'].update({'invalidated_at': 'date'} if kind == 'pbkdf2' else {})
    types = {'string': {'text', 'varchar'}, 'date': {'timestamp', 'timestamptz'}}
    for table, fields in required.items():
        for field, expected in fields.items():
            row = columns.get((table, field))
            if not row or row['udt_name'] not in types.get(expected, {expected}):
                raise ValueError('Het databaseschema past niet bij de gecontroleerde herstelroute. Laat eerst de app volledig starten en migreren; herstel anders een bijpassende back-up.')
    # A new required insert column must not silently acquire guessed data.
    for (table, field), row in columns.items():
        if (table == 'recovery_codes' and field not in required[table]
                and row['is_nullable'] == 'NO' and row['column_default'] is None):
            raise ValueError('De herstelcodetabel heeft een nieuwe verplichte kolom. Laat de herstelroute opnieuw controleren; de terminal blijft beschikbaar.')


def readiness():
    try:
        guard()
        check_schema(profile())
        return {'compatible': True, 'message': 'Deze build en database passen bij de gecontroleerde herstelroute. Je kunt hieronder verdergaan.'}
    except ValueError as error:
        return {'compatible': False, 'message': str(error)}
    except (OSError, RuntimeError, KeyError, json.JSONDecodeError, subprocess.SubprocessError):
        return {'compatible': False, 'message': 'Database nog niet bereikbaar. Controleer de appconfiguratie, herstart via HA en wacht tot Nocturne is gestart. Onderhoud start PostgreSQL niet zelfstandig.'}


def owner_query():
    # Official 0.2.7 retains revoked memberships; newer reviewed builds delete them.
    return OWNER_QUERY + (' AND m.revoked_at IS NULL' if profile() == 'hmac' else '')


def guard():
    if os.geteuid() != 0:
        raise ValueError('Eigenaarherstel vereist de lokale HA-appbeheerder')
    profile()


def owners():
    guard()
    check_schema(profile())
    # The query also checks the native schema; incompatible versions fail closed.
    return json.loads(database("SELECT coalesce(json_agg(o), '[]'::json) FROM (" +
                               owner_query() + ' ORDER BY tenant_id, subject_id) o;'))


def fresh_code(legacy=False):
    alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    value = ''.join(secrets.choice(alphabet) for _ in range(10))
    code = value[:5] + '-' + value[5:]
    if legacy:
        # Official's JWT key falls back to INSTANCE_KEY, as set by this wrapper.
        key = json.loads(Path('/data/secrets.json').read_text())['instance']
        return code, hmac.new(key.encode('utf-8'), value.encode('ascii'), hashlib.sha256).hexdigest()
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', value.encode('ascii'), salt, 100_000, 32)
    encoded = 'pbkdf2-sha256$100000$' + base64.b64encode(salt).decode() + '$' + base64.b64encode(digest).decode()
    return code, encoded


def write_receipt(receipt):
    RECEIPTS.mkdir(mode=0o700, parents=True, exist_ok=True)
    RECEIPTS.chmod(0o700)
    path = RECEIPTS / ('owner-recovery-' + receipt['code_id'] + '.json')
    # Create before committing so disk-full cannot leave an untracked code.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as handle:
        json.dump(receipt, handle)
        handle.flush()
        os.fsync(handle.fileno())
    return path


def issue(tenant, subject, write=False, backup_confirmed=False, username=None, reset_totp=False):
    if not write or not backup_confirmed:
        raise ValueError('Maak eerst een HA-back-up; bevestig met --backup-confirmed --write')
    tenant, subject = str(uuid.UUID(tenant)), str(uuid.UUID(subject))
    matches = [o for o in owners() if o['tenant_id'] == tenant and o['subject_id'] == subject]
    if len(matches) != 1:
        raise ValueError('Selecteer expliciet een bestaande actieve eigenaar en diens tenant')
    current = matches[0]['username']
    query = owner_query()
    legacy = profile() == 'hmac'
    if current:
        if username and username != current:
            raise ValueError('Een bestaande gebruikersnaam wordt niet gewijzigd')
        username = current
        rename = ''
    else:
        if not username or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{2,49}', username):
            raise ValueError('Eigenaar heeft geen gebruikersnaam: geef --username met 3–50 eenvoudige tekens')
        # The regex excludes all SQL delimiters. Assign only on an eligible owner
        # that still has no username; global collisions leave the transaction unchanged.
        rename = f"""UPDATE subjects SET username = '{username}', updated_at = now()
WHERE id = '{subject}' AND (username IS NULL OR username = '')
AND EXISTS (SELECT 1 FROM ({query} AND t.id = '{tenant}' AND s.id = '{subject}') e)
AND NOT EXISTS (SELECT 1 FROM subjects WHERE username = '{username}');"""
    code, hashed = fresh_code(legacy)
    sql_username = "'" + username.replace("'", "''") + "'"
    code_id = str(uuid.uuid4())
    receipt = {'code_id': code_id, 'subject_id': subject, 'tenant_id': tenant,
               'issued_at': datetime.now(timezone.utc).isoformat(), 'username': username,
               'previous_username': current, 'backup_confirmed': True, 'reset_totp': reset_totp}
    path = write_receipt(receipt)
    reset = (f"DELETE FROM totp_credentials WHERE subject_id = '{subject}' "
             f"AND EXISTS (SELECT 1 FROM recovery_codes WHERE id = '{code_id}');") if reset_totp else ''
    columns = 'id, subject_id, code_hash, used_at, created_at' if legacy else 'id, subject_id, code_hash, used_at, invalidated_at, created_at'
    values = f"'{code_id}', subject_id, '{hashed}', NULL, " + ('' if legacy else 'NULL, ') + 'now()'
    # All interpolated values are canonical UUIDs or generated hash alphabet.
    # Lock the authority rows and re-check eligibility in the transaction.
    result = database(f"""
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '15s';
LOCK TABLE subjects, tenants, tenant_members, tenant_roles, tenant_member_roles IN SHARE MODE;
{rename}
WITH eligible AS ({query} AND t.id = '{tenant}' AND s.id = '{subject}' AND s.username = {sql_username})
INSERT INTO recovery_codes ({columns})
SELECT {values} FROM eligible
RETURNING id;
{reset}
COMMIT;
""")
    if code_id not in result.splitlines():
        raise ValueError('Eigenaar gewijzigd tijdens herstel; geen code toegevoegd')
    return {**receipt, 'code': code, 'receipt': str(path),
            'next': 'Gebruik gebruikersnaam en code op /auth/recovery van het geldige HTTPS-domein. '
                    'Registreer een nieuwe passkey en meld opnieuw aan. De code is eenmalig; '
                    'hij verloopt niet automatisch. Trek een ongebruikte code in met owner-recovery revoke. '
                    'Stel na herstel opnieuw tweefactorauthenticatie in als die is gereset.'}


def revoke(code_id, write=False):
    if not write:
        raise ValueError('Intrekken vereist --write')
    guard()
    check_schema(profile())
    code_id = str(uuid.UUID(code_id))
    receipt = json.loads((RECEIPTS / ('owner-recovery-' + code_id + '.json')).read_text())
    subject = str(uuid.UUID(receipt['subject_id']))
    if receipt['code_id'] != code_id:
        raise ValueError('Herstelbewijs komt niet overeen')
    if profile() == 'hmac':
        database(f"DELETE FROM recovery_codes WHERE id = '{code_id}' "
                 f"AND subject_id = '{subject}' AND used_at IS NULL;")
    else:
        database(f"UPDATE recovery_codes SET invalidated_at = now() WHERE id = '{code_id}' "
                 f"AND subject_id = '{subject}' AND used_at IS NULL AND invalidated_at IS NULL;")
    return {'code_id': code_id, 'revoked': True}
