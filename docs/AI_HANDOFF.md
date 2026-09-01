# Developer / AI handoff

## Scope

This is a shareable, Nocturne-only **HA app wrapper**, not HACS and not the full upstream application. One repository exposes two apps. Read README, CHANNELS, both DOCS files, ARCHITECTURE, UPDATES and MIGRATION before changing runtime behavior. `upstream.json` + `nocturne_local/config.json` are authoritative for Official; `upstream-latest.json` + `nocturne_latest/config.json` for Latest. Never infer the active channel/version from an old screenshot.

## Start here

Current functional version source: `wrapper.json`, shared across both channels.
Runtime `version.json.app` is that version; `package` is the per-channel HA
delivery version (`<wrapper>-<counter>`). See [VERSIES](VERSIES.md).

## 0.1.4 handoff

- Native auth no longer forces/trusts the legacy `requireAuthentication` field.
  Upstream main hardcodes it false even for private instances. Require loaded,
  non-demo, `anonymousReadAccess: false` plus a real anonymous ChartData 401.
- Logs identify channel, wrapper, delivery and upstream before option validation.
  Setup/recovery/status/auth errors have distinct instructions; no raw responses are logged.
- Both channels share wrapper 0.1.4. Upstream-only promotions increment only
  their delivery counter. Do not let either updater bump wrapper functionality.
- Smoke CI now seeds a synthetic owner with a nonfunctional credential **only**
  in its disposable container, then tests native main-entrypoint boot/restart.
  This is not real enrollment/passkey or human-account upgrade evidence.
- No live HA configuration, app data or credentials are changed by this PR.
  The reported live startup failure still needs an exact installed version/log
  and the user's post-update test; do not claim the code fix proves their HA works.

## Working procedure

1. Read the current GitHub Actions results, open issues and `git status`.
2. Run the three offline commands in CONTRIBUTING. Docker testing must use a disposable environment, never the user's existing volume.
3. Keep changes small, deliver a clear next test and say precisely what was or was not verified.
4. If HA UI controls cannot be operated, ask the user to click immediately rather than investigating fragile UI workarounds.

## Non-negotiable boundaries

- Do not read/upload private databases, credentials, account recovery material or raw health data for public debugging.
- Do not expose ports publicly or weaken TLS/passkey validation to make setup appear to work. `gateway_auth: false` is a supported guarded mode from 0.1.2, not permission to remove its startup checks or make it the implicit default.
- Never regenerate instance/database keys or initialize over existing data. Preserve database and matching keys together.
- Do not uninstall a local prototype as a shortcut to subscribing it to this repository. Repository app identity differs; migration is not automated.
- A passing container boot/restart test is not an upgrade, passkey, connector or clinical validation.
- Official must never auto-merge. Latest may auto-merge only its isolated package after protected checks; its Dockerfile still uses exact digests, never a floating `latest` reference. Check source provenance and both guarded web patches.
- Preserve the slugs: `nocturne_local` is Official's existing data identity, while `nocturne_latest` is deliberately separate. Never copy `/data`, passkeys, keys or databases between them.

## Useful next bounded contributions

Read the [concrete solution proposals and acceptance tests](OPLOSPLAN.md) before choosing a follow-up. The [visual Dutch installation guide](INSTALLATIE.md) describes the current user-facing flow, not future functionality.

1. A verified, non-destructive local-to-repository migration and backup/restore rehearsal.
2. Expand the existing setup-only upgrade/restore CI with non-sensitive account/schema fixtures and real passkey recovery checks.
3. Safe gateway-code-only rotation, without changing instance or database credentials.
4. Validate the implemented TLS reload on HA/DuckDNS and multiple real clients; investigate IPv6 separately.
5. External connector authentication design, only after backup/security boundaries are proven.

The initial wrapper uses Dutch runtime messages. Preserve tested behavior while making the contributor documentation understandable internationally. Do not add unrelated Govee/PV/network configuration to this repository.

## Two-channel handoff

- Official is named **Nocturne Official Release**, keeps slug `nocturne_local`, defaults to host 8448 and is updated only through the manually triggered Official workflow.
- Latest is named **Nocturne Latest Release**, uses slug `nocturne_latest`, defaults to host 8449 and is checked daily from upstream `main`.
- Shared runtime/security files in both package directories must remain byte-identical; `tests/test_channels.py` enforces this. Channel manifests, pins and changelogs intentionally differ.
- A Latest automation PR must change only `upstream-latest.json` and the five allowed Latest metadata/build files, explicitly dispatch required Validate, and rely on branch protection before auto-merge.
- Adding the repository shows both apps. Installing one never creates, migrates or modifies the other. HA's per-app auto-update switch is the final delivery control.

## 0.1.1 handoff

- Implemented: `tls.py` immutable TLS snapshots, explicit hostname/validity/key validation, nginx-only reload with leaf confirmation, server-versus-browser status checks, disposable cold restore and baseline-to-candidate upgrade CI. Read [certificate behavior](CERTIFICATEN.md) and [recovery scope](HERSTELPROEF.md).
- `Validate` originally pinned wrapper 0.1.0; the 0.1.2 work deliberately advances it to immutable wrapper 0.1.1. Review/update that baseline only when the supported upgrade floor changes. The upstream updater separately builds its pre-update `HEAD`, so it tests the immediate candidate transition as well.
- No live HA configuration, credentials, account, backup or installation was changed as part of developing these features. Do not infer that the operator installed 0.1.1 from its source version or an ambient app URL.
- Next human checks: confirm installed/source app identity; coordinate backup/test environment; check status UI with real certificate; real login/second client; actual Supervisor restore. Keep the working source installation untouched until those choices are made.
- Certificates are stricter at startup in 0.1.1. A currently expired/mismatched/no-SAN certificate that formerly allowed process startup now blocks it safely; communicate this before an update. Never delete identity files to resolve TLS errors.

## 0.1.2 handoff

- Web readiness now requests exact `/health` instead of `/`; this prevents the wrapper's five-second probe from rendering the dashboard and creating anonymous chart `401` log noise. Do not fall back to `/`.
- `gateway_auth` defaults to `true`. Explicit `false` requires configured TLS and read-only startup verification that native authentication is mandatory, the instance is loaded/non-demo and anonymous chart access returns `401`. Keep the canonical-host nginx guard and stripped credential headers.
- Native-mode container CI uses an empty fixture and therefore cannot validate a real account/passkey. A user must verify existing passkey login, logout/login and app restart after a backup. Do not describe that as automated evidence.
