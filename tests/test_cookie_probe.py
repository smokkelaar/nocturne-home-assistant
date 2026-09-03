import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import cookie_smoke
from personal_feature_probe import complete_fixture_onboarding, expect_status


class CookieProbeTests(unittest.TestCase):
    def test_fixture_completes_real_onboarding_only_after_authentication(self):
        from unittest.mock import Mock
        request = Mock(side_effect=[
            (401, b''), (200, b'{"onboardingCompleted":false}'),
            (303, b''), (204, b''), (200, b'{"onboardingCompleted":true}'),
        ])
        anonymous = object()
        complete_fixture_onboarding(request, anonymous)
        calls = request.call_args_list
        self.assertIs(calls[0].kwargs['opener'], anonymous)
        self.assertEqual(calls[3].args, (8450, '/api/auth/passkey/onboarding/complete', 'POST'))
        self.assertNotIn('opener', calls[3].kwargs)
        self.assertTrue(all('raw_cookie' not in call.kwargs for call in calls))

    def test_fixture_rejects_a_completion_request_without_authentication(self):
        from unittest.mock import Mock
        from personal_feature_probe import ProbeHttpError
        request = Mock(return_value=(204, b''))
        with self.assertRaises(ProbeHttpError):
            complete_fixture_onboarding(request, object())
        self.assertEqual(request.call_count, 1)

    def test_fixture_verifies_persisted_completion_not_just_success_status(self):
        from unittest.mock import Mock
        request = Mock(side_effect=[
            (401, b''), (200, b'{"onboardingCompleted":false}'),
            (303, b''), (204, b''), (200, b'{"onboardingCompleted":false}'),
        ])
        with self.assertRaises(AssertionError):
            complete_fixture_onboarding(request, object())

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
