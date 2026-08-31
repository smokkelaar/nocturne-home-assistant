"""Local-only visual preview with fictional data; never connects to HA."""
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'nocturne_local/rootfs/opt/nocturne-ha'))
from settings import status_page, validate_options


def preview():
    page = status_page(validate_options({'public_url': 'https://nocturne.example.net:8448'}),
        {'PostgreSQL': 'gereed — voorbeeld', 'Nocturne API': 'gereed — voorbeeld',
         'Nocturne Web': 'HTTP-healthcheck geslaagd; passkey-login nog apart testen',
         'HTTPS': 'lokaal TLS-certificaat bevestigd; browservertrouwen nog testen'},
        'VOORBEELD-GEEN-WERKEND-WACHTWOORD', False,
        {'Geladen certificaat': 'SAN/domeinnaam en sleutelpaar gecontroleerd. Geldig tot 2030-01-01 12:00 UTC (voorbeeld).',
         'Certificaatvernieuwing': 'Geen nieuwe certificaatbestanden; geladen certificaat is nog geldig.'})
    return page.replace('<h1>Nocturne</h1>', '<h1>Nocturne — ontwerpvoorbeeld</h1><p>Fictieve gegevens; geen verbinding met Home Assistant.</p>').encode()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != '/':
            self.send_error(404)
            return
        body = preview()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8767)
    args = parser.parse_args()
    with HTTPServer(('127.0.0.1', args.port), Handler) as server:
        print(f'Fictional local preview: http://127.0.0.1:{server.server_port}/', flush=True)
        server.serve_forever()
