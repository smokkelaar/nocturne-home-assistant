# Nocturne Test A — installation and operation

> This is an isolated build of [Nocturne PR #1293](https://github.com/nightscout/nocturne/pull/1293). It is a separate HA app with its own data and default host port **8451**. Version **0.3.26-a13** pins PR commit `969896385` on main `b515516d4`; source and checksum are recorded in `upstream-test-a.json`.

## Public ports and native access

Test A passes the full public_url authority to BASE_DOMAIN. For
`https://nocturne.example.net:8451`, a generated link uses
`https://<token>.share.nocturne.example.net:8451`. Existing tokens do not need
rotation: copy or reveal the link again after restarting the updated app.

Share hostnames also need DNS pointing to this HA host and a trusted certificate
covering `*.share.nocturne.example.net`. A certificate covering only the apex,
or only `*.nocturne.example.net`, does not cover these two-level share names.
The wrapper does not create those DNS records or certificates.

To deliberately use public sharing without an additional gateway popup:

```yaml
gateway_auth: false
skip_gateway_check: true
```

Save and restart only Test A. This skips the wrapper's private-instance check,
not Nocturne's authentication or permission checks. Trusted configured TLS
certificates are still required. Public access remains governed by Nocturne's
sharing scopes; this configuration does not promise mandatory login for all
data. Leave `skip_gateway_check` false unless you deliberately accept that mode.
The old `verify_native_auth: false` option should be removed when migrating to
the canonical `skip_gateway_check: true` setting; the canonical option takes precedence.

## Source snapshot and retesting

Current source review and automated check results are available on
[PR #1293](https://github.com/nightscout/nocturne/pull/1293). The delivery's
container build and startup checks are on
[HA PR #95](https://github.com/smokkelaar/nocturne-home-assistant/pull/95).
Automated checks do not validate your Google account's consent or real data.

The update retains the database credential fix and diagnostics, and adds the
OAuth token-cache, overview authorization, UTC duration, sleep-stage overlap
and disconnect/purge queue-cancellation fixes. Port, settings, keys and
private storage remain unchanged. It also resolves the merge with current main
and fixes temporary Google account-identity errors being shown as reconnection failures.

Main adds sleep deletion columns, nullable heart-rate/step types and non-unique
original-ID indexes. These migrations do not remove existing records. Back up
before upgrading, then check recent synchronization and historical imports,
repeated sleep imports without duplicates, replacement of sleep stages and
continuation after restart. A manually deleted sleep session should remain
deleted after synchronization. Also verify disconnect/reconnect with a real
Google account. The sleep merge preserves existing IDs and creation times
while retaining main's locks and deletion protection.

The Google Health writer skips manually deleted sleep sessions and continues
the import. Provider-missing sessions become system soft-deletions, which a
later reimport can restore. Explicit purge still permanently removes Google's
records and reserved import keys.

## Diagnostic API logs

Version 0.3.26-a5 fixes the missing-password failure in Google Health's dedicated
PostgreSQL lock/listener sessions. Settings, keys and storage remain unchanged.
Separate NocturneRemote foreign-key errors still require independent diagnosis.

Version 0.3.26-a4 enables API warning/error logging in the shared Home Assistant
app log. Remote OTLP export remains unconfigured and web telemetry stays disabled.
This update changes logging only; it does not fix the Google Health save error.

After updating, reproduce the failed save once and inspect the app's Logs tab.
Alternatively, run `ha addons list` in the HA terminal to find Test A's slug,
then `ha addons logs SLUG`. Share only the relevant exception/stacktrace after
removing secrets, tokens and health data.

> **Nederlands, met afbeeldingen en exacte stappen:** [Volledige visuele installatiehandleiding](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/INSTALLATIE.md), van repository toevoegen tot dashboard en herstarttest. [Domein, certificaat en lokale DNS](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/HTTPS-EN-DNS.md) is apart uitgewerkt. These absolute links also work from Home Assistant's Documentation tab.

## Requirements

**Upgrading to wrapper 0.1.5:** session cookies are now isolated from Official and Latest even
on the same hostname. Sign in once again with your existing passkey; do not
recreate the account or change its URL. [Cookie isolation and browser checklist](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/COOKIES.md).

- Home Assistant OS with Supervisor and the app store, **amd64**.
- Spare memory, storage and network access for downloading/building the pinned images and running PostgreSQL/API/web. No reliable minimum resource benchmark has been established; do not exhaust the resources required by HA itself.
- One stable **DNS hostname**, reachable on the local network and covered by a certificate trusted by your browser/device. Passkey setup cannot use an IP address as its domain.
- A browser/device supporting passkeys. Decide the hostname **before creating the account**; it is part of the authentication identity.

No router port-forwarding is required or recommended for this test. A publicly registered DNS name/certificate does not require exposing the application to the internet: local DNS can resolve it to HA's LAN address. Certificate issuance and network routing remain the user's responsibility.

## Fresh installation

1. Add `https://github.com/smokkelaar/nocturne-home-assistant` in the HA app store repository settings.
2. Install or update **Nocturne Test A**. This channel has no prebuilt wrapper image: Supervisor builds it from its Dockerfile. Wait for that job to finish; repeatedly clicking install/update can produce “Another job is running”.
3. Configure the following options with **your own** hostname/certificate filenames:

   ```yaml
   public_url: https://nocturne.example.net:8451
   certificate: fullchain.pem
   private_key: privkey.pem
   ```

   `example.net` is documentation-only. Put the real certificate and private key in HA's `/ssl` directory. Options accept filenames directly inside that directory, not `/ssl/...` paths. This app mounts `/ssl` read-only. Never publish those files.

4. Leave the Test A host port at `8451` (container port `8448/tcp`), or ensure the externally configured port matches `public_url`. Do not expose API, PostgreSQL or ingress ports.
5. Start the app and open **Web interface**. Wait for PostgreSQL, API, web and HTTPS readiness. “Listening” is not proof of a successful account login.
6. Open the Nocturne link. By default, if the browser asks for HTTP Basic credentials, use username `nocturne` and the random gateway code shown in the protected HA page. This is **not** your HA login or your Nocturne account password.
7. Complete Nocturne's own setup and create a passkey. Skip Nightscout/data connections in this initial test.
8. Verify dashboard access, sign out/in, then restart **only this app** and verify it opens without repeating setup.

Changing options requires restarting the app. There is no need to restart all of HA for ordinary app option changes.

## Test certificate vs trusted HTTPS

Both certificate fields empty generates a self-signed 30-day test certificate. This is for boot testing only, **not a supported route to real account/passkey use**. Do not disable browser security to make it work.

Configure both certificate fields together for trusted HTTPS. Make sure the browser URL exactly matches the certificate hostname and the selected instance identity. If a hostname fails while an IPv4 connection succeeds, diagnose DNS/routing; switching permanently to an IP breaks passkeys. IPv6 host-port publication is not validated by this wrapper.

From wrapper 0.1.1, the app validates the certificate's DNS SAN/hostname, validity dates and matching key before startup. Invalid/expired pairs block startup without resetting data. During operation it checks changed files every 15 seconds, stages a stable validated pair, tests nginx and reloads only nginx. It confirms the served leaf certificate; failed candidates retain the old configuration. The old certificate can still expire. Browser trust remains a separate check. [Behavior and error codes](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/CERTIFICATEN.md).

## Persistence, backups and upgrades

The complete PostgreSQL database and generated keys are stored in the app-private `/data` directory. Keep the database and `secrets.json` together. The app refuses to replace missing/corrupt keys or reset an incomplete database.

The manifest requests **cold backups**. Before an update, make an HA backup including this app, download it to another device and verify you have its recovery information. Verify restore on a disposable installation before trusting it. This project has not yet validated the complete HA backup/restore flow.

CI now rehearses a full cold-data copy, restore into a different disposable volume and baseline-to-candidate wrapper upgrade. This is not a Supervisor archive importer, local-to-repository migration or proof of real-account/passkey recovery. [Test scope](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/HERSTELPROEF.md).

Do not assume downgrading an image reverses a database migration. Restoring a coordinated pre-upgrade database/key backup may be required. PostgreSQL major upgrades are explicitly refused; there is no automatic database reset.

Automatic app updates are optional per app in HA. Test A updates are published manually when a new PR snapshot is pinned. Keep Official's switch off. See the repository's `docs/UPDATES.md` for both update processes.

## Known boundaries

- Ingress is a status/launcher only; login takes place in a separate HTTPS tab.
- Gateway Basic authentication defaults to enabled. From wrapper 0.1.4, an existing fully configured owner account can set `gateway_auth: false` to remove only that browser popup. With the default `skip_gateway_check: false`, configured TLS and private Nocturne authentication are checked before startup; Nocturne login stays required. Explicit skip mode is described below. First setup must use `true`. [Exact switch, test and rollback steps](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/GATEWAY.md).
- Wrapper 0.1.6 forwards external OAuth Bearer tokens and routes authenticated v4 requests to the API in guarded native mode. Browser sessions keep their web bridge. The default Basic gate cannot be bypassed with a Bearer token. Legacy API-secret clients and real client consent/refresh still need separate validation. [OAuth gateway behavior](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/GATEWAY.md#home-assistant-via-oauth-vanaf-wrapper-016).
- No clinical reliability, automatic dosing, external data connectors or internet-facing deployment has been validated.
- Never paste full logs, keys, recovery codes or health data into public issues. Report only a sanitized relevant excerpt with the app/Nocturne versions.

Test A compiles API and web from its pinned PR source. Builds need more time and resources than Latest. Home Assistant Supervisor currently keeps the update dialog at 0% during this local Docker build; this does not mean the build is stuck. Follow the named `Nocturne build phase` entries in **Settings → System → Logs → Supervisor** for live detail. PR #1293 includes Google Health imports for steps, heart rate, weight and sleep. Progress refreshes while the connector page is open; the percentage estimates data-type stages, not remaining time. No dosing advice or insulin/IOB changes. [Personal versions, source and update behavior](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/PERSONAL.md).

From wrapper **0.1.10**, all six variants offer **Consciously skip gateway check** (`skip_gateway_check`, default false). Only effective with `gateway_auth: false`; save and restart this app. It skips only the wrapper authentication probe; Nocturne access/share permissions and TLS/host checks still apply. The helper prominently shows `GATEWAY_SKIPPED`. Test A now uses the same visible settings: migrate old `verify_native_auth: false` to `skip_gateway_check: true`, remove the old YAML key, save and restart. The canonical option takes precedence; restore the guard with `skip_gateway_check: false`. [Configuration and rollback](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/GATEWAY.md).

## Experimental maintenance

Opt-in CLI, ingress terminal and guided recovery for this app only. See [step-by-step maintenance guide](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/PERSONAL-MAINTENANCE.md). Disabled by default; requires its own maintenance password. Each image build checks the pinned recovery source contract and binds the result to the API binary. Unrelated source updates remain compatible; changed or unavailable recovery contracts block only new owner recovery. The actual database is checked before writes. No Nocturne source or schema changes; explicit owner recovery adds a native recovery-code hash.
