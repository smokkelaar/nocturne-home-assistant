# Testoverzicht

Wat staat er op elke Nocturne-app in Home Assistant, wat moet Sebastiaan daar nog bekijken, en hoe.

**Bijgewerkt:** 1 november 2026, 22:15 (NL-tijd)

Vernieuw eerst de store in HA: Instellingen → Apps → Store → ⋮ → Controleren op updates.

## Spelregels

- Een nieuwe feature test je op Test A, B of C tegen een **schone nightscout main met alleen die ene feature erbij**, tenzij expliciet anders is afgesproken.
- **Personal** is de verzamelbak van eigen wensen en eerste probeersels. Het is geen testbasis voor features die naar nightscout/nocturne gaan.
- Er gaat nooit iets naar nightscout/nocturne zonder expliciete vraag van Sebastiaan.
- Wie iets op een testinstantie zet, of hoort dat iets getest is, werkt dit bestand bij.

## Nu te doen voor Sebastiaan

| # | Waar | Wat | Status |
|---|---|---|---|
| 1 | Test A, B, C | Upstream-PR's #3073, #3080, #3078 na de review | Wacht op publicatie, zie Per instantie |
| 4 | Personal (8450) | Jaaroverzicht: buitenste bolletjes verplaatsen; eHbA1c-tooltip; help | Getest op 0.3.43 (27 okt): extra decimalen goed, bolletjes en tooltip nog niet goed, help-icoon ontbrak. Personal 0.3.45 bevat de fixes van [#82](https://github.com/smokkelaar/nocturne-personal/pull/82) en het help-icoon van [#88](https://github.com/smokkelaar/nocturne-personal/pull/88). Getest op 0.3.45 (28 okt): kleuren werken. Dim op aparte regel, presets, Mirror en Swap weg, + in de kleurenrij, verloop tussen de kleuren: aangepast in [#92](https://github.com/smokkelaar/nocturne-personal/pull/92) (0.3.46). Getest op 0.3.46 (29 okt): teksten in de kleurenrij ontbraken en het HbA1c-vangbereik was te groot; beide aangepast in [#93](https://github.com/smokkelaar/nocturne-personal/pull/93) (0.3.47, in de store als 1.0.104301 sinds 30 okt) |

## Upstream-PR's na de Copilot-reviews (1 nov)

De reviewpunten zijn verwerkt op de PR-branches en upstream main is erin gemerged. Op 1 nov op Test A (#3073), B (#3080) en C (#3078) gezet, elk op schone nightscout main `c253506` met alleen die PR. Zie Per instantie voor de status.

| PR | Branch | Wat handmatig te bekijken |
|---|---|---|
| [#3080](https://github.com/nightscout/nocturne/pull/3080) jaaroverzicht | `claude/project-thread-ivzrbr` | Een eerder opgeslagen TDD/bolus-venster houdt dezelfde kleuren. Eerste keer het venster verschuiven verandert de kleuren niet. Boven en onder de balk pak je de dim-streepjes, op de balk de bolletjes. Een grens buiten het kleurbereik staat in de rij aan de goede kant en houdt zijn eigen kleur; + werkt dan nog. |
| [#3073](https://github.com/nightscout/nocturne/pull/3073) Google Health in beheer | `claude/project-thread-tt1qyl` | Alleen het secret opslaan laat de callback-URL ongemoeid. Spaties rond client-ID/secret geen probleem. Foute client-ID geeft een leesbare melding. Client-ID wijzigen tijdens het Google-scherm geeft "Start again" in plaats van een fout. |
| [#3078](https://github.com/nightscout/nocturne/pull/3078) eHbA1c | `claude/project-thread-6a05k1` | Tooltip toont een labwaarde alleen bij het driehoekje, ook op dezelfde dag eronder niet. Datumfix komt nu uit upstream (#3120). |
| [#3075](https://github.com/nightscout/nocturne/pull/3075) ImageSharp | `claude/project-thread-let525` | Ongewijzigd; zie Test A-notitie over #84. |

## Voorbereiding voor dinsdag 27 oktober

HA #176 (A), #175 (B) en #172 (C) zijn samengevoegd. [Publicatie en tests](https://github.com/smokkelaar/nocturne-home-assistant/actions/runs/40403185802) zijn geslaagd voor alle drie de kanalen op AMD64 en ARM64, inclusief opstarten, accountherstel, cold restore en upgraden vanaf de vorige versie. Publieke beschikbaarheid en image-labels zijn gecontroleerd. [Storepromotie #177](https://github.com/smokkelaar/nocturne-home-assistant/pull/177) is gemerged.

**Personal staat op store-versie 1.0.104301 (0.3.47, 30 okt), Test A, B en C op 1.0.102701 (28 okt), Latest en Official op 1.0.101201.** Vernieuw de HA-store en update. Alle apps laten nu tenantadressen (`<tenant>.<hostname>:<poort>`) door en controleren bij meer tenants elke tenant apart (alleen de wrapper is gewijzigd). Installatie en werking op de eigen HA zijn vanuit deze sessie niet gecontroleerd; dit overzicht bevestigt de gepubliceerde pakketten.

## Per instantie

### Test A (poort 8451)

- **Bron (1 nov):** [Personal PR #97](https://github.com/smokkelaar/nocturne-personal/pull/97) = branch van upstream [#3073](https://github.com/nightscout/nocturne/pull/3073) (Google Health OAuth-client in instantiebeheer) na de review, commit `28a9bcf`, op schone nightscout main `c253506`. Testbuild, wordt niet gemerged.
- **Testen:**
  1. Instellingen → Administratie → Integraties → Google Health: vul client-ID en secret in (spaties eromheen mogen) en sla op. De callback-URL blijft staan.
  2. Sla alleen een nieuw secret op: de callback-URL verandert niet.
  3. Een client-ID zonder `.apps.googleusercontent.com` geeft een leesbare melding.
  4. Koppel Google Health als gebruiker. Wijzig je tijdens het Google-scherm de client-ID, dan vraagt Nocturne je opnieuw te beginnen.
- **Database:** de migratie van upstream #2842 is op deze database al klaar, dus de trage legacy-id-reparatie draait niet opnieuw.
- **Status:** wacht op publicatie.

**Wacht op een vrije testinstantie:**
- [Personal PR #83](https://github.com/smokkelaar/nocturne-personal/pull/83): Google Health-reset met begindatum (#80) bovenop #69. Stond hier tot 1 nov.
- [Personal PR #81](https://github.com/smokkelaar/nocturne-personal/pull/81): op de resetpagina per connector kiezen wat opnieuw wordt opgehaald.
- [Personal PR #84](https://github.com/smokkelaar/nocturne-personal/pull/84) / upstream [#3075](https://github.com/nightscout/nocturne/pull/3075): ImageSharp 3.2.0 met de Six Labors community-licentie. Test: de app start, en een profielfoto uploaden (PNG, JPEG, WebP) werkt.
- [Personal PR #88](https://github.com/smokkelaar/nocturne-personal/pull/88) (help-icoon + grafiekvoorbeelden, stond op Test B) en [#89](https://github.com/smokkelaar/nocturne-personal/pull/89) (Nederlandse paginahulp, stond op Test C).

### Test B (poort 8452)

- **Bron (1 nov):** [Personal PR #98](https://github.com/smokkelaar/nocturne-personal/pull/98) = branch van upstream [#3080](https://github.com/nightscout/nocturne/pull/3080) (jaaroverzicht: kleurbereik los van het venster, één kleurenrij) na de review, commit `2da2069`, op schone nightscout main `c253506`. Testbuild, wordt niet gemerged.
- **Testen:**
  1. Rapporten → Jaaroverzicht, kies TDD. Versleep de dim-streepjes boven of onder de balk: de kleuren blijven staan.
  2. Versleep de gekleurde bolletjes op de balk: de kleuren verschuiven, het venster niet.
  3. Voeg een kleurgrens toe en kleur die. Zet het kleurbereik zo dat de grens erbuiten valt: de grens staat in de rij aan die kant en houdt zijn kleur, en + werkt nog.
  4. Reset zet alles terug.
- **Status:** wacht op publicatie.

### Test C (poort 8453)

- **Bron (1 nov):** [Personal PR #99](https://github.com/smokkelaar/nocturne-personal/pull/99) = branch van upstream [#3078](https://github.com/nightscout/nocturne/pull/3078) (eHbA1c: extra decimaal, lab-tooltip) na de review, commit `acb156c`, op schone nightscout main `c253506`. Testbuild, wordt niet gemerged.
- **Testen:**
  1. Rapporten → eHbA1c: waarden tonen 2 decimalen in % en 1 in mmol/mol.
  2. Voer een labwaarde in (bijvoorbeeld 6,54%) met een datum: die staat op de juiste dag.
  3. Beweeg de muis vlak naast het driehoekje: de tooltip toont de labwaarde. Op dezelfde dag maar onderaan bij de datums toont hij alleen de schatting.
  4. Een notitie langer dan 500 tekens kan niet.
- **Status:** wacht op publicatie.

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
  5. (0.3.47) Jaaroverzicht: naast de lage en hoge waarde staat de eenheid, en de knop heet weer "+ Color boundary". eHbA1c: de tooltip springt alleen naar een labwaarde als de muis bij het driehoekje staat, niet onderaan bij de datums.
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
