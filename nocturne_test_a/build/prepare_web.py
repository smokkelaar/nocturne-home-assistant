"""Two guarded build-time patches to the pinned upstream web image."""
from pathlib import Path
import sys


def prepare_web(root):
    root = Path(root)
    patches = [
        (root / 'pnpm-workspace.yaml',
         'enableGlobalVirtualStore: true', 'enableGlobalVirtualStore: false'),
        (root / 'packages/app/server.js',
         'server.listen(PORT, () => {', "server.listen(PORT, '127.0.0.1', () => {"),
    ]
    prepared = []
    # Validate both before changing either; fail if the pinned upstream changes.
    for path, old, new in patches:
        original = path.read_text(encoding='utf-8')
        if original.count(old) != 1:
            raise ValueError(f'Unexpected upstream signature in {path.name}')
        prepared.append((path, original.replace(old, new)))
    for path, content in prepared:
        path.write_text(content, encoding='utf-8', newline='\n')


if __name__ == '__main__':
    prepare_web(sys.argv[1])
