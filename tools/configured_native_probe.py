"""Read-only probes INSIDE smoke.py's disposable, configured native container."""
import http.client
import json
from pathlib import Path
import ssl
import sys

sys.path.insert(0, '/opt/nocturne-ha')
import run

phase = 'CONFIGURED_GUARD'
try:
    options = run.validate_options(json.loads(Path('/data/options.json').read_text()))
    assert options['gateway_auth'] is False
    run.verify_native_auth(options)  # Real upstream status + authorization, no mocks.
    assert run.web_response_reachable(options)

    def probe(path, expected, host=None, body=None):
        connection = http.client.HTTPSConnection(
            '127.0.0.1', 8448, timeout=3,
            context=ssl._create_unverified_context())  # Only the disposable CI certificate.
        try:
            connection.request('GET', path, headers={'Host': host or options['authority']})
            response = connection.getresponse()
            assert response.status == expected
            assert not response.getheader('WWW-Authenticate', '').startswith('Basic')
            if body is not None:
                assert response.read(len(body) + 1) == body
        finally:
            connection.close()

    phase = 'CONFIGURED_HEALTH'
    probe('/health', 200, body=b'ok')
    phase = 'CONFIGURED_DATA_DENIAL'
    probe('/api/v4/ChartData/dashboard', 401)
    phase = 'CONFIGURED_HOST'
    probe('/health', 421, host='wrong.example.net')
    phase = 'CONFIGURED_DEV_BLOCK'
    probe('/api/v4/dev-only', 404)
except BaseException as error:
    print(f'NATIVE_PROBE_FAILED:{phase}:{type(error).__name__}', file=sys.stderr)
    raise SystemExit(1) from None
