"""CI-only native recovery test in cookie_smoke.py's disposable Personal fixture.

No real login credentials, real accounts or user data are accepted or logged.
"""
import http.client
import json
import os
from pathlib import Path
import re
import subprocess
import sys

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
                             '--subject', subject, '--backup-confirmed', '--write'],
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
    assert enrollment['challengeToken'] and json.loads(enrollment['options'])['rp']['id'] == options['hostname']
    phase = 'SINGLE_USE'
    assert post('recovery/verify', {'username': issued['username'], 'code': issued['code']})[0] == 400
    assert run.psql(database='nocturne', sql=f"SELECT count(*) FROM passkey_credentials WHERE subject_id = '{subject}'") == before
    phase = 'REVOKE'
    another = owner_recovery.issue(owner['tenant_id'], subject, True, True)
    owner_recovery.revoke(another['code_id'], True)
    assert post('recovery/verify', {'username': another['username'], 'code': another['code']})[0] == 400
except BaseException as error:
    print(f'NATIVE_PROBE_FAILED:OWNER_RECOVERY_{phase}:{type(error).__name__}', file=sys.stderr)
    raise SystemExit(1) from None
else:
    print('PASS: native owner recovery without old login/codes, enrollment permission, single use and revocation')
