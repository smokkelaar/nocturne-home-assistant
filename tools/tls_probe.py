"""Executed INSIDE the disposable smoke container, never an existing HA app.

The source test pair is deliberately staggered; /ssl production input is read-only.
Only status assertions are returned; keys and database timestamps are not printed.
"""
from pathlib import Path
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, '/opt/nocturne-ha')
import run
from tls import inspect_pair, peer_fingerprint

hostname = 'homeassistant.local'
data = Path('/data/tls')
assert (data / 'hostname').read_text() == hostname
old = peer_fingerprint(hostname)
database_started = run.psql('SELECT pg_postmaster_start_time()')
with tempfile.TemporaryDirectory() as directory:
    cert, key = Path(directory) / 'new.crt', Path(directory) / 'new.key'
    subprocess.run(['openssl', 'req', '-x509', '-newkey', 'ec', '-pkeyopt', 'ec_paramgen_curve:prime256v1',
                    '-nodes', '-days', '30', '-keyout', str(key), '-out', str(cert), '-subj', '/CN=' + hostname,
                    '-addext', 'subjectAltName=DNS:' + hostname], check=True, capture_output=True, timeout=15)
    expected = inspect_pair(cert, key, hostname).leaf_sha256
    assert expected != old
    (data / 'test.crt').write_bytes(cert.read_bytes())
    # At least two polling intervals: the mismatched pair must never be loaded.
    deadline = time.monotonic() + 40
    while time.monotonic() < deadline:
        assert peer_fingerprint(hostname) == old
        time.sleep(2)
    (data / 'test.key').write_bytes(key.read_bytes())
    deadline = time.monotonic() + 65
    while time.monotonic() < deadline:
        if peer_fingerprint(hostname) == expected:
            break
        time.sleep(2)
    else:
        raise AssertionError('Renewed certificate was not loaded')
assert run.psql('SELECT pg_postmaster_start_time()') == database_started
assert run.api_reachable(hostname)
print('PASS: mismatched renewal retained old TLS; corrected pair loaded without database restart')
