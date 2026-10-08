# Nocturne Test B — installation and operation

> Test B evaluates [Hypo comparison PR #2031](https://github.com/nightscout/nocturne/pull/2031), pinned to commit `33ad31c69`, based on upstream `main` `8e1de9070`. It is a separate HA app with its own data and default host port **8452**. The tested image is offered in the prebuilt **1.x** package series after publication.

> **Nederlands, met afbeeldingen en exacte stappen:** [Volledige visuele installatiehandleiding](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/INSTALLATIE.md), van repository toevoegen tot dashboard en herstarttest. [Domein, certificaat en lokale DNS](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/HTTPS-EN-DNS.md) is apart uitgewerkt. These absolute links also work from Home Assistant's Documentation tab.

## Requirements

**Upgrading to wrapper 0.1.5:** session cookies are now isolated from Official and Latest even
on the same hostname. Sign in once again with your existing passkey; do not
recreate the account or change its URL. [Cookie isolation and browser checklist](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/COOKIES.md).

- Home Assistant OS with Supervisor and the app store, **AMD64 or ARM64**.
- Spare memory, storage and network access for downloading the prebuilt image and running PostgreSQL/API/web.
- One stable **DNS hostname**, reachable on the local network and covered by a certificate trusted by your browser/device. Passkey setup cannot use an IP address as its domain.
- A browser/device supporting passkeys. Decide the hostname **before creating the account**; it is part of the authentication identity.

No router port-forwarding is required or recommended for this test. A publicly registered DNS name/certificate does not require exposing the application to the internet: local DNS can resolve it to HA's LAN address. Certificate issuance and network routing remain the user's responsibility.

## Fresh installation

1. Add `https://github.com/smokkelaar/nocturne-home-assistant` in the HA app store repository settings.
2. Install or update **Nocturne Test B**. Supervisor downloads the tested GitHub/GHCR image; compilation happens on GitHub. Existing installations use the ordinary update action.
3. Configure the following options with **your own** hostname/certificate filenames:

   ```yaml
   public_url: https://nocturne.example.net:8452
   certificate: fullchain.pem
   private_key: privkey.pem
   ```

   `example.net` is documentation-only. Put the real certificate and private key in HA's `/ssl` directory. Options accept filenames directly inside that directory, not `/ssl/...` paths. This app mounts `/ssl` read-only. Never publish those files.

4. Leave the Test B host port at `8452` (container port `8448/tcp`), or ensure the externally configured port matches `public_url`. Do not expose API, PostgreSQL or ingress ports.
5. Start the app and open **Web interface**. Wait for PostgreSQL, API, web and HTTPS readiness. “Listening” is not proof of a successful account login.
6. Open the Nocturne link. By default, if the browser asks for HTTP Basic credentials, use username `nocturne` and the random gateway code shown in the protected HA page. This is **not** your HA login or your Nocturne account password.
7. Complete Nocturne's own setup and create a passkey. Skip Nightscout/data connections in this initial test.
8. Verify dashboard access, sign out/in, then restart **only this app** and verify it opens without repeating setup.

## Hypo comparison test path

Open **Reports → Comparison** in Test B. The default host port is **8452**; **8453** belongs to Test C.

1. Choose two periods of equal length with glucose readings and press **Load**.
2. Check **Hypo Duration** (total covered time below range, in hours) and **Hypo Events** (qualifying low episodes), next to the existing hyper rows.
3. Check both period values and the signed change from A to B. Swap the periods: the values should exchange and the change should reverse sign. A lower value is an observation, not treatment advice.
4. A measured period without lows should show zero. A period without readings should show **No data**, with no invented difference.
5. One excursion through low and very low should count once. The existing detector requires at least 15 consecutive minutes below range to start an event and 15 minutes back within range to end it; short dips can contribute duration without counting as events.
6. Reload and print the report; both new rows should remain visible. Unequal periods compare absolute totals, just like the hyper rows, so choose equal periods when comparing counts and durations.

This replaces Test B's A1c preferences PR #1977 source with current upstream main plus the hypo comparison change. That separate draft A1c change is not included. Existing Test B storage, options and identity are retained.

## Test certificate vs trusted HTTPS

Both certificate fields empty generates a self-signed 30-day test certificate. This is for boot testing only, **not a supported route to real account/passkey use**. Do not disable browser security to make it work.

Configure both certificate fields together for trusted HTTPS. Make sure the browser URL exactly matches the certificate hostname and the selected instance identity. If a hostname fails while an IPv4 connection succeeds, diagnose DNS/routing; switching permanently to an IP breaks passkeys. IPv6 host-port publication is not validated by this wrapper.

From wrapper 0.1.1, the app validates the certificate's DNS SAN/hostname, validity dates and matching key before startup. Invalid/expired pairs block startup without resetting data. During operation it checks changed files every 15 seconds, stages a stable validated pair, tests nginx and reloads only nginx. It confirms the served leaf certificate; failed candidates retain the old configuration. The old certificate can still expire. Browser trust remains a separate check. [Behavior and error codes](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/CERTIFICATEN.md).

## Persistence, backups and upgrades

The complete PostgreSQL database and generated keys are stored in the app-private `/data` directory. Keep the database and `secrets.json` together. The app refuses to replace missing/corrupt keys or reset an incomplete database.

The manifest requests **cold backups**. Before an update, make an HA backup including this app, download it to another device and verify you have its recovery information. Verify restore on a disposable installation before trusting it. This project has not yet validated the complete HA backup/restore flow.

CI now rehearses a full cold-data copy, restore into a different disposable volume and baseline-to-candidate wrapper upgrade. This is not a Supervisor archive importer, local-to-repository migration or proof of real-account/passkey recovery. [Test scope](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/HERSTELPROEF.md).

Do not assume downgrading an image reverses a database migration. Restoring a coordinated pre-upgrade database/key backup may be required. PostgreSQL major upgrades are explicitly refused; there is no automatic database reset.

Automatic app updates are optional per app in HA. Keep automatic updates off for **Nocturne Test B**: it is pinned to a specific PR commit for manual verification and must not silently track a moving branch. Keep Official's switch off too. See the repository's `docs/UPDATES.md` for both update processes.

## Known boundaries

- Ingress is a status/launcher only; login takes place in a separate HTTPS tab.
- Gateway Basic authentication defaults to enabled. From wrapper 0.1.4, an existing fully configured owner account can set `gateway_auth: false` to remove only that browser popup. With the default `skip_gateway_check: false`, configured TLS and private Nocturne authentication are checked before startup; Nocturne login stays required. Explicit skip mode is described below. First setup must use `true`. [Exact switch, test and rollback steps](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/GATEWAY.md).
- Wrapper 0.1.6 forwards external OAuth Bearer tokens and routes authenticated v4 requests to the API in guarded native mode. Browser sessions keep their web bridge. The default Basic gate cannot be bypassed with a Bearer token. Legacy API-secret clients and real client consent/refresh still need separate validation. [OAuth gateway behavior](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/GATEWAY.md#home-assistant-via-oauth-vanaf-wrapper-016).
- No clinical reliability, automatic dosing, external data connectors or internet-facing deployment has been validated.
- Never paste full logs, keys, recovery codes or health data into public issues. Report only a sanitized relevant excerpt with the app/Nocturne versions.

Test B builds the exact hypo comparison PR #2031 source pinned in `upstream-test-b.json` inside the wrapper so it can be tested before that PR is merged or released. The package update keeps the Test B slug, host port, HA options, data directory and cookie namespace; no data is copied from another channel and no live HA installation is changed by this repository update. This test instance is not for clinical use.

From wrapper **0.1.10**, all six variants offer **Consciously skip gateway check** (`skip_gateway_check`, default false). Only effective with `gateway_auth: false`; save and restart this app. It skips only the wrapper authentication probe; Nocturne access/share permissions and TLS/host checks still apply. The helper prominently shows `GATEWAY_SKIPPED`. Test A now uses the same visible settings: migrate old `verify_native_auth: false` to `skip_gateway_check: true`, remove the old YAML key, save and restart. The canonical option takes precedence; restore the guard with `skip_gateway_check: false`. [Configuration and rollback](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/GATEWAY.md).

## Experimental maintenance

Opt-in CLI, ingress terminal and guided recovery for this app only. See [step-by-step maintenance guide](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/PERSONAL-MAINTENANCE.md). Disabled by default; requires its own maintenance password. Each image build checks the pinned recovery source contract and binds the result to the API binary. Unrelated source updates remain compatible; changed or unavailable recovery contracts block only new owner recovery. The actual database is checked before writes. No Nocturne source or schema changes; explicit owner recovery adds a native recovery-code hash.

## Experimental maintenance

Opt-in CLI, ingress terminal and guided recovery for this app only. See [step-by-step maintenance guide](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/PERSONAL-MAINTENANCE.md). Disabled by default; requires its own maintenance password. Each image build checks the pinned recovery source contract and binds the result to the API binary. Unrelated source updates remain compatible; changed or unavailable recovery contracts block only new owner recovery. The actual database is checked before writes. No Nocturne source or schema changes; explicit owner recovery adds a native recovery-code hash.
