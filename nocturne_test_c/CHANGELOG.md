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
