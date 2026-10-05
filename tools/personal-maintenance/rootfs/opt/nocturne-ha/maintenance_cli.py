#!/usr/bin/env python3
"""Personal-only local management client. Never edits accounts or the database."""
import argparse
import hashlib
import http.client
import json
from pathlib import Path
import socket
import sys
from urllib.parse import urlsplit

DATA = Path('/data')


def options():
    return json.loads((DATA / 'options.json').read_text())


def checked_options(raw):
    from settings import validate_options
    return validate_options(raw)


def doctor(raw=None):
    raw = options() if raw is None else raw
    result = {'configuration': 'invalid', 'dns': 'not checked',
              'certificate': 'not checked', 'api': 'not reachable'}
    try:
        checked = checked_options(raw)
    except ValueError:
        return result
    result['configuration'] = 'valid'
    result['public_url'] = checked['public_url']
    try:
        socket.getaddrinfo(checked['hostname'], None)
        result['dns'] = 'resolves from this container; browser reachability not proven'
    except OSError:
        result['dns'] = 'does not resolve from this container'
    if checked['certificate']:
        try:
            from tls import inspect_pair
            inspect_pair(Path('/ssl') / checked['certificate'],
                         Path('/ssl') / checked['private_key'], checked['hostname'])
            result['certificate'] = 'configured certificate checked'
        except (ValueError, RuntimeError, OSError):
            result['certificate'] = 'configured certificate failed validation'
    else:
        result['certificate'] = 'local test certificate; browser trust not guaranteed'
    connection = http.client.HTTPConnection('127.0.0.1', 8080, timeout=3)
    try:
        connection.request('GET', '/api/v4/status', headers={'Host': checked['authority']})
        response = connection.getresponse()
        result['api'] = 'responding (HTTP %s)' % response.status
        response.read(4096)
    except (OSError, http.client.HTTPException):
        pass
    finally:
        connection.close()
    return result


def recovery_plan(raw=None, public_url=None):
    raw = dict(options() if raw is None else raw)
    if public_url:
        raw['public_url'] = public_url
    checked = checked_options(raw)
    return {'public_url': checked['public_url'],
            'recovery_url': checked['public_url'] + '/auth/recovery',
            'steps': [
                'Maak eerst een volledige HA-back-up van deze app.',
                'Stel public_url en passende certificate/private_key in via de HA-appconfiguratie.',
                'Controleer DNS en browservertrouwen voor het nieuwe HTTPS-adres; herstart de app.',
                'Open het hersteladres buiten HA Ingress en gebruik een ongebruikte Nocturne-herstelcode.',
                'Registreer in de browser een nieuwe passkey; test daarna opnieuw aanmelden.',
                'Zonder herstelcode: gebruik een reeds gekoppelde inlogprovider of een bevoegde eigenaar. '
                'Deze wrapper maakt geen eigenaarlogin en reset geen accounts.'
            ]}


def api_request(path, method='GET', body=None, service=False):
    # Fixed loopback destination; no redirects, caller-supplied URLs or credentials.
    if (not path.startswith('/api/') or any(c in path for c in '\r\n#')
            or urlsplit(path).netloc or '..' in path.split('/')):
        raise ValueError('Gebruik een lokaal /api/... pad')
    checked = checked_options(options())
    headers = {'Host': checked['authority'], 'Content-Type': 'application/json'}
    if service:
        secret = json.loads((DATA / 'secrets.json').read_text())['instance']
        headers.update({'X-Instance-Key': hashlib.sha256(secret.encode()).hexdigest(),
                        'X-Instance-Service': 'nocturne-ha-maintenance'})
    connection = http.client.HTTPConnection('127.0.0.1', 8080, timeout=15)
    try:
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        payload = response.read(2_000_001)
        if len(payload) > 2_000_000:
            raise ValueError('Antwoord groter dan 2 MB; gebruik een gerichte aanvraag')
        print(payload.decode('utf-8', errors='replace'))
        return 0 if 200 <= response.status < 300 else 1
    finally:
        connection.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description='Personal wrapper onderhoud; nocturne-ha <command> --help')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('doctor', help='Configuratie, DNS, certificaat en lokale API controleren')
    commands.add_parser('status', help='Zelfde technische diagnose als doctor')
    recover = commands.add_parser('recover', help='Herstelplan zonder codes te verbruiken of accounts te wijzigen')
    recover.add_argument('--url', help='Nieuw HTTPS-adres om een herstelplan voor te maken')
    api = commands.add_parser('api', help='Algemene lokale API-client voor bestaande en toekomstige endpoints')
    api.add_argument('path')
    api.add_argument('--method', choices=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'], default='GET')
    api.add_argument('--body-file', help='JSON-bestand, of - voor stdin; geen geheimen in commandoregel')
    api.add_argument('--service', action='store_true', help='Gebruik de krachtige lokale instance-service identiteit')
    api.add_argument('--write', action='store_true', help='Bewuste toestemming voor een muterende aanvraag')
    args = parser.parse_args(argv)
    try:
        if args.command in ('doctor', 'status'):
            print(json.dumps(doctor(), indent=2, ensure_ascii=False))
        elif args.command == 'recover':
            print(json.dumps(recovery_plan(public_url=args.url), indent=2, ensure_ascii=False))
        else:
            if args.method != 'GET' and not args.write:
                parser.error('Een muterende aanvraag vereist --write')
            body = None
            if args.body_file:
                body = sys.stdin.read(1_000_001) if args.body_file == '-' else Path(args.body_file).read_text()
                if len(body) > 1_000_000:
                    raise ValueError('Aanvraag groter dan 1 MB')
                json.loads(body)
            return api_request(args.path, args.method, body, args.service)
        return 0
    except (ValueError, OSError, KeyError, http.client.HTTPException):
        print('Onderhoudsopdracht mislukt; controleer configuratie en dienststatus. Geen geheimen gelogd.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
