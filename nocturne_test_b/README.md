# Nocturne Test B

Pakket **0.3.25-b30** bouwt actuele Nocturne main met alleen de A1c-voorkeurenfix uit [PR #1977](https://github.com/nightscout/nocturne/pull/1977), inclusief de herstelde vertalingen en keuzelijsten voor alle elf beschikbare talen. Deze versie gebruikt PR-commit `bf5c517e3` op main `b515516d4`, na het oplossen van de mergeconflicten. De exacte bron en checksum staan in `upstream-test-b.json`.

Kies A1c/HbA1c en %/mmol/mol op één plek: **Settings → Appearance → Units & Formats**. Geschatte waarden blijven eA1c/eHbA1c; labmetingen blijven A1c/HbA1c. GMI blijft een aparte maat. [Installatie en teststappen](DOCS.md).

De veldnamen en eenheidsuitleg volgen nu ook de gekozen naam in alle talen. Als een periode te weinig metingen bevat om de A1c-streefwaarde te leveren, laat de samenvatting die streefwaarde weg in plaats van `Target: <–` te tonen.

Test B behoudt zijn slug, poort 8452, opties, data en cookie-namespace. De eerdere Google Health PR #1293-build wordt vervangen.
