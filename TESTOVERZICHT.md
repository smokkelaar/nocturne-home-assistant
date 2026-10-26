# Testoverzicht

Wat staat er op elke Nocturne-app in Home Assistant, wat moet Sebastiaan daar nog bekijken, en hoe.

**Bijgewerkt:** 26 oktober 2026, 19:50 (NL-tijd)

Vernieuw eerst de store in HA: Instellingen → Apps → Store → ⋮ → Controleren op updates.

## Spelregels

- Een nieuwe feature test je op Test A, B of C tegen een **schone nightscout main met alleen die ene feature erbij**, tenzij expliciet anders is afgesproken.
- **Personal** is de verzamelbak van eigen wensen en eerste probeersels. Het is geen testbasis voor features die naar nightscout/nocturne gaan.
- Er gaat nooit iets naar nightscout/nocturne zonder expliciete vraag van Sebastiaan.
- Wie iets op een testinstantie zet, of hoort dat iets getest is, werkt dit bestand bij.

## Nu te doen voor Sebastiaan

| # | Waar | Wat | Status |
|---|---|---|---|
| 1 | Test C (8453) | Helpboek op elke pagina controleren | Wacht op merge van [HA #172](https://github.com/smokkelaar/nocturne-home-assistant/pull/172), daarna op jou |
| 2 | Test A (8451) | Google Health instellen via beheer | Wacht op merge van [HA #176](https://github.com/smokkelaar/nocturne-home-assistant/pull/176), daarna op jou |
| 3 | Test B (8452) | Interactieve grafiekvoorbeelden in de help (#78) | Wacht op build via [HA #175](https://github.com/smokkelaar/nocturne-home-assistant/pull/175) |
| 4 | Personal (8450) | Jaaroverzicht-kleuren en HbA1c-precisie (0.3.43) | 0.3.43 wordt gebouwd |

## Per instantie

### Test A (poort 8451)

- **Store-versie:** 1.0.93301, nog met Personal PR [#63](https://github.com/smokkelaar/nocturne-personal/pull/63) op `personal`.
- **Komt eraan:** [HA #176](https://github.com/smokkelaar/nocturne-home-assistant/pull/176) zet Test A op Personal PR [#69](https://github.com/smokkelaar/nocturne-personal/pull/69) `c6a0571`: schone nightscout main `bd59934` met alleen de Google Health OAuth-instellingen in instantiebeheer. Daarmee volgt Test A de spelregel.
- **Testen zodra #176 in de store staat:**
  1. Ga naar Instellingen → Administratie → Integraties → Google Health.
  2. Vul Client ID, Client secret en Callback URL in, zet Enabled aan en kies Save. Het secret moet na opslaan gemaskeerd zijn.
  3. Koppel Google Health zonder herstart en controleer dat er data binnenkomt.
  4. Herstart de app. De instellingen moeten blijven staan.
- **Status:** wacht op merge van #176.

### Test B (poort 8452)

- **Store-versie:** 1.0.91501 met Personal PR [#68](https://github.com/smokkelaar/nocturne-personal/pull/68). Die is achterhaald: #68 zit al in Personal 0.3.42.
- **Komt eraan:** [HA #175](https://github.com/smokkelaar/nocturne-home-assistant/pull/175) zet Test B op Personal PR [#78](https://github.com/smokkelaar/nocturne-personal/pull/78), interactieve grafiekvoorbeelden in de help.
- **Basis:** `personal`. #78 is een aangepaste versie van #76 voor Personal en is al gemerged in `personal`.
- **Testen zodra #175 in de store staat:**
  1. Open het helpboek bij AGP, Dagprofiel, Voorspelnauwkeurigheid, CGM-vergelijking, IDP en Slaap.
  2. Het voorbeeld is een echte, interactieve grafiek met fictieve gegevens in plaats van een schets. Hover en wissel tussen licht en donker thema.
  3. Bekijk de nieuwe gidsen "Snel starten" en "Problemen oplossen", in het Nederlands en het Engels.
- **Status:** wacht op build.

### Test C (poort 8453)

- **Store-versie:** 1.0.92301
- **Wat erop staat:** Personal PR [#75](https://github.com/smokkelaar/nocturne-personal/pull/75), help-testbuild die alle open help-PR's combineert: dagelijks gebruik en meldingen (#70), instellingen en beheer (#72), connectors met Google Health (#63/#73), op `personal` dat de rapport-help (#71) al bevat.
- **Basis:** `personal` met meerdere features tegelijk. ⚠ Afwijking van de spelregel. Dit is bewust gedaan om alle help samen te bekijken; bevestig dat dit zo mag blijven.
- **Wacht klaar:** [HA #172](https://github.com/smokkelaar/nocturne-home-assistant/pull/172) zet Test C op #75 `e7a4e04`: help-testbuild op de nieuwste `personal` (0.3.43) met #70, #72, #77 en #63/#73. Elke pagina begint met een open blok "Wat je ziet en wat het betekent" (kleuren, percentages, drempels, routes voor stappen, hartslag en slaap), nu ook voor instellingen, beheer en koppelingen. De help is in het Nederlands vertaald. CI van #75 is groen op de vorige build; de nieuwe build draait.
- **Testen:**
  1. Open op elke pagina het helpboek (boekpictogram).
  2. Klopt de tekst met wat je ziet? Werken de uitklapblokken? Vindt zoeken in de help de pagina?
  3. Dagelijks: Dashboard, Calendar, Time spans, Clock en klokbouwer, Food, Meals, Tools → Packing, Alerts (Rules, Simulator, Do not disturb, History), Notifications. Zet de interfacetaal op Nederlands en controleer het open blok bovenaan.
  4. Instellingen: Profile, Appearance, Members, Setup, Dev tools → Compatibility.
  5. Rapporten: Reports en de vijf Loop analysis-pagina's.
  6. Connectors: Settings → Connectors en Google Health.
  7. Zoek op "snooze", "packing", "webhook" en "Google Health". Bekijk het in het Nederlands en het Engels.
- **Status:** wacht op test.

### Personal (poort 8450)

- **Store-versie:** 1.0.93301 = Personal 0.3.42 op nightscout main `3caa43c`.
- **In `personal`, nog niet in de store:** 0.3.43 met
  - [#78](https://github.com/smokkelaar/nocturne-personal/pull/78): interactieve grafiekvoorbeelden in de help (AGP, Dagprofiel, Voorspelnauwkeurigheid, CGM-vergelijking, IDP, Slaap).
  - [#79](https://github.com/smokkelaar/nocturne-personal/pull/79): jaaroverzicht, de twee buitenste bolletjes versmallen het kleurbereik (ook glucose); HbA1c met één decimaal extra (6,54% en 50,3 mmol/mol), ook bij lab-invoer.
- **Testen zodra 0.3.43 in de store staat:**
  1. Rapporten → Jaaroverzicht: versleep de buitenste bolletjes. Het palet loopt alleen tussen de bolletjes, waarden erbuiten krijgen de eindkleur en worden gedimd.
  2. Rapporten → eHbA1c: waarden tonen 2 decimalen in % en 1 in mmol/mol. Voer een lab-waarde in met die precisie en controleer de streefwaardecheck.
  3. Open de help bij AGP en Slaap: het voorbeeld is interactief.
- **Status:** 0.3.43 wordt gebouwd.

### Latest (poort 8449)

- **Store-versie:** 1.0.88301 = nightscout main `3caa43c`.
- **Doel:** volgt de nightscout main waarop Personal gebouwd is. Niets specifieks te testen.

### Official Release (poort 8448)

- **Store-versie:** 1.0.88301 = officiële release 0.2.7.
- **Doel:** officiële release. Niets te testen.

### Stable en Main (repo nocturne-home-assistant-upstream, poort 8448 en 8449)

- **Store-versie:** 0.2.40801 = nightscout main `971dd4a`.
- **Status:** loopt achter op main. Bijwerken staat op de lijst van de HA-onderhoudsthread.

## Klaar met testen

Hier komt wat je getest en goedgekeurd hebt, met datum.

| Datum | Instantie | Feature | Uitkomst |
|---|---|---|---|
| | | | |
