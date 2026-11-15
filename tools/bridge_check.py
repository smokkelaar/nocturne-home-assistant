"""Verify the temporary published v0.3.0 bridge without changing source locks."""
import re

import prebuilt_publish
from update_upstream import MIGRATION_BRIDGE


def require(root, channel):
    if channel not in prebuilt_publish.bridge_channels(root):
        return False
    package = prebuilt_publish.CHANNELS[channel]
    directory = root / package
    proof = prebuilt_publish.read(directory / 'provenance.json')
    config = prebuilt_publish.read(directory / 'config.json')
    runtime = prebuilt_publish.read(directory / 'rootfs/opt/nocturne-ha/version.json')
    expected = {**proof['runtime_metadata'], 'package': proof['version']}
    if (proof.get('migration_bridge') != '0.3.0' or
            proof['source_repository'] != 'nightscout/nocturne' or
            proof['source_commit'] != MIGRATION_BRIDGE['commit'] or
            proof['config'] != config or runtime != expected or
            config['slug'] != package or config['version'] != proof['version'] or
            runtime['source_commit'] != MIGRATION_BRIDGE['commit'] or
            proof['architectures'] != list(prebuilt_publish.PLATFORMS)):
        raise ValueError('Published migration bridge metadata is inconsistent: ' + channel)
    for arch in prebuilt_publish.PLATFORMS:
        pins = proof['runtime_pins'][arch]
        if set(pins) != {'api', 'web'} or any(not re.fullmatch(r'sha256:[0-9a-f]{64}', value)
                                                 for value in pins.values()):
            raise ValueError('Published migration bridge runtime pins are incomplete: ' + channel)
    return True
