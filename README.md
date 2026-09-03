# Nocturne for Home Assistant

[![Validate](https://github.com/smokkelaar/nocturne-home-assistant/actions/workflows/validate.yml/badge.svg)](https://github.com/smokkelaar/nocturne-home-assistant/actions/workflows/validate.yml)
[![Official release check](https://github.com/smokkelaar/nocturne-home-assistant/actions/workflows/upstream.yml/badge.svg)](https://github.com/smokkelaar/nocturne-home-assistant/actions/workflows/upstream.yml)
[![Latest daily](https://github.com/smokkelaar/nocturne-home-assistant/actions/workflows/latest.yml/badge.svg)](https://github.com/smokkelaar/nocturne-home-assistant/actions/workflows/latest.yml)

Three **experimental, unofficial Home Assistant apps** that each run [Nocturne](https://github.com/nightscout/nocturne), PostgreSQL and an HTTPS gateway in one container. Official and Latest remain unchanged; the separate [Personal app](docs/PERSONAL.md) builds your extension fork on the approved Daily base.

This repository is **Nocturne only**. It contains the HA wrapper, its small upstream compatibility patches, tests and contributor documentation; it is not a fork of the entire Nocturne application. Upstream Nocturne remains the source of the API and web interface. [Compare the two channels](docs/CHANNELS.md).

**Not a medical device or a clinically validated deployment.** Start with an empty test instance. Do not depend on it for treatment decisions, alarms or automated dosing. Automated tests use synthetic data; real health-source accuracy, device connections and internet exposure require separate evaluation.

## Install

**Start here: [Visuele Nederlandse installatiehandleiding — van repository tot werkend dashboard](docs/INSTALLATIE.md).** Eight numbered steps, diagrams, DNS/certificate setup, passkey registration and a restart checklist. [English installation reference](nocturne_local/DOCS.md).

[![Add repository to Home Assistant](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fsmokkelaar%2Fnocturne-home-assistant)

1. Add this repository to the **Home Assistant app store** (formerly add-on store).
2. Choose **Nocturne Official Release** or **Nocturne Latest Release**. Both can be installed; they have separate data. The initial installation builds a container locally and can take several minutes.
3. Configure a stable HTTPS hostname and trusted certificate. Official defaults to host port 8448; Latest to 8449.
4. Open its HA web interface for service status, the Nocturne link and the extra gateway access code. Complete Nocturne's own passkey setup in the separate tab. From wrapper 0.1.4 an existing configured instance can [safely opt out of only that extra popup](docs/GATEWAY.md); Nocturne's passkey login stays enabled.

**Personal extensions:** choose **Nocturne Personal Release** as a separate third
installation, default port **8450**. It starts with its own empty database/account
and compiles [the Personal fork](https://github.com/smokkelaar/nocturne-personal).
Personal 0.2.0 adds Google Health login/import for steps, heart rate and weight,
plus a separate medication log (including Mounjaro-style medications, without dosing advice).
Your own Google OAuth client and consent are required; real Google account access remains a user test.
[Personal installation, feature setup and daily updates](docs/PERSONAL.md).

Read the [Official installation reference](nocturne_local/DOCS.md) or [Latest reference](nocturne_latest/DOCS.md) first. Requirements: **Home Assistant OS / Supervisor, amd64**, enough free storage/memory for a local build and PostgreSQL, and working local DNS/trusted HTTPS for passkeys. ARM64 and Home Assistant Container/Core without Supervisor are not supported by this wrapper yet.

**Already using the local `0.1.0-test2` prototype? Do not uninstall it.** A repository installation has a different HA identity and data directory. [Migration is a separate, not-yet-automated operation](docs/MIGRATION.md).

This is an app-store repository, **not a HACS integration**. HA ingress currently provides a protected status/launcher page, not an embedded Nocturne dashboard.

## How updates reach you

Both apps use **one shared functional HA-wrapper version** (currently 0.1.6).
Official pairs it with Nocturne 0.2.4; Latest pairs it with a pinned main snapshot.
HA's technical package version adds a delivery counter, e.g. `0.1.5-1`.
Daily upstream updates change that counter, not wrapper functionality.
[Version numbers explained](docs/VERSIES.md).

**Official:** manually started release check → paired image/source pins → full tests → reviewed pull request → manual publication.

**Latest:** daily upstream-`main` check → successful upstream paired-image job → immutable digests → container and previous-Latest upgrade tests → protected pull request checks → automatic merge. A user's HA installation updates automatically only when automatic updates are enabled for **Latest itself**.

After an update is merged, HA's store refresh can offer the new app version. Users may enable HA's app auto-update option; keep it off during experimental use until backup/restore and upgrade behavior have been verified. This repository does not remotely update anyone's HA installation.

Neither Dockerfile contains a floating image reference: even Latest is converted to exact digests and an exact source commit before testing. Official never auto-merges. Latest may auto-merge only changes to its isolated package after protected checks pass. See [update policy and channel boundaries](docs/UPDATES.md).

## Collaborate

- [Contributing and local test commands](CONTRIBUTING.md)
- [Architecture and security boundaries](docs/ARCHITECTURE.md)
- [Official versus Latest: identity, ports, data and updates](docs/CHANNELS.md)
- [Known limitations and test evidence](docs/TESTING.md)
- [Certificate preflight, automatic reload and error codes (Dutch)](docs/CERTIFICATEN.md)
- [Extra gateway popup safely enable/disable (Dutch)](docs/GATEWAY.md)
- [Official/Latest session isolation and one-time re-login after 0.1.5](docs/COOKIES.md)
- [Cold restore and upgrade rehearsal: scope and remaining HA checks (Dutch)](docs/HERSTELPROEF.md)
- [Concrete solutions and priorities for the remaining gaps (Dutch)](docs/OPLOSPLAN.md)
- [Google Health implementation, limits and earlier bridge proposal (Dutch)](docs/GOOGLE_HEALTH.md)
- [Personal fork, separate third installation and update boundaries (Dutch)](docs/PERSONAL.md)
- [Handoff for the next developer or AI](docs/AI_HANDOFF.md)
- [Security reporting](SECURITY.md)
- [Upstream provenance and licensing](UPSTREAM.md)
- [Nederlandse snelstart](docs/NL.md)

Issues and pull requests are welcome. Share sanitized error excerpts only: no passwords, tokens, recovery codes, certificates/private keys, databases or health records.

## License and attribution

The original wrapper code is licensed under **AGPL-3.0-only**; see [LICENSE](LICENSE). Nocturne and third-party dependencies retain their own copyrights and licenses. This project is not affiliated with or endorsed by Nocturne, Nightscout or Home Assistant. See [UPSTREAM.md](UPSTREAM.md) before redistributing container binaries.
