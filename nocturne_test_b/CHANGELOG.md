## 1.0.43901

- New 1.x distribution: prebuilt GitHub/GHCR images for AMD64 and ARM64. HAOS downloads the tested image; no local compilation.
- Existing app identity, options, private data and Nocturne source remain intact.

## 0.3.25-b33

- Guided standalone TOTP reset button: selected owner, backup/account confirmation, one-use request, and clear reenrollment steps. No new recovery code or changes to passkeys/data; existing login sessions stay signed in.
- Shared wrapper 0.1.13: opt-in HA maintenance terminal, CLI and recovery wizard across all six channels. Disabled by default; separate password required.
- Existing identities, ports, source pins and data remain intact. Owner recovery accepts only reviewed source commits.

## 0.3.25-b31

- Wrapper 0.1.11 forwards the exact Nocturne source commit and actual API build date to Nocturne.
- Source builds record their own publish time; prebuilt API images retain their embedded build date.
- Source pins and stored data remain unchanged.

## 0.3.25-b30

- Pin PR #1977 source `bf5c517e3` after merging main `b515516d4` and resolving merge conflicts.
- Retain the PR translations and the new realtime availability message in all eleven locales.
- Keep shared wrapper 0.1.10 and Test B settings, ports and storage.

## 0.3.25-b29

- Apply the chosen A1c/HbA1c name to settings labels and unit explanations in all 11 supported languages.
- Omit the estimated A1c target in the executive summary when the backend cannot supply it for a range with insufficient readings.
- Include browser regressions for missing targets and both display units from Nocturne PR #1977.

## 0.3.25-b28

- Restore A1c preference labels, explanations and report navigation in all 11 supported languages.
- Preserve the scientific names and units in both dropdowns, including their persisted values; estimated values keep their e prefix.
- Include production catalog and locale render regression checks from Nocturne PR #1977.

## 0.3.25-b27

- Replace the Google Health PR #1293 test build with current Nocturne main plus A1c preferences [PR #1977](https://github.com/nightscout/nocturne/pull/1977).
- Configure A1c/HbA1c naming and %/mmol/mol units in Settings → Appearance → Units & Formats; estimated values keep the eA1c/eHbA1c prefix, lab measurements remain A1c/HbA1c, and GMI remains separate.
- Preserve the Test B identity, port 8452, existing data, options and cookie namespace. Pin API and web to one checksum-verified source archive.

## 0.3.25-b26

- Shared wrapper 0.1.10: explicit `skip_gateway_check`, default false, only effective with `gateway_auth: false`.
- Keep Nocturne permissions, TLS, hostname checks, existing data and keys unchanged; display skipped checks prominently.
- Test A now uses the same visible settings. Existing `verify_native_auth: false`: set `skip_gateway_check: true` in app Configuration, remove the old YAML key, save and restart. The canonical option takes precedence; its new default may restore the private check until migrated.

## 0.3.25-b25

- Preserve the configured external HTTPS port in BASE_DOMAIN for API and web URL generation.
- Keep internal listeners, hostname checks, data and upstream source pins unchanged.

## 0.3.25-b24

Test B builds the latest fully CI-validated Google Health PR #1293 source commit
`d28ced806e146804b355bc7a63130ce8a78f2e3e`.

- Preserves Nocturne and Google Health product names across translation catalogs.
- Uses existing native health tables; adds no Google Health database migrations or staging tables.
- Bounds reconciliation memory and splits oversized synchronization windows, preserving existing
  data and retry cursors on failure or empty results.
- Restores the explicit shared PostgreSQL test fixture required by the upstream test suite.
- Keeps the Test B identity, port 8452, data directory, accounts, connector settings, and cookie namespace.
  This update does not reset or delete stored data. Existing experimental staging tables, if present
  in an older test installation, are left untouched and are no longer used.
- Personal, Test A, Test C, Latest, and Official are unchanged.

## 0.3.25-b23

Test B now builds Google Health PR #1293 source commit
`8d7f70dd73d738b0bdda8c86616a34ad4b0c8a80`.

- Restored the historical-import progress sentence in all supported translation catalogs.
- Preserved the inline completion/progress placeholder used by the Svelte translation runtime,
  so the page now shows the date through which history was synchronized and whether the requested
  history is complete.
- No connector data, accounts, settings, or Test B storage is reset by this update.

## 0.3.25-b17

Test B now builds Google Health PR #1293 source commit
`5d97387bbaf2b0ff9456fc47f80c22c65a980b27`.

- Nocturne Remote now keeps JSON parsing and other response-processing causes in the connector
  status instead of replacing them with only “see preceding connector logs”. This makes a partial
  crawl actionable while preserving already imported records.
- Added a regression assertion for an unparseable remote page. Transport failures remain visible as
  before.

The Test B identity, port 8452, data directory, account, connector settings and cookie namespace
are unchanged. No data is deleted or reset by this update.

## 0.3.25-b16

Test B now builds Google Health PR #1293 source commit `4554bd6e1`.

- Nocturne Remote now reports the concrete transport cause when Personal cannot be reached (for
  example a TLS, DNS or connection failure), instead of hiding it behind a generic fetch error.
- Added a regression test for a transport failure. Google Health behavior and the Test B data store
  are unchanged; no data is deleted or reset.

The Test B identity, port 8452, data directory, account, connector settings and cookie namespace
are unchanged.

## 0.3.25-b15

Test B now builds Google Health PR #1293 source commit
`7aa241d14a4cff5fcc04d11c15b83d61ae3e3e4f`, with the checksum-verified archive pinned in
`upstream-google-health-pr1293.json`.

- Keep Google Health category identifiers locale-neutral so Body measurement/weight remains visible in translated locales.

The Test B identity, port 8452, data directory, account, connector settings
and cookie namespace are unchanged. No data is deleted or reset by this update.

## 0.3.25-b13

Test B now builds Google Health PR #1293 source commit
`bca63aa39`, with the checksum-verified archive pinned in
`upstream-google-health-pr1293.json`.

- Fixed a Dutch (and other translated-locale) rendering bug that hid the
  **Vitals** and **Body measurement** categories. The API uses stable English
  category keys while the UI labels are translated; the page now compares the
  stable keys and only translates the displayed label.
- Existing catalog fallback behavior remains: heart rate and weight rows stay
  visible as **Not scanned** while inventory is unavailable.

The Test B identity, port 8452, data directory, account, connector settings
and cookie namespace are unchanged. No data is deleted or reset by this update.

## 0.3.25-b12

Test B now builds the follow-up Google Health PR #1293 source commit
`817df386`, with the checksum-verified archive pinned in
`upstream-google-health-pr1293.json`.

- Google Health categories now remain visible while an inventory preview is
  still running or temporarily unavailable. Vitals (heart rate) and Body
  measurement (weight) show their server catalog rows as **Not scanned**
  instead of disappearing.
- Added a browser regression test for an `already_running` inventory scan.

The Test B identity, port 8452, data directory, account, connector settings
and cookie namespace are unchanged. No data is deleted or reset by this update.

## 0.3.25-b11

Test B now builds Google Health PR #1293 source commit `db80b8c`, with the
checksum-verified archive pinned in `upstream-google-health-pr1293.json`.

- The catalog fallback now satisfies the generated API types by ignoring
  malformed capability entries without a data type; valid Vitals and Body
  measurement entries remain visible during partial inventory previews.
- All b10 category-visibility and b9 preview-coordination fixes remain included.

The Test B identity, port 8452, data directory, account, connector settings
and cookie namespace are unchanged. No data is deleted or reset by this update.

## 0.3.25-b10

Test B now builds Google Health PR #1293 source commit `213ed1b`, with the
checksum-verified archive pinned in `upstream-google-health-pr1293.json`.

- The Google Health settings page now uses the server capability catalogue as
  the source of truth for categories. Vitals (heart rate) and Body measurement
  (weight) remain visible when a slow or partial inventory preview omits them,
  and those rows are clearly labelled **Not scanned** until the scan returns.
- The previous b9 preview-gate timeout and `already_running` coordination fix
  remain included, so a busy historical import cannot leave the inventory
  spinner running indefinitely.

The Test B identity, port 8452, data directory, account, connector settings
and cookie namespace are unchanged. No data is deleted or reset by this update.

## 0.3.25-b9

Test B now builds Google Health PR #1293 source commit `2d8f267`, with the
checksum-verified archive pinned in `upstream-google-health-pr1293.json`.

- The inventory preview now gives an active import a five-second coordination
  window. If the tenant slot is still occupied, the page explains that an
  import is running instead of leaving the inventory spinner indefinitely.
- The server-side guard and the UI both recognise the sanitised
  `already_running` coordination code without exposing provider or connector
  internals. No second import is started and no existing data is changed.

The Test B identity, port 8452, data directory, account, connector settings
and cookie namespace are unchanged. No data is deleted or reset by this update.

## 0.3.25-b8

Test B now builds Google Health PR #1293 source commit `2087a3f`, with the
checksum-verified archive pinned in `upstream-google-health-pr1293.json`.

- A scheduled import and a user-triggered **Sync now** request share one tenant
  slot. If the slot is already occupied, the UI keeps polling the existing run
  instead of showing a provider failure or overwriting the connector health
  state with a stale “already running” error.
- Heart-rate points used by the actogram are averaged to one UTC-minute point
  in PostgreSQL before the report response is serialized. Raw rows are kept
  unchanged for health history and day views; this reduces report payload and
  chart work for dense wearable data on both heart-rate and steps pages.
- “Google Health” stays as the product name in every supported locale.

The Test B identity, port 8452, data directory, account, connector settings
and cookie namespace are unchanged. No data is deleted or reset by this update.

## 0.3.25-b7

Test B now builds the Google Health-only PR #1293 source at commit `bc10407`, merged with Nightscout `main` at `de6b030`. The Test B identity, port 8452, data mount, options, and cookie namespace are unchanged; Personal and Test A are not changed.

## 0.3.25-b6

- Zelfde API- en web-image-digests als Latest 0.1.8-3, main `8635bd530e6f8b792c3f2442cd3198ec7104fa96`.
- Geen wijziging van poort, opslag, accounts of connectorinstellingen.

# 0.3.25-b5

Restores the missing eHbA1c and lab-result labels in production tooltips. PR #1361 commit `2b480c6` includes both labels in all 11 supported language catalogs, with English as the source language. A regression test reproduces production translation and verifies every language in CI. The earlier line-boundary fix remains included.

# 0.3.25-b4

Pinned Test B to PR #1361 follow-up commit `7dfdd53`. Lab-only markers outside glucose-estimate coverage no longer extend the eHbA1c line; the regression test covers a lab result before the first estimate. Test B's identity, options, port, data mount, and cookie namespace remain unchanged.

# 0.3.25-b3

Pinned Test B to PR #1361 merge commit `dacd76c`, including the resolved upstream `main` conflict. The HA app identity, options, port, data mount, and cookie namespace are unchanged.

# 0.3.25-b2

Klikbare broninformatie voor PR #1293, het testscenario en actuele systeemresources op de Home Assistant-statuspagina.

# 0.3.25-b1

Test B pinned to PR #1293 (Google Health connector), review follow-up commit `22e4a759f`; source `22e4a759fb4b176b2aba2fdc7ccf68cbe52b94c7`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`. Temporary isolated instance for manual verification only; Personal and Test A remain in use for other testing.
## 0.3.25-b32

- Add shared read-only `nocturne-ha` diagnostics.
- Use the setup-independent API version endpoint in fresh-instance smoke tests.
