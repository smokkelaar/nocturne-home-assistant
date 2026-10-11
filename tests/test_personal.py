"""Personal must not change existing HA app identities or silently use stock code."""
import importlib.util
import json
import re
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import update_personal as updater
import update_test_channels


class PersonalTests(unittest.TestCase):
    def test_personal_delivery_counters_migrate_and_keep_the_p_prefix(self):
        self.assertEqual('0.3.27-p1', updater.next_delivery('0.3.26', '0.3.26-10'))
        self.assertEqual('0.3.26-p10', updater.next_delivery('0.3.26', '0.3.26-p9'))
        self.assertEqual('0.3.26-p100', updater.next_delivery('0.3.26', '0.3.26-p99'))
        self.assertEqual('0.3.27-p1', updater.next_delivery('0.3.27'))
        self.assertEqual('0.3.27-p2', updater.next_delivery('0.3.26', '0.3.27-p1'))
        self.assertEqual('0.3.27-p3', updater.next_delivery('0.3.27', '0.3.27-p2'))
        self.assertEqual('0.3.28-p1', updater.next_delivery('0.3.28', '0.3.27-p99'))
        for previous in ('0.3.26-a10', '0.3.26-p0', '0.3.26-0'):
            with self.subTest(previous=previous), self.assertRaises(ValueError):
                updater.next_delivery('0.3.26', previous)

    def test_generator_rejects_bare_numeric_and_other_channel_versions(self):
        for delivery in (self.lock['version'] + '-10', self.lock['version'] + '-a10'):
            with self.subTest(delivery=delivery), self.assertRaises(ValueError):
                updater.files(self.lock, delivery)

    def test_higher_package_base_keeps_actual_personal_feature_version(self):
        major, minor, patch_version = map(int, self.lock['version'].split('.'))
        delivery = f'{major}.{minor}.{patch_version + 1}-p1'
        generated = updater.files(self.lock, delivery)
        runtime = json.loads(generated['rootfs/opt/nocturne-ha/version.json'])
        self.assertEqual(self.lock['version'], runtime['personal'])
        self.assertEqual(delivery, runtime['package'])
        with self.assertRaises(ValueError):
            updater.files(self.lock, '0.0.1-p1')

    def test_daily_promotion_keeps_package_floor_when_feature_catches_up(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = root / 'nocturne_personal'
            directory.mkdir()
            (root / 'upstream-personal.json').write_text(json.dumps({**self.lock, 'version': '0.3.26'}))
            (directory / 'config.json').write_text('{"version":"0.3.27-p2"}')
            (directory / 'CHANGELOG.md').write_text('Existing history\n')
            candidate = {**self.lock, 'version': '0.3.27'}
            with patch.object(updater, 'ROOT', root), \
                 patch.object(updater, 'resolve', return_value=candidate), \
                 patch.object(updater, 'validate_transition'), \
                 patch.object(updater, 'files', return_value={}) as generated, \
                 patch.object(updater, 'check'):
                updater.update()
            generated.assert_called_once_with(candidate, '0.3.27-p3')

    def setUp(self):
        self.lock = json.loads((ROOT / 'upstream-personal.json').read_text())
        self.clean_lock = {**self.lock, 'commit': self.lock['upstream']['commit'],
                           'commit_at': self.lock['upstream']['commit_at']}
        self.directory = ROOT / 'nocturne_personal'
        self.config = json.loads((self.directory / 'config.json').read_text())

    def test_generated_package_matches_exact_source_and_recipe(self):
        updater.check()

    def test_generated_test_channels_match_their_pins(self):
        for path, expected in update_test_channels.files().items():
            self.assertEqual(expected, (ROOT / path).read_bytes(), path)

    def test_generated_feature_docs_follow_extension_version(self):
        lock = {**self.lock, 'version': '0.2.99', 'commit': 'a' * 40}
        generated = updater.files(lock, '0.2.99-p1')
        for path in ('DOCS.md', 'README.md'):
            self.assertIn(b'Personal 0.2.99 includes Google Health imports for steps, heart rate, weight and sleep', generated[path])
            self.assertIn(b'Progress refreshes while the connector page is open', generated[path])
            self.assertNotIn(b'does not include the separate Google Health contribution', generated[path])
            self.assertNotIn(b'medication log', generated[path])

    def test_local_build_progress_is_explained_and_logged(self):
        generated = updater.files(self.lock, self.config['version'])
        config = json.loads(generated['config.json'])
        dockerfile = generated['Dockerfile'].decode()
        docs = generated['DOCS.md'].decode()

        if config.get('image'):
            self.assertIn('Vooraf gebouwd', config['description'])
        else:
            self.assertIn('HA may show 0% until it finishes', config['description'])
        if not config.get('image'):
            self.assertIn('Experimental; not for clinical use', config['description'])
        self.assertIn('compiled together on GitHub', docs)
        self.assertIn('prebuilt AMD64 and ARM64 images', docs)
        self.assertNotIn('keeps the update dialog at 0%', docs)
        for phase in range(1, 8):
            self.assertIn(f'Nocturne build phase {phase}/7:', dockerfile)

    def test_three_distinct_data_and_network_identities(self):
        all_configs = [json.loads((ROOT / package / 'config.json').read_text())
                   for package in ('nocturne_local', 'nocturne_latest', 'nocturne_personal', 'nocturne_test_a', 'nocturne_test_b', 'nocturne_test_c')]
        self.assertEqual(6, len({entry['slug'] for entry in all_configs}))
        self.assertEqual([8448, 8449, 8450, 8451, 8452, 8453], [entry['ports']['8448/tcp'] for entry in all_configs])
        self.assertEqual('Nocturne Personal Release', self.config['name'])
        self.assertEqual('nocturne_personal', self.config['slug'])
        self.assertTrue(self.config['options']['gateway_auth'])
        self.assertEqual('cold', self.config['backup'])
        self.assertNotIn('host_network', self.config)

    def test_test_b_rejects_invalid_provenance(self):
        source = json.loads((ROOT / 'upstream-test-b.json').read_text())
        for field, value in [('repository', 'untrusted/repo'), ('commit', 'main'),
                             ('base_commit', 'moving-branch'), ('archive_sha256', 'bad'),
                             ('pull_request', True), ('pull_request_url', 'https://example.com'),
                             ('commit_at', '2026-10-03')]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                update_test_channels.validate_test_b_source({**source, field: value})

    def test_test_channels_use_main_with_distinct_runtime_identities(self):
        latest = json.loads((ROOT / 'upstream-latest.json').read_text())
        for letter, port in zip('abc', (8451, 8452, 8453)):
            with self.subTest(channel=letter):
                package = ROOT / ('nocturne_test_' + letter)
                config = json.loads((package / 'config.json').read_text())
                runtime = json.loads((package / 'rootfs/opt/nocturne-ha/version.json').read_text())
                source = json.loads((ROOT / f'upstream-test-{letter}.json').read_text())
                self.assertEqual('main', source['channel'])
                self.assertEqual(latest['commit'], source['commit'])
                self.assertEqual(source['commit'], source['base_commit'])
                self.assertEqual(source['commit'], runtime['source_commit'])
                self.assertEqual(source['base_commit'], runtime['base_commit'])
                self.assertEqual(source['repository'], runtime['repository'])
                self.assertEqual(config['version'], runtime['package'])
                self.assertEqual('Nocturne Test ' + letter.upper(), config['name'])
                self.assertEqual('NocturneTest' + letter.upper() + '_', runtime['cookie_namespace'])
                self.assertEqual(port, config['ports']['8448/tcp'])
                self.assertEqual(f'https://homeassistant.local:{port}', runtime['default_public_url'])
                self.assertEqual('Nocturne main', runtime['release'])
                self.assertNotIn('personal', runtime)
                self.assertNotIn('PR #', runtime['purpose'])
                self.assertNotIn('pull_request', source)
                self.assertEqual('https://github.com/nightscout/nocturne/tree/' + latest['commit'], runtime['release_url'])
                recipe = (package / 'Dockerfile').read_text()
                self.assertIn('--checksum=sha256:' + source['archive_sha256'], recipe)
                self.assertIn(source['commit'], recipe)
                self.assertIn(f'ARG BUILD_VERSION={config["version"]}', recipe)
                self.assertIn("('NocturneTest" + letter.upper() + "_',)", (package / 'rootfs/opt/nocturne-ha/settings.py').read_text())
                self.assertIn("'NocturneTest" + letter.upper() + "_'", (package / 'rootfs/opt/nocturne-ha/cookies.mjs').read_text())

    def test_test_c_rejects_invalid_provenance(self):
        source = json.loads((ROOT / 'upstream-test-c.json').read_text())
        for field, value in [('repository', 'untrusted/repo'), ('commit', 'main'),
                             ('base_commit', 'moving-branch'), ('archive_sha256', 'bad'),
                             ('pull_request', True), ('pull_request_url', 'https://example.com'),
                             ('commit_at', '2026-10-03')]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                update_test_channels.validate_test_pr_source({**source, field: value}, 'Test C')

    def test_clean_personal_main_does_not_advertise_extensions(self):
        generated = updater.files(self.clean_lock, self.config['version'])
        self.assertEqual(self.clean_lock['upstream']['commit'], self.clean_lock['commit'])
        for path in ('DOCS.md', 'README.md'):
            self.assertIn(b'unmodified upstream main, without Personal extensions', generated[path])
            self.assertNotIn(b'Personal 0.3.28 includes', generated[path])
        runtime = json.loads(generated['rootfs/opt/nocturne-ha/version.json'])
        self.assertEqual('Nocturne main', runtime['release'])

    def test_clean_main_can_replace_previous_personal_history(self):
        old = {**self.clean_lock, 'commit': 'a' * 40}
        with patch.object(updater, 'github') as github:
            updater.validate_transition(old, self.clean_lock)
        github.assert_not_called()

    def test_clean_personal_resolves_without_extension_metadata(self):
        head = {'sha': self.clean_lock['commit'], 'commit': {'committer': {'date': self.clean_lock['commit_at']}}}
        comparison = {'status': 'identical', 'merge_base_commit': {'sha': self.clean_lock['commit']}}
        class Archive:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, size): return b''
        with patch.object(updater, 'github', side_effect=[head, comparison]) as github, \
             patch.object(updater.urllib.request, 'urlopen', return_value=Archive()):
            resolved = updater.resolve()
        self.assertEqual(self.clean_lock['commit'], resolved['commit'])
        self.assertEqual(self.clean_lock['version'], resolved['version'])
        self.assertEqual(['commits/personal', f"compare/{self.clean_lock['commit']}...{self.clean_lock['commit']}"],
                         [call.args[0] for call in github.call_args_list])

    def test_history_preserving_reset_resolves_exact_upstream_source(self):
        canonical = {'sha': self.clean_lock['commit'], 'commit': {
            'tree': {'sha': 'b' * 40}, 'committer': {'date': self.clean_lock['commit_at']}}}
        reset = {**canonical, 'sha': 'a' * 40}
        comparison = {'status': 'identical', 'merge_base_commit': {'sha': self.clean_lock['commit']}}
        class Archive:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, size): return b''
        with patch.object(updater, 'github', side_effect=[reset, canonical, comparison]), \
             patch.object(updater.urllib.request, 'urlopen', return_value=Archive()):
            resolved = updater.resolve()
        self.assertEqual(self.clean_lock['commit'], resolved['commit'])

    def test_personal_source_replaces_both_api_and_web(self):
        recipe = (self.directory / 'Dockerfile').read_text()
        self.assertIn('dotnet publish', recipe)
        self.assertIn('pnpm --filter @nocturne/app run build', recipe)
        self.assertIn('COPY --from=source /out/api/ /app/', recipe)
        self.assertIn('COPY --from=source /out/web/ /opt/nocturne-web/', recipe)
        self.assertIn(self.lock['commit'], recipe)
        self.assertIn('--checksum=sha256:' + self.lock['archive_sha256'], recipe)
        self.assertNotIn(':latest', recipe)
        for line in recipe.splitlines():
            if line.startswith('FROM '):
                self.assertIn('@sha256:', line)

    def test_settings_use_only_the_fixed_personal_namespace(self):
        path = self.directory / 'rootfs/opt/nocturne-ha/settings.py'
        spec = importlib.util.spec_from_file_location('personal_settings_test', path)
        settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(settings)
        options = settings.validate_options({'cookie_namespace': 'NocturneOfficial_'})
        self.assertEqual('NocturnePersonal_', options['cookie_namespace'])
        self.assertEqual('https://homeassistant.local:8450', options['public_url'])
        page = settings.status_page(options, {}, '', True)
        self.assertIn('Nocturne Personal Release', page)
        self.assertIn('Nocturne main', page)
        self.assertIn(self.lock['commit'][:12], page)
        options['cookie_namespace'] = 'NocturneLatest_'
        with self.assertRaises(ValueError):
            settings.nginx_config(options, '/cert', '/key')

    def test_lock_rejects_mutable_refs_and_foreign_sources(self):
        for field, value in [('repository', 'someone/else'), ('commit', 'personal'),
                             ('archive_sha256', 'wrong'), ('version', 'latest')]:
            lock = {**self.lock, field: value}
            with self.assertRaises(ValueError):
                updater.validate(lock)

    def test_updater_does_not_write_existing_packages(self):
        source = (ROOT / 'tools/update_personal.py').read_text()
        self.assertNotIn("ROOT / 'nocturne_local'", source)
        self.assertIn("directory = ROOT / 'nocturne_personal'", source)
        workflow = (ROOT / '.github/workflows/personal.yml').read_text()
        allowlist = workflow.split('add-paths:', 1)[1].split('body:', 1)[0]
        self.assertNotIn('nocturne_latest', allowlist)
        self.assertNotIn('nocturne_local', allowlist)
        self.assertIn('upstream-personal.json', allowlist)

    def test_transition_rejects_version_and_source_rollbacks(self):
        with self.assertRaises(ValueError):
            updater.validate_transition(self.lock, {**self.lock, 'version': '0.0.1'})
        changed = {**self.lock, 'commit': 'a' * 40}
        with patch.object(updater, 'github', return_value={'status': 'diverged', 'merge_base_commit': {'sha': 'b' * 40}}):
            with self.assertRaises(ValueError):
                updater.validate_transition(self.lock, changed)
        with patch.object(updater, 'github', return_value={'status': 'ahead', 'merge_base_commit': {'sha': self.lock['commit']}}):
            updater.validate_transition(self.lock, changed)

    def test_required_container_job_does_not_skip_missing_comparison_base(self):
        workflow = (ROOT / '.github/workflows/validate.yml').read_text()
        container = workflow.split('  container:', 1)[1]
        self.assertIn('fetch-depth: 0', container)
        missing = container.split('if ! git cat-file', 1)[1].split('fi', 1)[0]
        self.assertIn('git fetch --no-tags origin "$base"', missing)
        self.assertNotIn('base=origin/main', missing)


if __name__ == '__main__':
    unittest.main()
