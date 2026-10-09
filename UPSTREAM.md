# Upstream provenance and licensing

## Main synchronization — 2026-10-09

All development sources now include upstream main `ef8850840c349fa9519a7f3022599ec9adddff82` (2026-10-09 06:48:03 UTC).
Official remains Nocturne **0.2.7** because no newer release exists.
The functional wrapper remains **0.1.13**. HA package versions are generated only
after both native architectures pass publication checks; source versions are separate.

| Channel | Source | Upstream base | Additional code |
|---|---|---|---|
| Daily / Latest | `ef88508` | `ef88508` | None |
| Personal 0.3.27 | `6ec88de` | `ef88508` | Personal extensions, including Google Health and HbA1c method comparison |
| Test A | `4e2ec5c` | `ef88508` | Google Health PR #1293, still unmerged |
| Test B | `ef88508` | `ef88508` | Hypo comparison PR #2031 is already merged into main |
| Test C | `ef88508` | `ef88508` | Clock-face settings PR #2007 is already merged into main |

Main images come from the immutable `main-ef88508` publication tags and verified
OCI digests. `latest` now denotes an official upstream release, so it is not the
discovery source for Daily. [Upstream publication](https://github.com/nightscout/nocturne/actions/runs/37895441854).

Published package versions and image digests are in each channel's `config.json`
and `provenance.json`; the runtime source and feature version are in
`rootfs/opt/nocturne-ha/version.json`. These files must agree before HA is updated.

Canonical project: https://github.com/nightscout/nocturne

There are two machine-readable authorities:

- [`upstream.json`](upstream.json) records Official's stable release tag, exact source commit and published API/web OCI digests. `nocturne_local/Dockerfile` must agree with it. The initial release is Nocturne 0.2.4, source commit `66c35837d3719b592fa25e0aa09bb5f1c33c14a5`.
- [`upstream-latest.json`](upstream-latest.json) records Latest's exact upstream `main` commit, successful paired-image workflow run, publication time and API/web OCI digests. `nocturne_latest/Dockerfile` must agree with it. The moving registry tag is discovery input only and never remains in an installable Dockerfile.

Source for the initial paired images: https://github.com/nightscout/nocturne/tree/66c35837d3719b592fa25e0aa09bb5f1c33c14a5

## What this wrapper changes

It does not rebuild or replace Nocturne's application source. It uses the published API and prebuilt SvelteKit web output, adds a local PostgreSQL server and TLS gateway, then reinstalls the frontend's locked production dependencies for glibc.

Two exact-match, build-time web patches are maintained identically in each channel's `build/prepare_web.py`:

1. Disable pnpm's global virtual store so the non-root runtime user can access its dependencies.
2. Bind the web server explicitly to `127.0.0.1` inside the container.

Both source signatures must match before either is changed. An incompatible future upstream layout fails the build rather than silently weakening these checks. The complete wrapper source, patches, configuration generator and build recipe are in this repository.

## License evidence and limitations

The upstream README declares AGPL-3.0 and the pinned API image declares `AGPL-3.0-only`. At the initial source commit, its README's top-level `LICENSE` link did not resolve to a file. Do not interpret that absence as permission to ignore the declared license. Upstream source and package dependencies retain their own attribution and license requirements.

Our original wrapper code is explicitly AGPL-3.0-only; a complete license text is included in `LICENSE`. That file does not claim ownership of upstream code or replace upstream notices.

**The new 1.x distribution builds combined containers on GitHub for AMD64 and ARM64.** Store promotion requires both native platforms to pass tests and anonymous registry verification. Images contain this wrapper's AGPL-3.0-only license text and exact corresponding-source links/archive references for the public Nocturne source snapshots. Nocturne's declared AGPL license and dependency notices remain applicable; the earlier missing top-level upstream license-file observation is preserved as provenance, not treated as a grant to remove notices. Registry/runtime checks are not a complete legal audit. See [publication and source availability](docs/PREBUILT.md).

The Official updater verifies registry content hashes, linux/amd64 availability, a shared release tag and the API's embedded source revision. The Latest updater additionally requires one successful upstream paired `build-and-push` job, the exact current `main` commit and a repeated API/main lookup after resolving web. Nocturne's web image does not expose a source-revision label, so web correspondence relies on the same upstream paired-image job and immutable manifest digest rather than an embedded revision label.

## Other dependencies

Node is pinned by image digest in the Dockerfile. PostgreSQL 17/nginx/system libraries are installed from Ubuntu/PGDG package repositories; production JavaScript dependencies use the upstream pnpm lockfile. npm/pnpm and apt availability still affect builds. This is not a fully hermetic/reproducible binary build. Major PostgreSQL, Node, operating-system and dependency-policy changes require separate maintainer review; the Nocturne release watcher does not automatically upgrade them.
