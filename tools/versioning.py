"""One functional wrapper version; independent delivery counters per channel."""
import json
import re


def publication_mode(root):
    return (root / 'publication.json').is_file()


def published_number(version):
    return isinstance(version, str) and re.fullmatch(r'[1-9]\d*\.(0|[1-9]\d*)\.(0|[1-9]\d*)', version) is not None


def advertised_version(root, config, proposed):
    # Source promotions must not advertise an image before both platforms pass.
    return config['version'] if publication_mode(root) else proposed


def wrapper_version(root):
    version = json.loads((root / 'wrapper.json').read_text(encoding='utf-8'))['version']
    if not isinstance(version, str) or not re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', version):
        raise ValueError('Wrapper version must be three-part numeric semver')
    return version


def package_build(root, version):
    if published_number(version):
        return int(version.split('.')[2])
    wrapper = wrapper_version(root)
    if not isinstance(version, str) or not re.fullmatch(re.escape(wrapper) + r'-[1-9]\d*', version):
        raise ValueError('Package must match shared wrapper version with a positive delivery counter')
    return int(version.rsplit('-', 1)[1])


def next_package(root, version):
    if published_number(version):
        major, minor, patch = map(int, version.split('.'))
        return f'{major}.{minor}.{patch + 1}'
    return f'{wrapper_version(root)}-{package_build(root, version) + 1}'
