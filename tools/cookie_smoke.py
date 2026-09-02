"""CI-only: isolated real apps, same-host cookie jar, synthetic sessions, no host ports.

Never accepts a user's containers or volumes. No real passkey ceremony or health
data. Temporary refresh tokens and HTTP bodies remain in memory, never in logs.
"""
import argparse
import http.client
import http.cookiejar
import json
from pathlib import Path
import socket
import ssl
import sys
import urllib.error
import urllib.request
import uuid

from smoke import docker, wait_ready


SEED_SESSION = '''
import hashlib, json, os, re, secrets, sys, uuid
from pathlib import Path
sys.path.insert(0, '/opt/nocturne-ha')
import run
identity = os.environ.get('NOCTURNE_CI_FIXTURE', '')
assert re.fullmatch(r'nocturne-ci-[0-9a-f]{32}', identity)
assert Path('/data/.disposable-ci').read_text() == identity
assert not os.environ.get('SUPERVISOR_TOKEN')
assert run.psql(database='nocturne', sql='SELECT count(*) FROM tenants') == '1'
subject = str(uuid.UUID(run.psql(database='nocturne',
    sql="SELECT id FROM subjects WHERE username='ha-ci-owner'")))
token = secrets.token_urlsafe(48)
digest = hashlib.sha256(token.encode()).hexdigest()
run.psql(database='nocturne', sql=f"""
    INSERT INTO refresh_tokens
        (id, token_hash, subject_id, oidc_session_id, issued_at, expires_at, created_at, updated_at)
    VALUES ('{uuid.uuid4()}', '{digest}', '{subject}', '{uuid.uuid4()}',
            now(), now() + interval '1 hour', now(), now())
""")
print(json.dumps({'subject': subject, 'refresh': token}))
'''


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def cookie(name, value):
    return http.cookiejar.Cookie(
        0, name, value, None, False, 'homeassistant.local', False, False,
        '/', True, True, None, True, None, None, {}, False)


def main(official, latest, personal=None):
    containers, volumes, routes = [], [], {}
    phase = 'START'
    try:
        instances = []
        targets = [(official, 8448, 'NocturneOfficial_'), (latest, 8449, 'NocturneLatest_')]
        if personal:
            targets.append((personal, 8450, 'NocturnePersonal_'))
        for image, port, prefix in targets:
            phase = 'BOOT_' + str(port)
            name = 'nocturne-ci-' + uuid.uuid4().hex
            volume = name + '-data'
            volumes.append(volume)
            docker('volume', 'create', volume)
            docker('run', '--rm', '-i', '--entrypoint', 'python3', '-v', volume + ':/data', image, '-', input=(
                "from pathlib import Path\nPath('/data/options.json').write_text('{}')\n"
                f"Path('/data/.disposable-ci').write_text('{name}')\n"))
            containers.append(name)
            docker('run', '-d', '--name', name, '-v', volume + ':/data', image)
            wait_ready(name)
            docker('exec', '-i', '-e', 'NOCTURNE_CI_FIXTURE=' + name, name, 'python3', '-',
                   input=Path(__file__).with_name('configured_native_fixture.py').read_text())
            docker('stop', '-t', '100', name)
            docker('start', name)
            wait_ready(name, Path(__file__).with_name('configured_native_probe.py').read_text())
            routes[port] = docker('inspect', '--format',
                                 '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}', name)
            # Only the fixture just created above is accepted; not shipped in the image.
            session = json.loads(docker('exec', '-i', '-e', 'NOCTURNE_CI_FIXTURE=' + name,
                                        name, 'python3', '-', input=SEED_SESSION))
            instances.append((name, port, prefix, session))

        # Virtual URLs share one DNS hostname, just like a browser. Only their TCP
        # route is replaced with the corresponding unpublished Docker IP/port.
        class Connection(http.client.HTTPSConnection):
            def connect(self):
                assert self.host == 'homeassistant.local' and self.port in routes
                sock = socket.create_connection((routes[self.port], 8448), timeout=self.timeout)
                self.sock = self._context.wrap_socket(sock, server_hostname=self.host)

        class Handler(urllib.request.HTTPSHandler):
            def https_open(self, req):
                return self.do_open(Connection, req, context=ssl._create_unverified_context())
                # Untrusted TLS is allowed ONLY for these synthetic CI certificates.

        jar = http.cookiejar.CookieJar()
        browser = urllib.request.build_opener(urllib.request.ProxyHandler({}), Handler(),
                                             urllib.request.HTTPCookieProcessor(jar), NoRedirect())
        anonymous = urllib.request.build_opener(urllib.request.ProxyHandler({}), Handler(), NoRedirect())

        def request(port, path, method='GET', opener=browser, raw_cookie=None):
            base = f'https://homeassistant.local:{port}'
            headers = {'Origin': base, 'Content-Type': 'application/json'}
            if raw_cookie is not None:
                headers['Cookie'] = raw_cookie
            req = urllib.request.Request(base + path, headers=headers, method=method,
                                         data=b'{}' if method == 'POST' else None)
            try:
                response = opener.open(req, timeout=30)
            except urllib.error.HTTPError as error:
                response = error
            with response:
                # Test responses contain synthetic owner metadata only. Never print.
                return response.status, response.read(2_000_000)

        def session_for(port, expected, subject=None, opener=browser, raw_cookie=None):
            code, raw = request(port, '/api/auth/oidc/session', opener=opener, raw_cookie=raw_cookie)
            assert code == 200
            result = json.loads(raw)
            assert result['isAuthenticated'] is expected
            if subject:
                assert result['subjectId'] == subject

        def values(prefix):
            return {c.name: c.value for c in jar if c.name.startswith(prefix)}

        for _, port, prefix, seed in instances:
            phase = 'SSR_ROTATION_' + str(port)
            jar.set_cookie(cookie(prefix + '.Nocturne.RefreshToken', seed['refresh']))
            jar.set_cookie(cookie(prefix + 'IsAuthenticated', 'true'))
            # The real SSR auth handler refreshes the synthetic session. Its
            # internal Set-Cookie must survive SvelteKit AND the nginx edge.
            code, _ = request(port, '/auth/login')
            assert code in (200, 302, 303)
            assert prefix + '.Nocturne.AccessToken' in values(prefix)
            session_for(port, True, seed['subject'])

        phase = 'INTERLEAVED_SESSIONS'
        for _ in range(3):
            for _, port, _, seed in instances:
                session_for(port, True, seed['subject'])
        for _, port, prefix, seed in instances:
            phase = 'EXPLICIT_ROTATION_' + str(port)
            previous = {other: values(other) for _, other_port, other, _ in instances if other_port != port}
            assert request(port, '/api/auth/oidc/refresh', 'POST')[0] == 200
            assert all(values(other) == saved for other, saved in previous.items())
            session_for(port, True, seed['subject'])

        phase = 'LEGACY_AND_HINT_DENIAL'
        for _, port, prefix, _ in instances:
            token = values(prefix)[prefix + '.Nocturne.AccessToken']
            for raw in ['IsAuthenticated=true', '.Nocturne.AccessToken=' + token]:
                session_for(port, False, opener=anonymous, raw_cookie=raw)
                assert request(port, '/api/v4/ChartData/dashboard', opener=anonymous,
                               raw_cookie=raw)[0] == 401

        phase = 'LOGOUT_ONLY_OFFICIAL'
        other = values('NocturneLatest_')
        assert request(8448, '/api/auth/oidc/logout', 'POST')[0] == 200
        assert values('NocturneLatest_') == other
        session_for(8448, False)
        session_for(8449, True, instances[1][3]['subject'])
        if personal:
            phase = 'PERSONAL_SURVIVES_OTHER_LOGOUT_AND_OWN_RESTART'
            session_for(8450, True, instances[2][3]['subject'])
            name = instances[2][0]
            docker('stop', '-t', '100', name)
            docker('start', name)
            wait_ready(name, Path(__file__).with_name('configured_native_probe.py').read_text())
            routes[8450] = docker('inspect', '--format',
                                 '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}', name)
            session_for(8450, True, instances[2][3]['subject'])
            other = values('NocturneLatest_')
            assert request(8450, '/api/auth/oidc/logout', 'POST')[0] == 200
            assert values('NocturneLatest_') == other
            session_for(8449, True, instances[1][3]['subject'])
            session_for(8450, False)
            assert request(8450, '/api/v4/ChartData/dashboard')[0] == 401
        assert request(8448, '/api/v4/ChartData/dashboard')[0] == 401

        phase = 'LATEST_SESSION_AFTER_RESTART'
        name = instances[1][0]
        docker('stop', '-t', '100', name)
        docker('start', name)
        wait_ready(name, Path(__file__).with_name('configured_native_probe.py').read_text())
        routes[8449] = docker('inspect', '--format',
                             '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}', name)
        session_for(8449, True, instances[1][3]['subject'])
        print('PASS: real channel SSR rotation, shared cookie jar, session refresh, isolated logout, restart, legacy/hint denial; channels=' + str(len(instances)))
    except BaseException as error:
        print(f'COOKIE_PROBE_FAILED:{phase}:{type(error).__name__}', file=sys.stderr)
        raise SystemExit(1) from None
    finally:
        # Exact generated UUID names only; never accepts user containers/volumes.
        for name in containers:
            docker('rm', '-f', name, check=False)
        for name in volumes:
            docker('volume', 'rm', name, check=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--official', required=True)
    parser.add_argument('--latest', required=True)
    parser.add_argument('--personal')
    args = parser.parse_args()
    main(args.official, args.latest, args.personal)
