"""Use Supervisor's actual version parser to prevent counter-boundary regressions."""
import unittest
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

    def test_migration_is_a_valid_distinct_store_version_for_manual_ha_update(self):
        # Supervisor need_update compares inequality, not ordering. The legacy
        # numeric and new letter-based schemes must not be silently conflated.
        candidate = AwesomeVersion('0.3.26-p11')
        self.assertTrue(candidate.valid)
        for previous in ('0.3.26-9', '0.3.26-10'):
            self.assertNotEqual(candidate, AwesomeVersion(previous))


if __name__ == '__main__':
    unittest.main()
