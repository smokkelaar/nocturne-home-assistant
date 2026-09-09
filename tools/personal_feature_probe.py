"""Year Overview checks called only inside cookie_smoke.py's disposable fixtures."""
import json

YEAR_OVERVIEW = '/reports/year-overview?isDefault=true'


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
    expect_status(request(8450, YEAR_OVERVIEW)[0], 303)
    expect_status(request(8450, endpoint, 'POST')[0], 204)
    code, raw = request(8450, '/api/auth/passkey/status')
    expect_status(code, 200)
    assert json.loads(raw)['onboardingCompleted'] is True


def exercise(request, anonymous):
    expect_status(request(8450, YEAR_OVERVIEW, opener=anonymous)[0], 303)
    expect_status(request(8450, YEAR_OVERVIEW)[0], 200)
    expect_status(request(8450, '/personal')[0], 404)
    expect_status(request(8450, '/personal/medications')[0], 404)
    expect_status(request(8450, '/api/v4/personal/medications')[0], 404)
    expect_status(request(8450, '/personal/google')[0], 404)

    return None


def after_restart(request, record):
    expect_status(request(8450, YEAR_OVERVIEW)[0], 200)


STORAGE_PROBE = '''
import os, re, sys
from pathlib import Path
sys.path.insert(0, '/opt/nocturne-ha')
import run
identity = os.environ.get('NOCTURNE_CI_FIXTURE', '')
assert re.fullmatch(r'nocturne-ci-[0-9a-f]{32}', identity)
assert Path('/data/.disposable-ci').read_text() == identity
assert not os.environ.get('SUPERVISOR_TOKEN')
assert run.psql(database='nocturne', sql="SELECT count(*) FROM connector_configurations WHERE connector_name='GoogleHealth'") == '0'
for table in ('google_health_connections', 'google_health_readings'):
    assert run.psql(database='nocturne', sql=f"SELECT COALESCE(to_regclass('public.{table}')::text, '')") == ''
'''
