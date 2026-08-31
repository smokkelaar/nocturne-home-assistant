"""Disposable cold restore and baseline-to-candidate upgrade rehearsal.

Creates all names itself; accepts images, NEVER existing volumes/containers.
This is not a Supervisor backup importer or a real-account/passkey test.
"""
import argparse
import uuid

from smoke import docker, execute, wait_ready


IDENTITY = "import hashlib\nfrom pathlib import Path\nprint(hashlib.sha256(Path('/data/secrets.json').read_bytes()).hexdigest())"
CHECK_ROW = "import sys\nsys.path.insert(0, '/opt/nocturne-ha')\nimport run\nassert run.psql(database='nocturne', sql='SELECT id FROM public.ha_wrapper_recovery') == '73'"

# cp -a preserves database ownership/modes. Full /data includes WAL, roles,
# instance keys and options. Both source and destination must be offline.
COPY = '''
import hashlib, pathlib, stat, subprocess
source, target = pathlib.Path('/source'), pathlib.Path('/target')
assert not any(target.iterdir()), 'Refuse nonempty destination'
assert (source/'postgres/PG_VERSION').read_text().strip() == '17'
assert (source/'postgres/global/pg_control').is_file()
assert (source/'secrets.json').is_file()
assert not (source/'postgres/postmaster.pid').exists(), 'Source is not cold'
def inventory(root):
    result = {}
    for path in root.rglob('*'):
        metadata = path.lstat()
        assert not path.is_symlink(), 'No external tablespaces/symlinks in CI fixtures'
        digest = hashlib.sha256(path.read_bytes()).digest() if path.is_file() else None
        result[str(path.relative_to(root))] = (stat.S_IMODE(metadata.st_mode), metadata.st_uid, metadata.st_gid, digest)
    return result
expected = inventory(source)
subprocess.run(['cp', '-a', '/source/.', '/target/'], check=True)
assert inventory(target) == expected, 'Cold copy content/ownership/mode mismatch'
'''


def stop_clean(name):
    docker('stop', '-t', '100', name)
    if docker('inspect', '--format', '{{.State.ExitCode}}', name) != '0':
        raise RuntimeError('Refuse snapshot: source did not stop cleanly')


def main(image, baseline):
    prefix = 'nocturne-recovery-ci-' + uuid.uuid4().hex
    volumes, containers = [], []

    def volume(suffix):
        name = prefix + '-' + suffix
        docker('volume', 'create', name)
        volumes.append(name)
        return name

    def start(suffix, data, build):
        name = prefix + '-' + suffix
        containers.append(name)
        docker('run', '-d', '--name', name, '-v', data + ':/data', build)
        wait_ready(name)
        return name

    def copy(source, target):
        docker('run', '--rm', '-i', '--entrypoint', 'python3',
               '-v', source + ':/source:ro', '-v', target + ':/target', image, '-', input=COPY)

    try:
        original, backup, restored, broken = [volume(s) for s in ('original', 'backup', 'restored', 'broken')]
        docker('run', '--rm', '-i', '--entrypoint', 'python3', '-v', original + ':/data', baseline, '-',
               input="from pathlib import Path\nPath('/data/options.json').write_text('{}')")
        source = start('baseline', original, baseline)
        versions = execute(source, "from pathlib import Path\nprint(Path('/opt/nocturne-ha/version.json').read_text())")
        print('Baseline metadata: ' + versions)
        identity = execute(source, IDENTITY)
        execute(source, "import sys\nsys.path.insert(0, '/opt/nocturne-ha')\nimport run\nrun.psql(database='nocturne', sql='CREATE TABLE public.ha_wrapper_recovery (id integer); INSERT INTO public.ha_wrapper_recovery VALUES (73)')")
        stop_clean(source)
        copy(original, backup)

        candidate = start('candidate', original, image)
        print('Candidate metadata: ' + execute(candidate, "from pathlib import Path\nprint(Path('/opt/nocturne-ha/version.json').read_text())"))
        if execute(candidate, IDENTITY) != identity:
            raise RuntimeError('Identity changed on upgrade')
        execute(candidate, CHECK_ROW)
        stop_clean(candidate)
        print('PASS: baseline -> candidate, protected setup, test row and matching keys')

        # Restore the PRE-upgrade data to another volume and the OLD image.
        # Never start the old image against the candidate-mutated database.
        copy(backup, restored)
        recovered = start('restored', restored, baseline)
        if execute(recovered, IDENTITY) != identity:
            raise RuntimeError('Identity changed on cold restore')
        execute(recovered, CHECK_ROW)
        stop_clean(recovered)
        print('PASS: cold backup -> new volume -> baseline image; test row and keys restored')

        # Only a disposable copy is damaged. The source and backup stay untouched.
        copy(backup, broken)
        docker('run', '--rm', '-i', '--entrypoint', 'python3', '-v', broken + ':/data', image, '-', input='''
import hashlib, pathlib, sys
sys.path.insert(0, '/opt/nocturne-ha')
from settings import load_secrets
root = pathlib.Path('/data')
control = root/'postgres/global/pg_control'
before = hashlib.sha256(control.read_bytes()).digest()
(root/'secrets.json').unlink()
try:
    load_secrets(root)
except ValueError:
    pass
else:
    raise AssertionError('Missing identity was silently recreated')
assert not (root/'secrets.json').exists()
assert hashlib.sha256(control.read_bytes()).digest() == before
''')
        print('PASS: incomplete restore refused without replacing identity or database')
    finally:
        for name in reversed(containers):
            docker('rm', '-f', name, check=False)
        for name in reversed(volumes):
            docker('volume', 'rm', name, check=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', required=True)
    parser.add_argument('--baseline', required=True)
    args = parser.parse_args()
    main(args.image, args.baseline)
