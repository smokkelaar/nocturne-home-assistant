"""Run inside disposable CI container only, never against user storage."""
import base64
import http.client
import json
from pathlib import Path
import socket
import struct
import subprocess
import time

PASSWORD = 'ci-disposable-maintenance-password'
AUTH = 'Basic ' + base64.b64encode(('maintenance:' + PASSWORD).encode()).decode()


def request(path, auth=None, source=None, upgrade=False):
    connection = http.client.HTTPConnection('127.0.0.1', 8099, timeout=5,
        source_address=(source, 0) if source else None)
    headers = {'Host': 'ha.example.test'}
    if auth:
        headers['Authorization'] = auth
    if upgrade:
        headers.update({'Upgrade': 'websocket', 'Connection': 'Upgrade',
                        'Sec-WebSocket-Version': '13',
                        'Sec-WebSocket-Key': 'dGhlIHNhbXBsZSBub25jZQ=='})
    connection.request('GET', path, headers=headers)
    response = connection.getresponse()
    status = response.status
    body = response.read() if status != 101 else b''
    connection.close()
    return status, body


subprocess.run(['ip', 'address', 'add', '172.30.32.2/32', 'dev', 'lo'], check=True)
for _ in range(60):
    try:
        if request('/maintenance/')[0] == 403:
            break
    except OSError:
        pass
    time.sleep(1)
else:
    raise AssertionError('maintenance listener not ready')
assert request('/maintenance/', AUTH)[0] == 403  # direct clients, even with password
assert request('/maintenance/', source='172.30.32.2')[0] == 401
assert request('/maintenance/', 'Basic d3Jvbmc6d3Jvbmc=', '172.30.32.2')[0] == 401
status, page = request('/maintenance/', AUTH, '172.30.32.2')
assert status == 200 and b'Herstelwizard' in page
assert PASSWORD.encode() not in page
assert b'gestopt' in page  # invalid public_url killed Nocturne, not maintenance
config = Path('/run/nocturne-maintenance/nginx.conf').read_text()
terminal = config.split('location /maintenance/terminal/')[1].split('/ {')[0]
path = '/maintenance/terminal/' + terminal + '/'
assert request(path, source='172.30.32.2')[0] == 401
assert request(path, AUTH, '172.30.32.2')[0] == 200
assert request(path + 'ws', source='172.30.32.2', upgrade=True)[0] == 401
assert request(path + 'ws', AUTH, '172.30.32.2', upgrade=True)[0] == 101
assert subprocess.run(['nocturne-ha', 'doctor'], capture_output=True).returncode == 0
assert subprocess.run(['nocturne-ha', 'recover', '--url', 'https://new.example.net:8450'],
                      capture_output=True).returncode == 0
print('MAINTENANCE_SMOKE_OK: ingress auth, terminal/websocket, failed-start recovery, CLI')
