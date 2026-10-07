## 0.3.25-c32

- Guided standalone TOTP reset button: selected owner, backup/account confirmation, one-use request, and clear reenrollment steps. No new recovery code or changes to passkeys/data; existing login sessions stay signed in.
- Shared wrapper 0.1.13: opt-in HA maintenance terminal, CLI and recovery wizard across all six channels. Disabled by default; separate password required.
- Existing identities, ports, source pins and data remain intact. Owner recovery accepts only reviewed source commits.

## 0.3.25-c31

- Test C now builds Nocturne main `0198225` + [PR #2007](https://github.com/nightscout/nocturne/pull/2007) (clock face units and time format) from pinned head `e17d9ee`. Google Health development moves off Test C; Test A keeps Google Health PR #1293.
- Back up Test C before updating. Existing data, accounts and cookies are kept; Google Health connector data stays in the database but the connector is not part of this build.

## 0.3.25-c30

- Refresh the pinned Google Health source and continue running its complete connector unit suite in CI, including the bounded-memory regression.

## 0.3.25-c29

- Google Health heart-rate backfills now aggregate incrementally per UTC minute, bounding retained memory for large history windows.
- Test C runs the connector unit tests, including the paginated memory regression, in the HA CI image pipeline before building the candidate image.

## 0.3.25-c28

- Add shared read-only `nocturne-ha` diagnostics.
- Use the setup-independent API version endpoint in fresh-instance smoke tests.

## 0.3.25-c27

- Wrapper 0.1.11 forwards the exact Nocturne source commit and actual API build date to Nocturne.
- Source builds record their own publish time; prebuilt API images retain their embedded build date.
- Source pins and stored data remain unchanged.

## 0.3.25-c26

- Shared wrapper 0.1.10: explicit `skip_gateway_check`, default false, only effective with `gateway_auth: false`.
- Keep Nocturne permissions, TLS, hostname checks, existing data and keys unchanged; display skipped checks prominently.
- Test A now uses the same visible settings. Existing `verify_native_auth: false`: set `skip_gateway_check: true` in app Configuration, remove the old YAML key, save and restart. The canonical option takes precedence; its new default may restore the private check until migrated.

## 0.3.25-c25

- Preserve the configured external HTTPS port in BASE_DOMAIN for API and web URL generation.
- Keep internal listeners, hostname checks, data and upstream source pins unchanged.

# 0.3.25-c24

Google Health-ontwikkelbranch bijgewerkt met upstream main `8635bd5`.
Eigen migratie-IDs blijven behouden in het nieuwe migratieproject.
Connector-resetqueries zijn expliciet beperkt tot de huidige tenant.
Google Health-scherm en tests aangepast aan de nieuwe UI-componenten en API-types.
Deze pakketupdate wist geen gegevens en behoudt de Test C-identiteit en opties.

# 0.3.25-c23

De rode **Delete imported Google Health data**-knop na Disconnect wist nu ook de Google Health-backfillcursor en de voltooidmelding. Broncommit `0b42fca`.

# 0.3.25-c22

Corrigeert de koppeling voor de rode **Data verwijderen**-knop in Google Health. Deze actie wist nu daadwerkelijk de historische-importcursor en de melding dat de geschiedenis compleet is. Broncommit `03462fb`.

# 0.3.25-c21

Bij **Data verwijderen** voor Google Health worden nu ook de opgeslagen historische-importcursor en de melding dat de geschiedenis compleet is gewist. De volgende bewust gestarte import kan dezelfde periode daardoor opnieuw ophalen. Broncommit `ce86fd447`.

# 0.3.25-c20

Google Health vernieuwt nu bij iedere sync eerst vandaag en importeert daarna één oudere kalendermaand. Een mislukte of te grote maand wordt voor de volgende poging automatisch gehalveerd tot uiteindelijk minimaal één dag. Het connectoroverzicht toont blijvend tot welke datum de historische import is gevorderd. Broncommit `7428f5f6b`, nog niet naar PR #1293 gestuurd.

# 0.3.25-c19

Persoonlijke pre-PR testbuild: Google Health hartslagdata wordt per UTC-minuut samengevoegd tot één gemiddelde vóór opslag, en de import haalt voortaan één kalenderdag per keer op (vandaag eerst, dan stap voor stap terug), zodat een grote historische import niet meer op de 3-minuten synctimeout loopt. Broncommit `150df457a`, nog niet naar PR #1293 gestuurd.

# 0.3.25-c18

Test C volgt nu actuele Nocturne main (`87090087e`) met uitsluitend de Google Health-connector uit PR #1293 (`418d810a2`).

# 0.3.25-c17

Zoomfunctie verwijderd uit Test C; de eHbA1c-grafiek gebruikt weer de stabiele oorspronkelijke rendering. Zoom wordt later in een aparte PR opgepakt. Broncommit `796fbb9e7e46a6da136aa706c7057bd689b7d903`.

# 0.3.25-c16

Zoomselecties worden nu gevalideerd en begrensd, zodat een ongeldige selectie de eHbA1c-grafiek niet meer leeg maakt. Broncommit `0c88e489780bcbc482efd708f4d24a5436a6db05`.

# 0.3.25-c15

Svelte-buildfout in c14 opgelost: de LineChart-opening wordt correct gesloten vóór de zoom-snippets. Broncommit `eab66c16bad758a7201641c877ed06672b76eb22`.

# 0.3.25-c14

Tijdsrange-zoom toegevoegd aan de eHbA1c-grafiek met bestaande Nocturne brush-interactie en resetknop. Broncommit `c6f9cd0cf3eaf1ced7f1fcf9c8dd0cc28ec87cc4`.

# 0.3.25-c13

De eHbA1c-lijn blijft visueel doorlopen over lab-only datums; de tooltip blijft die datum als alleen labresultaat tonen. Broncommit `dbc4154d0ec1a761ea898e01f49112be2dc351dc`.

# 0.3.25-c12

Meerdere labresultaten op dezelfde dag worden nu allemaal als eigen rij met eigen waarde in de tooltip getoond. Broncommit `0d6ccb0fc0f78cb8871e2bcea77542ef3a0e2ef4`.

# 0.3.25-c11

Robuuste PR #1361-fix: lab-only datums worden opgenomen in het tooltip x-domein zonder een valse eHbA1c-waarde te tekenen. Broncommit `681631d445efc7e344fd253227fe0be590dfcce3`.

# 0.3.25-c10

Google Health vernieuwt nu bij iedere sync eerst vandaag en importeert daarna één oudere kalendermaand. Een mislukte of te grote maand wordt voor de volgende poging automatisch gehalveerd tot uiteindelijk minimaal één dag. Het connectoroverzicht toont blijvend tot welke datum de historische import is gevorderd. Broncommit `7428f5f6b`, nog niet naar PR #1293 gestuurd.

Documentatie en statusmetadata gecorrigeerd: Test C is Nocturne Daily/main met PR #1361, niet de Personal 0.3.25 Google Health-build.

# 0.3.25-c9

Laatste geldige controle: officiële Daily/main-runtimebasis met de broncode van PR #1361 erbovenop. Broncommit `79016d9e15bd35cab48e7412018d037c9fe01211`.

# 0.3.25-c8

Testbuild van PR #1361 voor de laatste controle van issue #1360. Broncommit `79016d9e15bd35cab48e7412018d037c9fe01211`.

# 0.3.25-c7

Lijn- en marker-hover koppelen labresultaten nu op kalenderdag, zodat beide routes dezelfde gecombineerde tooltip tonen. Broncommit `dfeb70646f8c052b5c83d0c63e2078adadcb48dc`.

# 0.3.25-c6

De eHbA1c-tooltip gebruikt nu altijd de canonieke waarde van de geselecteerde datum. De verticale muispositie kan dezelfde dag niet meer verschillende eHbA1c-waarden tonen. Broncommit `e237d1530621671aa81198dbe0835fce938d6b8a`.

# 0.3.25-c4

Labmarker vangt geen muis meer af bij benadering van boven; eHbA1c en labresultaat staan uitgelijnd in dezelfde tooltipweergave. Broncommit `ca3b0fb54d2b93132cadc329e00a245306c5d866`.

# 0.3.25-c3

Tooltipfix gepubliceerd: datum zonder tijd, eHbA1c en labresultaat samen zichtbaar, labnotitie in de popup en geen dubbele rechter SVG-tooltip. Broncommit `851ef00fb2a75725798f0c80a742c7c79d551e74`.

# 0.3.25-c2

Klikbare broninformatie voor issue #1360, het testscenario en actuele systeemresources op de Home Assistant-statuspagina.

# 0.3.25-c1

Test C uses the same Personal software as Test B, pinned to the eHbA1c lab-result tooltip fix for issue #1360 at commit `9b3a0977518e60837fd0b5bd6f3fae7e08f59218`. Temporary isolated instance for manual verification only; Test B remains available for comparison.
