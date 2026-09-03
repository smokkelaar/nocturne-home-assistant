## 0.1.5-2

- Update Nocturne Latest from `3b75145` to [`f5024f5`](https://github.com/nightscout/nocturne/compare/3b7514591f854f4794deeeb75d43e33d979d1ee4...f5024f57fd545da7f08ddde8fcf339ed53d32660).
- Upstream paired-image build: https://github.com/nightscout/nocturne/actions/runs/33687748274
- Automated container and previous-Latest upgrade tests are required before merge. Keep a cold backup; rollback after a development schema migration is not guaranteed.

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
