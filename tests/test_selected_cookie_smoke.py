import sys
from pathlib import Path
import unittest
import subprocess
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import selected_cookie_smoke as selected


class SelectedCookieTests(unittest.TestCase):
    def test_cookie_runner_imports_without_the_versioning_dependency(self):
        command = "import sys; sys.path.insert(0, 'tools'); import selected_cookie_smoke; assert 'awesomeversion' not in sys.modules"
        subprocess.run([sys.executable, '-S', '-c', command], cwd=ROOT, check=True)

    def test_publication_tests_selected_channels_together_with_their_new_versions(self):
        candidates = {}
        for channel in ('latest', 'personal'):
            config = selected.read(ROOT / selected.CHANNELS[channel] / 'config.json')
            config['version'] = '1.0.99999'
            candidates[channel] = {'config': config}
        images = selected.references(ROOT, 'latest', 'new-latest:local', candidates)
        self.assertEqual('new-latest:local', images['latest'])
        self.assertTrue(images['personal'].endswith(':1.0.99999'))
        self.assertFalse(images['official'].endswith(':1.0.99999'))

    def test_checks_the_selected_image_and_pulls_only_published_peers(self):
        for channel in ('official', 'latest', 'personal'):
            with self.subTest(channel=channel), patch.object(selected, 'docker') as docker, patch.object(selected.cookie_smoke, 'main') as probe:
                selected.main(ROOT, channel, 'candidate:local')
                images = probe.call_args.kwargs
                self.assertEqual('candidate:local', images[channel])
                self.assertEqual({'official', 'latest', 'personal'}, set(images))
                self.assertEqual(2, docker.call_count)
                self.assertTrue(all(call.args[0] == 'pull' for call in docker.call_args_list))
                self.assertNotIn('candidate:local', [call.args[1] for call in docker.call_args_list])

    def test_test_channels_do_not_start_unrelated_cookie_instances(self):
        with patch.object(selected, 'docker') as docker, patch.object(selected.cookie_smoke, 'main') as probe:
            selected.main(ROOT, 'test-c', 'candidate:local')
            docker.assert_not_called()
            probe.assert_not_called()
