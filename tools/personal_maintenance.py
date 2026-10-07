"""Apply the shared opt-in management overlay to every HA channel.

The historical module/template directory names are retained for compatibility.
Applying twice is intentional: Personal inherits Latest's shared runtime.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def once(text, old, new):
    if new in text and old not in text:
        return text
    if text.count(old) != 1:
        raise ValueError('Shared maintenance runtime signature changed')
    return text.replace(old, new)


def apply(generated):
    generated = {key: value.decode('utf-8') if isinstance(value, bytes) else value
                 for key, value in generated.items()}
    config = json.loads(generated['config.json'])
    config['options'].update(maintenance_enabled=False, maintenance_password='')
    config['schema'].update(maintenance_enabled='bool', maintenance_password='password')
    generated['config.json'] = json.dumps(config, indent=2) + '\n'
    labels = {
        'nl': {
            'maintenance_enabled': {'name': 'Experimenteel onderhoud inschakelen', 'description': 'CLI, herstelwizard en rootterminal binnen deze app via HA. Standaard uit. Eigen wachtwoord vereist. Maak eerst een back-up; opslaan en herstarten.'},
            'maintenance_password': {'name': 'Eigen onderhoudswachtwoord', 'description': 'Uniek wachtwoord van 16–256 tekens. Gebruiker: maintenance. Wordt niet op de statuspagina getoond. Alleen nodig als onderhoud is ingeschakeld.'}},
        'en': {
            'maintenance_enabled': {'name': 'Enable experimental maintenance', 'description': 'CLI, recovery wizard and root terminal inside this app through HA. Off by default. Separate password required. Back up first; save and restart.'},
            'maintenance_password': {'name': 'Separate maintenance password', 'description': 'Unique password of 16–256 characters. Username: maintenance. Not displayed on the status page. Required only when maintenance is enabled.'}}}
    for locale, additions in labels.items():
        key = 'translations/' + locale + '.json'
        translation = json.loads(generated[key])
        translation['configuration'].update(additions)
        generated[key] = json.dumps(translation, indent=2, ensure_ascii=False) + '\n'
    for path in (ROOT / 'personal-maintenance/rootfs').rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts:
            generated['rootfs/' + path.relative_to(ROOT / 'personal-maintenance/rootfs').as_posix()] = path.read_bytes()
    recipe = generated['Dockerfile']
    if 'tini ttyd' not in recipe:
        recipe = once(recipe, 'python3 openssl tini', 'python3 openssl tini ttyd')
    if '/usr/local/bin/nocturne-ha' not in recipe:
        recipe = once(recipe, '&& chmod 755 /opt/nocturne-ha/run.py',
                      '&& chmod 755 /opt/nocturne-ha/run.py /usr/local/bin/nocturne-ha')
    recipe = once(recipe, '"/opt/nocturne-ha/run.py"]', '"/opt/nocturne-ha/personal_entry.py"]')
    generated['Dockerfile'] = recipe
    check = 'RUN python3 /opt/nocturne-ha/recovery_compatibility.py'
    if check not in recipe:
        # The binary and metadata are both in the final image at this point.
        recipe = once(recipe, 'RUN python3 -m compileall -q /opt/nocturne-ha',
                      check + '\nRUN python3 -m compileall -q /opt/nocturne-ha')
        generated['Dockerfile'] = recipe
    runtime = generated['rootfs/opt/nocturne-ha/run.py']
    runtime = once(runtime, "if self.client_address[0] != '172.30.32.2':",
                   "if self.client_address[0] != ('127.0.0.1' if os.environ.get('NOCTURNE_PERSONAL_STATUS_PORT') == '8100' else '172.30.32.2'):")
    runtime = once(runtime, "(('0.0.0.0', 8099), handler)",
                   "(('127.0.0.1' if os.environ.get('NOCTURNE_PERSONAL_STATUS_PORT') == '8100' else '0.0.0.0', int(os.environ.get('NOCTURNE_PERSONAL_STATUS_PORT', '8099'))), handler)")
    if 'href="maintenance/"' not in runtime:
        runtime = once(runtime, "supervisor.checks, supervisor.resources.snapshot()).encode()",
                       "supervisor.checks, supervisor.resources.snapshot()).encode()\n            if os.environ.get('NOCTURNE_PERSONAL_STATUS_PORT') == '8100':\n                body = body.replace(b'</html>', b'<p><a href=\"maintenance/\">Onderhoud: CLI, terminal en herstelwizard</a></p></html>')")
    runtime = runtime.replace('Personal onderhoud: CLI', 'Onderhoud: CLI')
    generated['rootfs/opt/nocturne-ha/run.py'] = runtime
    docs = re.sub(r'\n## Experimental (?:Personal )?maintenance\n\n[^\n]+\n', '', generated['DOCS.md'])
    generated['DOCS.md'] = docs + '\n## Experimental maintenance\n\nOpt-in CLI, ingress terminal and guided recovery for this app only. See [step-by-step maintenance guide](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/PERSONAL-MAINTENANCE.md). Disabled by default; requires its own maintenance password. Each image build checks the pinned recovery source contract and binds the result to the API binary. Unrelated source updates remain compatible; changed or unavailable recovery contracts block only new owner recovery. The actual database is checked before writes. No Nocturne source or schema changes; explicit owner recovery adds a native recovery-code hash.\n'
    return generated
