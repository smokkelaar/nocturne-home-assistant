from unittest import TestCase
from unittest.mock import patch
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import update_personal as updater


class MergedBaseTests(TestCase):
    def test_same_approved_base_needs_no_extra_lookup(self):
        with patch.object(updater, 'github') as api:
            updater.require_merged_base('a' * 40, 'a' * 40, 'c' * 40)
            api.assert_not_called()

    def test_newer_merged_base_keeps_both_ancestry_proofs(self):
        responses = [{'status': 'ahead', 'merge_base_commit': {'sha': value * 40}} for value in ('a', 'b')]
        with patch.object(updater, 'github', side_effect=responses) as api:
            updater.require_merged_base('a' * 40, 'b' * 40, 'c' * 40)
        self.assertEqual([call.args[0] for call in api.call_args_list],
            ['compare/' + 'a' * 40 + '...' + 'b' * 40, 'compare/' + 'b' * 40 + '...' + 'c' * 40])

    def test_divergent_rollback_or_unmerged_base_fails_closed(self):
        good = {'status': 'ahead', 'merge_base_commit': {'sha': 'a' * 40}}
        for responses in (
            [{'status': 'diverged', 'merge_base_commit': {'sha': 'd' * 40}}],
            [{'status': 'behind', 'merge_base_commit': {'sha': 'b' * 40}}],
            [good, {'status': 'diverged', 'merge_base_commit': {'sha': 'd' * 40}}],
            [good, {'status': 'ahead', 'merge_base_commit': {'sha': 'd' * 40}}],
        ):
            with self.subTest(responses=responses), patch.object(updater, 'github', side_effect=responses):
                with self.assertRaises(ValueError):
                    updater.require_merged_base('a' * 40, 'b' * 40, 'c' * 40)

    def test_mutable_base_fails_before_network(self):
        with patch.object(updater, 'github') as api:
            with self.assertRaises(ValueError):
                updater.require_merged_base('a' * 40, 'main', 'c' * 40)
            api.assert_not_called()
