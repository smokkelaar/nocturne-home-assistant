import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import cookie_smoke
from personal_feature_probe import expect_status


class CookieProbeTests(unittest.TestCase):
    def test_http_diagnostic_has_status_and_source_location_not_response_data(self):
        secret = 'synthetic-secret-must-not-be-logged'
        try:
            expect_status(403, 200)
        except Exception as error:
            error.args = (secret,)
            output = cookie_smoke.failure_summary('PERSONAL_FEATURES', error)
        self.assertIn('HTTP_403_EXPECTED_200', output)
        self.assertIn('personal_feature_probe.py:', output)
        self.assertNotIn(secret, output)
        self.assertNotIn(str(Path(__file__).parent), output)

    def test_generic_exception_does_not_expose_its_message(self):
        output = cookie_smoke.failure_summary('PERSONAL_FEATURES', ValueError('private body'))
        self.assertNotIn('private body', output)
        self.assertIn('ValueError', output)

    def test_invalid_image_combinations_do_not_launch_containers(self):
        for options in ({}, {'official': 'one'}, {'latest': 'one', 'personal': 'two'}):
            with patch.object(cookie_smoke, 'docker') as docker:
                with self.assertRaises(ValueError):
                    cookie_smoke.main(**options)
                docker.assert_not_called()

    def test_workflow_keeps_three_instance_and_recovery_gates(self):
        workflow = (Path(__file__).resolve().parents[1] / '.github/workflows/validate.yml').read_text()
        fast = workflow.index('python3 tools/cookie_smoke.py --personal nocturne-personal:ci')
        baseline = workflow.index('Check out immutable Official baseline')
        self.assertLess(fast, baseline)
        self.assertIn('--official nocturne-official:ci --latest nocturne-latest:ci --personal nocturne-personal:ci', workflow)
        self.assertIn('python3 tools/recovery_smoke.py --image nocturne-personal:ci --baseline nocturne-personal:baseline', workflow)
