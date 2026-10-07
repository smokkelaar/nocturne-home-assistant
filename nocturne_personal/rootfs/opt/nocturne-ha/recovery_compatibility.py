"""Build-time source contract verification and offline runtime recovery checks.

Unknown contracts disable owner recovery, never the maintenance terminal.
No source or network access is required at runtime.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import urllib.error
import urllib.request

BASE = Path(__file__).resolve().parent
API = Path('/app/Nocturne.API.dll')
ALLOWED_REPOSITORIES = {'nightscout/nocturne', 'smokkelaar/nocturne-personal'}


def digest(data):
    return hashlib.sha256(data.replace(b'\r\n', b'\n')).hexdigest()


def binary_hash():
    if not API.is_file():
        raise ValueError('Nocturne API binary is missing')
    hashed = hashlib.sha256()
    for path in sorted(API.parent.glob('Nocturne*.dll')):
        hashed.update(path.name.encode('utf-8') + b'\0')
        hashed.update(hashlib.sha256(path.read_bytes()).digest())
    return hashed.hexdigest()


def identity(version):
    if not isinstance(version, dict):
        raise ValueError('Invalid pinned Nocturne source identity')
    repository, commit = version.get('repository'), version.get('source_commit', '')
    if repository not in ALLOWED_REPOSITORIES or not isinstance(commit, str) or not re.fullmatch('[0-9a-f]{40}', commit):
        raise ValueError('Invalid pinned Nocturne source identity')
    return repository, commit


def contracts():
    return json.loads((BASE / 'recovery-contracts.json').read_text(encoding='utf-8'))


def classify(hashes, rules):
    # Match the complete reviewed set, never mix independent per-file allowlists.
    return next((rule for rule in rules['profiles']
                 if rule['kind'] in ('hmac', 'pbkdf2') and rule['hashes'] == hashes), None)


def source_hashes(version, rules, source=None):
    repository, commit = identity(version)
    hashes = {}
    for path in rules['files']:
        if source:
            target = Path(source) / path
            data = target.read_bytes() if target.is_file() else b'NOCTURNE_HA_MISSING_SOURCE_FILE'
        else:
            request = urllib.request.Request(
                f'https://raw.githubusercontent.com/{repository}/{commit}/{path}',
                headers={'User-Agent': 'nocturne-ha-recovery-contract'})
            try:
                with urllib.request.urlopen(request, timeout=20) as response:
                    data = response.read(2_000_001)
            except urllib.error.HTTPError as error:
                if error.code != 404:
                    raise
                data = b'NOCTURNE_HA_MISSING_SOURCE_FILE'
        if len(data) > 2_000_000:
            raise ValueError('Recovery source file exceeds limit')
        hashes[path] = digest(data)
    return hashes


def build_manifest(version, rules, hashes, api_hash):
    identity(version)
    matched = classify(hashes, rules)
    return {'format': 1, 'repository': version['repository'],
            'source_commit': version['source_commit'], 'api_sha256': api_hash,
            'source_hashes': hashes, 'compatible': matched is not None,
            'profile': matched['kind'] if matched else None,
            'reason': 'verified-source-contract' if matched else 'unknown-source-contract'}


def verify_manifest(version, manifest, rules, api_hash):
    identity(version)
    if not isinstance(manifest, dict):
        raise ValueError('Herstelcontrole is ongeldig. Installeer een opnieuw gecontroleerde build; de terminal blijft beschikbaar.')
    if (manifest.get('format') != 1 or manifest.get('repository') != version['repository']
            or manifest.get('source_commit') != version['source_commit']
            or manifest.get('api_sha256') != api_hash or not re.fullmatch('[0-9a-f]{64}', api_hash)):
        raise ValueError('Herstelcontrole ontbreekt of hoort bij een andere build. Installeer een opnieuw gecontroleerde build; de terminal blijft beschikbaar.')
    matched = classify(manifest.get('source_hashes'), rules)
    if not matched or manifest.get('compatible') is not True or manifest.get('profile') != matched['kind']:
        raise ValueError('Het herstelmechanisme van deze build is gewijzigd of kon niet worden gecontroleerd. Gebruik een bestaande herstelcode of laat deze build controleren. Maak geen code via losse SQL-opdrachten.')
    return matched['kind']


def current_profile():
    version = json.loads((BASE / 'version.json').read_text(encoding='utf-8'))
    try:
        manifest = json.loads((BASE / 'recovery-compatibility.json').read_text(encoding='utf-8'))
        api_hash = binary_hash()
    except (OSError, ValueError) as error:
        raise ValueError('Deze build heeft geen geldige herstelcontrole. Bouw of installeer de app opnieuw; de onderhoudsterminal blijft beschikbaar.') from error
    return verify_manifest(version, manifest, contracts(), api_hash)


def report():
    try:
        current_profile()
        return {'compatible': True, 'message': 'Herstelmechanisme van deze build gecontroleerd. De database wordt vóór eigenaarherstel apart gecontroleerd.'}
    except (ValueError, OSError, KeyError):
        return {'compatible': False, 'message': 'Nieuwe eigenaarherstelcode niet beschikbaar: controle van deze build ontbreekt of het herstelmechanisme is gewijzigd. Terminal, diagnose en herstel met een bestaande code blijven beschikbaar.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, help='Exact checksum-verified source tree, when available')
    args = parser.parse_args()
    version = json.loads((BASE / 'version.json').read_text(encoding='utf-8'))
    api_hash = binary_hash()
    rules = contracts()
    try:
        hashes = source_hashes(version, rules, args.source)
        manifest = build_manifest(version, rules, hashes, api_hash)
    except (OSError, ValueError, urllib.error.URLError):
        manifest = build_manifest(version, rules, {}, api_hash)
        manifest['reason'] = 'source-check-unavailable'
    (BASE / 'recovery-compatibility.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print('OWNER_RECOVERY_CONTRACT: ' + ('compatible' if manifest['compatible'] else 'blocked; maintenance remains available'))


if __name__ == '__main__':
    main()
