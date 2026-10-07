#!/usr/bin/env python3
"""Shared opt-in ingress/ttyd host, independent of Nocturne/TLS startup."""
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
from urllib.parse import parse_qs, urlencode, urlsplit

from maintenance_cli import doctor, recovery_plan

BASE = Path('/opt/nocturne-ha')
DATA = Path('/data')
RUNTIME = Path('/run/nocturne-maintenance')


def app_name():
    return json.loads((BASE / 'version.json').read_text())['name']


def enabled_options(raw):
    enabled = raw.get('maintenance_enabled', False)
    if type(enabled) is not bool:
        raise ValueError('maintenance_enabled moet true of false zijn')
    password = raw.get('maintenance_password', '')
    if enabled and (not isinstance(password, str) or not 16 <= len(password) <= 256
                    or any(c in password for c in '\r\n\x00')):
        raise ValueError('Onderhoud vereist een eigen wachtwoord van 16 tot 256 tekens')
    return enabled, password


def nginx_configuration(terminal_path, wizard_key=None):
    # Unique terminal path is an unguessable CSRF capability in addition to Basic auth.
    # Never enable public host ports, forwarded-IP allowlists or Docker/host access.
    wizard_key = wizard_key or secrets.token_hex(32)
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
    client_max_body_size 8k;
    location /maintenance/ {{
      auth_basic "{app_name()} onderhoud";
      auth_basic_user_file {RUNTIME}/htpasswd;
      proxy_pass http://127.0.0.1:8102;
      proxy_set_header Authorization "";
      proxy_set_header X-Nocturne-Maintenance-Key "{wizard_key}";
    }}
    location {terminal_path}/ {{
      auth_basic "{app_name()} onderhoud";
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


class TotpResetRequests:
    """Bounded, expiring, one-use requests bound to the selected existing owner."""
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.lock = threading.Lock()
        self.pending = {}
        self.results = {}

    def issue(self, owner):
        with self.lock:
            now = self.clock()
            self.pending = {key: value for key, value in self.pending.items() if value['expires'] > now}
            if len(self.pending) >= 64:
                self.pending.pop(next(iter(self.pending)))
            token = secrets.token_urlsafe(32)
            self.pending[token] = {'expires': now + 1800, 'tenant': owner['tenant_id'],
                                   'subject': owner['subject_id'], 'expected_username': owner['username']}
            return token

    def take(self, fields):
        if (set(fields) != {'token', 'backup', 'confirm'}
                or any(len(values) != 1 for values in fields.values())
                or fields['backup'] != ['yes'] or fields['confirm'] != ['yes']):
            raise ValueError('Bevestig het gekozen account en de gemaakte back-up.')
        with self.lock:
            target = self.pending.pop(fields['token'][0], None)
        if target is None or target['expires'] <= self.clock():
            raise ValueError('Dit verzoek is verlopen of al verwerkt. Vernieuw de wizard en controleer de TOTP-status.')
        return {key: value for key, value in target.items() if key != 'expires'}

    def completed(self, selection, message):
        with self.lock:
            now = self.clock()
            self.results = {key: value for key, value in self.results.items() if value['expires'] > now}
            if len(self.results) >= 64:
                self.results.pop(next(iter(self.results)))
            token = secrets.token_urlsafe(32)
            self.results[token] = {'expires': now + 300, 'selection': selection, 'message': message}
            return token

    def notice(self, token, selection):
        with self.lock:
            result = self.results.pop(token, None)
        if result and result['expires'] > self.clock() and result['selection'] == selection:
            return result['message']
        return None


def owner_guidance(selection=None, target=None, reset_requests=None):
    import owner_recovery
    readiness = owner_recovery.readiness()
    status = '<p role="status">' + html.escape(readiness['message']) + '</p>'
    if not readiness['compatible']:
        return status + '<p><code>nocturne-ha owner-recovery check</code></p><p>Los eerst deze controle op. Gebruik intussen een bestaande herstelcode als je die hebt. Verwijder de app of database niet en maak geen nieuwe eigenaar aan.</p>'
    try:
        owners = owner_recovery.owners()
    except (ValueError, OSError, RuntimeError, subprocess.SubprocessError):
        return status + '<p>Eigenaars konden nog niet worden gelezen. Voer <code>nocturne-ha owner-recovery check</code> uit en herstart zo nodig de app via HA.</p>'
    if not owners:
        return status + '<p>Geen actieve eigenaar gevonden. Controleer of je de juiste app hebt geopend. Maak geen nieuwe installatie boven op je bestaande gegevens; laat de situatie eerst onderzoeken.</p>'
    options = '<option value="">Kies bewust het bestaande account dat je wilt herstellen</option>'
    chosen = None
    for owner in owners:
        key = owner['tenant_id'] + ':' + owner['subject_id']
        selected = ' selected' if selection == key else ''
        if selected:
            chosen = owner
        label = (owner.get('tenant_name') or owner.get('tenant_slug') or owner['tenant_id']) + ' · ' + (owner.get('username') or owner.get('name') or 'account zonder gebruikersnaam')
        options += '<option value="' + html.escape(key, quote=True) + '"' + selected + '>' + html.escape(label) + '</option>'
    hidden = '<input type="hidden" name="url" value="' + html.escape(target, quote=True) + '">' if target else ''
    form = '<form method="get" action="./">' + hidden + '<label>Bestaande eigenaar <select name="owner" required>' + options + '</select></label><button>Toon stappen voor dit account</button></form>'
    if chosen is None:
        return status + form + '<p>Selecteren leest alleen gegevens. Je maakt hier nog geen herstelcode.</p>'
    command = ('nocturne-ha owner-recovery issue --tenant ' + chosen['tenant_id'] + ' --subject ' + chosen['subject_id'] + ' --backup-confirmed --write')
    username_help = ''
    if not chosen.get('username'):
        command += ' --username recovery-owner'
        username_help = '<p>Dit bestaande account heeft geen gebruikersnaam. De opdracht geeft het de naam <strong>recovery-owner</strong>. Kies een andere eenvoudige, unieke naam als die al in gebruik is; je maakt geen nieuw account.</p>'
    totp = '<p><strong>TOTP staat al uit voor dit account.</strong> De optie <code>--reset-totp</code> is niet nodig.</p>'
    if chosen.get('totp_count', 0):
        totp = '<p>TOTP is actief voor dit account. Als je de authenticator kwijt bent, reset TOTP met de afzonderlijke knop of voeg bewust <code>--reset-totp</code> aan de herstelopdracht toe.</p>'
    if chosen.get('totp_count', 0) and reset_requests:
        token = reset_requests.issue(chosen)
        label = chosen.get('username') or chosen.get('name') or chosen['subject_id']
        totp = f'''<section><h3>Authenticator kwijt? TOTP direct uitschakelen</h3>
<p>Account: <strong>{html.escape(label)}</strong> · app: {html.escape(app_name())}.
Dit schakelt alleen de authenticator van dit bestaande account uit, ook in andere tenants.
Je passkeys, gegevens en herstelcodes blijven staan. Bestaande aanmeldsessies worden niet afgemeld.
De knop maakt geen herstelcode en geeft op zichzelf geen toegang tot Nocturne.</p>
<form method="post" action="totp-reset"><input type="hidden" name="token" value="{token}">
<p><label><input type="checkbox" name="backup" value="yes" required> Ik heb een volledige HA-back-up van deze app gemaakt.</label></p>
<p><label><input type="checkbox" name="confirm" value="yes" required> Ik wil TOTP voor {html.escape(label)} uitschakelen, ook in andere tenants van dit account.</label></p>
<button class="danger" type="submit">TOTP uitschakelen voor dit account</button></form>
<p>Na bevestiging wordt de reset direct uitgevoerd. Meld daarna aan met je passkey of volg de herstelcodestappen.
Stel vervolgens TOTP opnieuw in via de beveiligingsinstellingen van Nocturne.
Gebruik na deze knop geen extra <code>--reset-totp</code> in de herstelopdracht.</p></section>'''
    return status + form + totp + f'''<ol>
<li><strong>Controleer je keuze.</strong> App: {html.escape(app_name())}; gebruiker: {html.escape(chosen.get('username') or 'nog geen gebruikersnaam')}; tenant: <code>{html.escape(chosen['tenant_id'])}</code>. Kies bij twijfel geen account.</li>
<li><strong>Maak nu een volledige HA-back-up van deze app</strong>, inclusief appgegevens. Download de back-up en bewaar de bijbehorende herstelinformatie. Ga pas verder als die klaar is.</li>
<li><strong>Open de terminal</strong> en voer onderstaande opdracht uit. De opties <code>--backup-confirmed --write</code> bevestigen dat je bewust één nieuwe herstelcode aan dit bestaande account toevoegt.{username_help}<p><code>{html.escape(command)}</code><button type="button" class="copy">Kopieer opdracht</button></p>
<p>Heb je je authenticator ook verloren? Voeg alleen dan <code>--reset-totp</code> toe. Dat verwijdert de tweede factor voor dit account, ook als het in meerdere tenants voorkomt. Zonder die optie blijft TOTP actief.</p></li>
<li><strong>Bewaar de terminaluitvoer tijdelijk privé.</strong> Je ziet <code>username</code>, <code>code</code> en <code>code_id</code>. De nieuwe code verschijnt alleen in die uitvoer; deel die niet en plak hem niet in deze wizard, een issue of logbestand.</li>
<li><strong>Open het Nocturne-hersteladres hieronder in een aparte browsertab.</strong> Gebruik de getoonde gebruikersnaam en code en registreer een nieuwe passkey. Je moet toegang hebben tot het juiste HTTPS-domein; HA Ingress kan de passkey niet voor je aanmaken.</li>
</ol>'''


def wizard_page(raw, terminal_path, state, target=None, selection=None, reset_requests=None, notice=None):
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
    guidance = owner_guidance(selection, target, reset_requests)
    notice_html = '<section role="status"><strong>' + html.escape(notice) + '</strong></section>' if notice else ''
    return f'''<!doctype html><html lang="nl"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(app_name())} onderhoud</title>
<style>body{{font:16px system-ui;background:#101724;color:#e5edf7;max-width:850px;margin:30px auto;padding:20px}}
section{{background:#1d293c;padding:20px;border-radius:12px;margin:20px 0}}a{{color:#80d5fc}}input,button{{padding:10px}}
dt{{font-weight:bold}}dd{{margin:4px 0 15px}}li{{margin:12px 0}}code{{overflow-wrap:anywhere}}select{{max-width:100%;padding:10px}}button{{margin:5px}}.copy{{display:block}}.danger{{background:#a32c35;color:white;border:0;border-radius:6px}}input[type=checkbox]{{accent-color:#80d5fc}}</style>
<h1>{html.escape(app_name())} · onderhoudsproef</h1><p><a href="./">Terug naar onderhoud</a> · <a href="../">Dienststatus</a></p>
{notice_html}
<section><h2>Begin hier: wat is er mis?</h2><p>Je werkt alleen aan <strong>{html.escape(app_name())}</strong>. Controleer eerst of dit de juiste variant met jouw gegevens is.</p>
<ul><li><strong>Je hebt nog een ongebruikte herstelcode:</strong> controleer het HTTPS-adres hieronder en gebruik die code op het Nocturne-hersteladres. Je hoeft geen nieuwe code te maken.</li>
<li><strong>Het domein of certificaat is veranderd:</strong> herstel eerst <code>public_url</code>, DNS en certificaat via de HA-appconfiguratie. Herstart de app. Een passkey voor het oude domein werkt doorgaans niet op het nieuwe domein.</li>
<li><strong>Alle inloggegevens kwijt:</strong> volg hieronder de controle en kies bewust je bestaande eigenaar.</li>
<li><strong>Nocturne start niet:</strong> gebruik de diagnose. Onderhoud kan bereikbaar blijven terwijl PostgreSQL en Nocturne gestopt zijn; eigenaarherstel vereist een werkende database.</li></ul>
<p>Een herstelcode maak je alleen met een expliciete terminalopdracht. Selecteren of een herstelplan openen wijzigt niets.
De afzonderlijke TOTP-knop voert na de twee bevestigingen wel direct een reset uit.</p></section>
<section><h2>1 · CLI</h2><p><code>nocturne-ha doctor</code> · <code>nocturne-ha recover</code> · <code>nocturne-ha api --help</code></p>
<p>CLI-uitvoer kan privégegevens bevatten. Geheimen en commandogeschiedenis worden niet centraal gelogd.</p></section>
<section><h2>2 · Onderhoudsterminal</h2><p><a href="terminal/{terminal_path.rsplit('/', 1)[1]}/">Open terminal</a></p>
<p>De terminal heeft rootrechten binnen alleen deze app-container. Verkeerde opdrachten kunnen gegevens beschadigen.
Maak eerst een HA-back-up. Geen toegang tot de Docker-host of andere apps.</p></section>
<section><h2>3 · Herstelwizard</h2><p>Nocturne-proces: {html.escape(state())}</p><dl>{report_html}</dl>
<form method="get" action="./"><label>Gewenst HTTPS-adres <input name="url" type="url" required value="{html.escape(target or raw.get('public_url', ''), quote=True)}"></label>
<button>Herstelplan controleren</button></form><ol>{steps}</ol>{link}
<h3>Alle Nocturne-inloggegevens kwijt?</h3>
{guidance}{link}
<h3>Na herstel: controleer of je echt klaar bent</h3><ol>
<li>Meld af en weer aan met de nieuwe passkey. Controleer of je het oorspronkelijke account en je bestaande gegevens ziet.</li>
<li>Stel TOTP opnieuw in als je die hebt gereset. Verwijder daarna alleen de oude passkeys die je niet meer gebruikt.</li>
<li>Genereer en bewaar nieuwe Nocturne-herstelcodes op een veilige plek.</li>
<li>Heb je de zojuist gemaakte code niet gebruikt? Voer <code>nocturne-ha owner-recovery revoke --code-id CODE_ID --write</code> uit, met de <code>code_id</code> uit de terminaluitvoer. Een ongebruikte code verloopt niet automatisch.</li>
<li>Zet onderhoud uit in de HA-appconfiguratie en herstart. Controleer daarna dat de terminal niet meer bereikbaar is.</li></ol>
<details><summary>Het lukt nog niet — wat nu?</summary><ul>
<li><strong>Database niet bereikbaar:</strong> controleer URL/certificaat in HA, herstart en wacht tot de dienst gestart is. Voer daarna <code>nocturne-ha owner-recovery check</code> uit.</li>
<li><strong>Build niet geschikt voor eigenaarherstel:</strong> de terminal blijft werken. Gebruik een bestaande code of laat het gewijzigde herstelmechanisme controleren. Zet geen compatibiliteitscontrole uit.</li>
<li><strong>Code wordt geweigerd:</strong> gebruik de gebruikersnaam uit de uitvoer, controleer app en domein, en of de code al gebruikt is. Gebruik daarna de zojuist geregistreerde passkey.</li>
<li><strong>Certificaatwaarschuwing of geen passkeyknop:</strong> herstel DNS en vertrouwd HTTPS en open Nocturne buiten HA Ingress.</li>
<li><strong>Ook HA-toegang kwijt:</strong> herstel eerst HA-toegang of een vertrouwde back-up. Deze wizard kan geen beheerderstoegang tot HA maken.</li></ul></details>
<p>De wizard verbruikt geen herstelcodes en maakt geen accounts. Alleen de afzonderlijk bevestigde TOTP-knop schakelt de authenticator uit.
Passkeyregistratie gebeurt op het geldige Nocturne-domein, niet in HA Ingress.</p></section>
<script>document.querySelectorAll('.copy').forEach(button => button.addEventListener('click', async () => {{
try {{ await navigator.clipboard.writeText(button.previousElementSibling.textContent); button.textContent = 'Opdracht gekopieerd'; }}
catch {{ button.textContent = 'Selecteer en kopieer de opdracht handmatig'; }}
}}));</script></html>'''


def wizard_handler(raw, terminal_path, state, wizard_key):
    resets = TotpResetRequests()
    class Handler(http.server.BaseHTTPRequestHandler):
        def authenticated_backend(self):
            # nginx overwrites this header only after ingress IP + Basic auth checks.
            # Direct loopback clients must not obtain tokens or invoke root actions.
            supplied = self.headers.get('X-Nocturne-Maintenance-Key', '')
            return bool(wizard_key) and secrets.compare_digest(supplied.encode(), wizard_key.encode())

        def page_response(self, body):
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if not self.authenticated_backend():
                self.send_error(403)
                return
            if self.path.split('?')[0] != '/maintenance/':
                self.send_error(404)
                return
            target = parse_qs(urlsplit(self.path).query).get('url', [None])[0]
            selection = parse_qs(urlsplit(self.path).query).get('owner', [None])[0]
            result = parse_qs(urlsplit(self.path).query).get('result', [''])[0]
            if target and len(target) > 300:
                self.send_error(400)
                return
            if selection and len(selection) > 80:
                self.send_error(400)
                return
            notice = resets.notice(result, selection) if len(result) <= 80 else None
            body = wizard_page(raw, terminal_path, state, target, selection, resets, notice).encode()
            self.page_response(body)

        def do_POST(self):
            self.body_consumed = False
            if not self.authenticated_backend() or raw.get('maintenance_enabled') is not True:
                self.reject_post(403)
                return
            if self.path != '/maintenance/totp-reset':
                self.reject_post(404)
                return
            if self.headers.get('Content-Type', '').split(';')[0] != 'application/x-www-form-urlencoded':
                self.reject_post(415)
                return
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 4096:
                    self.reject_post(413)
                    return
                data = self.rfile.read(length)
                self.body_consumed = True
                if len(data) != length:
                    raise ValueError('Incomplete form')
                fields = parse_qs(data.decode('utf-8'), keep_blank_values=True,
                                  strict_parsing=True, max_num_fields=4)
                target = resets.take(fields)
            except (ValueError, UnicodeError):
                self.reject_post(400, 'Bevestiging ontbreekt of verzoek verlopen; vernieuw de wizard en controleer TOTP.')
                return
            import owner_recovery
            try:
                result = owner_recovery.reset_totp(**target, write=True, backup_confirmed=True)
            except (ValueError, OSError, RuntimeError, subprocess.SubprocessError):
                # Do not return database output, tokens, SQL or private errors.
                self.send_error(409, 'Reset niet bevestigd. Vernieuw de wizard, controleer de TOTP-status en de herstelcontrole.')
                return
            notice = ('TOTP is uitgeschakeld voor dit account.' if result['removed'] else
                      'TOTP stond al uit voor dit account; er is niets verwijderd.')
            notice += ' Stel je authenticator na aanmelden opnieuw in via de beveiligingsinstellingen van Nocturne.'
            selection = target['tenant'] + ':' + target['subject']
            result_token = resets.completed(selection, notice)
            # Relative PRG redirect preserves the HA ingress prefix. Refreshing
            # the resulting GET cannot submit another reset or spoof a result.
            self.send_response(303)
            self.send_header('Location', './?' + urlencode({'owner': selection, 'result': result_token}))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Content-Length', '0')
            self.end_headers()

        def reject_post(self, status, message=None):
            # Drain only small, bounded rejected forms so closing the socket does
            # not discard the error response on clients with unread request bytes.
            if not self.body_consumed:
                try:
                    length = int(self.headers.get('Content-Length', '0'))
                    if 0 < length <= 8192:
                        self.connection.settimeout(2)
                        self.rfile.read(length)
                except (ValueError, OSError):
                    pass
            self.send_error(status, message)

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
    wizard_key = secrets.token_hex(32)
    conf = RUNTIME / 'nginx.conf'
    conf.write_text(nginx_configuration(terminal_path, wizard_key))
    stop = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stop.set())
    children = []
    server = None
    app = None
    try:
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 8102),
            wizard_handler(raw, terminal_path, lambda: 'actief' if app and app.poll() is None else 'gestopt; onderhoud blijft beschikbaar', wizard_key))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        children.append(subprocess.Popen(terminal_command(terminal_path), start_new_session=True))
        subprocess.run(['nginx', '-t', '-c', str(conf)], check=True)
        children.append(subprocess.Popen(['nginx', '-c', str(conf), '-g', 'daemon off;'], start_new_session=True))
        env = {**os.environ, 'NOCTURNE_PERSONAL_STATUS_PORT': '8100'}
        app = subprocess.Popen(['python3', str(BASE / 'run.py')], env=env)
        print(app_name() + ' onderhoud ingeschakeld via HA Ingress; gebruiker maintenance. Geen extra hostpoort.', flush=True)
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
