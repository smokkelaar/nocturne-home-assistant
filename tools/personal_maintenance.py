"""Apply Personal-only management overlay after generating the stock wrapper."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Personal maintenance runtime signature changed')
    return text.replace(old, new)


def apply(generated):
    config = json.loads(generated['config.json'])
    config['options'].update(maintenance_enabled=False, maintenance_password='')
    config['schema'].update(maintenance_enabled='bool', maintenance_password='password')
    generated['config.json'] = json.dumps(config, indent=2) + '\n'
    labels = {
        'nl': {
            'maintenance_enabled': {'name': 'Experimenteel onderhoud inschakelen', 'description': 'Alleen Personal: CLI, herstelwizard en rootterminal binnen deze app via HA. Standaard uit. Eigen wachtwoord vereist. Maak eerst een back-up; opslaan en herstarten.'},
            'maintenance_password': {'name': 'Eigen onderhoudswachtwoord', 'description': 'Uniek wachtwoord van 16–256 tekens. Gebruiker: maintenance. Wordt niet op de statuspagina getoond. Alleen nodig als onderhoud is ingeschakeld.'}},
        'en': {
            'maintenance_enabled': {'name': 'Enable experimental maintenance', 'description': 'Personal only: CLI, recovery wizard and root terminal inside this app through HA. Off by default. Separate password required. Back up first; save and restart.'},
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
    recipe = once(recipe, 'python3 openssl tini', 'python3 openssl tini ttyd')
    recipe = once(recipe, '&& chmod 755 /opt/nocturne-ha/run.py',
                  '&& chmod 755 /opt/nocturne-ha/run.py /usr/local/bin/nocturne-ha')
    recipe = once(recipe, '"/opt/nocturne-ha/run.py"]', '"/opt/nocturne-ha/personal_entry.py"]')
    generated['Dockerfile'] = recipe
    runtime = generated['rootfs/opt/nocturne-ha/run.py'].decode()
    runtime = once(runtime, "if self.client_address[0] != '172.30.32.2':",
                   "if self.client_address[0] != ('127.0.0.1' if os.environ.get('NOCTURNE_PERSONAL_STATUS_PORT') == '8100' else '172.30.32.2'):")
    runtime = once(runtime, "(('0.0.0.0', 8099), handler)",
                   "(('127.0.0.1' if os.environ.get('NOCTURNE_PERSONAL_STATUS_PORT') == '8100' else '0.0.0.0', int(os.environ.get('NOCTURNE_PERSONAL_STATUS_PORT', '8099'))), handler)")
    runtime = once(runtime, "supervisor.checks, supervisor.resources.snapshot()).encode()",
                   "supervisor.checks, supervisor.resources.snapshot()).encode()\n            if os.environ.get('NOCTURNE_PERSONAL_STATUS_PORT') == '8100':\n                body = body.replace(b'</html>', b'<p><a href=\"maintenance/\">Personal onderhoud: CLI, terminal en herstelwizard</a></p></html>')")
    generated['rootfs/opt/nocturne-ha/run.py'] = runtime
    generated['DOCS.md'] += '\n## Experimental Personal maintenance\n\nOpt-in CLI, ingress terminal and guided recovery, including local HA-admin recovery when all Nocturne login details are lost. See [Personal maintenance test guide](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/PERSONAL-MAINTENANCE.md). Disabled by default; requires its own maintenance password. No Nocturne source or schema changes; explicit owner recovery adds a native recovery-code hash.\n'
    return generated
