"""Check real session isolation using one built candidate and published peers."""
import argparse
from pathlib import Path

import cookie_smoke
from prebuilt_publish import CHANNELS, baseline, read
from smoke import docker


def references(root, channel, image, candidates=None):
    if channel not in ('official', 'latest', 'personal'):
        return {}
    repository = read(root / 'publication.json')['repository']
    result = {}
    for peer in ('official', 'latest', 'personal'):
        if peer == channel:
            result[peer] = image
        else:
            config = candidates[peer]['config'] if candidates and peer in candidates else read(root / CHANNELS[peer] / 'config.json')
            result[peer] = baseline(config, peer, 'amd64', repository)
            if not result[peer]:
                raise ValueError('Session isolation needs a published peer: ' + peer)
    return result


def main(root, channel, image, candidates=None):
    images = references(root, channel, image, candidates)
    for reference in set(images.values()):
        if reference != image:
            docker('pull', reference)
    if images:
        cookie_smoke.main(**images)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--channel', choices=list(CHANNELS), required=True)
    parser.add_argument('--image', required=True)
    parser.add_argument('--candidates', type=Path)
    args = parser.parse_args()
    main(Path(__file__).resolve().parents[1], args.channel, args.image, read(args.candidates) if args.candidates else None)
