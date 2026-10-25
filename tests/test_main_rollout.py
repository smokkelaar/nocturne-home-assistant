import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import main_rollout
import prebuilt_publish
import update_test_channels


class MainRolloutTests(unittest.TestCase):
    def test_official_images_and_four_personal_sources_preserve_storage_identity(self):
        def inspect(repository, reference, arch, *args):
            return {'digest': reference if reference.startswith('sha256:') else 'sha256:' + 'a' * 64}

        with tempfile.TemporaryDirectory() as temporary, patch.object(prebuilt_publish.registry, 'image', side_effect=inspect):
            destination = Path(temporary)
            result = prebuilt_publish.prepare(ROOT, destination, 'd' * 40, 1000, 1, 'e' * 40, channels='all')
            self.assertEqual(12, len(result['include']))
            for item in result['include']:
                context = Path(item['context'])
                original = prebuilt_publish.read(ROOT / item['package'] / 'config.json')
                config = prebuilt_publish.read(context / 'config.json')
                for field in ('slug', 'ports', 'options'):
                    self.assertEqual(original[field], config[field])
                metadata = prebuilt_publish.read(context / 'rootfs/opt/nocturne-ha/version.json')
                recipe = (context / 'Dockerfile').read_text()
                rollout = main_rollout.load(ROOT, item['channel'])
                if rollout:
                    self.assertEqual(rollout['commit'], metadata['source_commit'])
                    self.assertEqual(rollout['repository'], metadata['repository'])
                    self.assertNotIn('codeload.github.com/smokkelaar', recipe)
                    self.assertNotIn('COPY --from=source', recipe)
                    self.assertEqual({'api', 'web'}, set(prebuilt_publish.read(destination / 'candidates.json')['official']['runtime_pins'][item['arch']]))
                    previous = prebuilt_publish.read(ROOT / item['package'] / 'rootfs/opt/nocturne-ha/version.json')
                    self.assertEqual(previous['cookie_namespace'], metadata['cookie_namespace'])
                    self.assertEqual(previous['default_public_url'], metadata['default_public_url'])
                elif item['channel'] == 'latest':
                    approved = prebuilt_publish.read(ROOT / 'upstream-latest.json')
                    self.assertEqual('nightscout/nocturne', metadata['repository'])
                    self.assertEqual(approved['commit'], metadata['source_commit'])
                    self.assertNotIn('COPY --from=source', recipe)
                else:
                    personal = prebuilt_publish.read(ROOT / 'upstream-personal.json')
                    source = (prebuilt_publish.read(ROOT / f"upstream-{item['channel']}.json")
                              if item['channel'].startswith('test-') else personal)
                    if source.get('channel') != 'personal-pr':
                        source = personal
                    self.assertEqual(source.get('personal_version', personal['version']), metadata['personal'])
                    self.assertEqual(source['commit'], metadata['source_commit'])
                    self.assertEqual(personal['repository'], metadata['repository'])
                    self.assertIn('/tar.gz/' + source['commit'], recipe)
                    self.assertIn('COPY --from=source /out/api/ /app/', recipe)
                    self.assertIn('COPY --from=source /out/web/', recipe)

    def test_invalid_source_cannot_enter_a_build(self):
        manifest = json.loads((ROOT / 'main-rollout.json').read_text())
        for field, value in [('source', 'unverified'), ('channels', ['latest']), ('repository', 'smokkelaar/nocturne-personal')]:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary)
                (path / 'main-rollout.json').write_text(json.dumps({**manifest, field: value}))
                with self.assertRaises(ValueError):
                    main_rollout.load(path, 'latest')

    def test_other_channels_keep_their_source_policy(self):
        self.assertIsNone(main_rollout.load(ROOT, 'personal'))
        self.assertIsNone(main_rollout.load(ROOT, 'unknown'))

    def test_personal_promotion_updates_all_four_installers_together(self):
        personal = prebuilt_publish.read(ROOT / 'upstream-personal.json')
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'upstream-personal.json').write_text(json.dumps(personal))
            for letter in 'abc':
                (root / f'upstream-test-{letter}.json').write_text('{"commit":"old"}')
            with patch.object(update_test_channels, 'ROOT', root):
                update_test_channels.follow_personal()
            for letter in 'abc':
                self.assertEqual(personal, prebuilt_publish.read(root / f'upstream-test-{letter}.json'))
        workflow = (ROOT / '.github/workflows/personal.yml').read_text()
        self.assertIn('update_test_channels.py --follow-personal --update', workflow)
        paths = workflow.split('add-paths:', 1)[1].split('body:', 1)[0]
        for name in ('upstream-personal.json', 'nocturne_personal'):
            self.assertIn(name, paths)
        for letter in 'abc':
            self.assertIn(f'upstream-test-{letter}.json', paths)
            self.assertIn(f'nocturne_test_{letter}', paths)
