#!/usr/bin/env python3
"""Supervise one self-contained HA app. A stopped child stops the whole app.

PostgreSQL is shut down LAST, after both clients; /data is never auto-deleted.
The only unauthenticated HTTP listener is reachable exclusively from HA Ingress.
"""
import http.server
import http.client
import json
import os
import signal
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

from settings import (load_secrets, nginx_config, service_environments,
                      status_page, validate_options)
from tls import CertificateWatcher, peer_fingerprint, reload_nginx

DATA = Path('/data')
RUNTIME = Path('/run/nocturne')
PG_BIN = '/usr/lib/postgresql/17/bin/'
BASE = Path(__file__).parent


def log(message):
    print(f'[nocturne-app] {message}', flush=True)


def private_file(path, content, mode=0o600):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    with os.fdopen(fd, 'w') as handle:
        handle.write(content)
    os.chmod(path, mode)


def as_user(name):
    import pwd
    user = pwd.getpwnam(name)
    return dict(user=user.pw_uid, group=user.pw_gid, extra_groups=[])


def owned_dir(path, name, mode=0o700):
    import pwd
    user = pwd.getpwnam(name)
    path.mkdir(parents=True, exist_ok=True)
    os.chown(path, user.pw_uid, user.pw_gid)
    path.chmod(mode)


def psql(sql=None, database='postgres', stdin=None):
    command = [PG_BIN + 'psql', '--no-psqlrc', '-h', str(RUNTIME / 'postgresql'),
               '-U', 'postgres', '-d', database, '-v', 'ON_ERROR_STOP=1', '-At']
    if sql is not None:
        command += ['-c', sql]
    # Do not echo SQL/stderr: bootstrap stdin may contain passwords.
    result = subprocess.run(command, input=stdin, capture_output=True, text=True,
                            cwd='/tmp', timeout=60, **as_user('postgres'))
    if result.returncode:
        raise RuntimeError('PostgreSQL-bootstrapquery mislukt; gegevens zijn behouden')
    return result.stdout.strip()


def bootstrap_database(passwords):
    if psql("SELECT count(*) FROM pg_database WHERE datname='nocturne'") == '0':
        psql('CREATE DATABASE nocturne')
    role_count = psql("SELECT count(*) FROM pg_roles WHERE rolname IN "
                     "('nocturne_app','nocturne_migrator','nocturne_web')")
    if role_count == '3':
        return
    if role_count != '0':
        raise RuntimeError('Onvolledige databaserollen; stop voor onderzoek, geen reset uitgevoerd')
    # Tokens are 64 hex characters, validated by load_secrets; psql quotes SQL values.
    variables = ''.join(f"\\set {role}_password '{passwords[role]}'\n"
                        for role in ('migrator', 'app', 'web'))
    psql(database='nocturne', stdin=variables + (BASE / 'bootstrap.sql').read_text())


def prepare_tls(options):
    if options['certificate']:
        cert, key = Path('/ssl') / options['certificate'], Path('/ssl') / options['private_key']
        if not cert.is_file() or not key.is_file():
            raise ValueError('Ingestelde certificaatbestanden bestaan niet in /ssl')
        return cert, key, False
    directory = DATA / 'tls'
    directory.mkdir(mode=0o700, exist_ok=True)
    cert, key, identity = directory / 'test.crt', directory / 'test.key', directory / 'hostname'
    if cert.exists() and key.exists():
        if not identity.exists() or identity.read_text() != options['hostname']:
            raise ValueError('Testcertificaat hoort bij een andere hostnaam; wijzig niet zomaar public_url')
    else:
        if cert.exists() or key.exists():
            raise ValueError('Onvolledig testcertificaat; bestanden behouden voor onderzoek')
        subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:3072', '-sha256',
                        '-nodes', '-days', '30', '-keyout', str(key), '-out', str(cert),
                        '-subj', f"/CN={options['hostname']}",
                        '-addext', f"subjectAltName=DNS:{options['hostname']}"],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        key.chmod(0o600)
        identity.write_text(options['hostname'])
    log('TESTCERTIFICAAT: vertrouwd HTTPS/accountregistratie nog apart controleren; geen echte gegevens')
    return cert, key, True


def api_reachable(hostname):
    request = urllib.request.Request('http://127.0.0.1:8080/api/v4/status',
                                     headers={'Host': hostname, 'X-Forwarded-Host': hostname,
                                              'X-Forwarded-Proto': 'https'})
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            return response.status == 200
    except urllib.error.HTTPError as err:
        # A fresh Nocturne instance legitimately reports setup_required as 503.
        # Other 503 responses (for example DB failure) are NOT treated as ready.
        if err.code == 503:
            try:
                result = json.loads(err.read(65536))
                return (result.get('setupRequired') is True or result.get('error') == 'setup_required'
                        or result.get('recoveryMode') is True or result.get('error') == 'recovery_mode_active')
            except (ValueError, AttributeError):
                pass
        return False
    except (OSError, TimeoutError):
        return False


def web_reachable():
    try:
        with socket.create_connection(('127.0.0.1', 8000), timeout=1):
            return True
    except OSError:
        return False


def web_response_reachable(options):
    """Check liveness without rendering the dashboard or supplying credentials."""
    connection = http.client.HTTPConnection('127.0.0.1', 8000, timeout=2)
    try:
        connection.request('GET', '/health', headers={'Host': options['authority'],
                           'X-Forwarded-Host': options['authority'], 'X-Forwarded-Proto': 'https'})
        response = connection.getresponse()
        # Pinned Nocturne returns exactly "ok". Reject HTML and redirects;
        # cap the read instead of mistaking a login page for a healthy response.
        return response.status == 200 and response.read(3) == b'ok'
    except (OSError, http.client.HTTPException):
        return False
    finally:
        connection.close()


def verify_native_auth(options):
    """Refuse to remove the outer gate until configured Nocturne enforces login.

    No session, instance key or health data is read. The bounded status document
    is inspected in memory only; the protected probe's response body is ignored.
    """
    headers = {'Host': options['authority'], 'X-Forwarded-Host': options['authority'],
               'X-Forwarded-Proto': 'https'}
    connection = http.client.HTTPConnection('127.0.0.1', 8080, timeout=3)
    try:
        connection.request('GET', '/api/v4/status', headers=headers)
        response = connection.getresponse()
        raw = response.read(65537)
        try:
            status = json.loads(raw) if len(raw) <= 65536 else None
        except (json.JSONDecodeError, UnicodeError):
            status = None
        if isinstance(status, dict) and (status.get('recoveryMode') is True
                                         or status.get('error') == 'recovery_mode_active'):
            raise ValueError('GATEWAY_RECOVERY: Nocturne vraagt accountherstel; zet gateway_auth: true en herstel het bestaande account, wis geen gegevens')
        if isinstance(status, dict) and (status.get('setupRequired') is True
                                        or status.get('error') == 'setup_required'
                                        or status.get('status') == 'setup_required'):
            raise ValueError('GATEWAY_SETUP: voltooi eerst Nocturne-accountaanmaak met gateway_auth: true')
        if response.status != 200:
            raise ValueError(f'GATEWAY_STATUS: statuscontrole gaf HTTP {response.status}; extra toegang blijft vereist')
        if not isinstance(status, dict):
            raise ValueError('GATEWAY_AUTH: ongeldige statusrespons; extra toegang blijft vereist')
        # requireAuthentication is a legacy Nightscout compatibility field.
        # Current upstream main always sets it false, even on a private instance.
        # Check actual anonymous access and the real authorization result below.
        if (status.get('status') != 'ok' or status.get('runtimeState') != 'loaded'
                or status.get('anonymousReadAccess') is not False
                or (status.get('isDemo') is not None and status.get('isDemo') is not False)):
            raise ValueError('GATEWAY_AUTH: geladen private Nocturne-instantie niet bevestigd')
    except (OSError, http.client.HTTPException, json.JSONDecodeError, UnicodeError):
        raise ValueError('GATEWAY_AUTH: Nocturne-aanmelding kon niet veilig worden gecontroleerd') from None
    finally:
        connection.close()

    connection = http.client.HTTPConnection('127.0.0.1', 8080, timeout=3)
    try:
        connection.request('GET', '/api/v4/ChartData/dashboard', headers=headers)
        code = connection.getresponse().status
        if code != 401:
            raise ValueError(f'GATEWAY_AUTH: niet-aangemelde gegevensaanvraag gaf HTTP {code}, verwacht 401')
    except (OSError, http.client.HTTPException):
        raise ValueError('GATEWAY_AUTH: toegangsweigering kon niet veilig worden gecontroleerd') from None
    finally:
        connection.close()


class Supervisor:
    def __init__(self):
        self.stop = threading.Event()
        self.children = []
        self.checks = {'Installatiecontrole': 'nog niet uitgevoerd'}
        self.status = {'PostgreSQL': 'nog niet gestart', 'Nocturne API': 'nog niet gestart',
                       'Nocturne Web': 'nog niet gestart', 'HTTPS': 'nog niet gestart'}

    def start(self, name, command, *, user=None, env=None, cwd=None):
        kwargs = as_user(user) if user else {}
        process = subprocess.Popen(command, cwd=cwd, env=env, start_new_session=True, **kwargs)
        self.children.append((name, process))
        self.status[name] = 'proces gestart; gereedheid wordt gecontroleerd'
        return process

    def check_children(self):
        for name, process in self.children:
            if process.poll() is not None:
                self.status[name] = f'gestopt (code {process.returncode})'
                raise RuntimeError(f'{name} is gestopt (code {process.returncode})')

    def wait_for(self, name, probe, timeout=180):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline and not self.stop.is_set():
            self.check_children()
            if probe():
                self.status[name] = 'gereed'
                log(f'{name}: gereed')
                return
            self.stop.wait(1)
        if self.stop.is_set():
            raise InterruptedError('Stop aangevraagd')
        raise RuntimeError(f'{name} werd niet gereed binnen {timeout} seconden')

    def shutdown(self):
        log('Stoppen: eerst web/API, als laatste PostgreSQL; /data blijft behouden')
        # Parallel termination of the clients avoids starving the DB's grace period.
        clients = [(n, p) for n, p in self.children if n != 'PostgreSQL']
        database = [(n, p) for n, p in self.children if n == 'PostgreSQL']
        for group, sig, grace in ((clients, signal.SIGTERM, 25), (database, signal.SIGINT, 45)):
            for _, process in group:
                if process.poll() is None:
                    process.send_signal(sig)
            deadline = time.monotonic() + grace
            for name, process in group:
                try:
                    process.wait(timeout=max(0.1, deadline - time.monotonic()))
                except subprocess.TimeoutExpired:
                    log(f'{name}: stop-timeout; proces wordt beëindigd')
                    process.kill()
                    process.wait(timeout=5)


def make_handler(supervisor, options, passwords, test_certificate):
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            # Ingress connections originate from Supervisor, not X-Forwarded-For.
            # Ignore any spoofed forwarded headers. Never expose this listener as a host port.
            if self.client_address[0] != '172.30.32.2':
                self.send_error(403)
                return
            if self.path.split('?')[0] != '/':
                self.send_error(404)
                return
            body = status_page(options, supervisor.status, passwords['gateway'], test_certificate,
                               supervisor.checks).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass
    return Handler


def main():
    os.umask(0o077)
    # None of the child applications need even the app-scoped Supervisor token.
    os.environ.pop('SUPERVISOR_TOKEN', None)
    supervisor = Supervisor()
    server = None
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: supervisor.stop.set())
    try:
        versions = json.loads((BASE / 'version.json').read_text())
        log(f"Start {versions['name']} | HA-wrapper {versions['app']} | "
            f"pakket {versions['package']} | Nocturne {versions['nocturne']}")
        options = validate_options(json.loads((DATA / 'options.json').read_text()))
        auth_check = ('Extra gatewaycode ingeschakeld; Nocturne heeft daarnaast zijn eigen aanmelding'
                      if options['gateway_auth'] else 'Zonder extra gatewaycode aangevraagd; startcontrole nog niet afgerond')
        log(auth_check)
        passwords = load_secrets(DATA)
        # Nginx master is root; workers need read access to the htpasswd file only.
        import grp
        RUNTIME.mkdir(parents=True, exist_ok=True)
        os.chown(RUNTIME, 0, grp.getgrnam('www-data').gr_gid)
        # PostgreSQL must traverse this parent; private subdirs/files remain 0700/0600.
        RUNTIME.chmod(0o755)
        owned_dir(RUNTIME / 'postgresql', 'postgres', 0o700)
        owned_dir(DATA / 'postgres', 'postgres')
        cert, key, test_certificate = prepare_tls(options)
        certificates = CertificateWatcher(cert, key, options['hostname'], RUNTIME / 'tls')
        cert, key = certificates.active.cert, certificates.active.key
        supervisor.checks = {**certificates.checks(), 'Toegangscontrole': auth_check}
        handler = make_handler(supervisor, options, passwords, test_certificate)
        server = http.server.ThreadingHTTPServer(('0.0.0.0', 8099), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        log('Appdiensten starten; bestaande appgegevens en sleutels blijven behouden')

        pgdata = DATA / 'postgres'
        if not (pgdata / 'PG_VERSION').exists():
            if any(pgdata.iterdir()):
                raise ValueError('Datamap is niet leeg maar mist PG_VERSION; niets verwijderd')
            password_file = RUNTIME / 'postgresql' / 'init-password'
            private_file(password_file, passwords['postgres'])
            import pwd
            pg_user = pwd.getpwnam('postgres')
            os.chown(password_file, pg_user.pw_uid, pg_user.pw_gid)
            try:
                subprocess.run([PG_BIN + 'initdb', '-D', str(pgdata), '-U', 'postgres',
                                '--auth-local=peer', '--auth-host=scram-sha-256',
                                '--encoding=UTF8', '--locale=C.UTF-8',
                                f'--pwfile={password_file}'], check=True, cwd='/tmp',
                               **as_user('postgres'))
            finally:
                password_file.unlink(missing_ok=True)
        elif (pgdata / 'PG_VERSION').read_text().strip() != '17':
            raise ValueError('Deze proef ondersteunt alleen PostgreSQL 17; geen automatische major-upgrade')
        if not (pgdata / 'global' / 'pg_control').is_file():
            raise ValueError('Onvolledige PostgreSQL-datamap; geen automatische reset')

        supervisor.start('PostgreSQL', [PG_BIN + 'postgres', '-D', str(pgdata),
                         '-k', str(RUNTIME / 'postgresql'), '-c', 'listen_addresses=127.0.0.1',
                         '-c', 'password_encryption=scram-sha-256', '-c', 'log_min_messages=warning',
                         '-c', 'log_statement=none', '-c', 'log_min_error_statement=panic'],
                         user='postgres', cwd='/tmp')
        supervisor.wait_for('PostgreSQL', lambda: subprocess.run(
            [PG_BIN + 'pg_isready', '-h', '127.0.0.1', '-U', 'postgres'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0, 60)
        bootstrap_database(passwords)
        api_env, web_env = service_environments(options, passwords, os.environ.get('TZ', 'Europe/Amsterdam'))
        supervisor.start('Nocturne API', ['dotnet', '/app/Nocturne.API.dll'],
                         user='app', env=api_env, cwd='/app')
        supervisor.wait_for('Nocturne API', lambda: api_reachable(options['hostname']), 300)
        if not options['gateway_auth']:
            verify_native_auth(options)
            auth_check = 'Private Nocturne-instantie bevestigd; anonieme gegevensaanvraag geweigerd (401), geen extra gatewaycode'
            supervisor.checks['Toegangscontrole'] = auth_check
            log('Geen extra gateway-pop-up; verplichte Nocturne-aanmelding en API-toegangsweigering bevestigd')
        supervisor.start('Nocturne Web', ['node', 'server.js'], user='nocturne-web',
                         env=web_env, cwd='/opt/nocturne-web/packages/app')
        supervisor.wait_for('Nocturne Web', lambda: web_response_reachable(options), 120)

        hashed = subprocess.run(['openssl', 'passwd', '-6', '-stdin'], input=passwords['gateway'],
                                text=True, capture_output=True, check=True).stdout.strip()
        authfile = RUNTIME / 'gateway.htpasswd'
        private_file(authfile, f'nocturne:{hashed}\n', 0o640)
        os.chown(authfile, 0, grp.getgrnam('www-data').gr_gid)
        conf = RUNTIME / 'nginx.conf'
        private_file(conf, nginx_config(options, cert, key))
        subprocess.run(['nginx', '-t', '-c', str(conf)], check=True)
        nginx = supervisor.start('HTTPS', ['nginx', '-c', str(conf), '-g', 'daemon off;'])
        # Nginx tests certificate/key parsing with -t; the process must also bind its listener.
        def tls_listener():
            try:
                with socket.create_connection(('127.0.0.1', 8448), timeout=1):
                    return True
            except OSError:
                return False
        supervisor.wait_for('HTTPS', tls_listener, 20)
        last_certificate_check = 0
        last_certificate_error = ''
        log('Alle diensten gestart. Open Webinterface in HA voor status, link en toegangsmodus.')
        while not supervisor.stop.wait(5):
            supervisor.check_children()
            supervisor.status['Nocturne API'] = ('gereed' if api_reachable(options['hostname']) else 'antwoordcontrole mislukt')
            supervisor.status['Nocturne Web'] = ('HTTP-healthcheck geslaagd; passkey-login nog apart testen'
                if web_response_reachable(options) else 'WEB_RESPONSE: geen geldig /health-antwoord')
            if time.monotonic() - last_certificate_check >= 15:
                certificates.poll(lambda snapshot: reload_nginx(
                    nginx, conf, nginx_config(options, snapshot.cert, snapshot.key),
                    snapshot.info.leaf_sha256, options['hostname']))
                last_certificate_check = time.monotonic()
                supervisor.checks = {**certificates.checks(), 'Toegangscontrole': auth_check, 'Laatste certificaatcontrole':
                    time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}
                error = certificates.message if certificates.message.startswith('CERT_') else ''
                if error and error != last_certificate_error:
                    log(error)
                last_certificate_error = error
            try:
                matched = peer_fingerprint(options['hostname']) == certificates.active.info.leaf_sha256
            except OSError:
                matched = False
            supervisor.status['HTTPS'] = ('lokaal TLS-certificaat bevestigd; browservertrouwen nog testen'
                if matched else 'TLS_RESPONSE: lokaal geladen certificaat niet bevestigd')
        return 0
    except InterruptedError:
        return 0
    except Exception as err:
        # Never serialize environment dictionaries, options or password files.
        if isinstance(err, (ValueError, RuntimeError)):
            log(f'STARTFOUT: {err}')
        else:
            log(f'STARTFOUT: {type(err).__name__}; zie de voorafgaande dienstmelding')
        return 1
    finally:
        supervisor.shutdown()
        if server:
            server.shutdown()
            server.server_close()


if __name__ == '__main__':
    raise SystemExit(main())
