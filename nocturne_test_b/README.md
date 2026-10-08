# Nocturne Test B

Test B bevat **Hypo Duration** en **Hypo Events** in **Reports → Comparison**, naast de bestaande hyperinformatie. Deze testversie gebruikt [draft-PR #2031](https://github.com/nightscout/nocturne/pull/2031), vastgezet op broncommit `4554d318d` en upstream main `8e1de9070`. De exacte bron en checksum staan in `upstream-test-b.json`.

De **1.x**-pakketreeks gebruikt vooraf gebouwde GitHub-images voor AMD64 en ARM64. Home Assistant downloadt de geteste image; lokaal compileren is niet nodig.

Vergelijk twee periodes van gelijke lengte. Hypo Duration toont de totale geregistreerde tijd onder bereik in uren; Hypo Events gebruikt de bestaande episode-definitie. Een overgang tussen laag en zeer laag binnen één episode telt één keer. Een periode zonder metingen toont **No data** in plaats van nul en een berekend verschil.

Controleer beide periodewaarden, het verschil, wisselen van periodes en de afdruk. [Installatie en volledige teststappen](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/nocturne_test_b/DOCS.md).

Test B behoudt zijn slug, standaardpoort **8452**, opties, data en cookie-namespace. Deze bron vervangt de vorige A1c-voorkeurentest uit PR #1977.
