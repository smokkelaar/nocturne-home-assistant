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
                        'Sec-WebSocket-Protocol': 'tty',
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
# The maintenance listener starts before the application: wait for the deliberate
# startup failure instead of treating that short startup interval as a failure.
for _ in range(20):
    if b'gestopt' in page:
        break
    time.sleep(0.5)
    status, page = request('/maintenance/', AUTH, '172.30.32.2')
assert b'gestopt' in page  # invalid public_url killed Nocturne, not maintenance
config = Path('/run/nocturne-maintenance/nginx.conf').read_text()
terminal = config.split('location /maintenance/terminal/')[1].split('/ {')[0]
path = '/maintenance/terminal/' + terminal + '/'
assert request(path, source='172.30.32.2')[0] == 401
assert request(path, AUTH, '172.30.32.2')[0] == 200
assert request(path + 'ws', source='172.30.32.2', upgrade=True)[0] == 401
assert request(path + 'ws', AUTH, '172.30.32.2', upgrade=True)[0] == 101

# Exercise actual terminal input/output, not merely the HTTP upgrade.
sock = socket.create_connection(('127.0.0.1', 8099), timeout=10,
                               source_address=('172.30.32.2', 0))
sock.sendall((f'GET {path}ws HTTP/1.1\r\nHost: ha.example.test\r\n'
              f'Authorization: {AUTH}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n'
              'Sec-WebSocket-Version: 13\r\nSec-WebSocket-Protocol: tty\r\n'
              'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n\r\n').encode())
headers = b''
while not headers.endswith(b'\r\n\r\n'):
    headers += sock.recv(1)
assert b'101 Switching Protocols' in headers


def send_frame(payload):
    payload = payload.encode()
    mask = b'\x12\x34\x56\x78'
    assert len(payload) < 126
    sock.sendall(bytes([0x81, 0x80 | len(payload)]) + mask +
                 bytes(value ^ mask[index % 4] for index, value in enumerate(payload)))


def exact(count):
    data = b''
    while len(data) < count:
        chunk = sock.recv(count - len(data))
        if not chunk:
            raise AssertionError('Terminal closed before command completed')
        data += chunk
    return data


send_frame(json.dumps({'AuthToken': '', 'columns': 80, 'rows': 24}))
send_frame("0printf 'CLI_SAFE_%s\\n' SMOKE\n")
output = b''
for _ in range(30):
    first, second = exact(2)
    length = second & 127
    if length == 126:
        length = struct.unpack('!H', exact(2))[0]
    elif length == 127:
        length = struct.unpack('!Q', exact(8))[0]
    assert length < 1_000_000
    payload = exact(length)
    if first & 15 in (1, 2):
        output += payload
    if b'CLI_SAFE_SMOKE' in output:
        break
else:
    raise AssertionError('Terminal command output missing')
sock.close()
assert subprocess.run(['nocturne-ha', 'doctor'], capture_output=True).returncode == 0
assert subprocess.run(['nocturne-ha', 'recover', '--url', 'https://new.example.net:8450'],
                      capture_output=True).returncode == 0
print('MAINTENANCE_SMOKE_OK: ingress auth, terminal/websocket, failed-start recovery, CLI')
