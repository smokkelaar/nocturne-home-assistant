# Installation and operation

## Requirements

- Home Assistant OS with Supervisor and the app store, **amd64**.
- Spare memory, storage and network access for downloading/building the pinned images and running PostgreSQL/API/web. No reliable minimum resource benchmark has been established; do not exhaust the resources required by HA itself.
- One stable **DNS hostname**, reachable on the local network and covered by a certificate trusted by your browser/device. Passkey setup cannot use an IP address as its domain.
- A browser/device supporting passkeys. Decide the hostname **before creating the account**; it is part of the authentication identity.

No router port-forwarding is required or recommended for this test. A publicly registered DNS name/certificate does not require exposing the application to the internet: local DNS can resolve it to HA's LAN address. Certificate issuance and network routing remain the user's responsibility.

## Fresh installation

1. Add `https://github.com/smokkelaar/nocturne-home-assistant` in the HA app store repository settings.
2. Install **Nocturne (experimental)**. This release has no prebuilt wrapper image: Supervisor builds it from its Dockerfile. Wait for that job to finish; repeatedly clicking install/update can produce “Another job is running”.
3. Configure the following options with **your own** hostname/certificate filenames:

   ```yaml
   public_url: https://nocturne.example.net:8448
   certificate: fullchain.pem
   private_key: privkey.pem
   ```

   `example.net` is documentation-only. Put the real certificate and private key in HA's `/ssl` directory. Options accept filenames directly inside that directory, not `/ssl/...` paths. This app mounts `/ssl` read-only. Never publish those files.

4. Leave the default published HTTPS port at `8448`, or ensure the externally configured port matches `public_url`. Do not expose API, PostgreSQL or ingress ports.
5. Start the app and open **Web interface**. Wait for PostgreSQL, API, web and HTTPS readiness. “Listening” is not proof of a successful account login.
6. Open the Nocturne link. If the browser asks for HTTP Basic credentials, use username `nocturne` and the random gateway code shown in the protected HA page. This is **not** your HA login or your Nocturne account password.
7. Complete Nocturne's own setup and create a passkey. Skip Nightscout/data connections in this initial test.
8. Verify dashboard access, sign out/in, then restart **only this app** and verify it opens without repeating setup.

Changing options requires restarting the app. There is no need to restart all of HA for ordinary app option changes.

## Test certificate vs trusted HTTPS

Both certificate fields empty generates a self-signed 30-day test certificate. This is for boot testing only, **not a supported route to real account/passkey use**. Do not disable browser security to make it work.

Configure both certificate fields together for trusted HTTPS. Make sure the browser URL exactly matches the certificate hostname and the selected instance identity. If a hostname fails while an IPv4 connection succeeds, diagnose DNS/routing; switching permanently to an IP breaks passkeys. IPv6 host-port publication is not validated by this wrapper.

This version loads certificates when nginx starts. **After renewal, restart the app** to load the new files. Automatic certificate-reload handling is a tracked follow-up, not an implemented guarantee.

## Persistence, backups and upgrades

The complete PostgreSQL database and generated keys are stored in the app-private `/data` directory. Keep the database and `secrets.json` together. The app refuses to replace missing/corrupt keys or reset an incomplete database.

The manifest requests **cold backups**. Before an update, make an HA backup including this app, download it to another device and verify you have its recovery information. Verify restore on a disposable installation before trusting it. This project has not yet validated the complete HA backup/restore flow.

Do not assume downgrading an image reverses a database migration. Restoring a coordinated pre-upgrade database/key backup may be required. PostgreSQL major upgrades are explicitly refused; there is no automatic database reset.

Automatic app updates are optional in HA. Leave them off for this experimental phase. See the repository's `docs/UPDATES.md` for the upstream update process.

## Known boundaries

- Ingress is a status/launcher only; login takes place in a separate HTTPS tab.
- Mandatory gateway Basic authentication remains enabled. External Nightscout clients/API tokens and connectors have **not** been validated through this gateway; incoming Authorization is stripped before reaching the backend.
- No clinical reliability, automatic dosing, external data connectors or internet-facing deployment has been validated.
- Never paste full logs, keys, recovery codes or health data into public issues. Report only a sanitized relevant excerpt with the app/Nocturne versions.
