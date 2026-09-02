"""Synthetic checks called only inside cookie_smoke.py's disposable CI fixtures.

Never follows the Google authorize URL, contacts Google or uses real health data.
"""
import json
import uuid
from urllib.parse import parse_qs, urlsplit

GOOGLE = '/api/v4/personal/google-health'
MEDICATIONS = '/api/v4/personal/medications'


def exercise(request, anonymous):
    def call(path, method='GET', body=None, expected=200):
        code, raw = request(8450, path, method, body=body)
        assert code == expected, f'Personal route/status mismatch: {path}: {code}'
        return json.loads(raw) if raw and expected == 200 else None

    for path in (GOOGLE, MEDICATIONS):
        assert request(8450, path, opener=anonymous)[0] == 401
    for path in ('/personal', '/personal/google', '/personal/medications'):
        assert request(8450, path)[0] == 200
    status = call(GOOGLE)
    assert status['configured'] is False and status['connected'] is False
    assert {c['dataType'] for c in status['capabilities'] if c['supported']} == {'steps', 'heart-rate', 'weight'}
    options = dict(clientId='ci-fixture.apps.googleusercontent.com',
                   clientSecret='ci-not-a-real-google-secret',
                   callbackUrl='https://homeassistant.local:8450/personal/google/callback',
                   dataTypes=['steps', 'heart-rate', 'weight'], historyDays=7)
    call(GOOGLE + '/options', 'PUT', {**options, 'dataTypes': ['sleep']}, 400)
    status = call(GOOGLE + '/options', 'PUT', options)
    assert status['configured'] and not status['connected']
    assert 'clientSecret' not in status and 'protectedSettings' not in status
    authorize = call(GOOGLE + '/start', 'POST')
    url = urlsplit(authorize['url'])
    assert url.scheme == 'https' and url.netloc == 'accounts.google.com'
    query = parse_qs(url.query)
    assert query['code_challenge_method'] == ['S256']
    assert len(query['state'][0]) >= 32 and len(query['code_challenge'][0]) >= 32
    assert query['redirect_uri'] == [options['callbackUrl']]
    assert all(s == 'openid' or s.endswith('.readonly') for s in query['scope'][0].split())
    # Reject locally before token exchange; no outbound Google request is made.
    call(GOOGLE + '/complete', 'POST', {'code': 'unused', 'state': 'invalid-state'}, 400)
    call(GOOGLE + '/disconnect', 'POST')
    assert call(GOOGLE + '/readings?dataType=weight') == []

    assert call(MEDICATIONS) == []
    record_id = str(uuid.uuid4())
    path = MEDICATIONS + '/' + record_id
    entry = dict(name='CI fixture', ingredient='synthetic test only', amount=1.25,
                 unit='mg', status='taken', route='subcutaneous', mills=1690000000123,
                 utcOffsetMinutes=120, notes='Disposable test', revision=str(uuid.UUID(int=0)))
    call(path, 'PUT', {**entry, 'amount': -1}, 400)
    call(path, 'PUT', {**entry, 'unit': 'IU'}, 400)
    call(path, 'PUT', {**entry, 'status': 'skipped'}, 400)
    saved = call(path, 'PUT', entry)
    assert saved['id'] == record_id and saved['amount'] == 1.25
    call(path, 'PUT', entry, 409)
    updated = call(path, 'PUT', {**entry, 'revision': saved['revision'], 'notes': 'Edited fixture'})
    assert updated['revision'] != saved['revision']
    call(path + '?revision=' + saved['revision'], 'DELETE', expected=409)
    assert len(call(MEDICATIONS)) == 1
    return updated


def after_restart(request, record):
    code, raw = request(8450, MEDICATIONS)
    assert code == 200 and json.loads(raw) == [record]
    code, raw = request(8450, GOOGLE)
    status = json.loads(raw)
    assert code == 200 and status['configured'] and not status['connected']
    path = MEDICATIONS + '/' + record['id']
    skipped = {**record, 'status': 'skipped', 'amount': None}
    code, raw = request(8450, path, 'PUT', body=skipped)
    result = json.loads(raw)
    assert code == 200 and result['status'] == 'skipped' and result.get('amount') is None
    assert request(8450, path + '?revision=' + result['revision'], 'DELETE')[0] == 204
    code, raw = request(8450, MEDICATIONS)
    assert code == 200 and json.loads(raw) == []


STORAGE_PROBE = '''
import os, re, sys, uuid
from pathlib import Path
sys.path.insert(0, '/opt/nocturne-ha')
import run
identity = os.environ.get('NOCTURNE_CI_FIXTURE', '')
assert re.fullmatch(r'nocturne-ci-[0-9a-f]{32}', identity)
assert Path('/data/.disposable-ci').read_text() == identity
assert not os.environ.get('SUPERVISOR_TOKEN')
tenant = str(uuid.UUID(run.psql(database='nocturne', sql='SELECT id FROM tenants')))
assert run.psql(database='nocturne', sql="SELECT count(*) FROM personal_google_connections WHERE protected_settings LIKE '%ci-not-a-real-google-secret%'") == '0'
for table in ('personal_google_connections', 'personal_health_readings', 'personal_medications'):
    assert run.psql(database='nocturne', sql=f"SELECT relrowsecurity AND relforcerowsecurity FROM pg_class WHERE relname='{table}'") == 't'
run.psql(database='nocturne', sql=f"""
BEGIN;
SET LOCAL ROLE nocturne_app;
SELECT set_config('app.current_tenant_id', '', true);
DO $$ BEGIN
  IF (SELECT count(*) FROM personal_medications) <> 0 THEN RAISE EXCEPTION 'tenant isolation failed'; END IF;
END $$;
SELECT set_config('app.current_tenant_id', '{tenant}', true);
SELECT set_config('app.is_share', 'true', true);
DO $$ BEGIN
  IF (SELECT count(*) FROM personal_medications) <> 0 THEN RAISE EXCEPTION 'share isolation failed'; END IF;
END $$;
SELECT set_config('app.is_share', 'false', true);
DO $$ BEGIN
  IF (SELECT count(*) FROM personal_medications) <> 1 THEN RAISE EXCEPTION 'tenant visibility failed'; END IF;
END $$;
ROLLBACK;
""")
'''
