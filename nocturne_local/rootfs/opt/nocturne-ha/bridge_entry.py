#!/usr/bin/env python3
"""Check embedded PostgreSQL ownership before starting the HA runtime.

The old and new API base images may assign different numeric UIDs to the
``postgres`` account. A Docker volume retains numeric ownership across image
upgrades. Only the embedded database tree is touched; contents, modes,
secrets, and tenant records remain unchanged.
"""
import os
from pathlib import Path
import pwd


DATA = Path('/data/postgres')
ENTRY = '/opt/nocturne-ha/personal_entry.py'


def repair_ownership(root=DATA):
    if not root.exists() and not root.is_symlink():
        return 0
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Database path is not a real directory')
    version = root / 'PG_VERSION'
    if not version.is_file() or version.is_symlink() or version.read_text().strip() != '17':
        raise ValueError('Existing database requires PostgreSQL 17')
    account = pwd.getpwnam('postgres')
    stack = [root]
    paths = []
    while stack:
        directory = stack.pop()
        paths.append(directory)
        for entry in os.scandir(directory):
            if entry.is_symlink():
                raise ValueError('Database tree contains a symlink; ownership unchanged')
            if entry.is_dir(follow_symlinks=False):
                stack.append(Path(entry.path))
            elif not entry.is_file(follow_symlinks=False):
                raise ValueError('Database tree contains an unsupported file type')
            paths.append(Path(entry.path))
    changed = 0
    for path in paths:
        metadata = path.stat(follow_symlinks=False)
        if (metadata.st_uid, metadata.st_gid) != (account.pw_uid, account.pw_gid):
            os.chown(path, account.pw_uid, account.pw_gid, follow_symlinks=False)
            changed += 1
    return changed


if __name__ == '__main__':
    count = repair_ownership()
    print(f'[nocturne-app] PostgreSQL 17 volume ownership checked; adjusted {count} paths', flush=True)
    os.execv('/usr/bin/python3', ['python3', ENTRY])
