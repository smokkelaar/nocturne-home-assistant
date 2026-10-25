import json
from pathlib import Path
import sys
import unittest
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import update_test_channels


class PersonalPrSourceTests(unittest.TestCase):
    def source(self):
        return {"channel": "personal-pr", "repository": "smokkelaar/nocturne-personal",
                "pull_request": 63, "pull_request_url": "https://github.com/smokkelaar/nocturne-personal/pull/63",
                "commit": "a" * 40, "base_commit": "b" * 40, "archive_sha256": "c" * 64,
                "commit_at": "2026-10-24T07:35:02Z", "base_commit_at": "2026-10-23T21:52:07Z"}

    def test_accepts_exact_personal_pr_for_each_test_channel_only(self):
        source = self.source()
        for channel in ("Test A", "Test B", "Test C"):
            update_test_channels.validate_test_pr_source(source, channel)
        with self.assertRaises(ValueError):
            update_test_channels.validate_test_pr_source(source, "Personal")

    def test_personal_pr_source_overrides_purpose_plan_docs_and_version(self):
        source = {**self.source(), "pull_request": 68,
                  "pull_request_url": "https://github.com/smokkelaar/nocturne-personal/pull/68",
                  "personal_version": "9.9.9", "purpose": "Doel", "test_plan": "Plan", "docs_note": "Note."}
        read = update_test_channels.read
        with patch.object(update_test_channels, "read", side_effect=lambda path:
                          source if path == "upstream-test-b.json" else read(path)):
            generated = update_test_channels.files()
        runtime = json.loads(generated["nocturne_test_b/rootfs/opt/nocturne-ha/version.json"])
        self.assertEqual(("Doel", "Plan", "9.9.9", "Personal PR #68"),
                         (runtime["purpose"], runtime["test_plan"], runtime["personal"], runtime["release"]))
        self.assertIn("Note.", generated["nocturne_test_b/DOCS.md"].decode())
        self.assertIn(source["archive_sha256"], generated["nocturne_test_b/Dockerfile"].decode())

    def test_rejects_mismatched_repository_url_and_invalid_provenance(self):
        for field, value in (("repository", "other/repo"), ("pull_request", True),
                             ("pull_request_url", "https://github.com/nightscout/nocturne/pull/63"),
                             ("archive_sha256", "bad"), ("commit", "main"),
                             ("base_commit", "main"), ("commit_at", "2026-10-24T07:35:02")):
            with self.subTest(field=field), self.assertRaises(ValueError):
                update_test_channels.validate_test_pr_source({**self.source(), field: value}, "Test A")

    def test_generated_test_a_identifies_the_pr_and_admin_test_plan(self):
        read = update_test_channels.read
        with patch.object(update_test_channels, "read", side_effect=lambda path:
                          self.source() if path == "upstream-test-a.json" else read(path)):
            generated = update_test_channels.files()
        runtime = json.loads(generated["nocturne_test_a/rootfs/opt/nocturne-ha/version.json"])
        self.assertEqual(self.source()["commit"], runtime["source_commit"])
        self.assertEqual(self.source()["pull_request_url"], runtime["release_url"])
        self.assertIn("platformbeheerder", runtime["test_plan"])
        self.assertIn("Personal PR #63", runtime["release"])
        self.assertIn(self.source()["archive_sha256"], generated["nocturne_test_a/Dockerfile"].decode())
        for letter in "bc":
            expected = (ROOT / f"nocturne_test_{letter}/rootfs/opt/nocturne-ha/version.json").read_bytes()
            self.assertEqual(expected, generated[f"nocturne_test_{letter}/rootfs/opt/nocturne-ha/version.json"])

    def test_daily_personal_promotion_keeps_the_explicit_test_a_pr_pin(self):
        personal = json.loads((ROOT / "upstream-personal.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, value in (("upstream-personal.json", personal), ("upstream-test-a.json", self.source()),
                                ("upstream-test-b.json", personal), ("upstream-test-c.json", personal)):
                (root / name).write_text(json.dumps(value), encoding="utf-8")
            with patch.object(update_test_channels, "ROOT", root):
                update_test_channels.follow_personal()
            self.assertEqual(self.source(), json.loads((root / "upstream-test-a.json").read_text()))
            for letter in "bc":
                self.assertEqual(personal, json.loads((root / f"upstream-test-{letter}.json").read_text()))
