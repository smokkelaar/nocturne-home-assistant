## 0.1.8-2

- Update Nocturne Latest from `761d988` to [`bfb0786`](https://github.com/nightscout/nocturne/compare/761d98876e93c13b557c5f89260701398718aff7...bfb0786c56b285457add9280b656b5ab9b369b8b).
- Upstream paired-image build: https://github.com/nightscout/nocturne/actions/runs/35722109791
- Automated container and previous-Latest upgrade tests are required before merge. Keep a cold backup; rollback after a development schema migration is not guaranteed.

## 0.1.8-1

- Toon bovenaan klikbare release-, base- en broncommitinformatie met het doel van het kanaal.
- Toon CPU, geheugen, persistente opslag, vrije schijfruimte en PostgreSQL-databasegrootte.

## 0.1.7-2

- Update Nocturne Latest from `3e30bf5` to [`761d988`](https://github.com/nightscout/nocturne/compare/3e30bf504a7d04cb49178edd6e67fc561b58b035...761d98876e93c13b557c5f89260701398718aff7).
- Upstream paired-image build: https://github.com/nightscout/nocturne/actions/runs/35212943354
- Automated container and previous-Latest upgrade tests are required before merge. Keep a cold backup; rollback after a development schema migration is not guaranteed.

## 0.1.7-1

- Restore the Latest channel to the existing approved Daily snapshot `3e30bf5`.
- The temporary upstream-only test build is retired; use Nocturne Personal and Test A for API development.

## 0.1.6-8

- Update Nocturne Latest from `d9e1430` to [`3e30bf5`](https://github.com/nightscout/nocturne/compare/d9e1430975c7a05967cba66374392f75f08c858f...3e30bf504a7d04cb49178edd6e67fc561b58b035).
- Upstream paired-image build: https://github.com/nightscout/nocturne/actions/runs/34744554099
- Automated container and previous-Latest upgrade tests are required before merge. Keep a cold backup; rollback after a development schema migration is not guaranteed.

## 0.1.6-7

- Update Nocturne Latest from `ea695ba` to [`d9e1430`](https://github.com/nightscout/nocturne/compare/ea695ba37ea82feaec607ad1ab81ecf3113a2fd7...d9e1430975c7a05967cba66374392f75f08c858f).
- Upstream paired-image build: https://github.com/nightscout/nocturne/actions/runs/34594017929
- Automated container and previous-Latest upgrade tests are required before merge. Keep a cold backup; rollback after a development schema migration is not guaranteed.

## 0.1.6-6

- Update Nocturne Latest from `0164494` to [`ea695ba`](https://github.com/nightscout/nocturne/compare/01644942c08ef27b4915763560a58aa1905951fc...ea695ba37ea82feaec607ad1ab81ecf3113a2fd7).
- Upstream paired-image build: https://github.com/nightscout/nocturne/actions/runs/34216675112
- Automated container and previous-Latest upgrade tests are required before merge. Keep a cold backup; rollback after a development schema migration is not guaranteed.

## 0.1.6-5

- Update Nocturne Latest from `543bbff` to [`0164494`](https://github.com/nightscout/nocturne/compare/543bbff8552d69c2ec39e2e4585c9c839e420f5d...01644942c08ef27b4915763560a58aa1905951fc).
- Upstream paired-image build: https://github.com/nightscout/nocturne/actions/runs/34028157973
- Automated container and previous-Latest upgrade tests are required before merge. Keep a cold backup; rollback after a development schema migration is not guaranteed.

## 0.1.6-4

- Update Nocturne Latest from `ad5dee2` to [`543bbff`](https://github.com/nightscout/nocturne/compare/ad5dee272c0d939b7b9e5f14f631c3434706b10e...543bbff8552d69c2ec39e2e4585c9c839e420f5d).
- Upstream paired-image build: https://github.com/nightscout/nocturne/actions/runs/33959803740
- Automated container and previous-Latest upgrade tests are required before merge. Keep a cold backup; rollback after a development schema migration is not guaranteed.

## 0.1.6-3

- Update Nocturne Latest from `f5024f5` to [`ad5dee2`](https://github.com/nightscout/nocturne/compare/f5024f57fd545da7f08ddde8fcf339ed53d32660...ad5dee272c0d939b7b9e5f14f631c3434706b10e).
- Upstream paired-image build: https://github.com/nightscout/nocturne/actions/runs/33785558820
- Automated container and previous-Latest upgrade tests are required before merge. Keep a cold backup; rollback after a development schema migration is not guaranteed.

## 0.1.6-2

- Update Nocturne Latest from `3b75145` to [`f5024f5`](https://github.com/nightscout/nocturne/compare/3b7514591f854f4794deeeb75d43e33d979d1ee4...f5024f57fd545da7f08ddde8fcf339ed53d32660).
- Upstream paired-image build: https://github.com/nightscout/nocturne/actions/runs/33687748274
- Automated container and previous-Latest upgrade tests are required before merge. Keep a cold backup; rollback after a development schema migration is not guaranteed.

## 0.1.6-1

- Wrapper 0.1.6 forwards external OAuth Bearer tokens in guarded native mode and routes authenticated v4 requests directly to the API.
- Browser session routing, TLS, tenant checks, Basic gateway mode, cookie isolation and internal-header filtering remain enforced.
- Upstream pins, database schema, stored accounts and keys are unchanged. Existing Home Assistant OAuth clients can retry after updating this app.

## 0.1.5-1 — shared wrapper 0.1.5

- Isolate session/setup cookies from Official even when both use the same hostname.
- Ignore old shared sessions; sign in once again using existing passkeys. No URL, account, database or key changes.
- Preserve internal Nocturne cookie names through a header-only nginx njs adapter; no frontend bundle rewrite.
- Add offline cookie tests and a two-real-container synthetic-session regression test. Real browser/passkey acceptance remains manual.

## 0.1.4-1 — shared wrapper 0.1.4

- Fix native startup against current Nocturne: verify private status and anonymous API denial instead of an obsolete auth flag.
- Keep TLS, completed-owner setup, canonical-host restrictions and Nocturne passkey authentication required. Preserve existing data, keys and default gateway settings.
- Share one functional wrapper version across both channels; independent delivery suffixes track upstream updates without implying different wrapper functionality.
- Show channel/wrapper/package/upstream at startup and the pinned main timestamp on Latest's status page.
- Test configured-native boot/restart in disposable containers with synthetic owner fixtures. Real browser/passkey acceptance remains a manual check.

## 0.1.1

- Show the exact upstream `main` commit date and time in UTC next to its short commit ID in the Home Assistant app-store description.
- Record and validate the commit timestamp as part of the immutable Latest provenance; daily promotions update it automatically.

## 0.1.0

- First separately installable **Nocturne Latest Release** channel.
- Pin API and web images from upstream `main` commit `3b7514591f854f4794deeeb75d43e33d979d1ee4` by immutable digest; HA never builds from a floating image reference.
- Use slug `nocturne_latest`, a separate private data directory and default host port 8449. Official data, accounts, passkeys and keys are not copied.
- Include the same guarded TLS, gateway/passkey, health and persistence wrapper as the Official channel.
- Daily automation may promote newer tested `main` snapshots. Schema changes can be frequent and rollback is not guaranteed; keep cold backups.
