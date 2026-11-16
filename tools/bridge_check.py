"""Verify the published bridge or follow-up release while source templates stay separate."""
import re

import prebuilt_publish
from update_upstream import MIGRATION_BRIDGE


def require(root, channel):
    bridge_policy = channel in prebuilt_publish.bridge_channels(root)
    release_policy = channel in prebuilt_publish.release_channels(root)
    if not bridge_policy and not release_policy:
        return False
    package = prebuilt_publish.CHANNELS[channel]
    directory = root / package
    proof = prebuilt_publish.read(directory / 'provenance.json')
    config = prebuilt_publish.read(directory / 'config.json')
    runtime = prebuilt_publish.read(directory / 'rootfs/opt/nocturne-ha/version.json')
    expected = {**proof['runtime_metadata'], 'package': proof['version']}
    old_bridge = proof.get('migration_bridge') == '0.3.0'
    new_release = proof.get('release_rollout') == '0.3.2'
    if (not (old_bridge or new_release) or (bridge_policy and not old_bridge) or
            (new_release and not release_policy)):
        raise ValueError('Published bridge/release mode is inconsistent: ' + channel)
    source_commit = MIGRATION_BRIDGE['commit'] if old_bridge else prebuilt_publish.RELEASE_032_COMMIT
    if (
            proof['source_repository'] != 'nightscout/nocturne' or
            proof['source_commit'] != source_commit or
            proof['config'] != config or runtime != expected or
            config['slug'] != package or config['version'] != proof['version'] or
            runtime['source_commit'] != source_commit or
            proof['architectures'] != list(prebuilt_publish.PLATFORMS)):
        raise ValueError('Published bridge/release metadata is inconsistent: ' + channel)
    for arch in prebuilt_publish.PLATFORMS:
        pins = proof['runtime_pins'][arch]
        if set(pins) != {'api', 'web'} or any(not re.fullmatch(r'sha256:[0-9a-f]{64}', value)
                                                 for value in pins.values()):
            raise ValueError('Published bridge/release runtime pins are incomplete: ' + channel)
    return True
