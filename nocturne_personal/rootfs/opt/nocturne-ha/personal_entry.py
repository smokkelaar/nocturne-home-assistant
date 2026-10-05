#!/usr/bin/env python3
"""Opt-in Personal ingress/ttyd host, independent of Nocturne/TLS startup."""
import html
import http.server
import json
import os
from pathlib import Path
import secrets
import signal
import subprocess
import threading
import time
from urllib.parse import parse_qs, urlsplit

from maintenance_cli import doctor, recovery_plan

BASE = Path('/opt/nocturne-ha')
DATA = Path('/data')
RUNTIME = Path('/run/nocturne-maintenance')


def enabled_options(raw):
    enabled = raw.get('maintenance_enabled', False)
    if type(enabled) is not bool:
        raise ValueError('maintenance_enabled moet true of false zijn')
    password = raw.get('maintenance_password', '')
    if enabled and (not isinstance(password, str) or not 16 <= len(password) <= 256
                    or any(c in password for c in '\r\n\x00')):
        raise ValueError('Onderhoud vereist een eigen wachtwoord van 16 tot 256 tekens')
    return enabled, password


def nginx_configuration(terminal_path):
    # Unique terminal path is an unguessable CSRF capability in addition to Basic auth.
    # Never enable public host ports, forwarded-IP allowlists or Docker/host access.
    return f'''user www-data;
pid {RUNTIME}/nginx.pid;
error_log stderr warn;
events {{ worker_connections 128; }}
http {{
  access_log off;
  map $http_upgrade $connection_upgrade {{ default upgrade; '' close; }}
  server {{
    listen 8099;
    allow 172.30.32.2;
    deny all;
    add_header Cache-Control "no-store" always;
    add_header Referrer-Policy "no-referrer" always;
    add_header X-Content-Type-Options "nosniff" always;
    location /maintenance/ {{
      auth_basic "Nocturne Personal onderhoud";
      auth_basic_user_file {RUNTIME}/htpasswd;
      proxy_pass http://127.0.0.1:8102;
      proxy_set_header Authorization "";
    }}
    location {terminal_path}/ {{
      auth_basic "Nocturne Personal onderhoud";
      auth_basic_user_file {RUNTIME}/htpasswd;
      proxy_pass http://127.0.0.1:8101;
      proxy_http_version 1.1;
      proxy_set_header Upgrade $http_upgrade;
      proxy_set_header Connection $connection_upgrade;
      proxy_set_header Authorization "";
      proxy_read_timeout 3600s;
      proxy_buffering off;
    }}
    location / {{
      proxy_pass http://127.0.0.1:8100;
      proxy_intercept_errors on;
      error_page 502 503 504 = @maintenance_fallback;
    }}
    location @maintenance_fallback {{
      return 302 maintenance/;
    }}
  }}
}}
'''


def wizard_page(raw, terminal_path, state, target=None):
    report = doctor(raw)
    try:
        plan = recovery_plan(raw, target)
        steps = ''.join('<li>' + html.escape(step) + '</li>' for step in plan['steps'])
        link = '<p><a target="_blank" rel="noopener noreferrer" href="' + html.escape(plan['recovery_url'], quote=True) + '">Open Nocturne-herstel buiten HA</a></p>'
    except ValueError:
        steps = '<li>Vul een geldig HTTPS-domein in en controleer de HA-appconfiguratie.</li>'
        link = ''
    report_html = ''.join('<dt>' + html.escape(key) + '</dt><dd>' + html.escape(str(value)) + '</dd>'
                          for key, value in report.items())
    return f'''<!doctype html><html lang="nl"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Personal onderhoud</title>
<style>body{{font:16px system-ui;background:#101724;color:#e5edf7;max-width:850px;margin:30px auto;padding:20px}}
section{{background:#1d293c;padding:20px;border-radius:12px;margin:20px 0}}a{{color:#80d5fc}}input,button{{padding:10px}}
dt{{font-weight:bold}}dd{{margin:4px 0 15px}}li{{margin:12px 0}}code{{overflow-wrap:anywhere}}</style>
<h1>Nocturne Personal · onderhoudsproef</h1><p><a href="../">Dienststatus</a></p>
<section><h2>1 · CLI</h2><p><code>nocturne-ha doctor</code> · <code>nocturne-ha recover</code> · <code>nocturne-ha api --help</code></p>
<p>CLI-uitvoer kan privégegevens bevatten. Geheimen en commandogeschiedenis worden niet centraal gelogd.</p></section>
<section><h2>2 · Onderhoudsterminal</h2><p><a href="terminal/{terminal_path.rsplit('/', 1)[1]}/">Open terminal</a></p>
<p>De terminal heeft rootrechten binnen alleen deze app-container. Verkeerde opdrachten kunnen gegevens beschadigen.
Maak eerst een HA-back-up. Geen toegang tot de Docker-host of andere apps.</p></section>
<section><h2>3 · Herstelwizard</h2><p>Nocturne-proces: {html.escape(state())}</p><dl>{report_html}</dl>
<form method="get"><label>Gewenst HTTPS-adres <input name="url" type="url" required value="{html.escape(target or raw.get('public_url', ''), quote=True)}"></label>
<button>Herstelplan controleren</button></form><ol>{steps}</ol>{link}
<h3>Alle Nocturne-inloggegevens kwijt?</h3>
<p>Open de onderhoudsterminal en voer <code>nocturne-ha owner-recovery list</code> uit.
Hiermee vind je ook een vergeten gebruikersnaam. Maak eerst een HA-back-up en kies de juiste tenant en bestaande eigenaar.</p>
<p><code>nocturne-ha owner-recovery issue --tenant TENANT_ID --subject SUBJECT_ID --backup-confirmed --write</code></p>
<p>Deze opdracht voegt een nieuwe eenmalige herstelcode toe. Gebruik die met de getoonde gebruikersnaam op het hersteladres;
registreer daar een nieuwe passkey. Er is geen oude Nocturne-login of oude herstelcode nodig.
Toegang tot HA of de lokale containerconsole blijft vereist. PostgreSQL moet draaien;
herstel een ongeldige domeinconfiguratie eerst via HA en herstart de app.</p>
<p>De wizard zelf wijzigt geen instellingen, verbruikt geen herstelcodes en reset geen accounts.
Passkeyregistratie gebeurt op het geldige Nocturne-domein, niet in HA Ingress.</p></section></html>'''


def wizard_handler(raw, terminal_path, state):
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.split('?')[0] != '/maintenance/':
                self.send_error(404)
                return
            target = parse_qs(urlsplit(self.path).query).get('url', [None])[0]
            if target and len(target) > 300:
                self.send_error(400)
                return
            body = wizard_page(raw, terminal_path, state, target).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass
    return Handler


def terminal_command(terminal_path):
    return ['ttyd', '-i', '127.0.0.1', '-p', '8101', '-b', terminal_path,
            '-W', '-m', '2', '-d', '0', '-w', '/data',
            '-t', 'disableReconnect=true', '/bin/bash', '--noprofile',
            '--rcfile', str(BASE / 'maintenance.bashrc')]


def main():
    os.umask(0o077)
    # Maintenance and its shell never inherit the Supervisor credential.
    os.environ.pop('SUPERVISOR_TOKEN', None)
    raw = json.loads((DATA / 'options.json').read_text())
    try:
        enabled, password = enabled_options(raw)
    except ValueError as error:
        print(str(error), flush=True)
        return 1
    if not enabled:
        os.execv('/usr/bin/python3', ['python3', str(BASE / 'run.py')])
    RUNTIME.mkdir(parents=True, exist_ok=True)
    import grp
    proxy_group = grp.getgrnam('www-data').gr_gid
    os.chown(RUNTIME, 0, proxy_group)
    RUNTIME.chmod(0o750)
    # stdin keeps the password out of argv/process listings; no raw option logging.
    hashed = subprocess.run(['openssl', 'passwd', '-6', '-stdin'], input=password + '\n',
                            capture_output=True, text=True, check=True).stdout.strip()
    (RUNTIME / 'htpasswd').write_text('maintenance:' + hashed + '\n')
    os.chown(RUNTIME / 'htpasswd', 0, proxy_group)
    (RUNTIME / 'htpasswd').chmod(0o640)
    terminal_path = '/maintenance/terminal/' + secrets.token_hex(24)
    conf = RUNTIME / 'nginx.conf'
    conf.write_text(nginx_configuration(terminal_path))
    stop = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stop.set())
    children = []
    server = None
    app = None
    try:
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 8102),
            wizard_handler(raw, terminal_path, lambda: 'actief' if app and app.poll() is None else 'gestopt; onderhoud blijft beschikbaar'))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        children.append(subprocess.Popen(terminal_command(terminal_path), start_new_session=True))
        subprocess.run(['nginx', '-t', '-c', str(conf)], check=True)
        children.append(subprocess.Popen(['nginx', '-c', str(conf), '-g', 'daemon off;'], start_new_session=True))
        env = {**os.environ, 'NOCTURNE_PERSONAL_STATUS_PORT': '8100'}
        app = subprocess.Popen(['python3', str(BASE / 'run.py')], env=env)
        print('Personal onderhoud ingeschakeld via HA Ingress; gebruiker maintenance. Geen extra hostpoort.', flush=True)
        while not stop.wait(1):
            if any(process.poll() is not None for process in children):
                raise RuntimeError('Onderhoudsdienst gestopt')
        return 0
    finally:
        if app and app.poll() is None:
            app.terminate()
            try:
                app.wait(timeout=100)
            except subprocess.TimeoutExpired:
                app.kill()
                app.wait(timeout=5)
        for process in reversed(children):
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=5)
        if server:
            server.shutdown()
            server.server_close()


if __name__ == '__main__':
    raise SystemExit(main())
