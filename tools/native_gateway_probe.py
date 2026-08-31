"""Run INSIDE the disposable smoke container, never an existing HA app.

Test the opt-in nginx configuration against the real, still-unconfigured
Nocturne services, on an unpublished extra loopback port. This does not prove
login for an existing account; that remains a manual acceptance test.
"""
from pathlib import Path
import re
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

sys.path.insert(0, '/opt/nocturne-ha')
import run
from settings import nginx_config, validate_options

phase = 'BOOTSTRAP_GUARD'
try:
    options = validate_options({'public_url': 'https://homeassistant.local:18448',
                                'certificate': 'ci.crt', 'private_key': 'ci.key', 'gateway_auth': False})
    try:
        run.verify_native_auth(options)
    except ValueError as error:
        assert str(error).startswith('GATEWAY_SETUP:'), 'Unexpected bootstrap guard result'
    else:
        raise AssertionError('Native mode accepted a fresh instance without an owner account')

# Read only this fixture's nginx paths, never publish certificates or logs.
    phase = 'READ_FIXTURE'
    existing = Path('/run/nocturne/nginx.conf').read_text()
    cert = re.search(r'^\s+ssl_certificate (.+);$', existing, re.M).group(1)
    key = re.search(r'^\s+ssl_certificate_key (.+);$', existing, re.M).group(1)
    context = ssl._create_unverified_context()  # Only this disposable CI certificate.


    def request(path, host='homeassistant.local:18448'):
        request = urllib.request.Request('https://127.0.0.1:18448' + path, headers={'Host': host})
        try:
            return urllib.request.urlopen(request, context=context, timeout=3)
        except urllib.error.HTTPError as error:
            return error


    with tempfile.TemporaryDirectory(prefix='native-gateway-ci-', dir='/run/nocturne') as directory:
        phase = 'NGINX_CONFIG'
        config = nginx_config(options, cert, key)
        config = config.replace('listen 8448 ssl;', 'listen 127.0.0.1:18448 ssl;')
        config = config.replace('pid /run/nocturne/nginx.pid;', f'pid {directory}/nginx.pid;')
        path = Path(directory) / 'nginx.conf'
        path.write_text(config)
        subprocess.run(['nginx', '-t', '-c', str(path)], check=True, capture_output=True, timeout=10)
        process = subprocess.Popen(['nginx', '-c', str(path), '-g', 'daemon off;'],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            phase = 'HEALTH'
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                assert process.poll() is None, 'Native nginx fixture exited early'
                try:
                    with request('/health') as response:
                        assert response.status == 200
                        assert response.read(3) == b'ok'
                        assert not response.headers.get('WWW-Authenticate', '').startswith('Basic')
                    break
                except urllib.error.URLError:
                    time.sleep(0.2)
            else:
                raise AssertionError('Native nginx fixture did not start')
            phase = 'WRONG_HOST'
            with request('/health', 'wrong.example.net:18448') as response:
                assert response.status == 421
            phase = 'DATA_DENIAL'
            with request('/api/v4/ChartData/dashboard') as response:
                # No owner has been created: Nocturne itself must still reject data
                # access. Its startup guard prevents using this state in native mode.
                assert response.status in (401, 503)
                assert not response.headers.get('WWW-Authenticate', '').startswith('Basic')
            phase = 'DEV_BLOCK'
            with request('/api/v4/dev-only') as response:
                assert response.status == 404
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
except BaseException as error:
    print(f'NATIVE_PROBE_FAILED:{phase}:{type(error).__name__}', file=sys.stderr)
    raise
else:
    print('PASS: native nginx has no Basic prompt; canonical host enforced; fresh-owner guard and data denial preserved')
