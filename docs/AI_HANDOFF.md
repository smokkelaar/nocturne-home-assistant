# Developer / AI handoff

## Scope

This is a shareable, Nocturne-only **HA app wrapper**, not HACS and not the full upstream application. Read README, DOCS, ARCHITECTURE, UPDATES and MIGRATION before changing runtime behavior. `upstream.json` and `nocturne_local/config.json` are authoritative version inputs; never infer the active version from an old screenshot.

## Start here

1. Read the current GitHub Actions results, open issues and `git status`.
2. Run the three offline commands in CONTRIBUTING. Docker testing must use a disposable environment, never the user's existing volume.
3. Keep changes small, deliver a clear next test and say precisely what was or was not verified.
4. If HA UI controls cannot be operated, ask the user to click immediately rather than investigating fragile UI workarounds.

## Non-negotiable boundaries

- Do not read/upload private databases, credentials, account recovery material or raw health data for public debugging.
- Do not expose ports publicly, remove gateway/authentication checks or weaken TLS/passkey validation to make setup appear to work.
- Never regenerate instance/database keys or initialize over existing data. Preserve database and matching keys together.
- Do not uninstall a local prototype as a shortcut to subscribing it to this repository. Repository app identity differs; migration is not automated.
- A passing container boot/restart test is not an upgrade, passkey, connector or clinical validation.
- Do not auto-merge upstream schema changes or add `latest` tags. Check source provenance and the two guarded web patches.

## Useful next bounded contributions

Read the [concrete solution proposals and acceptance tests](OPLOSPLAN.md) before choosing a follow-up. The [visual Dutch installation guide](INSTALLATIE.md) describes the current user-facing flow, not future functionality.

1. A verified, non-destructive local-to-repository migration and backup/restore rehearsal.
2. Expand the existing setup-only upgrade/restore CI with non-sensitive account/schema fixtures and real passkey recovery checks.
3. Safe gateway-code-only rotation, without changing instance or database credentials.
4. Validate the implemented TLS reload on HA/DuckDNS and multiple real clients; investigate IPv6 separately.
5. External connector authentication design, only after backup/security boundaries are proven.

The initial wrapper uses Dutch runtime messages. Preserve tested behavior while making the contributor documentation understandable internationally. Do not add unrelated Govee/PV/network configuration to this repository.

## 0.1.1 handoff

- Implemented: `tls.py` immutable TLS snapshots, explicit hostname/validity/key validation, nginx-only reload with leaf confirmation, server-versus-browser status checks, disposable cold restore and baseline-to-candidate upgrade CI. Read [certificate behavior](CERTIFICATEN.md) and [recovery scope](HERSTELPROEF.md).
- `Validate` pins baseline wrapper 0.1.0 by full commit. Review/update that baseline deliberately when the supported upgrade floor changes. The upstream updater separately builds its pre-update `HEAD`, so it tests the immediate candidate transition as well.
- No live HA configuration, credentials, account, backup or installation was changed as part of developing these features. Do not infer that the operator installed 0.1.1 from its source version or an ambient app URL.
- Next human checks: confirm installed/source app identity; coordinate backup/test environment; check status UI with real certificate; real login/second client; actual Supervisor restore. Keep the working source installation untouched until those choices are made.
- Certificates are stricter at startup in 0.1.1. A currently expired/mismatched/no-SAN certificate that formerly allowed process startup now blocks it safely; communicate this before an update. Never delete identity files to resolve TLS errors.
