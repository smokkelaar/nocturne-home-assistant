# Contributing

Use issues to agree on a focused change, fork this repository and submit a pull request against `main`. No credentials or access to a live Home Assistant instance are required to run the offline tests.

## Development checks

Python 3.12+ and Node 24:

```sh
python -m unittest discover -s tests -v
node --test tests/test_web_check.mjs
python tools/update_upstream.py --check
```

With a Linux amd64 Docker daemon (or Docker Desktop Linux containers):

```sh
docker build --platform linux/amd64 --tag nocturne-ha:dev nocturne_local
python tools/smoke.py --image nocturne-ha:dev
```

The smoke test creates and removes only its own UUID-named container and volume. It does not mount user files or publish host ports. Never repurpose it to point at an existing instance's data. A production database should never be used as a CI fixture.

## Rules for changes

- Keep this repository focused on Nocturne packaging and HA integration. Prefer upstream Nocturne PRs for product features.
- Keep Python runtime helpers dependency-light and testable offline. Write LF/UTF-8 files.
- Keep API and web image releases paired; update `upstream.json` together with the manifest, Dockerfile, `version.json` and changelog. Run the consistency test.
- Bump the wrapper's three-part `config.json` version for installable changes. It is independent of the upstream Nocturne version.
- Preserve stable slug, keys, database state, loopback listeners and least-privilege roles. No silent reset or authentication bypass.
- Describe migration implications and unresolved verification clearly. Passing a clean-start test does not prove a real-data upgrade is safe.
- GitHub Actions dependencies are pinned by commit and reviewed through Dependabot. No privileged `pull_request_target` execution of contribution code.
- Do not publish locally generated data, certs, credentials, raw logs, personal hostnames/IPs or machine paths.

The initial runtime/status messages are Dutch; documentation is English with a Dutch quickstart. Translation improvements are welcome without changing behavior unnecessarily.

By contributing original code you agree to license it under this repository's AGPL-3.0-only license. Preserve third-party license/attribution notices.
