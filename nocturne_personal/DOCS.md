# Nocturne Personal Release — installation and operation

> This is the Personal source-fork channel following the approved Daily base. It is a separate HA app with its own data and default host port **8450**. For the manually promoted stable channel choose **Nocturne Official Release**. Never copy `/data`, accounts or keys between them.

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
2. Install **Nocturne Personal Release**. This channel has no prebuilt wrapper image: Supervisor builds it from its Dockerfile. Wait for that job to finish; repeatedly clicking install/update can produce “Another job is running”.
3. Configure the following options with **your own** hostname/certificate filenames:

   ```yaml
   public_url: https://nocturne.example.net:8450
   certificate: fullchain.pem
   private_key: privkey.pem
   ```

   `example.net` is documentation-only. Put the real certificate and private key in HA's `/ssl` directory. Options accept filenames directly inside that directory, not `/ssl/...` paths. This app mounts `/ssl` read-only. Never publish those files.

4. Leave the Personal host port at `8450` (container port `8448/tcp`), or ensure the externally configured port matches `public_url`. Do not expose API, PostgreSQL or ingress ports.
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

Automatic app updates are optional per app in HA. Enable them only for **Nocturne Personal Release** if its data is replaceable and you deliberately accept daily tested development snapshots. Keep Official's switch off. See the repository's `docs/UPDATES.md` for both update processes.

## Known boundaries

- Ingress is a status/launcher only; login takes place in a separate HTTPS tab.
- Gateway Basic authentication defaults to enabled. From wrapper 0.1.4, an existing fully configured owner account can set `gateway_auth: false` to remove only that browser popup. Trusted configured TLS and native Nocturne authentication are then checked before startup; Nocturne's own passkey stays required. First setup must use `true`. [Exact switch, test and rollback steps](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/GATEWAY.md).
- Wrapper 0.1.6 forwards external OAuth Bearer tokens and routes authenticated v4 requests to the API in guarded native mode. Browser sessions keep their web bridge. The default Basic gate cannot be bypassed with a Bearer token. Legacy API-secret clients and real client consent/refresh still need separate validation. [OAuth gateway behavior](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/GATEWAY.md#home-assistant-via-oauth-vanaf-wrapper-016).
- No clinical reliability, automatic dosing, external data connectors or internet-facing deployment has been validated.
- Never paste full logs, keys, recovery codes or health data into public issues. Report only a sanitized relevant excerpt with the app/Nocturne versions.

Personal compiles API and web from its pinned fork source. Builds need more time and resources than Latest. Personal 0.2.4 adds Google Health (steps, heart rate, weight) and a separate medication log. Google requires your own OAuth client and consent; real account access must still be tested. No dosing advice or insulin/IOB changes. [Feature setup](https://github.com/smokkelaar/nocturne-personal/blob/personal/PERSONAL_USAGE.md). [Personal versions, source and update behavior](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/PERSONAL.md).
