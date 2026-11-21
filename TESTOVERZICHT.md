# Testoverzicht

Wat staat er op elke Nocturne-app in Home Assistant, wat moet Sebastiaan daar nog bekijken, en hoe.

**Bijgewerkt:** 21 november 2026, 04:10 (NL-tijd)

**Stand 21 november:**

| App | Poort | Bron | Doel |
|---|---|---|---|
| Official (deze repo) | 8448 | officiële release v0.3.2 | nieuwste release |
| Latest (deze repo) | 8449 | nightscout main `cf719c4` (19 nov), volgt main daarna dagelijks | nieuwste main |
| Personal | 8450 | Personal 0.4.0 = nightscout main `cf719c4` + de help (boekicoon), commit `701a289` | eigen wensen op de nieuwste main; volgt Latest weer |
| Test A, B, C | 8451-8453 | schone v0.3.2 | vrij voor de volgende featuretest |
| Stable (upstream-repo) | 8448 | officiële release v0.3.2, store 0.2.44701 | nieuwste release |
| Main (upstream-repo) | 8449 | nightscout main `cf719c4`, store 0.2.44701, volgt main daarna dagelijks | nieuwste main |

Test A/B/C krijgen bij de publicatie van Personal 0.4.0 een nieuw pakketnummer met dezelfde v0.3.2-inhoud; dat komt doordat hun bouwrecept meeschuift (.NET 11 en Rust 1.99 voor de nieuwe main).

**Release-overgang 16 november:** na de verplichte v0.3.0-migratiebridge gingen alle HA-apps naar de officiële Nocturne v0.3.2. De onderstaande featuretests beschrijven de eerdere Personal- en Test-bronnen; die staan op [archive/channel-source-pre-v032](https://github.com/smokkelaar/nocturne-home-assistant/tree/archive/channel-source-pre-v032) en zijn nu niet actief. De afzonderlijke HA-installaties, tenantgegevens en onderhoudsfuncties blijven bestaan.

Vernieuw eerst de store in HA: Instellingen → Apps → Store → ⋮ → Controleren op updates.

## Spelregels

- Een nieuwe feature test je op Test A, B of C tegen een **schone nightscout main met alleen die ene feature erbij**, tenzij expliciet anders is afgesproken.
- **Personal** is de verzamelbak van eigen wensen en eerste probeersels. Het is geen testbasis voor features die naar nightscout/nocturne gaan.
- Er gaat nooit iets naar nightscout/nocturne zonder expliciete vraag van Sebastiaan.
- Wie iets op een testinstantie zet, of hoort dat iets getest is, werkt dit bestand bij.

## Nu te doen voor Sebastiaan

| # | Waar | Wat | Status |
|---|---|---|---|
| 1 | Test A, B, C | Upstream-PR's #3073, #3080, #3078 na de review | Klaar om te testen: in de store als 1.0.105701 (1 nov), zie Per instantie |
| 2 | Personal (8450) | Help terug op de nieuwste main (0.4.0) | Klaar om te testen zodra de store-update er is, zie Per instantie → Personal |
| 4 | Personal (8450) | Jaaroverzicht: buitenste bolletjes verplaatsen; eHbA1c-tooltip; help | Getest op 0.3.43 (27 okt): extra decimalen goed, bolletjes en tooltip nog niet goed, help-icoon ontbrak. Personal 0.3.45 bevat de fixes van [#82](https://github.com/smokkelaar/nocturne-personal/pull/82) en het help-icoon van [#88](https://github.com/smokkelaar/nocturne-personal/pull/88). Getest op 0.3.45 (28 okt): kleuren werken. Dim op aparte regel, presets, Mirror en Swap weg, + in de kleurenrij, verloop tussen de kleuren: aangepast in [#92](https://github.com/smokkelaar/nocturne-personal/pull/92) (0.3.46). Getest op 0.3.46 (29 okt): teksten in de kleurenrij ontbraken en het HbA1c-vangbereik was te groot; beide aangepast in [#93](https://github.com/smokkelaar/nocturne-personal/pull/93) (0.3.47). **Let op:** deze jaaroverzicht- en eHbA1c-onderdelen zitten niet in Personal 0.4.0; ze lopen via upstream-PR's #3080 en #3078 (Test B en C) |

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

**Personal staat op store-versie 1.0.104301 (0.3.47, 30 okt), Test A, B en C op 1.0.105701 (1 nov, [publicatie #214](https://github.com/smokkelaar/nocturne-home-assistant/pull/214)), Latest en Official op 1.0.101201.** Vernieuw de HA-store en update. Alle apps laten nu tenantadressen (`<tenant>.<hostname>:<poort>`) door en controleren bij meer tenants elke tenant apart (alleen de wrapper is gewijzigd). Installatie en werking op de eigen HA zijn vanuit deze sessie niet gecontroleerd; dit overzicht bevestigt de gepubliceerde pakketten.

## Per instantie

### Test A (poort 8451)

- **Bron (1 nov):** [Personal PR #97](https://github.com/smokkelaar/nocturne-personal/pull/97) = branch van upstream [#3073](https://github.com/nightscout/nocturne/pull/3073) (Google Health OAuth-client in instantiebeheer) na de review, commit `28a9bcf`, op schone nightscout main `c253506`. Testbuild, wordt niet gemerged.
- **Testen:**
  1. Instellingen → Administratie → Integraties → Google Health: vul client-ID en secret in (spaties eromheen mogen) en sla op. De callback-URL blijft staan.
  2. Sla alleen een nieuw secret op: de callback-URL verandert niet.
  3. Een client-ID zonder `.apps.googleusercontent.com` geeft een leesbare melding.
  4. Koppel Google Health als gebruiker. Wijzig je tijdens het Google-scherm de client-ID, dan vraagt Nocturne je opnieuw te beginnen.
- **Database:** de migratie van upstream #2842 is op deze database al klaar, dus de trage legacy-id-reparatie draait niet opnieuw.
- **Status:** klaar om te testen in 1.0.105701 (1 nov). Vernieuw de store: Instellingen → Apps → App store → ⋮ → Controleren op updates.

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
- **Status:** klaar om te testen in 1.0.105701 (1 nov). Vernieuw de store: Instellingen → Apps → App store → ⋮ → Controleren op updates.

### Test C (poort 8453)

- **Bron (1 nov):** [Personal PR #99](https://github.com/smokkelaar/nocturne-personal/pull/99) = branch van upstream [#3078](https://github.com/nightscout/nocturne/pull/3078) (eHbA1c: extra decimaal, lab-tooltip) na de review, commit `acb156c`, op schone nightscout main `c253506`. Testbuild, wordt niet gemerged.
- **Testen:**
  1. Rapporten → eHbA1c: waarden tonen 2 decimalen in % en 1 in mmol/mol.
  2. Voer een labwaarde in (bijvoorbeeld 6,54%) met een datum: die staat op de juiste dag.
  3. Beweeg de muis vlak naast het driehoekje: de tooltip toont de labwaarde. Op dezelfde dag maar onderaan bij de datums toont hij alleen de schatting.
  4. Een notitie langer dan 500 tekens kan niet.
- **Status:** klaar om te testen in 1.0.105701 (1 nov). Vernieuw de store: Instellingen → Apps → App store → ⋮ → Controleren op updates.

### Personal (poort 8450)

- **Bron (21 nov):** Personal 0.4.0, commit `701a289` ([PR #103](https://github.com/smokkelaar/nocturne-personal/pull/103)) = nightscout main `cf719c4` met de in-app help erbij. Gebouwd met .NET 11 en Rust 1.99, alleen AMD64.
- **Wat erin zit:** het boekicoon linksboven in de zijbalk en in de mobiele kop, de help per pagina (ook nieuwe pagina's zoals Site, Uitnodigingen, Trackers, Community en Eigen rapport), dashboardvoorbeelden met fictieve gegevens, de leeshulp en de Nederlandse helpteksten. Google Health-hulp beschrijft de client in Instellingen → Administratie → Integraties.
- **Wat er niet meer in zit:** de oude Personal-extra's van 0.3.47 (jaaroverzicht-kleurbereik, eHbA1c-tooltip). Die staan op `archive/personal-feature-base-before-v032` en lopen via upstream #3080 en #3078.
- **Testen:**
  1. Vernieuw de store: Instellingen → Apps → Store → ⋮ → Controleren op updates, en update Personal.
  2. Het boekicoon staat linksboven in de zijbalk. Op een telefoon staat het in de kop.
  3. Open de help op het dashboard, bij Rapporten en bij Instellingen: elke pagina toont zijn eigen uitleg in het Nederlands.
  4. Dashboardhulp: de widgets tonen voorbeeldgegevens, en de voorspelknop in het voorbeeld verandert je eigen instellingen niet.
  5. Instellingen → Weergave: de helpvoorkeuren (indeling, transparantie, vervaging) werken.
- **Status:** gemerged 21 nov; wacht op de store-publicatie.

### Latest (poort 8449)

- **Bron:** nightscout main `cf719c4` (19 nov 2026); volgt daarna dagelijks de nieuwste gepubliceerde main.
- **Doel:** volgt de nightscout main waarop Personal gebouwd is. Niets specifieks te testen.

### Official Release (poort 8448)

- **Bron:** officiële release v0.3.2.
- **Doel:** officiële release. Niets te testen.

### Stable en Main (repo nocturne-home-assistant-upstream, poort 8448 en 8449)

- **Store-versie:** 0.2.44701. Stable = officiële release v0.3.2, Main = nightscout main `cf719c4` (20 nov).
- **Status:** bij. Stable volgt voortaan zelf de nieuwste release en Main de nieuwste main.

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
