"""One functional wrapper version; independent delivery counters per channel."""
import json
import re


def wrapper_version(root):
    version = json.loads((root / 'wrapper.json').read_text(encoding='utf-8'))['version']
    if not isinstance(version, str) or not re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', version):
        raise ValueError('Wrapper version must be three-part numeric semver')
    return version


def package_build(root, version):
    wrapper = wrapper_version(root)
    if not isinstance(version, str) or not re.fullmatch(re.escape(wrapper) + r'-[1-9]\d*', version):
        raise ValueError('Package must match shared wrapper version with a positive delivery counter')
    return int(version.rsplit('-', 1)[1])


def next_package(root, version):
    return f'{wrapper_version(root)}-{package_build(root, version) + 1}'
