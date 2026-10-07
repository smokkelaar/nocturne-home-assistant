"""CI-only native recovery test in smoke.py's disposable configured fixture.

No real login credentials, real accounts or user data are accepted or logged.
"""
import http.client
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import uuid

sys.path.insert(0, '/opt/nocturne-ha')
import owner_recovery
import run
from settings import validate_options

phase = 'GUARD'
try:
    identity = os.environ.get('NOCTURNE_CI_FIXTURE', '')
    assert re.fullmatch(r'nocturne-ci-[0-9a-f]{32}', identity)
    assert Path('/data/.disposable-ci').read_text() == identity
    options = validate_options(json.loads(Path('/data/options.json').read_text()))
    owner = owner_recovery.owners()[0]
    assert owner['username'] == 'ha-ci-owner'
    subject = owner['subject_id']
    assert run.psql(database='nocturne', sql=f"SELECT count(*) FROM recovery_codes WHERE subject_id = '{subject}'") == '0'
    before = run.psql(database='nocturne', sql=f"SELECT count(*) FROM passkey_credentials WHERE subject_id = '{subject}'")
    # Synthetic unusable second factor: no secret is ever read or decrypted.
    run.psql(database='nocturne', sql=f"INSERT INTO totp_credentials (id, subject_id, secret_key, created_at) "
             f"VALUES ('{uuid.uuid4()}', '{subject}', decode('010203', 'hex'), now())")
    phase = 'STANDALONE_TOTP_RESET'
    reset = owner_recovery.reset_totp(owner['tenant_id'], subject, write=True,
                                     backup_confirmed=True, expected_username=owner['username'])
    assert reset['removed'] == 1
    assert run.psql(database='nocturne', sql=f"SELECT count(*) FROM totp_credentials WHERE subject_id = '{subject}'") == '0'
    assert run.psql(database='nocturne', sql=f"SELECT count(*) FROM recovery_codes WHERE subject_id = '{subject}'") == '0'
    assert run.psql(database='nocturne', sql=f"SELECT count(*) FROM passkey_credentials WHERE subject_id = '{subject}'") == before
    assert owner_recovery.reset_totp(owner['tenant_id'], subject, True, True, owner['username'])['removed'] == 0
    # Preserve coverage of the separate CLI flag as well as the standalone action.
    run.psql(database='nocturne', sql=f"INSERT INTO totp_credentials (id, subject_id, secret_key, created_at) "
             f"VALUES ('{uuid.uuid4()}', '{subject}', decode('010203', 'hex'), now())")

    def post(path, payload, cookie=None):
        connection = http.client.HTTPConnection('127.0.0.1', 8080, timeout=30)
        headers = {'Content-Type': 'application/json', 'Host': options['authority'],
                   'X-Forwarded-Host': options['authority'], 'X-Forwarded-Proto': 'https'}
        if cookie:
            headers['Cookie'] = cookie
        try:
            connection.request('POST', '/api/auth/passkey/' + path, json.dumps(payload), headers)
            response = connection.getresponse()
            body = response.read(131073)
            assert len(body) <= 131072
            return response.status, body, response.getheader('Set-Cookie')
        finally:
            connection.close()

    phase = 'CLI_ISSUE'
    result = subprocess.run(['nocturne-ha', 'owner-recovery', 'issue', '--tenant', owner['tenant_id'],
                             '--subject', subject, '--backup-confirmed', '--write', '--reset-totp'],
                            capture_output=True, text=True, check=True)
    issued = json.loads(result.stdout)
    assert issued['code'] not in Path(issued['receipt']).read_text()
    phase = 'NATIVE_VERIFY'
    status, body, cookie = post('recovery/verify', {'username': issued['username'], 'code': issued['code']})
    assert status == 200 and json.loads(body)['success'] is True
    assert cookie and '.Nocturne.RecoverySession=' in cookie
    cookie = cookie.split(';', 1)[0]
    phase = 'ENROLL_WITHOUT_OLD_LOGIN'
    assert post('register/options', {'username': issued['username']})[0] == 401
    status, body, _ = post('register/options', {'username': issued['username']}, cookie)
    assert status == 200
    enrollment = json.loads(body)
    creation = json.loads(enrollment['options'])
    assert enrollment['challengeToken'] and creation['rp']['id'] == options['hostname']
    phase = 'SINGLE_USE'
    assert post('recovery/verify', {'username': issued['username'], 'code': issued['code']})[0] == 400
    assert run.psql(database='nocturne', sql=f"SELECT count(*) FROM passkey_credentials WHERE subject_id = '{subject}'") == before
    assert run.psql(database='nocturne', sql=f"SELECT count(*) FROM totp_credentials WHERE subject_id = '{subject}'") == '0'

    # Disposable software authenticator using real ES256 signatures. This tests
    # the server ceremony; it does not claim real-browser/device UX acceptance.
    def b64(value):
        return base64.urlsafe_b64encode(value).rstrip(b'=').decode()

    def cbor(value):
        def head(major, count):
            if count < 24:
                return bytes([(major << 5) | count])
            if count < 256:
                return bytes([(major << 5) | 24, count])
            return bytes([(major << 5) | 25]) + count.to_bytes(2, 'big')
        if isinstance(value, int):
            return head(0, value) if value >= 0 else head(1, -1 - value)
        if isinstance(value, bytes):
            return head(2, len(value)) + value
        if isinstance(value, str):
            encoded = value.encode()
            return head(3, len(encoded)) + encoded
        if isinstance(value, dict):
            return head(5, len(value)) + b''.join(cbor(k) + cbor(v) for k, v in value.items())
        raise AssertionError('unsupported CBOR fixture value')

    def client_data(kind, challenge):
        return json.dumps({'type': kind, 'challenge': challenge, 'origin': options['public_url'],
                           'crossOrigin': False}, separators=(',', ':')).encode()

    phase = 'REPLACEMENT_PASSKEY'
    with tempfile.TemporaryDirectory() as directory:
        private = str(Path(directory) / 'disposable-virtual-authenticator.pem')
        subprocess.run(['openssl', 'genpkey', '-algorithm', 'EC', '-pkeyopt', 'ec_paramgen_curve:P-256',
                        '-out', private], capture_output=True, check=True)
        public = subprocess.run(['openssl', 'pkey', '-in', private, '-pubout', '-outform', 'DER'],
                                capture_output=True, check=True).stdout[-65:]
        assert public[0] == 4
        credential = os.urandom(32)
        cose = cbor({1: 2, 3: -7, -1: 1, -2: public[1:33], -3: public[33:]})
        rp_hash = hashlib.sha256(creation['rp']['id'].encode()).digest()
        auth_data = rp_hash + b'\x45' + bytes(4) + bytes(16) + len(credential).to_bytes(2, 'big') + credential + cose
        attestation = cbor({'fmt': 'none', 'attStmt': {}, 'authData': auth_data})
        response = {'id': b64(credential), 'rawId': b64(credential), 'type': 'public-key',
                    'authenticatorAttachment': 'platform', 'clientExtensionResults': {},
                    'response': {'clientDataJSON': b64(client_data('webauthn.create', creation['challenge'])),
                                 'attestationObject': b64(attestation), 'transports': ['internal']}}
        status, body, _ = post('register/complete', {'attestationResponseJson': json.dumps(response),
                                                   'challengeToken': enrollment['challengeToken'],
                                                   'label': 'Disposable CI recovery authenticator'}, cookie)
        assert status == 200 and json.loads(body)['subjectId'] == subject
        phase = 'LOGIN_WITH_REPLACEMENT'
        status, body, _ = post('login/options', {'username': issued['username']})
        assert status == 200
        login = json.loads(body)
        assertion = json.loads(login['options'])
        client = client_data('webauthn.get', assertion['challenge'])
        auth_data = rp_hash + b'\x05' + (1).to_bytes(4, 'big')
        signature = subprocess.run(['openssl', 'dgst', '-sha256', '-sign', private],
                                   input=auth_data + hashlib.sha256(client).digest(),
                                   capture_output=True, check=True).stdout
        response['response'] = {'clientDataJSON': b64(client), 'authenticatorData': b64(auth_data),
                                'signature': b64(signature), 'userHandle': creation['user']['id']}
        status, body, _ = post('login/complete', {'assertionResponseJson': json.dumps(response),
                                                'challengeToken': login['challengeToken']})
        assert status == 200 and json.loads(body)['success'] and json.loads(body)['accessToken']
        assert not json.loads(body).get('totpRequired', False)
    phase = 'REVOKE'
    another = owner_recovery.issue(owner['tenant_id'], subject, True, True)
    owner_recovery.revoke(another['code_id'], True)
    assert post('recovery/verify', {'username': another['username'], 'code': another['code']})[0] == 400
except BaseException as error:
    print(f'NATIVE_PROBE_FAILED:OWNER_RECOVERY_{phase}:{type(error).__name__}', file=sys.stderr)
    raise SystemExit(1) from None
else:
    print('PASS: lost-credential owner recovery, replacement passkey registration/login, standalone and CLI TOTP reset, single use and revocation')
