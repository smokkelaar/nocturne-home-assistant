"""CI-only container smoke test; creates and removes its OWN disposable volume.

Never run against a user container/volume. No credentials or raw logs are printed.
This checks boot/restart, not WebAuthn, data import, or database upgrade compatibility.
"""
import argparse
from pathlib import Path
import subprocess
import time
import uuid


def docker(*args, check=True, input=None):
    result = subprocess.run(['docker', *args], input=input, text=True, capture_output=True, timeout=180)
    if check and result.returncode:
        raise RuntimeError('Docker operation failed: ' + args[0])
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
url = 'https://127.0.0.1:8448/setup'
headers = {'Host': 'homeassistant.local:8448'}
try:
    urllib.request.urlopen(urllib.request.Request(url, headers=headers), context=context, timeout=10)
except urllib.error.HTTPError as e:
    assert e.code == 401
else:
    raise AssertionError('Gateway accepted unauthenticated request')
secret = json.loads(Path('/data/secrets.json').read_text())['gateway']
headers['Authorization'] = 'Basic ' + base64.b64encode(('nocturne:' + secret).encode()).decode()
with urllib.request.urlopen(urllib.request.Request(url, headers=headers), context=context, timeout=10) as response:
    assert response.status == 200
    assert b'nocturne' in response.read(2_000_000).lower()
try:
    urllib.request.urlopen('http://127.0.0.1:8099/', timeout=10)
except urllib.error.HTTPError as e:
    assert e.code == 403  # A direct client cannot read the ingress gateway code.
else:
    raise AssertionError('Ingress accepted a direct client')
'''


def wait_ready(name):
    deadline = time.monotonic() + 420
    while time.monotonic() < deadline:
        if docker('inspect', '--format', '{{.State.Running}}', name) != 'true':
            raise RuntimeError('Container exited before becoming ready (inspect CI locally; no raw logs published)')
        try:
            execute(name, PROBE)
            return
        except RuntimeError:
            time.sleep(3)
    raise RuntimeError('Container readiness/authentication smoke test timed out')


def main(image):
    identity = 'nocturne-ci-' + uuid.uuid4().hex
    volume = identity + '-data'
    docker('volume', 'create', volume)
    try:
        docker('run', '--rm', '-i', '--entrypoint', 'python3', '-v', volume + ':/data', image, '-', input=(
            "from pathlib import Path\nPath('/data/options.json').write_text('{}')\n"))
        # No published host ports and no Supervisor token; never mounts user paths.
        docker('run', '-d', '--name', identity, '-v', volume + ':/data', image)
        wait_ready(identity)
        print('PASS: boot, API, authenticated setup, gateway rejection, ingress isolation')
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
    finally:
        # These exact UUID names were created above, never accepted from user input.
        docker('rm', '-f', identity, check=False)
        docker('volume', 'rm', volume, check=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', required=True)
    main(parser.parse_args().image)
