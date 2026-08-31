"""HTTP liveness must never render the dashboard or borrow user credentials."""
import http.client
import http.server
import importlib
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'nocturne_local/rootfs/opt/nocturne-ha'))
runtime = importlib.import_module('run')
settings = importlib.import_module('settings')


class WebHealthTests(unittest.TestCase):
    def setUp(self):
        self.options = settings.validate_options({'public_url': 'https://nocturne.example.net:8448'})

    def test_fixed_loopback_health_path_without_credentials(self):
        with patch.object(runtime.http.client, 'HTTPConnection') as factory:
            connection = factory.return_value
            connection.getresponse.return_value.status = 200
            connection.getresponse.return_value.read.return_value = b'ok'
            self.assertTrue(runtime.web_response_reachable(self.options))
            factory.assert_called_once_with('127.0.0.1', 8000, timeout=2)
            connection.request.assert_called_once_with('GET', '/health', headers={
                'Host': 'nocturne.example.net:8448',
                'X-Forwarded-Host': 'nocturne.example.net:8448',
                'X-Forwarded-Proto': 'https',
            })
            connection.getresponse.return_value.read.assert_called_once_with(3)
            connection.close.assert_called_once()

    def test_requires_exact_success_body_not_dashboard_html(self):
        for body in (b'', b'o', b'ok\n', b'OK', b'<html>Login</html>'):
            with self.subTest(body=body), patch.object(runtime.http.client, 'HTTPConnection') as factory:
                connection = factory.return_value
                connection.getresponse.return_value.status = 200
                connection.getresponse.return_value.read.return_value = body
                self.assertFalse(runtime.web_response_reachable(self.options))
                connection.getresponse.return_value.read.assert_called_once_with(3)
                connection.close.assert_called_once()

    def test_redirects_and_errors_fail_without_followup_requests(self):
        for status in (204, 301, 302, 303, 307, 308, 401, 403, 404, 500, 503):
            with self.subTest(status=status), patch.object(runtime.http.client, 'HTTPConnection') as factory:
                connection = factory.return_value
                response = connection.getresponse.return_value
                response.status = status
                response.getheader.return_value = '/setup'
                response.read.return_value = b'ok'
                self.assertFalse(runtime.web_response_reachable(self.options))
                self.assertEqual(1, connection.request.call_count)
                response.read.assert_not_called()
                connection.close.assert_called_once()

    def test_transport_and_body_errors_fail_and_close_connection(self):
        for phase in ('request', 'getresponse', 'read'):
            for error in (OSError('offline'), TimeoutError('slow'), http.client.HTTPException('bad HTTP')):
                with self.subTest(phase=phase, error=type(error).__name__), \
                        patch.object(runtime.http.client, 'HTTPConnection') as factory:
                    connection = factory.return_value
                    response = connection.getresponse.return_value
                    response.status = 200
                    operation = response.read if phase == 'read' else getattr(connection, phase)
                    operation.side_effect = error
                    self.assertFalse(runtime.web_response_reachable(self.options))
                    connection.close.assert_called_once()

    def test_repeated_probes_do_not_render_dashboard(self):
        # A disposable HTTP fixture models the regression: / renders a page and
        # attempts two protected chart requests; /health is independent of auth.
        paths = []
        protected_chart_attempts = []

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                paths.append(self.path)
                if self.path == '/health':
                    body = b'ok'
                else:
                    protected_chart_attempts.extend(('initial', 'historical'))
                    body = b'<html>Dashboard with unavailable charts</html>'
                self.send_response(200)
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        original_connection = http.client.HTTPConnection
        with http.server.HTTPServer(('127.0.0.1', 0), Handler) as server:
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                # Only redirect the test's fixed loopback connection to its own
                # ephemeral port. Never connect to a real HA installation.
                with patch.object(runtime.http.client, 'HTTPConnection', side_effect=lambda *a, **kw:
                                  original_connection('127.0.0.1', server.server_port, timeout=2)):
                    for _ in range(3):
                        self.assertTrue(runtime.web_response_reachable(self.options))
                self.assertEqual(['/health'] * 3, paths)
                self.assertEqual([], protected_chart_attempts)
            finally:
                server.shutdown()
                worker.join(timeout=2)


if __name__ == '__main__':
    unittest.main()
