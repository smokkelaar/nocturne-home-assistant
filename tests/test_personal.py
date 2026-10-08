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
            (root / 'upstream-personal.json').write_text(json.dumps(self.lock))
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
        self.directory = ROOT / 'nocturne_personal'
        self.config = json.loads((self.directory / 'config.json').read_text())

    def test_generated_package_matches_exact_source_and_recipe(self):
        updater.check()

    def test_generated_test_channels_match_their_pins(self):
        for path, expected in update_test_channels.files().items():
            self.assertEqual(expected, (ROOT / path).read_bytes(), path)

    def test_generated_feature_docs_follow_extension_version(self):
        lock = {**self.lock, 'version': '0.2.99'}
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
        self.assertIn('keeps the update dialog at 0%', docs)
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

    def test_test_a_pins_pr1293_independently_with_a_distinct_runtime_identity(self):
        test_a = json.loads((ROOT / 'nocturne_test_a/config.json').read_text())
        test_runtime = json.loads((ROOT / 'nocturne_test_a/rootfs/opt/nocturne-ha/version.json').read_text())
        self.assertNotEqual(self.config['slug'], test_a['slug'])
        self.assertTrue(updater.published_number(test_a['version']) or test_a['version'].startswith(self.lock['version'] + '-'))
        source = json.loads((ROOT / 'upstream-test-a.json').read_text())
        self.assertEqual(source['commit'], test_runtime['source_commit'])
        self.assertEqual(source['base_commit'], test_runtime['base_commit'])
        self.assertEqual(source['pull_request_url'], test_runtime['release_url'])
        self.assertNotIn('personal', test_runtime)
        test_recipe = (ROOT / 'nocturne_test_a/Dockerfile').read_text()
        self.assertIn('--checksum=sha256:' + source['archive_sha256'], test_recipe)
        self.assertIn(source['commit'], test_recipe)
        self.assertIn('Google Health PR #1293', test_a['description'])
        self.assertEqual(test_a['version'], test_runtime['package'])
        self.assertEqual('Nocturne Test A', test_a['name'])
        self.assertEqual('NocturneTestA_', test_runtime['cookie_namespace'])
        self.assertEqual('https://homeassistant.local:8451', test_runtime['default_public_url'])
        test_settings = (ROOT / 'nocturne_test_a/rootfs/opt/nocturne-ha/settings.py').read_text()
        self.assertIn("('NocturneTestA_',)", test_settings)
        test_cookies = (ROOT / 'nocturne_test_a/rootfs/opt/nocturne-ha/cookies.mjs').read_text()
        self.assertIn("'NocturneTestA_'", test_cookies)

    def test_test_b_rejects_invalid_provenance(self):
        source = json.loads((ROOT / 'upstream-test-b.json').read_text())
        for field, value in [('repository', 'untrusted/repo'), ('commit', 'main'),
                             ('base_commit', 'moving-branch'), ('archive_sha256', 'bad'),
                             ('pull_request', True), ('pull_request_url', 'https://example.com'),
                             ('commit_at', '2026-10-03')]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                update_test_channels.validate_test_b_source({**source, field: value})

    def test_test_b_pins_hypo_comparison_with_a_distinct_runtime_identity(self):
        test_b = json.loads((ROOT / 'nocturne_test_b/config.json').read_text())
        test_runtime = json.loads((ROOT / 'nocturne_test_b/rootfs/opt/nocturne-ha/version.json').read_text())
        self.assertNotEqual(self.config['slug'], test_b['slug'])
        self.assertTrue(updater.published_number(test_b['version']) or test_b['version'].startswith('0.3.25-'))
        self.assertEqual(test_b['version'], test_runtime['package'])
        self.assertEqual('Nocturne Test B', test_b['name'])
        self.assertEqual('NocturneTestB_', test_runtime['cookie_namespace'])
        self.assertEqual('https://homeassistant.local:8452', test_runtime['default_public_url'])
        pr = json.loads((ROOT / 'upstream-test-b.json').read_text())
        self.assertEqual(pr['commit'], test_runtime['source_commit'])
        self.assertEqual(pr['base_commit'], test_runtime['base_commit'])
        self.assertEqual(pr['repository'], test_runtime['repository'])
        self.assertEqual(pr['pull_request_url'], test_runtime['release_url'])
        test_b_recipe = (ROOT / 'nocturne_test_b/Dockerfile').read_text()
        self.assertIn(pr['commit'], test_b_recipe)
        self.assertIn('--checksum=sha256:' + pr['archive_sha256'], test_b_recipe)
        self.assertIn('codeload.github.com', test_b_recipe)
        self.assertIn(f'ARG BUILD_VERSION={test_b["version"]}', test_b_recipe)
        self.assertIn(f"Hypo comparison PR #{pr['pull_request']}", test_runtime['release'])
        self.assertIn('Hypo Duration', test_runtime['purpose'])
        self.assertIn('Hypo Events', test_runtime['test_plan'])
        self.assertNotIn('Google Health', test_runtime['purpose'])
        self.assertNotIn('Google Health', test_b['description'])
        test_settings = (ROOT / 'nocturne_test_b/rootfs/opt/nocturne-ha/settings.py').read_text()
        self.assertIn("('NocturneTestB_',)", test_settings)
        test_cookies = (ROOT / 'nocturne_test_b/rootfs/opt/nocturne-ha/cookies.mjs').read_text()
        self.assertIn("'NocturneTestB_'", test_cookies)
        self.assertNotEqual(test_b['ports']['8448/tcp'],
                             json.loads((ROOT / 'nocturne_test_a/config.json').read_text())['ports']['8448/tcp'])

    def test_test_c_rejects_invalid_provenance(self):
        source = json.loads((ROOT / 'upstream-test-c.json').read_text())
        for field, value in [('repository', 'untrusted/repo'), ('commit', 'main'),
                             ('base_commit', 'moving-branch'), ('archive_sha256', 'bad'),
                             ('pull_request', True), ('pull_request_url', 'https://example.com'),
                             ('commit_at', '2026-10-03')]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                update_test_channels.validate_test_pr_source({**source, field: value}, 'Test C')

    def test_test_c_pins_clock_face_pr_with_a_distinct_runtime_identity(self):
        test_c = json.loads((ROOT / 'nocturne_test_c/config.json').read_text())
        test_runtime = json.loads((ROOT / 'nocturne_test_c/rootfs/opt/nocturne-ha/version.json').read_text())
        self.assertNotEqual(self.config['slug'], test_c['slug'])
        self.assertTrue(updater.published_number(test_c['version']) or test_c['version'].startswith('0.3.25-'))
        self.assertEqual(test_c['version'], test_runtime['package'])
        test_c_changelog = (ROOT / 'nocturne_test_c/CHANGELOG.md').read_text()
        self.assertTrue(test_c_changelog.startswith(f"## {test_c['version']}\n"))
        changelog_versions = [
            int(version) for version in re.findall(
                r'(?m)^#{1,2} 0\.3\.25-c(\d+)$', test_c_changelog)
        ]
        self.assertEqual(len(changelog_versions), len(set(changelog_versions)))
        self.assertEqual(sorted(changelog_versions, reverse=True), changelog_versions)
        self.assertEqual('Nocturne Test C', test_c['name'])
        self.assertEqual('NocturneTestC_', test_runtime['cookie_namespace'])
        self.assertEqual('https://homeassistant.local:8453', test_runtime['default_public_url'])
        pr = json.loads((ROOT / 'upstream-test-c.json').read_text())
        self.assertEqual(pr['commit'], test_runtime['source_commit'])
        self.assertEqual(pr['base_commit'], test_runtime['base_commit'])
        self.assertEqual(pr['repository'], test_runtime['repository'])
        self.assertEqual(pr['pull_request_url'], test_runtime['release_url'])
        test_recipe = (ROOT / 'nocturne_test_c/Dockerfile').read_text()
        self.assertIn(pr['commit'], test_recipe)
        self.assertIn('--checksum=sha256:' + pr['archive_sha256'], test_recipe)
        self.assertIn('codeload.github.com', test_recipe)
        self.assertIn(f'ARG BUILD_VERSION={test_c["version"]}', test_recipe)
        self.assertIn('Clock face units PR #2007', test_c['description'])
        self.assertNotIn('Google Health', test_runtime['purpose'])
        self.assertNotIn('Google Health', test_c['description'])
        self.assertNotIn('RUN_GOOGLE_HEALTH_TESTS', test_recipe)
        test_settings = (ROOT / 'nocturne_test_c/rootfs/opt/nocturne-ha/settings.py').read_text()
        self.assertIn("('NocturneTestC_',)", test_settings)
        test_cookies = (ROOT / 'nocturne_test_c/rootfs/opt/nocturne-ha/cookies.mjs').read_text()
        self.assertIn("'NocturneTestC_'", test_cookies)
        self.assertNotEqual(test_c['ports']['8448/tcp'],
                            json.loads((ROOT / 'nocturne_test_b/config.json').read_text())['ports']['8448/tcp'])

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
        self.assertIn('Personal ' + self.lock['version'], page)
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
