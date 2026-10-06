#!/usr/bin/env python3
"""Read-only diagnostics for Nocturne Home Assistant app containers."""
import argparse
import http.client
import json
from pathlib import Path
import socket
import sys
from urllib.parse import urlsplit

DATA = Path('/data')


def checked_options():
    from settings import validate_options
    return validate_options(json.loads((DATA / 'options.json').read_text()))


def doctor():
    result = {'configuration': 'invalid', 'dns': 'not checked',
              'certificate': 'not checked', 'api': 'not reachable'}
    try:
        checked = checked_options()
    except (OSError, UnicodeError, ValueError, KeyError):
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
            inspect_pair(DATA.parent / 'ssl' / checked['certificate'],
                         DATA.parent / 'ssl' / checked['private_key'], checked['hostname'])
            result['certificate'] = 'configured certificate checked'
        except (OSError, RuntimeError, ValueError):
            result['certificate'] = 'configured certificate failed validation'
    else:
        result['certificate'] = 'local test certificate; browser trust not guaranteed'
    connection = http.client.HTTPConnection('127.0.0.1', 8080, timeout=3)
    try:
        connection.request('GET', '/api/v3/version',
                          headers={'Host': checked['authority'], 'Accept': 'application/json'})
        response = connection.getresponse()
        result['api'] = 'responding (HTTP %s)' % response.status
        response.read(4096)
    except (OSError, http.client.HTTPException):
        pass
    finally:
        connection.close()
    return result


def api_request(path):
    if (not path.startswith('/api/') or any(c in path for c in '\r\n#\x00')
            or any(c.isspace() for c in path) or urlsplit(path).netloc
            or '..' in path.split('/')):
        raise ValueError('Use a local /api/... path')
    checked = checked_options()
    connection = http.client.HTTPConnection('127.0.0.1', 8080, timeout=15)
    try:
        connection.request('GET', path, headers={'Host': checked['authority'],
                                                  'Accept': 'application/json'})
        response = connection.getresponse()
        payload = response.read(2_000_001)
        if len(payload) > 2_000_000:
            raise ValueError('Response exceeds 2 MB; use a narrower request')
        print(payload.decode('utf-8', errors='replace'))
        return 0 if 200 <= response.status < 300 else 1
    finally:
        connection.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description='Read-only Nocturne diagnostics')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('doctor', help='Check wrapper configuration, DNS, TLS and local API')
    commands.add_parser('status', help='Alias for doctor')
    api = commands.add_parser('api', help='Read a local Nocturne API endpoint')
    api.add_argument('path', help='Local /api/... path; request uses GET only')
    args = parser.parse_args(argv)
    try:
        if args.command in ('doctor', 'status'):
            print(json.dumps(doctor(), indent=2, ensure_ascii=False))
            return 0
        return api_request(args.path)
    except (OSError, UnicodeError, ValueError, KeyError, http.client.HTTPException) as error:
        print(f'Diagnostics failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
