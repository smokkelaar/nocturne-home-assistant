"""Check native-recovery orchestration without accepting any real container."""
import contextlib
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import smoke


class SmokeRecoveryTests(unittest.TestCase):
    def exercise(self, capability):
        state = {'skip': False}
        commands = []
        probes = []
        def docker(*args, **options):
            commands.append((args, options))
            if args[0] == 'inspect':
                return '0'
            if args[0] == 'logs':
                return 'GATEWAY_SKIPPED' if state['skip'] else ''
            return 'PASS: synthetic test command'
        def execute(name, code, **options):
            probes.append(code)
            if 'recovery_compatibility.report' in code:
                return json.dumps(capability)
            if "options['skip_gateway_check'] = " in code:
                state['skip'] = "options['skip_gateway_check'] = True" in code
            return 'fixed-synthetic-secret-digest'
        with patch.object(smoke, 'docker', side_effect=docker), \
             patch.object(smoke, 'execute', side_effect=execute), \
             patch.object(smoke, 'wait_ready'), contextlib.redirect_stdout(io.StringIO()):
            smoke.main('synthetic-ci-image')
        return commands, probes

    def test_compatible_image_runs_actual_native_probe_and_keeps_isolation(self):
        commands, _ = self.exercise({'compatible': True, 'reason': 'verified-source-contract'})
        native = [(args, options) for args, options in commands if 'STANDALONE_TOTP_RESET' in options.get('input', '')]
        self.assertEqual(1, len(native))
        self.assertRegex(native[0][0][3], '^NOCTURNE_CI_FIXTURE=nocturne-ci-[0-9a-f]{32}$')
        self.assertTrue(any(args[:2] == ('volume', 'rm') for args, _ in commands))

    def test_unknown_contract_skips_native_mutation_and_probes_fail_closed(self):
        commands, probes = self.exercise({'compatible': False, 'reason': 'unknown-source-contract'})
        self.assertFalse(any('STANDALONE_TOTP_RESET' in options.get('input', '') for _, options in commands))
        self.assertTrue(any('owner_recovery.guard()' in code for code in probes))

    def test_network_failure_is_not_mistaken_for_a_reviewed_incompatible_build(self):
        with self.assertRaisesRegex(RuntimeError, 'source check unavailable'):
            self.exercise({'compatible': False, 'reason': 'source-check-unavailable'})


if __name__ == '__main__':
    unittest.main()
