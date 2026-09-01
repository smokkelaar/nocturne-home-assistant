"""CI-only synthetic configured owner; NEVER run on an existing HA instance.

This is deliberately NOT passkey enrollment or a login test. A nonfunctional
credential fixture lets the real pinned API's setup and authorization middleware
run in configured mode. All state lives in smoke.py's disposable private volume.
"""
import http.client
import json
import os
from pathlib import Path
import re
import shutil
import sys
import uuid

sys.path.insert(0, '/opt/nocturne-ha')
import run
from settings import validate_options

phase = 'FIXTURE_GUARD'
try:
    # Require the opt-in marker created by our orchestrator, never shipped in an image.
    identity = os.environ.get('NOCTURNE_CI_FIXTURE', '')
    assert re.fullmatch(r'nocturne-ci-[0-9a-f]{32}', identity)
    assert Path('/data/.disposable-ci').read_text() == identity
    assert not os.environ.get('SUPERVISOR_TOKEN')
    assert run.psql(database='nocturne', sql='SELECT count(*) FROM tenants') == '0'
    options = validate_options({})

    def post(path, payload):
        global phase
        connection = http.client.HTTPConnection('127.0.0.1', 8080, timeout=30)
        try:
            connection.request('POST', '/api/v4/setup/' + path, json.dumps(payload), {
                'Content-Type': 'application/json', 'Host': options['authority'],
                'X-Forwarded-Host': options['authority'], 'X-Forwarded-Proto': 'https',
            })
            response = connection.getresponse()
            if response.status != 200:
                phase += f'_HTTP_{response.status}'
            assert response.status == 200, f'Unexpected fixture response HTTP {response.status}'
            raw = response.read(65537)
            assert len(raw) <= 65536
            return json.loads(raw)
        finally:
            connection.close()

    phase = 'FIXTURE_TENANT'
    post('tenant', {'slug': 'ha-ci', 'displayName': 'Disposable CI'})
    phase = 'FIXTURE_OWNER'
    post('owner/options', {'username': 'ha-ci-owner', 'displayName': 'Synthetic CI owner'})
    phase = 'FIXTURE_CREDENTIAL'
    subject = run.psql(database='nocturne',
                       sql="SELECT id FROM subjects WHERE username='ha-ci-owner'")
    subject = str(uuid.UUID(subject))
    # Synthetic bytes cannot sign/authenticate. No user credential is generated/read.
    run.psql(database='nocturne', sql=f"""
        INSERT INTO passkey_credentials
            (id, subject_id, credential_id, public_key, sign_count, transports, label, created_at)
        VALUES ('{uuid.uuid4()}', '{subject}', decode('01020304','hex'), decode('05060708','hex'),
                0, ARRAY[]::text[], 'Nonfunctional disposable CI fixture', now())
    """)
    phase = 'FIXTURE_OPTIONS'
    existing = Path('/run/nocturne/nginx.conf').read_text()
    cert = re.search(r'^\s+ssl_certificate (.+);$', existing, re.M).group(1)
    key = re.search(r'^\s+ssl_certificate_key (.+);$', existing, re.M).group(1)
    # No /ssl host mount exists in this disposable container.
    Path('/ssl').mkdir(exist_ok=True)
    shutil.copyfile(cert, '/ssl/ci.crt')
    shutil.copyfile(key, '/ssl/ci.key')
    Path('/ssl/ci.key').chmod(0o600)
    Path('/data/options.json').write_text(json.dumps({
        'public_url': options['public_url'], 'certificate': 'ci.crt',
        'private_key': 'ci.key', 'gateway_auth': False,
    }))
except BaseException as error:
    print(f'NATIVE_PROBE_FAILED:{phase}:{type(error).__name__}', file=sys.stderr)
    raise SystemExit(1) from None
else:
    print('PASS: isolated synthetic owner fixture prepared; not a real passkey enrollment')
