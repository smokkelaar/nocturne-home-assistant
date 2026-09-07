"""Synthetic checks called only inside cookie_smoke.py's disposable CI fixtures.

Never follows the Google authorize URL, contacts Google or uses real health data.
"""
import json
from urllib.parse import parse_qs, urlsplit

GOOGLE = '/api/v4/google-health'


class ProbeHttpError(AssertionError):
    def __init__(self, actual, expected):
        self.actual = int(actual)
        self.expected = int(expected)
        super().__init__('Unexpected HTTP status')


def expect_status(actual, expected):
    if actual != expected:
        raise ProbeHttpError(actual, expected)


def complete_fixture_onboarding(request, anonymous):
    """Complete normal onboarding through the API, only for the disposable owner.

    Seeding a nonfunctional credential is enough for API readiness, but the web
    UI correctly redirects to setup until the owner finishes onboarding. Do not
    forge the setup cookie or bypass that guard in application code.
    """
    endpoint = '/api/auth/passkey/onboarding/complete'
    expect_status(request(8450, endpoint, 'POST', opener=anonymous)[0], 401)
    code, raw = request(8450, '/api/auth/passkey/status')
    expect_status(code, 200)
    assert json.loads(raw)['onboardingCompleted'] is False
    expect_status(request(8450, '/settings/connectors/google-health')[0], 303)
    expect_status(request(8450, endpoint, 'POST')[0], 204)
    code, raw = request(8450, '/api/auth/passkey/status')
    expect_status(code, 200)
    assert json.loads(raw)['onboardingCompleted'] is True


def exercise(request, anonymous):
    def call(path, method='GET', body=None, expected=200):
        code, raw = request(8450, path, method, body=body)
        expect_status(code, expected)
        return json.loads(raw) if raw and expected == 200 else None

    expect_status(request(8450, GOOGLE, opener=anonymous)[0], 401)
    expect_status(request(8450, '/settings/connectors/google-health')[0], 200)
    expect_status(request(8450, '/personal')[0], 404)
    expect_status(request(8450, '/personal/medications')[0], 404)
    expect_status(request(8450, '/api/v4/personal/medications')[0], 404)
    expect_status(request(8450, '/personal/google')[0], 404)
    status = call(GOOGLE)
    assert status['configured'] is False and status['connected'] is False
    assert {c['dataType'] for c in status['capabilities'] if c['supported']} == {'steps', 'heart-rate', 'weight', 'sleep'}
    options = dict(clientId='ci-fixture.apps.googleusercontent.com',
                   clientSecret='ci-not-a-real-google-secret',
                   callbackUrl='https://homeassistant.local:8450/settings/connectors/google-health/callback',
                   dataTypes=['steps', 'heart-rate', 'weight'], historyDays=7)
    call(GOOGLE + '/options', 'PUT', {**options, 'dataTypes': ['body-fat']}, 400)
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

    return None


def after_restart(request, record):
    code, raw = request(8450, GOOGLE)
    status = json.loads(raw)
    assert code == 200 and status['configured'] and not status['connected']


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
assert run.psql(database='nocturne', sql="SELECT count(*) FROM google_health_connections WHERE protected_settings LIKE '%ci-not-a-real-google-secret%'") == '0'
for table in ('google_health_connections', 'google_health_readings'):
    assert run.psql(database='nocturne', sql=f"SELECT relrowsecurity AND relforcerowsecurity FROM pg_class WHERE relname='{table}'") == 't'
run.psql(database='nocturne', sql=f"""
BEGIN;
SET LOCAL ROLE nocturne_app;
SELECT set_config('app.current_tenant_id', '', true);
DO $$ BEGIN
  IF (SELECT count(*) FROM google_health_connections) <> 0 THEN RAISE EXCEPTION 'tenant isolation failed'; END IF;
END $$;
SELECT set_config('app.current_tenant_id', '{tenant}', true);
SELECT set_config('app.is_share', 'true', true);
DO $$ BEGIN
  IF (SELECT count(*) FROM google_health_connections) <> 0 THEN RAISE EXCEPTION 'share isolation failed'; END IF;
END $$;
SELECT set_config('app.is_share', 'false', true);
DO $$ BEGIN
  IF (SELECT count(*) FROM google_health_connections) <> 1 THEN RAISE EXCEPTION 'tenant visibility failed'; END IF;
END $$;
ROLLBACK;
""")
'''
