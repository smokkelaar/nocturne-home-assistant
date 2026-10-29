# Testoverzicht

Wat staat er op elke Nocturne-app in Home Assistant, wat moet Sebastiaan daar nog bekijken, en hoe.

**Bijgewerkt:** 29 oktober 2026, 00:40 (NL-tijd)

Vernieuw eerst de store in HA: Instellingen → Apps → Store → ⋮ → Controleren op updates.

## Spelregels

- Een nieuwe feature test je op Test A, B of C tegen een **schone nightscout main met alleen die ene feature erbij**, tenzij expliciet anders is afgesproken.
- **Personal** is de verzamelbak van eigen wensen en eerste probeersels. Het is geen testbasis voor features die naar nightscout/nocturne gaan.
- Er gaat nooit iets naar nightscout/nocturne zonder expliciete vraag van Sebastiaan.
- Wie iets op een testinstantie zet, of hoort dat iets getest is, werkt dit bestand bij.

## Nu te doen voor Sebastiaan

| # | Waar | Wat | Status |
|---|---|---|---|
| 1 | Test C (8453) | Helpboek op elke pagina controleren | Klaar om te testen in 1.0.102701: help-icoon terug (testbuild #89 = #75 + #88) |
| 3 | Test B (8452) | Interactieve grafiekvoorbeelden in de help (#78) en het help-icoon (#88) | Help-icoon hersteld via [#88](https://github.com/smokkelaar/nocturne-personal/pull/88), bovenop Personal 0.3.43 (met #78). Klaar om te testen in 1.0.102701 |
| 4 | Personal (8450) | Jaaroverzicht: buitenste bolletjes verplaatsen; eHbA1c-tooltip; help | Getest op 0.3.43 (27 okt): extra decimalen goed, bolletjes en tooltip nog niet goed, help-icoon ontbrak. Personal 0.3.45 bevat de fixes van [#82](https://github.com/smokkelaar/nocturne-personal/pull/82) en het help-icoon van [#88](https://github.com/smokkelaar/nocturne-personal/pull/88). Getest op 0.3.45 (28 okt): kleuren werken. Dim op aparte regel, presets, Mirror en Swap weg, + in de kleurenrij, verloop tussen de kleuren: aangepast in [#92](https://github.com/smokkelaar/nocturne-personal/pull/92) (0.3.46, gemerged 29 okt, store-build volgt) |

## Voorbereiding voor dinsdag 27 oktober

HA #176 (A), #175 (B) en #172 (C) zijn samengevoegd. [Publicatie en tests](https://github.com/smokkelaar/nocturne-home-assistant/actions/runs/40403185802) zijn geslaagd voor alle drie de kanalen op AMD64 en ARM64, inclusief opstarten, accountherstel, cold restore en upgraden vanaf de vorige versie. Publieke beschikbaarheid en image-labels zijn gecontroleerd. [Storepromotie #177](https://github.com/smokkelaar/nocturne-home-assistant/pull/177) is gemerged.

**Personal, Test A, B en C staan op store-versie 1.0.102701 (28 okt), Latest en Official op 1.0.101201.** Vernieuw de HA-store en update. Alle apps laten nu tenantadressen (`<tenant>.<hostname>:<poort>`) door en controleren bij meer tenants elke tenant apart (alleen de wrapper is gewijzigd). Installatie en werking op de eigen HA zijn vanuit deze sessie niet gecontroleerd; dit overzicht bevestigt de gepubliceerde pakketten.

## Per instantie

### Test A (poort 8451)

- **Store-versie:** 1.0.102701, zelfde bron als 1.0.100501 (#69 + #80 op nightscout main `970031f`, met de herschreven migratiestap). Vernieuw de HA-store en update Test A. De migratie van upstream #2842 is op deze database al klaar.
- **Wrapper (alleen Test A):** tenantadressen `<tenant>.<hostname>:8451` worden doorgelaten; met meer dan één tenant controleert de start elke tenant apart op privétoegang. `skip_gateway_check` hoeft niet meer aan.
- **Bron (nieuw):** [Personal PR #83](https://github.com/smokkelaar/nocturne-personal/pull/83), commit `4500f692ff57feebbe6c8c29315b8a79946b2823`. Testbuild, wordt niet gemerged.
- **Basis:** schone nightscout main `970031f` met alleen [#69](https://github.com/smokkelaar/nocturne-personal/pull/69) (Google Health-instellingen in instantiebeheer) en [#80](https://github.com/smokkelaar/nocturne-personal/pull/80) (reset met begindatum in stukken lezen). Bewust gecombineerd (keuze 27 okt): zonder #69 kan de HA-app Google Health op schone main niet koppelen.
- **Afwijking van schone main:** de migratie `RepairThirtyTwoHexEntryLegacyIds` (upstream #2842) verzamelt de dubbele metingen eerst in een geanalyseerde tijdelijke tabel. De oorspronkelijke query bleef op deze database ruim een uur rekenen zonder iets te schrijven. Uitkomst is gelijk. Losgezet op upstream main in branch `claude/project-thread-o4mhnl-legacy-id-repair` van nocturne-personal, voor een PR naar nightscout/nocturne die Sebastiaan zelf opent.
- **Testen:**
  1. Ga naar Instellingen → Administratie → Reset connector cursors en kies je tenant.
  2. Kies een begindatum van een paar maanden terug (bijvoorbeeld 1 augustus) en start de reset.
  3. Google Health moet nu slagen in plaats van `google_unavailable:heart-rate` te geven. Het kan even duren.
  4. Controleer daarna dat hartslag, stappen en slaap over die periode compleet zijn.
  5. De Google Health-instellingen uit #69 blijven staan na de update.
- **Eerder getest (#69, 1.0.96501, 27 okt):** alles goed behalve de toegang voor tenants, die nu niet te testen is door beperkingen van het testsysteem. Later oppakken.
- **Status:** wacht op build.

**Wacht op een vrije testinstantie:** [Personal PR #81](https://github.com/smokkelaar/nocturne-personal/pull/81), op de resetpagina per connector kiezen wat opnieuw wordt opgehaald. Schone main `970031f` + alleen deze feature, CI groen.

**Wacht ook op een vrije testinstantie (keuze 27 okt):** [Personal PR #84](https://github.com/smokkelaar/nocturne-personal/pull/84), ImageSharp 3.1.12 naar 3.2.0 met de Six Labors community-licentie (`sixlabors.lic`, geldig tot 25 jan 2028). Schone main `970031f` + alleen deze upgrade; bedoeld om later zelf naar nightscout/nocturne te sturen. Test: na de update start de app, en een profielfoto uploaden (PNG, JPEG, WebP) werkt.

### Test B (poort 8452)

- **Store-versie:** 1.0.102701 (28 okt), met het help-icoon.
- **Bron (nieuw):** [Personal PR #88](https://github.com/smokkelaar/nocturne-personal/pull/88), commit `a7959d715baf544f840d4c51b78764a9c609fe4f`.
- **Doel:** het help-icoon linksboven is terug (de merge van #68 had het weggehaald), zodat de interactieve grafiekvoorbeelden van #78 te testen zijn. #88 zet ook ImageSharp op 3.2 met de Six Labors-licentie.
- **Basis:** Personal 0.3.43 (`3b72219`, bevat #78) + alleen #88. Dit is geen schone-main-test voor upstream.
- **Testen:**
  0. Het boekicoontje staat linksboven (desktop) en in de mobiele kop, en opent de help.
  1. Open het helpboek bij AGP, Dagprofiel, Voorspelnauwkeurigheid, CGM-vergelijking, IDP en Slaap.
  2. Controleer het blok Verken de grafiek: knoppen wisselen uitleg, hover en pijltjestoetsen tonen waarden; eenheden en licht/donker thema volgen de instellingen.
  3. Klik in het slaapvoorbeeld op een nacht: je blijft in de help.
  4. Bekijk Snel starten en Problemen oplossen in het Nederlands en Engels; zoek op ontbrekende gegevens.
  5. De voorbeelden gebruiken fictieve gegevens; je eigen gegevens en voorkeuren blijven behouden.
- **Status:** klaar om te testen in 1.0.102701 (28 okt). Eerder (27 okt) geblokkeerd omdat het help-icoon ontbrak.

### Test C (poort 8453)

- **Store-versie:** 1.0.102701 (28 okt), met het help-icoon.
- **Bron (nieuw):** [Personal draft PR #89](https://github.com/smokkelaar/nocturne-personal/pull/89), commit `227e18b7c83e021c94a0eb7431a1c141d4e672e5`: [#75](https://github.com/smokkelaar/nocturne-personal/pull/75) + [#88](https://github.com/smokkelaar/nocturne-personal/pull/88) (help-icoon terug). Testbuild, wordt niet gemerged.
- **Doel:** Nederlandse paginahulp met bovenaan het open blok Wat je ziet en wat het betekent.
- **Basis:** bestaande gecombineerde help-testbuild op Personal 0.3.43, met #70, #72, #77 en #63/#73. Dit is geen geïsoleerde schone-main-test. De bron-PR #75 blijft een testbuild en is niet gemerged.
- **Testen:**
  0. Het boekicoontje staat linksboven (desktop) en in de mobiele kop, en opent de help.
  1. Zet de interfacetaal op Nederlands en open het helpboek op Dashboard, Calendar, Time spans, Clock, Food, Meals, Packing, Alerts en Notifications.
  2. Controleer ook rapporten zoals AGP, Executive summary, Steps, Heart rate en Sleep, plus Therapy, Appearance, Connectors & Apps en een koppeling.
  3. Bovenaan staat Wat je ziet en wat het betekent open; uitleg over kleuren, percentages en drempels moet kloppen met de pagina.
  4. Controleer uitklapblokken en zoek op Health Connect, Garmin, snooze, packing, webhook en Google Health.
  5. Bekijk de teksten in het Nederlands en Engels.
- **Status:** klaar om te testen in 1.0.102701 (28 okt). Eerder (27 okt) geblokkeerd omdat het help-icoon ontbrak.

### Personal (poort 8450)

- **Store-versie:** 1.0.102701 = Personal 0.3.45 (commit `5adf0ca`), Latest-basis nightscout main `3caa43c`. Bevat 0.3.44 (hieronder) en het help-icoon ([#88](https://github.com/smokkelaar/nocturne-personal/pull/88)).
- **Nieuw in 0.3.43:**
  - [#78](https://github.com/smokkelaar/nocturne-personal/pull/78): interactieve grafiekvoorbeelden in de help (AGP, Dagprofiel, Voorspelnauwkeurigheid, CGM-vergelijking, IDP, Slaap).
  - [#79](https://github.com/smokkelaar/nocturne-personal/pull/79): jaaroverzicht, de twee buitenste bolletjes versmallen het kleurbereik (ook glucose); HbA1c met één decimaal extra (6,54% en 50,3 mmol/mol), ook bij lab-invoer.
- **Nieuw in 0.3.44** ([#82](https://github.com/smokkelaar/nocturne-personal/pull/82), gemerged 28 okt, merge `7080e5c`):
  - Jaaroverzicht: kleurbereik los van Dim outside, zoals het oude Personal. De twee buitenste bolletjes op de kleurbalk hebben de eindkleuren en bepalen waar de kleuren beginnen en eindigen. Het dimvenster heeft een eigen schuifbalk erboven en verandert de kleuren niet meer.
  - eHbA1c-tooltip: toont een labwaarde binnen 24 px van het driehoekje (32 px bij touch), ruimer dan de 44 px-richtlijn van WCAG.
  - Build: ImageSharp-melding GHSA-v76p-62qx-wwq2 onderdrukt tot nightscout/nocturne een update levert.
- **Open, wordt 0.3.46** ([#92](https://github.com/smokkelaar/nocturne-personal/pull/92)):
  - De kleuren lopen alleen nog tussen de ingestelde kleuren (eindkleuren en gekleurde grenzen), dus blauw loopt naar groen zonder geel of grijs ertussen.
  - De dim-streepjes staan weer op de kleurbalk, hoger dan de bolletjes. Pak een streepje boven of onder het bolletje als ze op dezelfde plek staan.
  - De standaard kleurschema's zijn weg, en Mirror en Swap ook.
  - De knop + voor een kleurgrens staat in de rij met de kleuren, op de plek waar de nieuwe grens komt.
- **Jaaroverzicht op Test A:** Test A (PR #83) is schone main met alleen Google Health en heeft dus het upstream-jaaroverzicht zonder deze Personal-onderdelen. Dat is verwacht; test het jaaroverzicht hier op Personal.
- **Waarom hier en niet op Test A/B/C:** dit zijn Personal-wensen, en Test A, B en C zijn bezet. De Test B-build van #68 (26 okt) had #79 nog niet; daarom kon je de buitenste kleuren daar niet verplaatsen.
- **Testen:**
  1. (0.3.44) Rapporten → Jaaroverzicht: versleep de buitenste gekleurde bolletjes op de kleurbalk. De kleuren lopen alleen tussen de bolletjes, waarden erbuiten krijgen de eindkleur. Versleep daarna de streepjes op de dunne balk erboven: alleen het dimmen verandert, de kleuren blijven staan. Het bereik onthoudt zich per metriek, en Reset zet alles terug.
  2. Rapporten → eHbA1c: waarden tonen 2 decimalen in % en 1 in mmol/mol. Voer een lab-waarde in met die precisie en controleer de streefwaardecheck.
  2b. (0.3.44) Beweeg de muis tot ruim een halve centimeter naast een lab-driehoekje: de tooltip toont de labwaarde zonder precies te mikken.
  3. Open de help bij AGP en Slaap: het voorbeeld is interactief.
  4. (0.3.46) Jaaroverzicht: zet gekleurde grenzen (bijvoorbeeld blauw, groen, rood, geel). Elk stuk loopt rechtstreeks van de ene kleur naar de volgende. De dim-streepjes staan op dezelfde lijn als de kleuren. De rij kleurschema's, Mirror en Swap zijn weg, en de + staat tussen de kleuren waar de nieuwe grens komt.
- **Status:** getest op 0.3.43 (27 okt). Stap 2 (decimalen) goed. Stap 1 (buitenste bolletjes) werkt niet: niet versleepbaar. Tooltip vraagt nog steeds extreem precies mikken; [#82](https://github.com/smokkelaar/nocturne-personal/pull/82) zat nog niet in deze versie, en de vraag is of 12 px genoeg is (best practices en schermafhankelijkheid bekijken). Stap 3: help-icoon ontbreekt, help niet te openen. Bolletjes en tooltip aangepast in #82 (0.3.44); de help wordt apart uitgezocht. **Nu klaar om te hertesten in 1.0.102701 (Personal 0.3.45), inclusief de help.**

### Latest (poort 8449)

- **Store-versie:** 1.0.101201 = nightscout main `3caa43c`.
- **Doel:** volgt de nightscout main waarop Personal gebouwd is. Niets specifieks te testen.

### Official Release (poort 8448)

- **Store-versie:** 1.0.101201 = officiële release 0.2.7.
- **Doel:** officiële release. Niets te testen.

### Stable en Main (repo nocturne-home-assistant-upstream, poort 8448 en 8449)

- **Store-versie:** 0.2.40801 = nightscout main `971dd4a`.
- **Status:** loopt achter op main. Bijwerken staat op de lijst van de HA-onderhoudsthread.

## Klaar met testen

Hier komt wat je getest en goedgekeurd hebt, met datum.

| Datum | Instantie | Feature | Uitkomst |
|---|---|---|---|
| 26 okt 2026 | Test B (8452) | Personal #68: jaaroverzicht-kleuren | Crasht niet meer, extra kleuren terug. Buitenste kleuren niet verplaatsbaar: opgelost in #79, hertest op Personal 0.3.43 |
| 26 okt 2026 | Test B (8452) | Personal #68: HbA1c | Werkt; tooltip vraagt precieze muis: verruimd in #82 (0.3.44) |
| 27 okt 2026 | Test A (8451) | Personal #69: Google Health via instantiebeheer | Goed, behalve tenanttoegang: nu niet testbaar, later oppakken |
| 27 okt 2026 | Personal (8450) | 0.3.43: HbA1c met extra decimaal | Goed |
| 28 okt 2026 | Test A (8451) | Personal #69: tenants (testa, testa2) en Google Health per tenant | Goed. Google werkt in elke tenant, met één Google-account door de beperkte toegang van de andere accounts. Jaaroverzicht mist nog functionaliteit: in de jaaroverzicht-thread |
| 28 okt 2026 | Test A (8451) | Personal #80: Google Health-reset met begindatum, op #69 | Goed: Google werkt, tenants werken zoals verwacht |
