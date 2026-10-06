"""Each channel must expose its own API identity instead of the base image's."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
CHANNELS = ('nocturne_local', 'nocturne_latest', 'nocturne_personal',
            'nocturne_test_a', 'nocturne_test_b', 'nocturne_test_c')


def settings(channel):
    spec = importlib.util.spec_from_file_location('build_metadata_' + channel,
        ROOT / channel / 'rootfs/opt/nocturne-ha/settings.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BuildMetadataTests(unittest.TestCase):
    def test_smoke_probe_reports_only_safe_failure_markers(self):
        spec = importlib.util.spec_from_file_location('smoke_probe', ROOT / 'tools/smoke.py')
        smoke = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(smoke)
        marker = smoke.safe_failure_marker(
            'AssertionError: credential-value\n'
            'CI_PROBE_FAILED:HTTPError:LINE_12:STATUS_404')
        self.assertEqual('CI_PROBE_FAILED:HTTPError:LINE_12:STATUS_404', marker.group(0))
        self.assertIsNone(smoke.safe_failure_marker('credential-value'))

    def test_fresh_instance_smoke_reads_setup_independent_version_endpoint(self):
        probe = (ROOT / 'tools/smoke.py').read_text()
        self.assertIn('http://127.0.0.1:8080/api/v3/version', probe)
        self.assertNotIn('http://127.0.0.1:8080/api/v1/status', probe)

    def test_all_channels_export_pinned_commit_and_only_selected_parent_metadata(self):
        for channel in CHANNELS:
            with self.subTest(channel=channel):
                module = settings(channel)
                version = json.loads((ROOT / channel / 'rootfs/opt/nocturne-ha/version.json').read_text())
                with patch.dict(module.os.environ, {'GIT_COMMIT': 'wrong-base-image',
                    'BUILD_DATE': '2026-10-05T18:00:00Z', 'SUPERVISOR_TOKEN': 'never-inherited'}, clear=True):
                    api, web = module.service_environments(module.validate_options({}),
                        {key: 'a' * 64 for key in module.SECRET_FIELDS})
                self.assertEqual(version['source_commit'], api['GIT_COMMIT'])
                self.assertEqual('2026-10-05T18:00:00Z', api['BUILD_DATE'])
                self.assertNotIn('SUPERVISOR_TOKEN', api)
                self.assertNotIn('SUPERVISOR_TOKEN', web)

    def test_source_build_stamp_overrides_inherited_base_image_date(self):
        with tempfile.TemporaryDirectory() as directory:
            stamp = Path(directory) / 'api-build-date'
            stamp.write_text('2026-10-05T19:00:00Z\n')
            for channel in CHANNELS:
                with self.subTest(channel=channel):
                    metadata = settings(channel).api_build_metadata(
                        {'source_commit': 'correct-source', 'source_at': '1999-01-01T00:00:00Z'},
                        stamp, {'BUILD_DATE': '2026-09-26T12:00:00Z'})
                    self.assertEqual({'GIT_COMMIT': 'correct-source',
                                      'BUILD_DATE': '2026-10-05T19:00:00Z'}, metadata)

    def test_source_commit_date_is_never_misrepresented_as_build_date(self):
        with tempfile.TemporaryDirectory() as directory:
            metadata = settings('nocturne_local').api_build_metadata(
                {'source_commit': 'correct-source', 'commit_at': '1999-01-01T00:00:00Z'},
                Path(directory) / 'missing', {})
            self.assertNotIn('BUILD_DATE', metadata)

    def test_each_compiled_channel_stamps_and_copies_its_own_api_build_date(self):
        for channel in CHANNELS[2:]:
            with self.subTest(channel=channel):
                dockerfile = (ROOT / channel / 'Dockerfile').read_text()
                self.assertIn('&& date -u +%Y-%m-%dT%H:%M:%SZ > /out/api-build-date', dockerfile)
                self.assertIn('COPY --from=source /out/api-build-date /opt/nocturne-ha/api-build-date', dockerfile)
