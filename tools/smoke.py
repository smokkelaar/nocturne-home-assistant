"""CI-only container smoke test; creates and removes its OWN disposable volume.

Never run against a user container/volume. No credentials or raw logs are printed.
This checks boot/restart, not WebAuthn, data import, or database upgrade compatibility.
"""
import argparse
from pathlib import Path
import re
import subprocess
import time
import uuid


def docker(*args, check=True, input=None):
    result = subprocess.run(['docker', *args], input=input, text=True, capture_output=True, timeout=180)
    if check and result.returncode:
        # A dedicated probe may emit only this bounded, non-sensitive marker.
        # Never publish arbitrary container output, which can contain secrets.
        marker = re.search(r'NATIVE_PROBE_FAILED:[A-Z_0-9]+:[A-Za-z]+', result.stdout + result.stderr)
        detail = ' (' + marker.group(0) + ')' if marker else ''
        raise RuntimeError('Docker operation failed: ' + args[0] + detail)
    return result.stdout.strip()


def execute(name, code):
    return docker('exec', '-i', name, 'python3', '-', input=code)


PROBE = '''
import json, ssl, urllib.request, urllib.error, base64
from pathlib import Path
import sys
sys.path.insert(0, '/opt/nocturne-ha')
import run
assert run.api_reachable('homeassistant.local')
if hasattr(run, 'web_response_reachable'):  # Baseline 0.1.0 predates this check.
    assert run.web_response_reachable(run.validate_options({}))
context = ssl._create_unverified_context()  # Only the disposable CI test certificate.
base_url = 'https://127.0.0.1:8448'
headers = {'Host': 'homeassistant.local:8448'}
for path in ('/setup', '/health'):
    try:
        urllib.request.urlopen(urllib.request.Request(base_url + path, headers=headers), context=context, timeout=10)
    except urllib.error.HTTPError as e:
        assert e.code == 401
    else:
        raise AssertionError('Gateway accepted unauthenticated request')
secret = json.loads(Path('/data/secrets.json').read_text())['gateway']
headers['Authorization'] = 'Basic ' + base64.b64encode(('nocturne:' + secret).encode()).decode()
with urllib.request.urlopen(urllib.request.Request(base_url + '/setup', headers=headers), context=context, timeout=10) as response:
    assert response.status == 200
    assert b'nocturne' in response.read(2_000_000).lower()
with urllib.request.urlopen(urllib.request.Request(base_url + '/health', headers=headers), context=context, timeout=10) as response:
    assert response.status == 200
    assert response.read(3) == b'ok'
try:
    urllib.request.urlopen('http://127.0.0.1:8099/', timeout=10)
except urllib.error.HTTPError as e:
    assert e.code == 403  # A direct client cannot read the ingress gateway code.
else:
    raise AssertionError('Ingress accepted a direct client')
'''


def wait_ready(name, probe=PROBE):
    deadline = time.monotonic() + 420
    last_error = ''
    while time.monotonic() < deadline:
        if docker('inspect', '--format', '{{.State.Running}}', name) != 'true':
            # Inspect logs ONLY in this disposable test, returning fixed markers
            # instead of publishing raw errors/headers/credentials.
            logs = docker('logs', name, check=False)
            markers = [label for label, signature in (
                ('JS_SYNTAX', 'SyntaxError'), ('JS_REFERENCE', 'ReferenceError'),
                ('NGINX_CONFIG', 'nginx:'), ('JS_NAMESPACE', 'Invalid cookie namespace'),
                ('PY_KEY', 'KeyError'), ('PERMISSION', 'Permission denied'),
            ) if signature in logs]
            raise RuntimeError('Container exited before becoming ready; safe markers: '
                               + (','.join(markers) or 'NONE'))
        try:
            execute(name, probe)
            return
        except RuntimeError as error:
            last_error = str(error)  # docker() only exposes bounded safe markers.
            time.sleep(3)
    raise RuntimeError('Container readiness/authentication smoke test timed out: ' + last_error)


def main(image):
    identity = 'nocturne-ci-' + uuid.uuid4().hex
    volume = identity + '-data'
    docker('volume', 'create', volume)
    try:
        docker('run', '--rm', '-i', '--entrypoint', 'python3', '-v', volume + ':/data', image, '-', input=(
            "from pathlib import Path\nPath('/data/options.json').write_text('{}')\n"
            f"Path('/data/.disposable-ci').write_text('{identity}')\n"))
        # No published host ports and no Supervisor token; never mounts user paths.
        docker('run', '-d', '--name', identity, '-v', volume + ':/data', image)
        wait_ready(identity)
        print('PASS: boot, API, authenticated setup, gateway rejection, ingress isolation')
        print(execute(identity, Path(__file__).with_name('native_gateway_probe.py').read_text()))
        print(execute(identity, Path(__file__).with_name('tls_probe.py').read_text()))
        execute(identity, PROBE)
        before = execute(identity, "import hashlib\nfrom pathlib import Path\nprint(hashlib.sha256(Path('/data/secrets.json').read_bytes()).hexdigest())")
        execute(identity, "import sys\nsys.path.insert(0, '/opt/nocturne-ha')\nimport run\nrun.psql(database='nocturne', sql='CREATE TABLE public.ha_wrapper_smoke (id integer); INSERT INTO public.ha_wrapper_smoke VALUES (42)')")
        docker('stop', '-t', '100', identity)
        if docker('inspect', '--format', '{{.State.ExitCode}}', identity) != '0':
            raise RuntimeError('Container did not stop cleanly')
        docker('start', identity)
        wait_ready(identity)
        after = execute(identity, "import hashlib\nfrom pathlib import Path\nprint(hashlib.sha256(Path('/data/secrets.json').read_bytes()).hexdigest())")
        if before != after:
            raise RuntimeError('Secrets changed on restart')
        execute(identity, "import sys\nsys.path.insert(0, '/opt/nocturne-ha')\nimport run\nassert run.psql(database='nocturne', sql='SELECT id FROM public.ha_wrapper_smoke') == '42'")
        print('PASS: clean stop, restart, persistent secrets and database row')
        # Exercise the actual main() startup with false, not only generated nginx.
        # Deliberately no real enrollment, login, health data, or published ports.
        print(docker('exec', '-i', '-e', 'NOCTURNE_CI_FIXTURE=' + identity,
                     identity, 'python3', '-', input=Path(__file__).with_name(
                         'configured_native_fixture.py').read_text()))
        native_probe = Path(__file__).with_name('configured_native_probe.py').read_text()
        for attempt in range(2):
            docker('stop', '-t', '100', identity)
            if docker('inspect', '--format', '{{.State.ExitCode}}', identity) != '0':
                raise RuntimeError('Native-mode container did not stop cleanly')
            docker('start', identity)
            wait_ready(identity, native_probe)
            after = execute(identity, "import hashlib\nfrom pathlib import Path\nprint(hashlib.sha256(Path('/data/secrets.json').read_bytes()).hexdigest())")
            if before != after:
                raise RuntimeError('Secrets changed in native mode')
        print('PASS: configured native startup and second restart; no Basic prompt; anonymous data 401; stable keys')
    finally:
        # These exact UUID names were created above, never accepted from user input.
        docker('rm', '-f', identity, check=False)
        docker('volume', 'rm', volume, check=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', required=True)
    main(parser.parse_args().image)
