"""Guard subprocess bounds without importing probes that operate on /data."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def subprocess_calls(source):
    return [node for node in ast.walk(ast.parse(source)) if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute) and node.func.attr == 'run'
            and isinstance(node.func.value, ast.Name) and node.func.value.id == 'subprocess']


class CITimeoutTests(unittest.TestCase):
    def assert_bounded(self, source, expected):
        calls = subprocess_calls(source)
        self.assertEqual(1, len(calls))
        values = {keyword.arg: keyword.value for keyword in calls[0].keywords}
        self.assertIn('timeout', values, 'Inner subprocess needs its own timeout')
        timeout = ast.literal_eval(values['timeout'])
        self.assertEqual(expected, timeout)
        self.assertGreater(timeout, 0)
        self.assertLess(timeout, 180, 'Leave room inside the outer Docker timeout')
        self.assertIs(True, ast.literal_eval(values['check']))

    def test_certificate_generation_is_bounded(self):
        self.assert_bounded((ROOT / 'tools/tls_probe.py').read_text(), 15)

    def test_embedded_cold_copy_is_bounded(self):
        tree = ast.parse((ROOT / 'tools/recovery_smoke.py').read_text())
        copy_source = next(ast.literal_eval(node.value) for node in tree.body
                           if isinstance(node, ast.Assign) and any(
                               isinstance(target, ast.Name) and target.id == 'COPY' for target in node.targets))
        self.assert_bounded(copy_source, 90)


if __name__ == '__main__':
    unittest.main()
