"""Pure configuration generation; no network, no HA changes, no secrets in logs."""
import html
import ipaddress
import json
import re
import secrets
from pathlib import Path
from urllib.parse import urlsplit

SECRET_FIELDS = ('instance', 'postgres', 'migrator', 'app', 'web', 'gateway')


def validate_options(options):
    versions = json.loads(Path(__file__).with_name('version.json').read_text())
    public_url = options.get('public_url', versions['default_public_url']).rstrip('/')
    if any(c.isspace() for c in public_url):
        raise ValueError('public_url mag geen spaties of regelovergangen bevatten')
    try:
        parsed = urlsplit(public_url)
        port = parsed.port if parsed.port is not None else 443
    except ValueError as err:
        raise ValueError('public_url heeft een ongeldige poort') from err
    hostname = parsed.hostname or ''
    if (parsed.scheme != 'https' or parsed.username or parsed.password or
            parsed.query or parsed.fragment or parsed.path or not 1 <= port <= 65535):
        raise ValueError('public_url moet een HTTPS-adres zonder pad of inloggegevens zijn')
    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        pass
    else:
        raise ValueError('Gebruik een hostnaam, geen IP-adres: Nocturne gebruikt domeinen/passkeys')
    if ('.' not in hostname or len(hostname) > 253 or
            any(not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', label)
                for label in hostname.split('.'))):
        raise ValueError('public_url bevat geen geldige domeinnaam')
    cert, key = options.get('certificate', ''), options.get('private_key', '')
    if bool(cert) != bool(key):
        raise ValueError('Vul certificate en private_key beide in, of laat beide leeg')
    for value in (cert, key):
        if value and (not re.fullmatch(r'[a-zA-Z0-9_.-]+', value) or '..' in value):
            raise ValueError('Certificaten moeten bestandsnamen direct in /ssl zijn')
    gateway_auth = options.get('gateway_auth', True)
    if type(gateway_auth) is not bool:
        raise ValueError('gateway_auth moet true of false zijn')
    if not gateway_auth and not cert:
        raise ValueError('GATEWAY_TLS: zonder extra gatewaycode zijn eigen certificate/private_key-bestanden vereist')
    return dict(public_url=public_url, hostname=hostname, authority=parsed.netloc.lower(),
                certificate=cert, private_key=key, gateway_auth=gateway_auth)


def load_secrets(data_dir):
    path = Path(data_dir) / 'secrets.json'
    if path.exists():
        values = json.loads(path.read_text())
        if set(values) != set(SECRET_FIELDS) or any(
                not re.fullmatch(r'[a-f0-9]{64}', value) for value in values.values()):
            raise ValueError('secrets.json beschadigd; herstel de back-up, genereer geen nieuwe sleutels')
        path.chmod(0o600)
        return values
    if (Path(data_dir) / 'postgres' / 'PG_VERSION').exists():
        raise ValueError('Bestaande database zonder secrets.json; herstel beide uit dezelfde back-up')
    values = {key: secrets.token_hex(32) for key in SECRET_FIELDS}
    # Exclusive creation with private permissions; never overwrite existing keys.
    import os
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as handle:
        json.dump(values, handle)
        handle.flush()
        os.fsync(handle.fileno())
    return values


def service_environments(options, passwords, timezone='Europe/Amsterdam'):
    common = {'PATH': '/usr/local/bin:/usr/bin:/bin', 'TZ': timezone,
              'BASE_DOMAIN': options['hostname'], 'INSTANCE_KEY': passwords['instance'],
              'OTEL_EXPORTER_OTLP_ENDPOINT': '', 'OTEL_SDK_DISABLED': 'true'}
    api = dict(common, HOME='/home/app', DOTNET_ENVIRONMENT='Production',
               ASPNETCORE_ENVIRONMENT='Production', ASPNETCORE_URLS='http://127.0.0.1:8080',
               ASPNETCORE_FORWARDEDHEADERS_ENABLED='true', DemoService__Enabled='false',
               WEB_URL='http://127.0.0.1:8000', Logging__LogLevel__Default='Warning')
    if not options.get('gateway_auth', True):
        # This is upstream Nocturne's own site lockdown, not an auth bypass.
        api['Security__RequireAuthentication'] = 'true'
    for name, role in [('nocturne-postgres', 'app'), ('nocturne-postgres-migrator', 'migrator')]:
        api[f'ConnectionStrings__{name}'] = (
            f'Host=127.0.0.1;Port=5432;Database=nocturne;Username=nocturne_{role};Password={passwords[role]}')
    web = dict(common, HOME='/home/nocturne-web', NODE_ENV='production', PORT='8000',
               NOCTURNE_API_HTTP='http://127.0.0.1:8080',
               NOCTURNE_API_URL='http://127.0.0.1:8080', PUBLIC_API_URL='http://127.0.0.1:8080',
               PROTOCOL_HEADER='x-forwarded-proto', HOST_HEADER='x-forwarded-host',
               NOCTURNE_POSTGRES_URI=f"postgresql://nocturne_web:{passwords['web']}@127.0.0.1:5432/nocturne")
    return api, web


def nginx_config(options, cert_path, key_path):
    # Native mode is opt-in and is verified before nginx starts. Neither mode
    # sends a service credential or bypasses Nocturne's account authentication.
    gate = ('auth_basic "Nocturne lokale test - code staat in Home Assistant";\n'
            '    auth_basic_user_file /run/nocturne/gateway.htpasswd;')
    if not options.get('gateway_auth', True):
        gate = ('auth_basic off;\n'
                f'    if ($host != "{options["hostname"]}") {{ return 421; }}')
    return f'''user www-data;
worker_processes 1;
pid /run/nocturne/nginx.pid;
error_log /dev/stderr warn;
events {{ worker_connections 256; }}
http {{
  access_log off;
  client_max_body_size 20m;
  map $http_upgrade $connection_upgrade {{ default upgrade; '' close; }}
  server {{
    listen 8448 ssl;
    server_name {options['hostname']};
    ssl_certificate {cert_path};
    ssl_certificate_key {key_path};
    ssl_protocols TLSv1.2 TLSv1.3;
    {gate}
    proxy_http_version 1.1;
    proxy_set_header Host $http_host;
    proxy_set_header X-Forwarded-Host $http_host;
    proxy_set_header X-Forwarded-Proto https;
    proxy_set_header X-Forwarded-For $remote_addr;
    # Strip untrusted headers used by Nocturne service-to-service authentication.
    proxy_set_header X-Instance-Key "";
    proxy_set_header X-Instance-Service "";
    proxy_set_header Authorization "";
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;
    proxy_read_timeout 300s;
    proxy_buffering off;
    proxy_buffer_size 32k;
    proxy_buffers 8 32k;
    # Block dev/operator internals irrespective of the backend's own checks.
    location ^~ /api/v4/dev-only {{ return 404; }}
    location ~ ^/(scalar|openapi)(/|$) {{ return 404; }}
    location ~ ^/(api/auth/(oidc|platform-access)(/|$)|api/oauth(/|$)|\\.well-known/|hubs/) {{
      proxy_pass http://127.0.0.1:8080;
    }}
    location / {{ proxy_pass http://127.0.0.1:8000; }}
  }}
}}
'''


def status_page(options, statuses, gateway_password, test_certificate, checks=None):
    esc = html.escape
    versions = json.loads(Path(__file__).with_name('version.json').read_text())
    app_name = versions.get('name', 'Nocturne')
    rows = ''.join(f'<li><strong>{esc(name)}</strong>: {esc(state)}</li>' for name, state in statuses.items())
    check_rows = ''.join(f'<li><strong>{esc(name)}</strong>: {esc(state)}</li>'
                         for name, state in (checks or {'Controles': 'nog niet uitgevoerd'}).items())
    certificate_text = ('Zelfondertekend testcertificaat: nog niet geschikt voor echte medische '
                        'gegevens. Vertrouwd HTTPS/passkey-inloggen moet apart worden getest.'
                        if test_certificate else 'Eigen certificaat ingesteld. Controleer de geldigheid in de browser.')
    gateway_section = f'''<details><summary>Toegangscode voor deze lokale test tonen</summary>
<p>Gebruiker: <code>nocturne</code><br>Wachtwoord: <code>{esc(gateway_password)}</code></p>
<p>Dit is de extra beveiliging van de app, niet je Nocturne-account. Deel deze code niet.</p></details>'''
    if not options.get('gateway_auth', True):
        gateway_section = ('<p><strong>Geen extra gatewaycode nodig.</strong> '
                           'Log rechtstreeks in met je Nocturne-account/passkey. '
                           'Nocturne-aanmelding blijft verplicht.</p>')
    open_url = options['public_url'] + ('' if options.get('gateway_auth', True) else '/auth/login')
    return f'''<!doctype html><html lang="nl"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(app_name)}</title>
<style>body{{font:16px system-ui;max-width:760px;margin:32px auto;padding:20px;background:#101724;color:#e5edf7}}
a{{color:#80d5fc}}li{{margin:10px 0}}section{{background:#1d293c;padding:20px;border-radius:12px;margin:20px 0}}
code{{overflow-wrap:anywhere}}button{{padding:10px;cursor:pointer}}.warning{{color:#ffd291}}</style>
<h1>{esc(app_name)}</h1><p>HA-pakket {esc(versions['app'])} · Nocturne {esc(versions['nocturne'])} · amd64</p>
<section><h2>Werkelijke dienststatus</h2><ul>{rows}</ul>
<button onclick="location.reload()">Status vernieuwen</button></section>
<section><h2>Nocturne openen</h2>
<p><a href="{esc(open_url, quote=True)}" target="_blank" rel="noopener noreferrer">Open Nocturne</a></p>
<p>Deze HA-pagina toont alleen de technische status; het is niet het Nocturne-dashboard.</p>
{gateway_section}
<p class="warning">{esc(certificate_text)}</p></section>
<section><h2>Installatiecontrole</h2>
<p><strong>Publiek adres:</strong> <code>{esc(options['public_url'])}</code> — URL-syntax gecontroleerd.</p>
<h3>Door de app gecontroleerd</h3><ul>{check_rows}</ul>
<p>Bij een fout blijft het laatst geladen certificaat in gebruik. De geldigheidsduur daarvan loopt wel door.
De app vraagt geen nieuwe certificaten aan; bijvoorbeeld DuckDNS blijft daarvoor verantwoordelijk.</p>
<h3>Nog op jouw browser te controleren</h3>
<ol><li>Open Nocturne via precies het publieke adres hierboven, niet via het IP-adres.</li>
<li>Controleer dat de browser het certificaat vertrouwt, zonder waarschuwing.</li>
<li>Controleer accountaanmaak/passkey-login en bewaar de herstelcodes veilig.</li>
<li>Test opnieuw op een tweede apparaat en na een geplande app-herstart.</li></ol>
<p>Deze browsercontroles zijn <strong>niet automatisch uitgevoerd</strong>.
De server kan jouw DNS-route, certificaatvertrouwen of passkeyvoorziening niet bewijzen.</p>
<p><a href="https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/INSTALLATIE.md" target="_blank" rel="noopener noreferrer">Visuele installatiehandleiding</a> ·
<a href="https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/CERTIFICATEN.md" target="_blank" rel="noopener noreferrer">Certificaatcontrole en foutcodes</a></p></section>
<p>Test eerst alleen starten en het installatiescherm. Geen CGM/pomp koppelen, geen behandelgegevens invoeren.
Geen internetpoorten openzetten. Deze experimentele app is geen HACS-integratie en geen medisch hulpmiddel.</p>
<p><a href="https://github.com/smokkelaar/nocturne-home-assistant" target="_blank" rel="noopener noreferrer">Broncode, documentatie en bijdragen</a></p>
</html>'''
