## 0.1.5-1 — shared wrapper 0.1.5

- Isolate session/setup cookies from Latest even when both use the same hostname.
- Ignore old shared sessions; sign in once again using existing passkeys. No URL, account, database or key changes.
- Preserve internal Nocturne cookie names through a header-only nginx njs adapter; no frontend bundle rewrite.
- Add offline cookie tests and a two-real-container synthetic-session regression test. Real browser/passkey acceptance remains manual.

## 0.1.4-1 — shared wrapper 0.1.4

- Fix native startup against current Nocturne: verify private status and anonymous API denial instead of an obsolete auth flag.
- Keep TLS, completed-owner setup, canonical-host restrictions and Nocturne passkey authentication required. Preserve existing data, keys and default gateway settings.
- Share one functional wrapper version across both channels; independent delivery suffixes track upstream updates without implying different wrapper functionality.
- Show channel/wrapper/package/upstream at startup and the pinned main timestamp on Latest's status page.
- Test configured-native boot/restart in disposable containers with synthetic owner fixtures. Real browser/passkey acceptance remains a manual check.

## 0.1.3

- Rename the existing app to **Nocturne Official Release** without changing its `nocturne_local` slug or private data directory.
- Add a separately installable Latest channel elsewhere in the same repository; no data, account, passkey or settings are copied between channels.
- Nocturne remains the pinned official 0.2.4 release.

## 0.1.2

- Probe Nocturne Web through its dedicated `/health` route. The previous five-second request to `/` could render the dashboard and generate repeated, harmless `401 Bearer` chart errors in the app log.
- Add an explicit `gateway_auth: false` option for an existing instance whose owner account and passkey are already configured. This removes only the extra browser Basic-authentication prompt; Nocturne's own account/passkey authentication remains required.
- Native Nocturne authentication fails closed: startup verifies trusted TLS is configured, Nocturne reports authentication as mandatory and an anonymous protected-data request is denied. A fresh/unconfigured instance must first be completed with `gateway_auth: true`.
- Preserve existing database, account, passkey, instance keys and gateway secret. The option defaults to `true`, so updating does not switch authentication mode automatically.
- Nocturne remains 0.2.4. Real-account/passkey acceptance of the opt-in mode still requires a manual post-install test; CI uses only a disposable empty instance and no medical data.

## 0.1.1

- Validate TLS SAN/hostname, leaf validity and matching private key before startup; reject invalid pairs with safe error codes. Browser trust is still a separate test.
- Stage immutable private certificate copies; automatically check renewed source files and reload only nginx after validation. Reject partial/mismatched renewals and verify the served leaf before accepting a change.
- HA status now distinguishes server checks from unverified browser DNS/trust/passkey checks, shows certificate expiry, and checks a real web HTTP response.
- Add disposable cold-data restore, baseline 0.1.0-to-candidate upgrade, and missing-identity refusal tests. The upstream updater tests its current-main baseline before proposing a candidate.
- Bound the certificate-generation and cold-copy subprocesses themselves (15/90 seconds), inside the existing Docker/workflow limits; regression tests cover both bounds.
- Nocturne remains 0.2.4. No automatic local-to-repository migration, Supervisor backup importer, real-account upgrade proof or live installation changes.
- **Before updating:** confirm your configured certificate is currently valid, covers `public_url` in a DNS SAN and matches its unencrypted key. Invalid/expired certificates now block startup rather than merely causing browser warnings. Keep a coordinated app backup.

## 0.1.0

- First public repository release, based on the locally tested `0.1.0-test2` wrapper.
- Nocturne API/web 0.2.4, pinned by digest; PostgreSQL 17; amd64 only.
- Shared lock/version metadata, daily stable-upstream update proposals, regression checks and disposable container smoke testing.
- Generic installation, migration, architecture and contributor documentation; no personal configuration included.
- Runtime design remains experimental. Repository installation does not migrate an existing local app's data.
