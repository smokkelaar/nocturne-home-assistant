# Nocturne for Home Assistant

[![Validate](https://github.com/smokkelaar/nocturne-home-assistant/actions/workflows/validate.yml/badge.svg)](https://github.com/smokkelaar/nocturne-home-assistant/actions/workflows/validate.yml)
[![Upstream updates](https://github.com/smokkelaar/nocturne-home-assistant/actions/workflows/upstream.yml/badge.svg)](https://github.com/smokkelaar/nocturne-home-assistant/actions/workflows/upstream.yml)

An **experimental, unofficial Home Assistant app** that runs [Nocturne](https://github.com/nightscout/nocturne), PostgreSQL and an HTTPS gateway in one container. No separate database server or Docker administration is needed for a fresh installation.

This repository is **Nocturne only**. It contains the HA wrapper, its small upstream compatibility patches, tests and contributor documentation; it is not a fork of the entire Nocturne application. Upstream Nocturne remains the source of the API and web interface.

**Not a medical device or a clinically validated deployment.** Start with an empty test instance. Do not depend on it for treatment decisions, alarms or automated dosing. Importing health data, connecting devices and internet exposure are outside this initial test scope.

## Install

[![Add repository to Home Assistant](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fsmokkelaar%2Fnocturne-home-assistant)

1. Add this repository to the **Home Assistant app store** (formerly add-on store).
2. Install **Nocturne (experimental)**. The initial installation builds a container locally and can take several minutes.
3. Configure a stable HTTPS hostname and trusted certificate, then start the app.
4. Open its HA web interface for service status, the Nocturne link and the extra gateway access code. Complete Nocturne's own passkey setup in the separate tab.

Read the [installation guide](nocturne_local/DOCS.md) first. Requirements: **Home Assistant OS / Supervisor, amd64**, enough free storage/memory for a local build and PostgreSQL, and working local DNS/trusted HTTPS for passkeys. ARM64 and Home Assistant Container/Core without Supervisor are not supported by this wrapper yet.

**Already using the local `0.1.0-test2` prototype? Do not uninstall it.** A repository installation has a different HA identity and data directory. [Migration is a separate, not-yet-automated operation](docs/MIGRATION.md).

This is an app-store repository, **not a HACS integration**. HA ingress currently provides a protected status/launcher page, not an embedded Nocturne dashboard.

## How updates reach you

**Stable Nocturne release → daily discovery → paired image/source pins → tests and container smoke test → maintainer-reviewed pull request → HA app update.**

After an update is merged, HA's store refresh can offer the new app version. Users may enable HA's app auto-update option; keep it off during experimental use until backup/restore and upgrade behavior have been verified. This repository does not remotely update anyone's HA installation.

There is intentionally **no floating `latest` image and no unattended merge of database-changing releases**. This is automatic discovery/preparation, not a guarantee of immediate or completely unattended upstream upgrades. See [update policy and maintainer setup](docs/UPDATES.md).

## Collaborate

- [Contributing and local test commands](CONTRIBUTING.md)
- [Architecture and security boundaries](docs/ARCHITECTURE.md)
- [Known limitations and test evidence](docs/TESTING.md)
- [Handoff for the next developer or AI](docs/AI_HANDOFF.md)
- [Security reporting](SECURITY.md)
- [Upstream provenance and licensing](UPSTREAM.md)
- [Nederlandse snelstart](docs/NL.md)

Issues and pull requests are welcome. Share sanitized error excerpts only: no passwords, tokens, recovery codes, certificates/private keys, databases or health records.

## License and attribution

The original wrapper code is licensed under **AGPL-3.0-only**; see [LICENSE](LICENSE). Nocturne and third-party dependencies retain their own copyrights and licenses. This project is not affiliated with or endorsed by Nocturne, Nightscout or Home Assistant. See [UPSTREAM.md](UPSTREAM.md) before redistributing container binaries.
