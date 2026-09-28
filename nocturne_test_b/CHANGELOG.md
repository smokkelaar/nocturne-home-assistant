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
