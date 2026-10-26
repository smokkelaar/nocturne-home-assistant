# Testoverzicht

Wat staat er op elke Nocturne-app in Home Assistant, wat moet Sebastiaan daar nog bekijken, en hoe.

**Bijgewerkt:** 26 oktober 2026, 23:55 (NL-tijd)

Vernieuw eerst de store in HA: Instellingen → Apps → Store → ⋮ → Controleren op updates.

## Spelregels

- Een nieuwe feature test je op Test A, B of C tegen een **schone nightscout main met alleen die ene feature erbij**, tenzij expliciet anders is afgesproken.
- **Personal** is de verzamelbak van eigen wensen en eerste probeersels. Het is geen testbasis voor features die naar nightscout/nocturne gaan.
- Er gaat nooit iets naar nightscout/nocturne zonder expliciete vraag van Sebastiaan.
- Wie iets op een testinstantie zet, of hoort dat iets getest is, werkt dit bestand bij.

## Nu te doen voor Sebastiaan

| # | Waar | Wat | Status |
|---|---|---|---|
| 1 | Test C (8453) | Helpboek op elke pagina controleren | 1.0.95701 beschikbaar; wacht op jouw test |
| 2 | Test A (8451) | Google Health instellen via beheer | 1.0.95701 beschikbaar; wacht op jouw test |
| 3 | Test B (8452) | Interactieve grafiekvoorbeelden in de help (#78) | 1.0.95701 beschikbaar; wacht op jouw test |
| 4 | Personal (8450) | Jaaroverzicht: buitenste bolletjes verplaatsen (hertest van Test B-feedback), HbA1c-precisie en tooltip | 0.3.43 wordt gebouwd; tooltip-fix in [#82](https://github.com/smokkelaar/nocturne-personal/pull/82) (0.3.44) open |

## Voorbereiding voor dinsdag 27 oktober

HA #176 (A), #175 (B) en #172 (C) zijn samengevoegd. [Publicatie en tests](https://github.com/smokkelaar/nocturne-home-assistant/actions/runs/40403185802) zijn geslaagd voor alle drie de kanalen op AMD64 en ARM64, inclusief opstarten, accountherstel, cold restore en upgraden vanaf de vorige versie. Publieke beschikbaarheid en image-labels zijn gecontroleerd. [Storepromotie #177](https://github.com/smokkelaar/nocturne-home-assistant/pull/177) is gemerged.

**Alle drie staan nu op store-versie 1.0.95701.** Vernieuw de HA-store en update Test A, B en C. Installatie en werking op de eigen HA zijn vanuit deze sessie niet gecontroleerd; dit overzicht bevestigt de gepubliceerde pakketten.

## Per instantie

### Test A (poort 8451)

- **Store-versie:** 1.0.95701.
- **Bron:** [Personal PR #69](https://github.com/smokkelaar/nocturne-personal/pull/69), commit `c6a05714b17ac353374257b6b8832509398a887b`.
- **Basis:** schone nightscout main `bd59934` met alleen Google Health OAuth-instellingen in instantiebeheer; vervangt de eerdere #63-build op Personal.
- **Testen:**
  1. Open Instellingen → Administratie → Integraties → Google Health als platformbeheerder.
  2. Vul Client ID, Client secret en Callback URL in, zet Enabled aan en sla op. Het secret blijft daarna gemaskeerd.
  3. Koppel Google Health zonder herstart en controleer dat er data binnenkomt.
  4. Herstart de app: de instellingen blijven staan.
  5. Controleer dat een gewone gebruiker en tenantbeheerder geen toegang hebben tot de beheerinstellingen of de instellingen-API.
- **Status:** gepubliceerd; wacht op jouw test.

### Test B (poort 8452)

- **Store-versie:** 1.0.95701.
- **Bron:** [Personal PR #78](https://github.com/smokkelaar/nocturne-personal/pull/78), commit `012348422c25dc16f95aac290a1951de2c898975`.
- **Doel:** interactieve grafiekvoorbeelden in de help, plus Snel starten en Problemen oplossen. Vervangt de achterhaalde #68-test.
- **Basis:** Personal; #78 is de op Personal aangepaste variant van #76. Dit is geen schone-main-test voor upstream.
- **Testen:**
  1. Open het helpboek bij AGP, Dagprofiel, Voorspelnauwkeurigheid, CGM-vergelijking, IDP en Slaap.
  2. Controleer het blok Verken de grafiek: knoppen wisselen uitleg, hover en pijltjestoetsen tonen waarden; eenheden en licht/donker thema volgen de instellingen.
  3. Klik in het slaapvoorbeeld op een nacht: je blijft in de help.
  4. Bekijk Snel starten en Problemen oplossen in het Nederlands en Engels; zoek op ontbrekende gegevens.
  5. De voorbeelden gebruiken fictieve gegevens; je eigen gegevens en voorkeuren blijven behouden.
- **Status:** gepubliceerd; wacht op jouw test.

### Test C (poort 8453)

- **Store-versie:** 1.0.95701.
- **Bron:** [Personal PR #75](https://github.com/smokkelaar/nocturne-personal/pull/75), commit `e7a4e04059cf438e1b0a011a102c6be85a21e659`.
- **Doel:** Nederlandse paginahulp met bovenaan het open blok Wat je ziet en wat het betekent.
- **Basis:** bestaande gecombineerde help-testbuild op Personal 0.3.43, met #70, #72, #77 en #63/#73. Dit is geen geïsoleerde schone-main-test. De bron-PR #75 blijft een testbuild en is niet gemerged.
- **Testen:**
  1. Zet de interfacetaal op Nederlands en open het helpboek op Dashboard, Calendar, Time spans, Clock, Food, Meals, Packing, Alerts en Notifications.
  2. Controleer ook rapporten zoals AGP, Executive summary, Steps, Heart rate en Sleep, plus Therapy, Appearance, Connectors & Apps en een koppeling.
  3. Bovenaan staat Wat je ziet en wat het betekent open; uitleg over kleuren, percentages en drempels moet kloppen met de pagina.
  4. Controleer uitklapblokken en zoek op Health Connect, Garmin, snooze, packing, webhook en Google Health.
  5. Bekijk de teksten in het Nederlands en Engels.
- **Status:** gepubliceerd; wacht op jouw test.

### Personal (poort 8450)

- **Store-versie:** 1.0.93301 = Personal 0.3.42 op nightscout main `3caa43c`.
- **In `personal`, nog niet in de store:** 0.3.43 met
  - [#78](https://github.com/smokkelaar/nocturne-personal/pull/78): interactieve grafiekvoorbeelden in de help (AGP, Dagprofiel, Voorspelnauwkeurigheid, CGM-vergelijking, IDP, Slaap).
  - [#79](https://github.com/smokkelaar/nocturne-personal/pull/79): jaaroverzicht, de twee buitenste bolletjes versmallen het kleurbereik (ook glucose); HbA1c met één decimaal extra (6,54% en 50,3 mmol/mol), ook bij lab-invoer.
- **Open, wordt 0.3.44:** [#82](https://github.com/smokkelaar/nocturne-personal/pull/82): de eHbA1c-tooltip toont een labwaarde al als de muis binnen 12 px van het driehoekje staat.
- **Waarom hier en niet op Test A/B/C:** dit zijn Personal-wensen, en Test A, B en C zijn bezet. De Test B-build van #68 (26 okt) had #79 nog niet; daarom kon je de buitenste kleuren daar niet verplaatsen.
- **Testen zodra 0.3.43 in de store staat:**
  1. Rapporten → Jaaroverzicht: versleep de buitenste bolletjes. Het palet loopt alleen tussen de bolletjes, waarden erbuiten krijgen de eindkleur en worden gedimd.
  2. Rapporten → eHbA1c: waarden tonen 2 decimalen in % en 1 in mmol/mol. Voer een lab-waarde in met die precisie en controleer de streefwaardecheck.
  2b. (0.3.44) Beweeg de muis vlak naast een lab-driehoekje: de tooltip toont de labwaarde zonder precies te mikken.
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
| 26 okt 2026 | Test B (8452) | Personal #68: jaaroverzicht-kleuren | Crasht niet meer, extra kleuren terug. Buitenste kleuren niet verplaatsbaar: opgelost in #79, hertest op Personal 0.3.43 |
| 26 okt 2026 | Test B (8452) | Personal #68: HbA1c | Werkt; tooltip vraagt precieze muis: verruimd in #82 (0.3.44) |
