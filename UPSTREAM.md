# Upstream provenance and licensing

Canonical project: https://github.com/nightscout/nocturne

The machine-readable authority for the selected upstream release is [`upstream.json`](upstream.json). It records the stable release tag, exact source commit and the published API/web OCI digests. `nocturne_local/Dockerfile` must agree with it. The initial release is Nocturne 0.2.4, source commit `66c35837d3719b592fa25e0aa09bb5f1c33c14a5`.

Source for the initial paired images: https://github.com/nightscout/nocturne/tree/66c35837d3719b592fa25e0aa09bb5f1c33c14a5

## What this wrapper changes

It does not rebuild or replace Nocturne's application source. It uses the published API and prebuilt SvelteKit web output, adds a local PostgreSQL server and TLS gateway, then reinstalls the frontend's locked production dependencies for glibc.

Two exact-match, build-time web patches are maintained in `nocturne_local/build/prepare_web.py`:

1. Disable pnpm's global virtual store so the non-root runtime user can access its dependencies.
2. Bind the web server explicitly to `127.0.0.1` inside the container.

Both source signatures must match before either is changed. An incompatible future upstream layout fails the build rather than silently weakening these checks. The complete wrapper source, patches, configuration generator and build recipe are in this repository.

## License evidence and limitations

The upstream README declares AGPL-3.0 and the pinned API image declares `AGPL-3.0-only`. At the initial source commit, its README's top-level `LICENSE` link did not resolve to a file. Do not interpret that absence as permission to ignore the declared license. Upstream source and package dependencies retain their own attribution and license requirements.

Our original wrapper code is explicitly AGPL-3.0-only; a complete license text is included in `LICENSE`. That file does not claim ownership of upstream code or replace upstream notices.

**This initial repository distributes wrapper source, not prebuilt combined container images.** Supervisor builds locally using upstream images. Before introducing public binary distribution, resolve the missing upstream license-file detail with upstream and audit corresponding-source availability, notices and dependency obligations. The updater does not perform a legal/license compliance audit; maintainers must recheck provenance/licensing on upgrades.

The updater verifies registry content hashes, linux/amd64 availability, a shared release tag and the API's embedded source revision. Nocturne 0.2.4's web image does not expose a source-revision label, so its exact source-to-binary correspondence is an upstream release assertion, not independently proved here.

## Other dependencies

Node is pinned by image digest in the Dockerfile. PostgreSQL 17/nginx/system libraries are installed from Ubuntu/PGDG package repositories; production JavaScript dependencies use the upstream pnpm lockfile. npm/pnpm and apt availability still affect builds. This is not a fully hermetic/reproducible binary build. Major PostgreSQL, Node, operating-system and dependency-policy changes require separate maintainer review; the Nocturne release watcher does not automatically upgrade them.
