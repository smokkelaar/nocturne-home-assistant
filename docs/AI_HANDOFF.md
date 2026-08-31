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

1. A verified, non-destructive local-to-repository migration and backup/restore rehearsal.
2. Cross-version upgrade CI using non-sensitive synthetic fixtures and a restore test.
3. Safe gateway-code-only rotation, without changing instance or database credentials.
4. Validated TLS certificate renewal reload and IPv6 behavior.
5. External connector authentication design, only after backup/security boundaries are proven.

The initial wrapper uses Dutch runtime messages. Preserve tested behavior while making the contributor documentation understandable internationally. Do not add unrelated Govee/PV/network configuration to this repository.
