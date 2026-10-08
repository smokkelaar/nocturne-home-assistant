"""Use Supervisor's actual version parser to prevent counter-boundary regressions."""
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from update_personal import next_delivery
try:
    from awesomeversion import AwesomeVersion
except ImportError:
    AwesomeVersion = None


@unittest.skipIf(AwesomeVersion is None, 'CI installs the Supervisor-pinned version parser')
class HAPersonalVersionTests(unittest.TestCase):
    def test_personal_updates_increase_across_digit_boundaries(self):
        for older, newer in (('0.3.26-p9', '0.3.26-p10'), ('0.3.26-p99', '0.3.26-p100'),
                             ('0.3.26-p11', '0.3.26-p12'), ('0.3.26-p100', '0.3.27-p1')):
            with self.subTest(older=older, newer=newer):
                self.assertTrue(AwesomeVersion(newer).valid)
                self.assertGreater(AwesomeVersion(newer), AwesomeVersion(older))

    def test_migration_must_rank_above_installed_legacy_and_failed_p_version(self):
        candidate = AwesomeVersion('0.3.27-p1')
        self.assertTrue(candidate.valid)
        for previous in ('0.3.26-9', '0.3.26-10', '0.3.26-p11'):
            self.assertGreater(candidate, AwesomeVersion(previous))

    def test_generator_preserves_upgrade_order_when_feature_catches_package_base(self):
        previous = '0.3.27-p1'
        for feature in ('0.3.26', '0.3.27', '0.3.28'):
            candidate = next_delivery(feature, previous)
            self.assertGreater(AwesomeVersion(candidate), AwesomeVersion(previous))
            previous = candidate

    def test_legacy_suffix_migration_generated_version_is_a_real_upgrade(self):
        for previous in ('0.3.26-9', '0.3.26-10'):
            self.assertGreater(AwesomeVersion(next_delivery('0.3.26', previous)), AwesomeVersion(previous))


if __name__ == '__main__':
    unittest.main()
