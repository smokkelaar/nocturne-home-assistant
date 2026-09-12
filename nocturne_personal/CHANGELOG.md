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
