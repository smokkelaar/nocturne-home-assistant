"""Build candidates separately from the HA store; advertise only verified public images.

Publication follows the upstream HA publisher's build/test/push/promote design.
Existing repository URL, slugs, ports, options and private /data identities stay intact.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import urllib.request
from awesomeversion import AwesomeVersion
import registry

ROOT = Path(__file__).resolve().parents[1]
CHANNELS = {'official': 'nocturne_local', 'latest': 'nocturne_latest',
            'personal': 'nocturne_personal', 'test-a': 'nocturne_test_a',
            'test-b': 'nocturne_test_b', 'test-c': 'nocturne_test_c'}
PLATFORMS = {'amd64': {'hass': 'amd64', 'runner': 'ubuntu-24.04', 'rid': 'linux-x64'},
             'arm64': {'hass': 'aarch64', 'runner': 'ubuntu-24.04-arm', 'rid': 'linux-arm64'}}


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, indent=2) + '\n').encode('utf-8'))


def require_upgrade(candidate, previous=None):
    if not re.fullmatch(r'[1-9]\d*\.(0|[1-9]\d*)\.(0|[1-9]\d*)', candidate):
        raise ValueError('Prebuilt packages require plain MAJOR.MINOR.PATCH at or above 1.0.0')
    if previous and not AwesomeVersion(candidate) > AwesomeVersion(previous):
        raise ValueError('Candidate is not an HA upgrade from ' + previous)


def next_version(previous, run_number, attempt):
    if run_number < 1 or not 1 <= attempt < 100:
        raise ValueError('Invalid publication run/attempt')
    bases = [(1, 0, 0)]
    for value in previous:
        match = re.fullmatch(r'(\d+)\.(\d+)\.(\d+)(?:-(?:[abcp])?[1-9]\d*)?', value)
        if not match:
            raise ValueError('Unrecognized published version')
        bases.append(tuple(map(int, match.groups())))
    major, minor, patch = max(bases)
    version = f'{major}.{minor}.{max(patch + 1, run_number * 100 + attempt)}'
    for value in previous:
        require_upgrade(version, value)
    return version


def image_name(repository, channel, hass_arch='{arch}'):
    if not re.fullmatch(r'[a-z0-9_.-]+/[a-z0-9_.-]+', repository) or channel not in CHANNELS:
        raise ValueError('Invalid publication identity')
    return f'ghcr.io/{repository}/nocturne-{channel}-{hass_arch}'


def recipe_hash(root, package):
    hashed = hashlib.sha256()
    paths = list((root / package / 'rootfs').rglob('*')) + list((root / package / 'build').rglob('*'))
    paths += [root / package / 'Dockerfile', root / package / 'config.json', root / 'build-platforms.json',
              root / 'publication.json', root / 'tools/prebuilt_publish.py']
    for path in sorted(paths):
        if not path.is_file() or '__pycache__' in path.parts:
            continue
        raw = path.read_bytes().replace(b'\r\n', b'\n')
        if path.name == 'Dockerfile':
            raw = re.sub(rb'ARG BUILD_VERSION=\S+', b'ARG BUILD_VERSION=@PUBLISHED@', raw)
        elif path.name == 'config.json':
            value = json.loads(raw)
            for field in ('version', 'image', 'arch', 'description'):
                value.pop(field, None)
            raw = json.dumps(value, sort_keys=True).encode()
        elif path.name == 'version.json':
            value = json.loads(raw)
            for field in ('package', 'distribution', 'architectures', 'wrapper_commit'):
                value.pop(field, None)
            raw = json.dumps(value, sort_keys=True).encode()
        hashed.update(path.relative_to(root).as_posix().encode() + b'\0' + raw)
    return hashed.hexdigest()


def runtime_pin(lock, kind, arch, tools):
    reference = lock[kind].get('platforms', {}).get(arch)
    if not reference:
        # Official retains its immutable multi-platform index. Legacy Latest
        # was pinned to an amd64 child; its sibling was recovered from the same
        # successful paired upstream run, not from today's floating latest tag.
        reference = lock[kind]['digest']
        legacy = tools['legacy_latest']
        if arch == 'arm64' and lock.get('commit') == legacy['commit']:
            if lock[kind]['digest'] != legacy[kind]['amd64']:
                raise ValueError('Legacy Latest architecture proof does not match approved pin')
            reference = legacy[kind][arch]
    verified = registry.image('nightscout/nocturne/nocturne-' + kind, reference, arch,
                              lock['commit'] if kind == 'api' else None)
    return verified['digest']


def baseline(config, channel, arch, repo):
    hass_arch = PLATFORMS[arch]['hass']
    if 'image' not in config or hass_arch not in config['arch']:
        return ''
    if config['image'] != image_name(repo, channel):
        raise ValueError('Published image belongs to a different app identity')
    return image_name(repo, channel, hass_arch) + ':' + config['version']


def prepare(root, destination, wrapper_commit, run_number, attempt, baseline_ref, force=False):
    policy, tools = read(root / 'publication.json'), read(root / 'build-platforms.json')
    repo = policy['repository']
    if policy['architectures'] != list(PLATFORMS) or not re.fullmatch('[0-9a-f]{40}', wrapper_commit):
        raise ValueError('All publications require native amd64 and arm64 and exact source SHA')
    configs = {channel: read(root / package / 'config.json') for channel, package in CHANNELS.items()}
    version = next_version([config['version'] for config in configs.values()], run_number, attempt)
    locks = {'official': read(root / 'upstream.json'), 'latest': read(root / 'upstream-latest.json')}
    matrix = []
    proofs = {}
    for channel, package in CHANNELS.items():
        config = configs[channel]
        recipe = recipe_hash(root, package)
        previous_proof = root / package / 'provenance.json'
        if not force and previous_proof.is_file() and read(previous_proof).get('recipe') == recipe:
            continue
        require_upgrade(version, config['version'])
        metadata = read(root / package / 'rootfs/opt/nocturne-ha/version.json')
        lock = locks['official' if channel == 'official' else 'latest']
        # Source-built variants use Personal's separately approved runtime base.
        if channel not in ('official', 'latest'):
            lock = read(root / 'upstream-personal.json')['upstream']
        pins = {arch: {kind: runtime_pin(lock, kind, arch, tools)
                      for kind in (('api', 'web') if channel in ('official', 'latest') else ('api',))}
                for arch in PLATFORMS}
        config.update(version=version, image=image_name(repo, channel), arch=['amd64', 'aarch64'],
                      description=f"Vooraf gebouwd 1.x · AMD64/ARM64 · {metadata.get('release', metadata['nocturne'])} · HA wrapper {metadata['app']}")
        proof = {'format': 1, 'channel': channel, 'package': package, 'version': version,
                 'repository': repo, 'wrapper_commit': wrapper_commit, 'recipe': recipe,
                 'source_repository': metadata['repository'], 'source_commit': metadata['source_commit'],
                 'architectures': list(PLATFORMS), 'runtime_pins': pins,
                 'config': config, 'previous_config': configs[channel].copy()}
        # configs[channel] was mutated above; read the actual published store again.
        proof['previous_config'] = read(root / package / 'config.json')
        proofs[channel] = proof
        for arch, platform in PLATFORMS.items():
            context = destination / f'{channel}-{arch}'
            shutil.copytree(root / package, context, ignore=shutil.ignore_patterns('__pycache__', 'provenance.json'), dirs_exist_ok=True)
            recipe_text = (context / 'Dockerfile').read_text(encoding='utf-8')
            for kind, digest in pins[arch].items():
                recipe_text = re.sub(rf'FROM ghcr.io/nightscout/nocturne/nocturne-{kind}@sha256:[0-9a-f]{{64}}',
                                     f'FROM ghcr.io/nightscout/nocturne/nocturne-{kind}@{digest}', recipe_text)
            for name in ('sdk', 'rust'):
                pattern = r'FROM ' + ('mcr.microsoft.com/dotnet/sdk' if name == 'sdk' else 'rust') + r'@sha256:[0-9a-f]{64}'
                recipe_text = re.sub(pattern, 'FROM ' + tools[name][arch], recipe_text)
            recipe_text = re.sub(r'ARG DOTNET_RID=\S+', 'ARG DOTNET_RID=' + platform['rid'], recipe_text)
            recipe_text = re.sub(r'ARG BUILD_VERSION=\S+', 'ARG BUILD_VERSION=' + version, recipe_text)
            recipe_text = re.sub(r'ARG BUILD_ARCH=\S+', 'ARG BUILD_ARCH=' + platform['hass'], recipe_text)
            recipe_text = recipe_text.replace('COPY rootfs/ /',
                'COPY rootfs/ /\nLABEL org.opencontainers.image.revision="' + wrapper_commit + '"')
            (context / 'Dockerfile').write_bytes(recipe_text.encode())
            write(context / 'config.json', config)
            runtime = {**metadata, 'package': version, 'distribution': 'prebuilt-ghcr',
                       'architectures': ['amd64', 'aarch64'], 'wrapper_commit': wrapper_commit}
            write(context / 'rootfs/opt/nocturne-ha/version.json', runtime)
            legal = context / 'rootfs/usr/share/doc/nocturne-ha'
            legal.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / 'LICENSE', legal / 'LICENSE')
            write(legal / 'corresponding-source.json', {
                'license': 'AGPL-3.0-only', 'wrapper': f'https://github.com/{repo}/tree/{wrapper_commit}',
                'nocturne': f"https://github.com/{metadata['repository']}/tree/{metadata['source_commit']}",
                'archive': f"https://codeload.github.com/{metadata['repository']}/tar.gz/{metadata['source_commit']}",
                'upstream_notices': 'Nocturne and dependency copyrights/licenses remain applicable.'})
            matrix.append({'channel': channel, 'package': package, 'arch': arch,
                           'hass_arch': platform['hass'], 'runner': platform['runner'],
                           'context': str(context.as_posix()), 'version': version,
                           'image': image_name(repo, channel, platform['hass']) + ':' + version,
                           'baseline': baseline(read(root / package / 'config.json'), channel, arch, repo),
                           'legacy_baseline_ref': baseline_ref if arch == 'amd64' and 'image' not in proof['previous_config'] else ''})
    write(destination / 'matrix.json', {'include': matrix})
    write(destination / 'candidates.json', proofs)
    return {'include': matrix}


def promote(root, candidates):
    proofs = read(candidates)
    prepared = {}
    # Verify all channels/platforms before touching any advertised store file.
    for channel, proof in proofs.items():
        if proof['repository'] != read(root / 'publication.json')['repository'] or proof['channel'] != channel:
            raise ValueError('Untrusted publication identity')
        package = CHANNELS[channel]
        current = read(root / package / 'config.json')
        require_upgrade(proof['version'], current['version'])
        if current != proof['previous_config'] or recipe_hash(root, package) != proof['recipe']:
            raise ValueError('Source/store changed while images were being built; rerun publication')
        if proof['architectures'] != list(PLATFORMS) or proof['config']['image'] != image_name(proof['repository'], channel):
            raise ValueError('Incomplete or wrong image publication')
        digests = {}
        for arch, platform in PLATFORMS.items():
            inspected = registry.image(image_name(proof['repository'], channel, platform['hass']).removeprefix('ghcr.io/'),
                proof['version'], arch, proof['wrapper_commit'],
                {'io.hass.version': proof['version'], 'io.hass.arch': platform['hass'], 'io.hass.type': 'app'})
            digests[platform['hass']] = inspected['digest']
        prepared[channel] = {**proof, 'digests': digests}
    for channel, proof in prepared.items():
        directory = root / CHANNELS[channel]
        write(directory / 'config.json', proof['config'])
        write(directory / 'provenance.json', proof)
        runtime = read(directory / 'rootfs/opt/nocturne-ha/version.json')
        runtime['package'] = proof['version']
        write(directory / 'rootfs/opt/nocturne-ha/version.json', runtime)
        recipe = (directory / 'Dockerfile').read_text(encoding='utf-8')
        (directory / 'Dockerfile').write_bytes(re.sub(r'ARG BUILD_VERSION=\S+', 'ARG BUILD_VERSION=' + proof['version'], recipe).encode())
        changelog = directory / 'CHANGELOG.md'
        note = f"## {proof['version']}\n\n- New 1.x distribution: prebuilt GitHub/GHCR images for AMD64 and ARM64. HAOS downloads the tested image; no local compilation.\n- Existing app identity, options, private data and Nocturne source remain intact.\n\n"
        changelog.write_bytes((note + changelog.read_text(encoding='utf-8')).encode())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('prepare')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--wrapper-commit', required=True)
    p.add_argument('--run-number', type=int, required=True)
    p.add_argument('--attempt', type=int, required=True)
    p.add_argument('--baseline-ref', required=True)
    p.add_argument('--force', action='store_true')
    p = sub.add_parser('promote')
    p.add_argument('--candidates', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        result = prepare(ROOT, args.output, args.wrapper_commit, args.run_number, args.attempt, args.baseline_ref, args.force)
        print(json.dumps(result, separators=(',', ':')))
    else:
        promote(ROOT, args.candidates)
