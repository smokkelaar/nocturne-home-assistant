# 0.3.24-1

Personal 0.3.24; source `4635241949b599a8f9788a5b0fcf95e3c6233cfd`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

# 0.3.23-1

Personal 0.3.23; source `e001e386d2cee62f160848cd17ee891e98056892`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

# 0.3.22-1

Personal 0.3.22; source `9617c6996d3b4a59849e8c3c00ae741df423bcb1`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

# 0.3.21-1

Personal 0.3.21; source `b190b64c322d492af6bc4a4d54265fa3f3d6766e`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

# 0.3.20-1

Personal 0.3.20; source `923ec265bb2f84af0e5b02644cfbbf6652c7e1fe`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

# 0.3.19-1

Personal 0.3.19; source `de1724b6b5135b2e91fa5c6b9b502b3aed31f9e2`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

# 0.3.18-1

Personal 0.3.18; source `dc876bf906ebb5f92030cdacca399d418306d070`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

# 0.3.17-1

Personal 0.3.17; source `d4a3ddf1daf1feec670cde6755bca7aa7911929d`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

# 0.3.16-1

Personal 0.3.16; source `dbabc5384865ff330843f433ada3656b7c39b8db`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

# 0.3.15-1

Personal 0.3.15; source `4b3c29b2057f37921647e2b2119cb1250e7580fc`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

# 0.3.14-5

Personal 0.3.14; source `1deeb6494d51bddc88441fe4a1648bec8c3b910c`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

- Fixes the custom palettes only blending between 2 colors, losing every colormap's real in-between hues (e.g. Viridis' purple→blue→green→yellow). Every palette now uses its full multi-stop spectrum.
- Fixes the Theme swatch preview showing whichever palette was currently active instead of Theme's own fixed colors.
- Makes each palette preview swatch show its full spectrum too, so similar-looking palettes (Inferno vs Magma, Mako vs Rocket) are easier to tell apart before picking one.

# 0.3.14-4

Personal 0.3.14; source `1ff0982a3a153c74848db09c93501f068cb9129c`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

- Moves the Dim % input into the Focus Window card, since dimming only affects cells outside that window.
- Reset now also turns Invert back off, instead of leaving it on.
- Replaces Blue/Orange with the full set of perceptually-uniform colormap palettes (Viridis, Plasma, Inferno, Magma, Cividis, Turbo, Mako, Rocket), for 9 choices total alongside Theme.

# 0.3.14-3

Personal 0.3.14; source `6081ab100de24d1793e6583a7b648a426db8c18b`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

- Fixes the custom Avg Glucose palette's High point showing the wrong color; Low/High now mark the true color endpoints instead of a position inside the fixed 2.2-19.4 scale.
- Hides the 2 extra (non-adjustable) slider dots on the bar when a custom palette is active, matching the Low/High inputs below it.
- Keeps the Theme ramp (Red → Yellow → Green → Blue → White/Black) fixed; Invert now only affects a selected custom palette, not Theme.

# 0.3.14-2

Personal 0.3.14; source `a034d6889ca286966b8643afa97db2197742f786`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

- Fixes Average Glucose showing 4 confusing color points (Point 2/3 did nothing meaningful) when a custom palette (Blue/Orange, Viridis, Cividis) is selected. Now shows just Low/High, matching the other metrics; the Theme palette still shows all 4 points since its color bands are real.

# 0.3.14-1

Personal 0.3.14; source `ed81d59ecf5fc04b8c50da4c3ff4172ba7339a11`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

- Version bump only (0.3.13 → 0.3.14) so Home Assistant shows this as an update; no functional changes since 0.3.13-10. Replaces the earlier 3.14.0-1 build, which used the wrong version scheme.

# 0.3.13-10

Personal 0.3.13; source `e3817dc4d2ce5fd9e5cdf58b92bfd1722b77cf82`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

- Removes the redundant "Reset focus window" button (the main Reset already covers it).
- Fixes the Dim % input snapping back to its old value while typing, so it can't be cleared to type a new number; it now shows an invalid message like the other fields instead.
- Adds the same color palette choices (Theme, Blue/Orange, Viridis, Cividis) to Average Glucose as the other metrics.
- Renames the average glucose boundary controls from "Very low/Low/High/Very high" to neutral "Point 1-4" labels with a color swatch, so changing them isn't mistaken for changing glucose targets.
- Adds an Invert control to reverse the direction of any metric's color scale, including Average Glucose.

# 0.3.13-9

Personal 0.3.13; source `3ea1b10a641e848eaf150a90af644bb37849a524`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

- Fixes the "Reset" buttons losing their descriptive accessible name (screen readers again announce, e.g., "Reset TDD color range to automatic").
- Fixes non-glucose color slider accessible names reading "Min color color value" instead of "minimum color value".
- Fixes the default (non-Advanced) scale label for non-glucose metrics using an inconsistent lowercase transform.
- Strict review pass for upstream publication: reconfirmed prior code-review feedback (SyncedPref-based storage, dark-mode heatmap colors, consolidated slider component, no new svelte-check diagnostics) is still satisfied.

# 0.3.13-8

Personal 0.3.13; source `97407a921f02b4806fc5297f6ee3c5c8321a414e`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

- Fixes the focus-window slider grabbing the color-range handle even when the two are far apart.
- Removes the Blue/Green/Yellow/Red multicolor palette option.
- Renames the "Auto" button to "Reset".
- Fixes the average glucose focus window always excluding the highest values, even at maximum.
- Aligns the average glucose control layout with the other metrics' card style.
- Fixes the average glucose default (non-Advanced) scale showing mg/dL numbers mislabeled with the mmol/L unit.

# 0.3.13-7

Personal 0.3.13; source `cb14cf97b7edaab935bab0867bf7b1a398d242d1`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

- Fixes the Year Overview runtime error `cellSize is not defined` caused by the extra mobile swipe-area rectangle.
- Keeps the wider horizontally scrollable heatmap behavior from 0.3.13-6.

# 0.3.13-6

Personal 0.3.13; source `ecf1d759ea464a8bcb8e7ec9cb47d225b0582937`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

- Puts color-range handles above focus-window handles, so overlapping handles grab the color range first.
- Makes the Blue / Green / Yellow / Red palette actually use all four colors for the scale and cells.
- Removes the month jump buttons above each year now that horizontal scrolling is improved.
- Adds a larger transparent swipe area below week numbers for easier mobile horizontal scrolling.
- Verified with the Docker-style production web build using the HA Node memory setting.

# 0.3.13-5

Personal 0.3.13; source `9e25fbf584ac8c03cb14c6f7331d82845f638b00`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

- Reuses the preferred Time in Range control layout for Bolus, Basal, TDD and Carbs.
- Shows color palette choices as larger round swatches instead of small text-heavy buttons.
- Reduces palette presets to Theme plus four contrast options: Blue/Orange, Viridis, Cividis and Blue-Green-Yellow-Red.
- Color choices remain saved per metric, so changing TDD does not change Bolus, Basal, TIR or Carbs.
- Verified with the Docker-style production web build using the HA Node memory setting.

# 0.3.13-4

Personal 0.3.13; source `967bb0c055715615c49b99933b57617a97999a1e`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

- Fixes the HA install failure caused by an extra closing tag in the Year Overview floating controls panel.
- Verified with full local API/client generation plus bridge, bot and app production web builds using the HA Docker Node memory setting.

# 0.3.13-3

Personal 0.3.13; source `3fa9bb08c0457ba77c89a4e26480107670020139`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

- Replaces the minimize behavior with a `Float` / `Dock` toggle: inline above the graphs by default, or fixed in the top-right corner while scrolling.
- Keeps the scale panel at the same compact width in both modes.
- Widens the mobile heatmap canvas so the year can scroll past September through the final months.

# 0.3.13-2

Personal 0.3.13; source `86e4ff320083b98a82b5322b5da5e228dfb92ce9`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

- Adds mobile month quick-scroll pills (Jan–Dec) to instantly jump to any month.
- Adds smooth horizontal drag and touch panning across the entire heatmap area.

# 0.3.13-1

Personal 0.3.13; source `f216ef6274985dbbdcb01f5a56df5cb1c6c042f3`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

- Makes the Year Overview scale and focus box floating in the top right corner so it follows as you scroll through all years.
- Adds a minimize button to collapse the box into a single compact pill button.

# 0.3.12-9

Personal 0.3.12; source `46419ef2b405d39777184c5f14ea428fcb7a5736`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

- Fixes runtime error `activeTab is not defined` on the Basal metric tab.

# 0.3.12-8

Personal 0.3.12; source `33a4a5ef979178527547c849f6be461af5636e21`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

- Fixes runtime error `metricKey is not defined` when enabling Advanced settings.

# 0.3.12-7

Personal 0.3.12; source `2523ec0af703b6b3525df45f4ad7cdf5bcf5c8dc`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

- Fixed compact bar width (identical in default and advanced mode, without stretching).
- Positioned all inputs cleanly underneath the slider bar.
- Implemented 6 distinct UI design variants across metrics (Avg Glucose, TIR, Bolus, Basal, TDD, Carbs) for visual comparison.

# 0.3.12-6

Personal 0.3.12; source `02ea5800a1b8c70ad96b3e59139c71bce5bfb759`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

- Responsive side-by-side layout: on wide screens/containers, inputs and controls sit beside the slider to save vertical space.
- Per-metric color palettes: color choices for TIR, Bolus, Basal, TDD, and Carbs are now saved independently per metric.

# 0.3.12-5

Personal 0.3.12; source `04cda4238a244519b668271a0110d2b3d3d93325`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

- Adds an "Advanced settings" toggle to show or hide custom focus lines and color thresholds.
- When toggled off, display defaults are used; custom values are remembered when toggled back on.
- Adds custom out-of-band transparency percentage input (0–100%, default 90%).
- Adds alternative color palette presets for non-glucose metrics (Cool Blue/Hot Red, Teal/Amber, Indigo/Rose, etc.).
- All strings in English for localization support.

# 0.3.12-4

Personal 0.3.12; source `006bfccb7971f3f01120393304339d44a2b9d949`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

- Separates color scaling bullets from 90% out-of-band transparency focus lines on all Year Overview metrics.
- All pages now have both the color scale adjustment and the freely movable focus lines with input fields.

# 0.3.12-3

Personal 0.3.12; source `e697ad656d02743f95bef0292cf484951020704c`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

- Adds movable focus lines with 90% out-of-band transparency across all Year Overview metrics (Avg Glucose, TIR, Bolus, Basal, TDD, Carbs).
- Allows adjusting line values via input fields; on Avg Glucose, lines slide freely across the entire range independently of the 4 color threshold dots.

# 0.3.12-2

Personal 0.3.12; source `d2c03ffde8ec90afef1f62c9d516ec4e4d085b02`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

- Restores the original Year Overview heatmap implementation by reverting upstream PR #1315 (`17128d045`).
- Maintains all Daily base features and Google Health connector improvements.

# 0.3.12-1

Personal 0.3.12; source `c4103ba07365947d65adb410bba2c405c8a45287`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

- Includes Google Health PR review follow-up `22e4a759f`: omitted OAuth scopes now match the actual authorization request; explicit partial consent remains authoritative.
- A configured but disconnected Google Health source remains visible as Offline. The overview no longer shows a blank source card after filtering Google entries.
- Database recovery policy: only when the initial staging migration is not registered, pre-existing Google reconciliation staging tables are transactionally replaced with a warning. Only temporary import administration is discarded; native health histories and connector settings/credentials are unchanged. Unexpected external dependencies stop and roll back recovery instead of being removed. Normal upgrades with registered migrations do not reset staging.
- Verified locally with 28 Google Health API tests, 59 connector tests, 6 real PostgreSQL tests, 11 Chromium source/overview tests and API/client generation. Live Google-account acceptance of this delivery still requires manual testing.
- Back up before updating, then check **Refresh inventory**, save the desired selection and run **Sync now**. Confirm steps, heart rate, weight and sleep remain present and continue updating. No disconnect, purge or reset is needed. If you deliberately test disconnect/reconnect, imported data should remain and the source should show Offline until reconnected.
- Uses delivery `0.3.12-1` rather than `0.3.11-10`; app identity, approved Daily base and wrapper version remain unchanged.

# 0.3.11-9

Personal 0.3.11; source `9e03adcce0dee3bc69b666df3b2b181676b1a854`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

- Saving Google Health import settings no longer clears an existing operational sync error or marks a failed connector healthy.
- Refresh inventory now recovers once from a rejected access token, saves rotated credentials, and retries the inventory. Reconnection is requested only when the renewed token is also rejected or the refresh session is revoked.
- Temporary Google failures and cancellation preserve the connection. No import, reconciliation, database schema or account-binding changes are required for this update.
- Verified with 26 Google Health API regression tests, including both reproduced review findings and recovery/error paths.
- After backing up and updating Personal, use **Refresh inventory**, save your desired selection, then **Sync now**. Confirm counts and imported history remain correct. A pre-existing sync error should remain after saving settings and clear only after a successful connection or sync. Do not revoke credentials or delete data to induce a failure; rejected-token cases are covered by automated tests.

# 0.3.11-8

Personal 0.3.11; source `b2a875e3a64dcf595a844d415116c373be2d4590`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

- Repairs Google Health staging migration discovery, which could leave imports failing with `internal_sync` even when inventory found data.
- Preserves history for empty or invalid result pages, batches staged identifiers, and adds tenant isolation and abandoned-run cleanup.
- Reloads saved credentials after waiting for another sync and restores the explicit-purge watermark reset.
- Verified with connector/API tests and real PostgreSQL reconciliation tests. Live Google account imports still need operator testing.
- After backing up and updating Personal, use Google Health **Sync now**. Do not disconnect, purge imported data, or reset the app to apply this fix.

# 0.3.11-7

Personal 0.3.11; source `5607320166f272261756aa3a919122272216c0ed`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

# 0.3.11-6

Personal 0.3.11; source `7db1906737ea57736e03975a1c8e29ba18485b46`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`.

# 0.3.11-5

Personal 0.3.11; source `1d295abe81ab0b3894d8eaa8ce26e95025498315`; Daily base `d9e1430975c7a05967cba66374392f75f08c858f`.

- Keeps Google Health inventory categories open or closed as selected while the page refreshes import status.
- Includes a browser regression test for category expansion state during two-second polling.

# 0.3.11-4

Personal 0.3.11; source `46496c3a10e25968fef880ba8ae6b23cbc599ac8`; Daily base `d9e1430975c7a05967cba66374392f75f08c858f`.

- Includes the latest Nightscout PR review fixes for Google Health.
- Prevents a queued manual import from being dropped when scheduled progress reporting runs at the same time.
- Also includes the purge watermark reset, partial-consent checkpoint protection, preview-timeout handling, and restored upstream logging configuration.
- Use this delivery for practical Home Assistant testing of the current PR candidate.

# 0.3.11-3

Personal 0.3.11; source `a17401128ff2a07559339424eee015b811960d96`; Daily base `d9e1430975c7a05967cba66374392f75f08c858f`.

- Removes the Google Health import diagnostics history and JSON export after the connector's import, error and progress behavior was covered by automated tests.
- Keeps import progress, technical error codes and server logs available while removing the extra in-memory event collection.

# 0.3.11-2

Personal 0.3.11; source `d0ca6753a8fa9fcded1f100c632749eb210bd84e`; Daily base `d9e1430975c7a05967cba66374392f75f08c858f`.

- Pins this Home Assistant candidate to the reviewed Google Health source branch after merging current upstream main.
- Removes Personal-only workflows, metadata and unrelated Year Overview changes from the upstream review contribution.
- Keeps Google record identities stable, retains current consent errors over historic successful runs, and uses pnpm 11.5.0 for the upstream web lockfile.
- Test this update on a backed-up Personal instance before considering the upstream pull request.

# 0.3.11-1

Personal 0.3.11; source `bccd0a87b015b9aafdbd5990996b11e348abd699`; Daily base `d9e1430975c7a05967cba66374392f75f08c858f`.

- Fixes `invalid_google_filter` in sleep inventory and import by using Google's supported session end-time filter.
- Uses matching end-time boundaries for local filtering and reconciliation, preserving overnight stages and sessions outside the requested window.
- Adds regression coverage for pagination, boundary nights, repeated imports and source/tenant isolation.
- After updating: Refresh inventory, select Sleep sessions and stages, then Save selection and import. No reconnect or data deletion is needed.

# 0.3.10-1

Personal 0.3.10; source `a5e575b6a72d0520e96d9d7192ec32abb17a8908`; Daily base `d9e1430975c7a05967cba66374392f75f08c858f`.

- Fixes Google Health sync failing after successful data writes at `watermark_save` when a previous watermark exists.
- Fixes the same invalid date-parser options when scheduled sync resumes from a saved watermark.
- Tests repeat imports, UTC/offset normalization and preservation of newer watermarks during old backfills.
- No Google reconnect or deletion of imported data is needed. Run Sync now after updating.

# 0.3.9-1

Personal 0.3.9; source `268393306c6d9f0ef2ec2157d4418da0bca2a448`; Daily base `d9e1430975c7a05967cba66374392f75f08c858f`.

- Refreshes Google Health sync progress every two seconds while its settings page is open.
- Adds in-app Import diagnostics with bounded run history, native write counts, timestamps, structured errors and JSON export.
- Fixes the reproduced 0.3.8 sleep-session primary-key regression during reimport.
- Restores API console logging when OpenTelemetry is disabled in HA.
- No reconnect or data deletion is required for this update. Real Google-account import success still requires runtime verification.

# 0.3.8-1

Personal 0.3.8; source `346cb775bb4bb577727aee42050b0a93cbe1ec0a`; Daily base `d9e1430975c7a05967cba66374392f75f08c858f`.

# 0.3.7-1

Personal 0.3.7; source `a3501f25db98543836c330543efb4e0464c3d67e`; Daily base `d9e1430975c7a05967cba66374392f75f08c858f`.

# 0.3.6-2

Personal 0.3.6; source `727ff0c7b206250bbf66f5da9697c4a2360ced2e`; Daily base `d9e1430975c7a05967cba66374392f75f08c858f`.

# 0.3.6-1

Personal 0.3.6; source `e302b6f38950bd326e2aec035f48cf3e792c9611`; Daily base `d9e1430975c7a05967cba66374392f75f08c858f`.

# 0.3.5-10

Personal 0.3.5; source `057b0cb9aebd93eb56c74343048ef68be63688bd`; Daily base `d9e1430975c7a05967cba66374392f75f08c858f`.

# 0.3.5-9

Personal 0.3.5; source `8d0aa9f3c07b662d02226f0c0cc560a34272d66d`; Daily base `d9e1430975c7a05967cba66374392f75f08c858f`.

# 0.3.5-8

Personal 0.3.5; source `51bc65c936d0ace38d9f3acb4e13f59b284ff2bb`; Daily base `d9e1430975c7a05967cba66374392f75f08c858f`.

# 0.3.5-7

Personal 0.3.5; source `9952cc0f5d11eef755f2de37fdc025cf9a60f7c8`; Daily base `d9e1430975c7a05967cba66374392f75f08c858f`.

# 0.3.5-6

Personal 0.3.5; source `21ebb5b7bb54f18991e8f4c9308d5a4a5a01167a`; Daily base `d9e1430975c7a05967cba66374392f75f08c858f`.

# 0.3.5-5

Personal 0.3.5; source `b4c0284bcf2e6d46de6e609d2a3bbaf7823b2006`; Daily base `d9e1430975c7a05967cba66374392f75f08c858f`.

# 0.3.5-4

Personal 0.3.5; source `d13f8d37649c83f62d43198b20c17fb78191fdbd`; Daily base `d9e1430975c7a05967cba66374392f75f08c858f`.

# 0.3.5-3

Personal 0.3.5; source `f55492ab66b267895de249aacd1192c917f89177`; Daily base `d9e1430975c7a05967cba66374392f75f08c858f`.

# 0.3.5-2

Personal 0.3.5; source `99d104eaea2132b716c59e028da1aa73518a4320`; Daily base `d9e1430975c7a05967cba66374392f75f08c858f`.

# 0.3.5-1

Personal 0.3.5; source `5bd54c59d03e4a35624daff27e76063972f20335`; Daily base `d9e1430975c7a05967cba66374392f75f08c858f`.

# 0.3.3-1

Year Overview review fixes for nightscout/nocturne#1273; source `7d85408af96d32f9a5f462c62b69edfc104ace44`.

- Saves color selections through the existing user-preferences backend and shared appearance.
- Uses one accessible control for ranges and glucose color boundaries.
- Transitions from 4 to 3 mmol/L and stays solid below 3: black in light mode, white in dark mode.
- Prints on white report cards with the black endpoint and the active scale.
- Fixes input types, metric switching and slider step performance.

# 0.3.2-1

Private Year Overview-only preview of nightscout/nocturne#1273; source `309c0b23e64c76d222a481919092c9ca3b24ad2a`; Daily runtime base `ea695ba37ea82feaec607ad1ab81ecf3113a2fd7`.

- Adds remembered minimum and maximum color-focus ranges for Time in Range, bolus, basal, TDD and carbohydrates.
- Adds four adjustable average-glucose color boundaries while preserving glucose target and Time in Range calculations.
- Keeps the exceptionally-low heatmap stop black and the following low stop blue so adjacent ranges remain distinct.
- Includes keyboard, pointer, touch, numeric-input, print and unavailable-storage behavior.
- Does not include the separate Google Health connector contribution.

# 0.3.1-2

Private Google Health cleanup preview; source `e56b74e2e48ddd1fad04d0cc909a65d80c5b49d4`; Daily base `01644942c08ef27b4915763560a58aa1905951fc`.

- Removes the temporary Google Health connection and reading tables, entities and migration.
- Stores configuration, secrets and health state only through the connector framework.
- Imports directly into Nocturne step, heart-rate, weight and sleep histories.
- Routes manual, queued and scheduled imports through the connector lifecycle.
- Excludes the separate Year Overview color work and unrelated UI fixes.

# 0.3.1-1

Private preview of the separated Google Health connector-framework work; source `26f945645379681c9911b6b2963fe35b6c8a79de`; Daily base `01644942c08ef27b4915763560a58aa1905951fc`.

- Uses Nocturne's connector HTTP and token lifecycle infrastructure.
- Does not include the Year Overview color controls; those are reviewed separately upstream.
- Existing Personal Google Health configuration is not migrated; disconnect and reconnect before testing.

# 0.3.0-1

Preview of upstream PR nightscout/nocturne#1240; source `88cecca7862d9fafa2403b5542f10a50584ce4ef`; Daily base `01644942c08ef27b4915763560a58aa1905951fc`.

- Uses the generic Google Health API, callback and database schema intended for new upstream installations.
- Existing Personal Google Health configuration is not migrated; reconnect Google before testing.
- Includes the configurable Year Overview color ranges from the upstream contribution.

# 0.2.12-1

Personal 0.2.12; source `6a7ef6c8600acf5864b7ff743060fa724ad9dd5e`; Daily base `01644942c08ef27b4915763560a58aa1905951fc`.

# 0.2.11-1

Personal 0.2.11; source `c1f3e955d1686e276ee99e00efb84d0c47521113`; Daily base `01644942c08ef27b4915763560a58aa1905951fc`.

# 0.2.10-1

Personal 0.2.10; source `6411f3a7606349315ac7a541805e816a2796a4f7`; Daily base `543bbff8552d69c2ec39e2e4585c9c839e420f5d`.

# 0.2.9-1

Personal 0.2.9; source `c58d1f5bd88ff0e7669b662b2f6d1abc8d1dc4cf`; Daily base `543bbff8552d69c2ec39e2e4585c9c839e420f5d`.

- Four adjustable average-glucose color boundaries, with numeric inputs, unit conversion and remembered settings. Existing two-bound metric controls remain available.
- Google Health under Server Connectors, with discovered data types, supported destinations, selected imports and a history start date.
- Accurate Google Health import status, English diagnostics and extended historical pagination with runaway protection.
- Obsolete Personal navigation and medication/GLP-1 interface removed.
- Retains seven named local-build log phases; Home Assistant's native update percentage can still remain at 0% during the build.

# 0.2.8-3

The update dialog now explains Supervisor's 0% limitation, and the local build log reports seven named progress phases.

# 0.2.8-2

Personal 0.2.8; source `0a3c3b128a3a76b79ee59b822c1fd3f8624fce7e`; Daily base `543bbff8552d69c2ec39e2e4585c9c839e420f5d`.

# 0.2.8-1

Personal 0.2.8; source `5612840a8f7b00f830b3ba1151fb8ab168e318de`; Daily base `543bbff8552d69c2ec39e2e4585c9c839e420f5d`.

# 0.2.7-1

Personal 0.2.7; source `5a041c0a3a4cac4278c794a8b685a40514dea0ac`; Daily base `543bbff8552d69c2ec39e2e4585c9c839e420f5d`.

# 0.2.6-1

Personal 0.2.6; source `4d9b4c9e434b0951a01a2f5409503c03f838f0ec`; Daily base `ad5dee272c0d939b7b9e5f14f631c3434706b10e`.

# 0.2.5-1

Personal 0.2.5; source `8ee2e8ae87b237ba16f17e6924cc635ec932baee`; Daily base `ad5dee272c0d939b7b9e5f14f631c3434706b10e`.

# 0.2.4-1

Personal 0.2.4; source `8767174644e028e8fe97a3c09b9448f9c537c759`; Daily base `ad5dee272c0d939b7b9e5f14f631c3434706b10e`.

# 0.2.3-1

Personal 0.2.3; source `496223c865d76427785f2e49dc955d1262050303`; Daily base `ad5dee272c0d939b7b9e5f14f631c3434706b10e`.

# 0.2.2-1

Personal 0.2.2; source `dbd72d8cbc6ace66599bc29b4d6c6d5ffad40718`; Daily base `ad5dee272c0d939b7b9e5f14f631c3434706b10e`.

# 0.2.1-1

Personal 0.2.1; source `b35c4952f6718c82d1207a3cb7fad9bfddfb851c`; Daily base `ad5dee272c0d939b7b9e5f14f631c3434706b10e`.

# 0.2.0-3

Personal 0.2.0; source `033a77fb38853c7975b4c6e511d458540fc59157`; Daily base `ad5dee272c0d939b7b9e5f14f631c3434706b10e`.

## 0.2.0-2

- Wrapper 0.1.6 forwards external OAuth Bearer tokens in guarded native mode and routes authenticated v4 requests directly to the API.
- Browser session routing, TLS, tenant checks, Basic gateway mode, cookie isolation and internal-header filtering remain enforced.
- Upstream pins, database schema, stored accounts and keys are unchanged. Existing Home Assistant OAuth clients can retry after updating this app.

# 0.2.0-1

Personal 0.2.0; source `752ebf65017a41508b76346090778d8965c87f9a`; Daily base `3b7514591f854f4794deeeb75d43e33d979d1ee4`.

- Google Health OAuth, selectable steps/heart rate/weight, periodic read-only import and history.
- Encrypted credentials, partial-consent handling, disconnect and explicit import deletion.
- Separate medication log: actual/skipped, explicit units, notes, edits and deletion; no dosing advice.
- New Personal database migrations; take a cold Personal backup before updating.
- Real Google client/consent remains a user setup/test. Official and Latest are unchanged.

# 0.1.0-1

Personal 0.1.0; source `fdf290aab0e5ab5eccedfb15026622a94a0f2d56`; Daily base `3b7514591f854f4794deeeb75d43e33d979d1ee4`.
