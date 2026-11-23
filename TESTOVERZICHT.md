# Testoverzicht

Wat staat er op elke Nocturne-app in Home Assistant, wat moet Sebastiaan daar nog bekijken, en hoe.

**Bijgewerkt:** 23 november 2026, 18:00 (NL-tijd)

**Stand 21 november** (HA-store, [publicatie #237](https://github.com/smokkelaar/nocturne-home-assistant/pull/237)):

| App | Poort | Bron | Doel |
|---|---|---|---|
| Official (deze repo) | 8448 | officiële release v0.3.2, store 1.0.115601 | nieuwste release |
| Latest (deze repo) | 8449 | nightscout main `cf719c4` (19 nov), store 1.0.115601, volgt main daarna dagelijks | nieuwste main |
| Personal | 8450 | Personal 0.4.0 = nightscout main `cf719c4` + de help (boekicoon), commit `701a289`, store 1.0.116501 | eigen wensen op de nieuwste main; volgt Latest weer |
| Test A | 8451 | Personal PR #104 (meervoudsvormen) op schone nightscout main `a29dbba`, store 1.0.116501 | featuretest meervoudsvormen |
| Test B | 8452 | Personal PR #105 (eHbA1c-grafiek, gekozen combinatie van B en C + eHbA1c in Eigen rapport) op schone nightscout main `d112136` | featuretest eHbA1c, combinatie |
| Test C | 8453 | Personal PR #106 (eHbA1c-grafiek ontwerp C + eHbA1c in Eigen rapport) op schone nightscout main `d112136` | featuretest eHbA1c, ontwerp C |
| Stable (upstream-repo) | 8448 | officiële release v0.3.2, store 0.2.44701 | nieuwste release |
| Main (upstream-repo) | 8449 | nightscout main `cf719c4`, store 0.2.44701, volgt main daarna dagelijks | nieuwste main |

Op 21 nov 16:45 kregen Test A, B, C en Personal pakket 1.0.116501. Alleen Test A kreeg nieuwe inhoud (meervoudsvormen). Personal en Test B/C hebben dezelfde inhoud, met een herstel in het bouwrecept: de ARM64-build laadde een oude alarm-bibliotheek uit het basisimage. Official en Latest blijven op 1.0.115601. Op 23 nov 16:30 kregen Test B en C pakket 1.0.117601 met de eHbA1c-grafiek (#105 en #106).

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
| 1 | Test A (8451) | Meervoudsvormen ([Personal PR #104](https://github.com/smokkelaar/nocturne-personal/pull/104)), voor een upstream issue + draft-PR | Klaar om te testen in 1.0.116501 (21 nov), zie Per instantie → Test A |
| 5 | Test B (8452) | eHbA1c-grafiek in de gekozen combinatie, met naam en bereik boven en onder elke grenslijn, en eHbA1c in Eigen rapport, in % of mmol/mol ([#105](https://github.com/smokkelaar/nocturne-personal/pull/105)) | Klaar om te testen in 1.0.118301 (23 nov), zie Per instantie → Test B. Test C (ontwerp C) gaat over naar de kleuren van het jaaroverzicht |
| 2 | Personal (8450) | Help terug op de nieuwste main (0.4.0) | Klaar om te testen in 1.0.115601 (21 nov), zie Per instantie → Personal |
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

**Stand 1 november (vervangen door de stand hierboven):** Personal stond op store-versie 1.0.104301 (0.3.47, 30 okt), Test A, B en C op 1.0.105701 (1 nov, [publicatie #214](https://github.com/smokkelaar/nocturne-home-assistant/pull/214)), Latest en Official op 1.0.101201. Alle apps laten nu tenantadressen (`<tenant>.<hostname>:<poort>`) door en controleren bij meer tenants elke tenant apart (alleen de wrapper is gewijzigd). Installatie en werking op de eigen HA zijn vanuit deze sessie niet gecontroleerd; dit overzicht bevestigt de gepubliceerde pakketten.

## Per instantie

### Test A (poort 8451)

- **Bron (21 nov):** [Personal PR #104](https://github.com/smokkelaar/nocturne-personal/pull/104), branch `claude/project-thread-6r1zdz`, commit `b3a7b67`, op schone nightscout main `a29dbba`. Tellingen gaan via `plural()` in plaats van een Engelse s-uitgang, en de Plural-Forms van ru, fr, pt, ja, ko en zh zijn gecorrigeerd. Testbuild, wordt niet gemerged; de upstream issue- en PR-tekst staat in `upstream-pr/plural-forms-issue-en-pr.md`.
- **Testen:**
  1. In het Engels leest alles als voorheen. Controleer tellingen met 1 en met meer: Instellingen → Leden, Rapporten → Slaap (nachten), Rapporten → Batterij (apparaten, dagen), Rapporten → Behandelingen (records selecteren en verwijderen), het dashboard (maaltijden), Community → Vertalingen (concepten).
  2. Zet de taal op Nederlands: deze teksten vallen terug op Engels tot ze vertaald zijn, en tonen nergens een losse `{1}` of Engelse s-uitgang.
- **Status:** klaar om te testen in 1.0.116501 (21 nov). Vernieuw de store: Instellingen → Apps → App store → ⋮ → Controleren op updates.

**Wacht op een vrije testinstantie:**
- [Personal PR #83](https://github.com/smokkelaar/nocturne-personal/pull/83): Google Health-reset met begindatum (#80) bovenop #69. Stond hier tot 1 nov.
- [Personal PR #81](https://github.com/smokkelaar/nocturne-personal/pull/81): op de resetpagina per connector kiezen wat opnieuw wordt opgehaald.
- [Personal PR #84](https://github.com/smokkelaar/nocturne-personal/pull/84) / upstream [#3075](https://github.com/nightscout/nocturne/pull/3075): ImageSharp 3.2.0 met de Six Labors community-licentie. Test: de app start, en een profielfoto uploaden (PNG, JPEG, WebP) werkt.
- [Personal PR #88](https://github.com/smokkelaar/nocturne-personal/pull/88) (help-icoon + grafiekvoorbeelden, stond op Test B) en [#89](https://github.com/smokkelaar/nocturne-personal/pull/89) (Nederlandse paginahulp, stond op Test C).

### Test B (poort 8452)

- **Bron (23 nov):** [Personal PR #105](https://github.com/smokkelaar/nocturne-personal/pull/105), branch `claude/project-thread-bn7dz0`, commit `6132256`, op schone nightscout main `d112136`. eHbA1c-grafiek in de **gekozen combinatie** en eHbA1c als signaal in Eigen rapport. Testbuild, wordt niet gemerged.
- **Combinatie (keuze 23 nov):** harde zonekleuren uit ontwerp B, stippellijnen in de kleur van de zone erboven uit ontwerp C, met het label bij de lijn uit ontwerp B, en de overzichtsbalk om in te zoomen uit ontwerp C.
- **Testen:**
  1. Rapporten → eHbA1c: de grafiek staat op de gewone (donkere) kaartachtergrond, zonder kleurvlakken.
  2. De lijnkleur volgt de zone: groen onder 5,7%, geelgroen tot 7%, oranje tot 9%, rood daarboven. Stippellijnen in de zonekleur bij 5,7%, 7% en 9%. Direct boven en onder elke lijn staan de naam en het bereik van de zone aan die kant (aangepast 23 nov, `0c7e077`).
  3. Zoom met 3 maanden, 6 maanden, 1 jaar en Alles, en met de overzichtsbalk onder de grafiek. Reset zoom gaat terug.
  4. Bekijk het ook in het lichte schema (Instellingen → Weergave).
  5. Labwaarden staan als driehoekje; de tooltip werkt zoals voorheen.
  6. Rapporten → Eigen rapport: voeg het signaal Estimated HbA1c (eHbA1c) toe (Glucose → Statistieken). De lijn verschijnt, ook samen met Lab HbA1c, en ook als eHbA1c het enige signaal op de tijdlijn is (hersteld 23 nov, `6132256`).
  7. Zet je HbA1c-eenheid op mmol/mol (Instellingen → Weergave). In Eigen rapport staan eHbA1c en Lab HbA1c dan in mmol/mol (nieuw 23 nov, `6132256`).
- **Status:** klaar om te testen in pakket 1.0.118301 (23 nov), met de labels boven en onder de lijnen, mmol/mol en de tijdlijn in Eigen rapport. Vernieuw de store: Instellingen → Apps → App store → ⋮ → Controleren op updates.

### Test C (poort 8453)

- **Bron (23 nov):** [Personal PR #106](https://github.com/smokkelaar/nocturne-personal/pull/106), branch `claude/project-thread-bn7dz0-c`, commit `9300d54`, op schone nightscout main `d112136`. Hetzelfde als Test B, met **ontwerp C**. Testbuild, wordt niet gemerged.
- **Ontwerp C:** de lijnkleur loopt vloeiend over tussen de zones (zoals de glucosegrafiek met "doorlopende" kleuring), je zoomt in met een overzichtsbalk onder de grafiek (zoals op het dashboard), en de stippellijnen hebben de kleur van de zone erboven, met de uitleg alleen in de legenda.
- **Testen:** alleen ter vergelijking met Test B; de keuze is de combinatie op Test B.
- **Status:** klaar om te testen in pakket 1.0.117601 (23 nov). Vernieuw de store: Instellingen → Apps → App store → ⋮ → Controleren op updates.

### Personal (poort 8450)

- **Bron (21 nov):** Personal 0.4.0, commit `701a289` ([PR #103](https://github.com/smokkelaar/nocturne-personal/pull/103)) = nightscout main `cf719c4` met de in-app help erbij. Gebouwd met .NET 11 en Rust 1.99.
- **Wat erin zit:** het boekicoon linksboven in de zijbalk en in de mobiele kop, de help per pagina (ook nieuwe pagina's zoals Site, Uitnodigingen, Trackers, Community en Eigen rapport), dashboardvoorbeelden met fictieve gegevens, de leeshulp en de Nederlandse helpteksten. Google Health-hulp beschrijft de client in Instellingen → Administratie → Integraties.
- **Wat er niet meer in zit:** de oude Personal-extra's van 0.3.47 (jaaroverzicht-kleurbereik, eHbA1c-tooltip). Die staan op `archive/personal-feature-base-before-v032` en lopen via upstream #3080 en #3078.
- **Testen:**
  1. Vernieuw de store: Instellingen → Apps → Store → ⋮ → Controleren op updates, en update Personal.
  2. Het boekicoon staat linksboven in de zijbalk. Op een telefoon staat het in de kop.
  3. Open de help op het dashboard, bij Rapporten en bij Instellingen: elke pagina toont zijn eigen uitleg in het Nederlands.
  4. Dashboardhulp: de widgets tonen voorbeeldgegevens, en de voorspelknop in het voorbeeld verandert je eigen instellingen niet.
  5. Instellingen → Weergave: de helpvoorkeuren (indeling, transparantie, vervaging) werken.
- **Status:** klaar om te testen in 1.0.115601 (21 nov). Vernieuw de store: Instellingen → Apps → Store → ⋮ → Controleren op updates.

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
