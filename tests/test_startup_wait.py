"""The API wait stays open while a startup migration works, and says what it is doing."""
import importlib
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'nocturne_local/rootfs/opt/nocturne-ha'))
runtime = importlib.import_module('run')


class Clock:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now


class StartupWaitTests(unittest.TestCase):
    def supervisor(self, clock):
        supervisor = runtime.Supervisor.__new__(runtime.Supervisor)
        supervisor.children, supervisor.status = [], {}
        supervisor.stop = threading.Event()
        supervisor.stop.wait = lambda seconds: setattr(clock, 'now', clock.now + seconds)
        return supervisor

    def test_progress_reports_statement_wait_and_blockers(self):
        answers = ['312|Lock/transactionid|1|UPDATE sensor_glucose SET deleted_at = now() WHERE x|y',
                   '2104 MB']
        with patch.object(runtime, 'psql', side_effect=answers):
            busy, lines = runtime.database_progress()
        self.assertTrue(busy)
        self.assertEqual('database 2104 MB', lines[0])
        self.assertIn('312 s bezig (Lock/transactionid, geblokkeerd door 1', lines[1])
        self.assertTrue(lines[1].endswith('WHERE x|y'))

    def test_idle_database_is_not_busy(self):
        with patch.object(runtime, 'psql', side_effect=['', '10 MB']):
            self.assertEqual((False, ['database 10 MB']), runtime.database_progress())
        with patch.object(runtime, 'psql', side_effect=RuntimeError):
            self.assertFalse(runtime.database_progress()[0])

    def test_busy_database_keeps_the_wait_open_past_its_timeout(self):
        clock = Clock()
        supervisor = self.supervisor(clock)
        ready_at = 5000
        with patch.object(runtime.time, 'monotonic', clock.monotonic), \
             patch.object(runtime, 'log'):
            supervisor.wait_for('API', lambda: clock.now >= ready_at, 3600,
                                lambda: (True, []))
        self.assertGreaterEqual(clock.now, ready_at)

    def test_idle_database_times_out_and_the_cap_holds(self):
        for busy, limit in ((False, 3600), (True, runtime.MAX_STARTUP_WAIT)):
            clock = Clock()
            supervisor = self.supervisor(clock)
            with self.subTest(busy=busy), patch.object(runtime.time, 'monotonic', clock.monotonic), \
                 patch.object(runtime, 'log'), self.assertRaises(RuntimeError):
                supervisor.wait_for('API', lambda: False, 3600, lambda: (busy, []))
            self.assertLessEqual(clock.now, limit + 2)


if __name__ == '__main__':
    unittest.main()
