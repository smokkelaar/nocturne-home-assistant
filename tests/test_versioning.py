"""Delivery counters must never change the shared functional wrapper."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from versioning import next_package, package_build, wrapper_version


class VersionTests(unittest.TestCase):
    def test_delivery_order_and_shared_version(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'wrapper.json').write_text(json.dumps({'version': '0.1.4'}))
            self.assertEqual('0.1.4', wrapper_version(root))
            self.assertEqual('0.1.4-10', next_package(root, '0.1.4-9'))
            self.assertEqual(10, package_build(root, '0.1.4-10'))
            for invalid in ('0.1.3-1', '0.1.5-1', '0.1.4', '0.1.4-0',
                            '0.1.4-01', '0.1.4-1.1', '0.1.4-1x', None):
                with self.subTest(value=invalid), self.assertRaises(ValueError):
                    package_build(root, invalid)

    def test_invalid_wrapper_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for invalid in ('0.1', '01.1.4', '0.1.4-1', None):
                (root / 'wrapper.json').write_text(json.dumps({'version': invalid}))
                with self.subTest(value=invalid), self.assertRaises(ValueError):
                    wrapper_version(root)
