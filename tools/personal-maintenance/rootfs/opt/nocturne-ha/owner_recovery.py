"""Local HA-admin break-glass recovery for one explicitly supported Nocturne build.

Adds a native single-use recovery code, never changes owners, passkeys or roles.
Database access is by the existing local PostgreSQL OS account, not an HTTP API.
"""
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import uuid

SUPPORTED_COMMIT = '6f112069122e1ded12ddac7eee7e6cbd2dcd01dc'
BASE = Path('/opt/nocturne-ha')
RECEIPTS = Path('/data/maintenance')

OWNER_QUERY = """
SELECT DISTINCT s.id AS subject_id, s.username, s.name,
       t.id AS tenant_id, t.slug AS tenant_slug, t.display_name AS tenant_name
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


def guard():
    if os.geteuid() != 0:
        raise ValueError('Eigenaarherstel vereist de lokale HA-appbeheerder')
    version = json.loads((BASE / 'version.json').read_text())
    if version.get('source_commit') != SUPPORTED_COMMIT:
        raise ValueError('Deze Nocturne-versie is nog niet gecontroleerd voor eigenaarherstel')


def owners():
    guard()
    # The query also checks the native schema; incompatible versions fail closed.
    return json.loads(database("SELECT coalesce(json_agg(o), '[]'::json) FROM (" +
                               OWNER_QUERY + ' ORDER BY tenant_id, subject_id) o;'))


def fresh_code():
    alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    value = ''.join(secrets.choice(alphabet) for _ in range(10))
    code = value[:5] + '-' + value[5:]
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


def issue(tenant, subject, write=False, backup_confirmed=False, username=None):
    if not write or not backup_confirmed:
        raise ValueError('Maak eerst een HA-back-up; bevestig met --backup-confirmed --write')
    tenant, subject = str(uuid.UUID(tenant)), str(uuid.UUID(subject))
    matches = [o for o in owners() if o['tenant_id'] == tenant and o['subject_id'] == subject]
    if len(matches) != 1:
        raise ValueError('Selecteer expliciet een bestaande actieve eigenaar en diens tenant')
    current = matches[0]['username']
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
AND EXISTS (SELECT 1 FROM ({OWNER_QUERY} AND t.id = '{tenant}' AND s.id = '{subject}') e)
AND NOT EXISTS (SELECT 1 FROM subjects WHERE username = '{username}');"""
    code, hashed = fresh_code()
    sql_username = "'" + username.replace("'", "''") + "'"
    code_id = str(uuid.uuid4())
    receipt = {'code_id': code_id, 'subject_id': subject, 'tenant_id': tenant,
               'issued_at': datetime.now(timezone.utc).isoformat(), 'username': username,
               'previous_username': current, 'backup_confirmed': True}
    path = write_receipt(receipt)
    # All interpolated values are canonical UUIDs or generated hash alphabet.
    # Lock the authority rows and re-check eligibility in the transaction.
    result = database(f"""
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '15s';
LOCK TABLE subjects, tenants, tenant_members, tenant_roles, tenant_member_roles IN SHARE MODE;
{rename}
WITH eligible AS ({OWNER_QUERY} AND t.id = '{tenant}' AND s.id = '{subject}' AND s.username = {sql_username})
INSERT INTO recovery_codes (id, subject_id, code_hash, used_at, invalidated_at, created_at)
SELECT '{code_id}', subject_id, '{hashed}', NULL, NULL, now() FROM eligible
RETURNING id;
COMMIT;
""")
    if code_id not in result.splitlines():
        raise ValueError('Eigenaar gewijzigd tijdens herstel; geen code toegevoegd')
    return {**receipt, 'code': code, 'receipt': str(path),
            'next': 'Gebruik gebruikersnaam en code op /auth/recovery van het geldige HTTPS-domein. '
                    'Registreer een nieuwe passkey en meld opnieuw aan. De code is eenmalig; '
                    'hij verloopt niet automatisch. Trek een ongebruikte code in met owner-recovery revoke.'}


def revoke(code_id, write=False):
    if not write:
        raise ValueError('Intrekken vereist --write')
    guard()
    code_id = str(uuid.UUID(code_id))
    receipt = json.loads((RECEIPTS / ('owner-recovery-' + code_id + '.json')).read_text())
    subject = str(uuid.UUID(receipt['subject_id']))
    if receipt['code_id'] != code_id:
        raise ValueError('Herstelbewijs komt niet overeen')
    database(f"UPDATE recovery_codes SET invalidated_at = now() WHERE id = '{code_id}' "
             f"AND subject_id = '{subject}' AND used_at IS NULL AND invalidated_at IS NULL;")
    return {'code_id': code_id, 'revoked': True}
