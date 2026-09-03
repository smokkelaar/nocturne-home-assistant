"""Exercise real nginx routing with disposable local HTTP backends and tokens.

Run in the disposable smoke container, or pass a local wrapper helper directory.
No production services, credentials or health data are read.
"""
import base64
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
import os
from pathlib import Path
import pwd
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
import time


class Backend(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({
            'backend': self.server.label,
            'path': self.path,
            'authorization': self.headers.get('Authorization', ''),
            'cookie': self.headers.get('Cookie', ''),
            'instance_key': self.headers.get('X-Instance-Key', ''),
            'instance_service': self.headers.get('X-Instance-Service', ''),
        }).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        pass


def main():
    code = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('/opt/nocturne-ha')
    if len(sys.argv) == 1:
        assert Path('/data/.disposable-ci').is_file(), 'Disposable fixture required'
    spec = importlib.util.spec_from_file_location('gateway_probe_settings', code / 'settings.py')
    settings = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(settings)
    nginx = os.environ.get('NOCTURNE_TEST_NGINX', 'nginx')
    module = os.environ.get('NOCTURNE_TEST_NJS', '/usr/lib/nginx/modules/ngx_http_js_module.so')
    servers = []
    for label in ('web', 'api'):
        server = ThreadingHTTPServer(('127.0.0.1', 0), Backend)
        server.label = label
        threading.Thread(target=server.serve_forever, daemon=True).start()
        servers.append(server)
    try:
        with tempfile.TemporaryDirectory(prefix='nocturne-oauth-probe-') as directory:
            root = Path(directory)
            cert, key = root / 'cert.pem', root / 'key.pem'
            subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes',
                            '-keyout', str(key), '-out', str(cert), '-days', '1',
                            '-subj', '/CN=homeassistant.local',
                            '-addext', 'subjectAltName=DNS:homeassistant.local'],
                           check=True, capture_output=True, timeout=15)
            basic_file = root / 'htpasswd'
            password_hash = subprocess.run(['openssl', 'passwd', '-apr1', 'fixture-only'],
                                           check=True, capture_output=True, text=True).stdout.strip()
            basic_file.write_text('nocturne:' + password_hash + '\n')
            basic = 'Basic ' + base64.b64encode(b'nocturne:fixture-only').decode()
            for gateway_auth in (False, True):
                with socket.socket() as listener:
                    listener.bind(('127.0.0.1', 0))
                    port = listener.getsockname()[1]
                options = settings.validate_options({
                    'public_url': f'https://homeassistant.local:{port}',
                    'certificate': 'cert.pem', 'private_key': 'key.pem',
                    'gateway_auth': gateway_auth,
                })
                config = settings.nginx_config(options, cert, key)
                # Keep the disposable worker under the fixture owner's identity.
                worker = f'user {pwd.getpwuid(os.getuid()).pw_name};' if os.getuid() == 0 else ''
                config = config.replace('user www-data;', worker)
                temp_paths = '\n'.join(
                    f'  {kind}_temp_path {root / kind};'
                    for kind in ('client_body', 'proxy', 'fastcgi', 'uwsgi', 'scgi'))
                config = config.replace('  access_log off;', '  access_log off;\n' + temp_paths)
                config = config.replace('/usr/lib/nginx/modules/ngx_http_js_module.so', module)
                config = config.replace('/opt/nocturne-ha/cookies.mjs', str(code / 'cookies.mjs'))
                config = config.replace('/run/nocturne/nginx.pid', str(root / 'nginx.pid'))
                config = config.replace('/run/nocturne/gateway.htpasswd', str(basic_file))
                config = config.replace('listen 8448 ssl;', f'listen 127.0.0.1:{port} ssl;')
                for original, server in zip((8000, 8080), servers):
                    config = config.replace(f'127.0.0.1:{original}', f'127.0.0.1:{server.server_port}')
                path = root / 'nginx.conf'
                path.write_text(config)
                subprocess.run([nginx, '-p', str(root), '-t', '-c', str(path)],
                               check=True, capture_output=True, timeout=10)
                process = subprocess.Popen([nginx, '-p', str(root), '-c', str(path), '-g', 'daemon off;'],
                                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                # Trust only the self-created fixture certificate and its hostname.
                context = ssl.create_default_context(cafile=str(cert))

                def request(path, authorization='', cookie='', host=None):
                    connection = http.client.HTTPSConnection('homeassistant.local', port, context=context, timeout=3)
                    # Connect locally without changing DNS or disabling TLS verification.
                    raw = socket.create_connection(('127.0.0.1', port), timeout=3)
                    connection.sock = context.wrap_socket(raw, server_hostname='homeassistant.local')
                    try:
                        headers = {'Host': host or f'homeassistant.local:{port}',
                                   'X-Instance-Key': 'untrusted-fixture',
                                   'X-Instance-Service': 'untrusted-fixture'}
                        if authorization:
                            headers['Authorization'] = authorization
                        if cookie:
                            headers['Cookie'] = cookie
                        connection.request('GET', path, headers=headers)
                        response = connection.getresponse()
                        raw_body = response.read()
                        return response.status, json.loads(raw_body) if response.status == 200 else None
                    finally:
                        connection.close()

                def check(path, auth, expected_backend, expected_auth='', cookie=''):
                    status, body = request(path, auth, cookie)
                    assert status == 200
                    assert body['backend'] == expected_backend
                    assert body['authorization'] == expected_auth
                    assert body['path'] == path
                    assert not body['instance_key'] and not body['instance_service']
                    return body

                try:
                    deadline = time.monotonic() + 8
                    while True:
                        assert process.poll() is None, 'Probe nginx exited'
                        try:
                            request('/health', basic if gateway_auth else '')
                            break
                        except (OSError, http.client.HTTPException):
                            if time.monotonic() >= deadline:
                                raise
                            time.sleep(0.1)
                    protected = '/api/v4/glucose/sensor?limit=1&sort=timestamp_desc'
                    if gateway_auth:
                        assert request(protected, 'Bearer fixture.jwt.token')[0] == 401
                        assert request(protected)[0] == 401
                        check(protected, basic, 'web')
                        check('/api/oauth/test', basic, 'api')
                    else:
                        for token in ('Bearer fixture.jwt.token', 'bearer fixture-opaque_token'):
                            check(protected, token, 'api', token)
                            check('/api/oauth/test', token, 'api', token)
                            assert request('/api/v4/dev-only', token)[0] == 404
                            assert request('/openapi/test', token)[0] == 404
                            assert request(protected, token, host='wrong.example.net')[0] == 421
                        for auth in ('', basic, 'Digest fixture', 'Bearer bad token', 'Bearer'):
                            check(protected, auth, 'web')
                        namespace = options['cookie_namespace']
                        body = check(protected, '', 'web', cookie=(
                            f'{namespace}.Nocturne.AccessToken=fixture-cookie; '
                            'NocturneOther_.Nocturne.AccessToken=foreign; '
                            '.Nocturne.AccessToken=old-unscoped; IsAuthenticated=true'))
                        assert body['cookie'] == '.Nocturne.AccessToken=fixture-cookie'
                        check('/health', '', 'web')
                finally:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)
    finally:
        for server in servers:
            server.shutdown()
            server.server_close()
    print('PASS: real nginx Bearer routing, original URI, browser cookies, Basic gate, host and internal-header filtering')


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        print('OAUTH_GATEWAY_PROBE_FAILED:' + type(error).__name__, file=sys.stderr)
        raise SystemExit(1) from None
