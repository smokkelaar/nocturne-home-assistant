# Contributing

Use issues to agree on a focused change, fork this repository and submit a pull request against `main`. No credentials or access to a live Home Assistant instance are required to run the offline tests.

## Development checks

Python 3.12+, Node 24 and OpenSSL (installed in Ubuntu CI; required for actual certificate fixtures):

```sh
python -m unittest discover -s tests -v
node --test tests/test_web_check.mjs
python tools/update_upstream.py --check
python tools/update_latest.py --check
```

With a Linux amd64 Docker daemon (or Docker Desktop Linux containers):

```sh
docker build --platform linux/amd64 --tag nocturne-ha:dev nocturne_local
python tools/smoke.py --image nocturne-ha:dev
docker build --platform linux/amd64 --tag nocturne-ha-latest:dev nocturne_latest
python tools/smoke.py --image nocturne-ha-latest:dev
```

The smoke test creates and removes only its own UUID-named container and volume. It does not mount user files or publish host ports. Never repurpose it to point at an existing instance's data. A production database should never be used as a CI fixture.

See [cold restore / baseline upgrade CI](docs/HERSTELPROEF.md) and [TLS tests](docs/CERTIFICATEN.md) for their precise evidence limits. A CI pass does not prove a Supervisor restore or a real passkey/account migration.

For visual review without HA or real credentials, run `python tools/preview_status.py` and open the printed loopback URL. The page explicitly uses fictional examples and the server serves no files. Stop it with Ctrl+C. Do not replace its example data with a user's credentials.

## Rules for changes

- Keep this repository focused on Nocturne packaging and HA integration. Prefer upstream Nocturne PRs for product features.
- Keep Python runtime helpers dependency-light and testable offline. Write LF/UTF-8 files.
- Keep API and web images paired. Official changes use `upstream.json`; Latest changes use `upstream-latest.json`. Update only the corresponding package's manifest, Dockerfile, `version.json` and changelog, then run both consistency tests.
- Bump the changed channel's three-part `config.json` wrapper version for installable changes. It is independent of the upstream Nocturne version.
- Preserve both stable slugs: `nocturne_local` for Official and `nocturne_latest` for Latest. Preserve keys, database state, loopback listeners and least-privilege roles. No silent reset, cross-channel data copy or authentication bypass.
- Shared runtime/security files in both packages must remain byte-identical. Channel names, slugs, default host ports, upstream pins, wrapper versions and changelogs intentionally differ.
- Describe migration implications and unresolved verification clearly. Passing a clean-start test does not prove a real-data upgrade is safe.
- GitHub Actions dependencies are pinned by commit and reviewed through Dependabot. No privileged `pull_request_target` execution of contribution code.
- Do not publish locally generated data, certs, credentials, raw logs, personal hostnames/IPs or machine paths.

The initial runtime/status messages are Dutch; documentation is English with a Dutch quickstart. Translation improvements are welcome without changing behavior unnecessarily.

By contributing original code you agree to license it under this repository's AGPL-3.0-only license. Preserve third-party license/attribution notices.
