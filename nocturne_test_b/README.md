# Nocturne Test B

## Main synchronization — 2026-10-09

All development sources now include upstream main `ef8850840c349fa9519a7f3022599ec9adddff82` (2026-10-09 06:48:03 UTC).
Official remains Nocturne **0.2.7** because no newer release exists.
The functional wrapper remains **0.1.13**. HA package versions are generated only
after both native architectures pass publication checks; source versions are separate.

| Channel | Source | Upstream base | Additional code |
|---|---|---|---|
| Daily / Latest | `ef88508` | `ef88508` | None |
| Personal 0.3.27 | `6ec88de` | `ef88508` | Personal extensions, including Google Health and HbA1c method comparison |
| Test A | `4e2ec5c` | `ef88508` | Google Health PR #1293, still unmerged |
| Test B | `ef88508` | `ef88508` | Hypo comparison PR #2031 is already merged into main |
| Test C | `ef88508` | `ef88508` | Clock-face settings PR #2007 is already merged into main |

Main images come from the immutable `main-ef88508` publication tags and verified
OCI digests. `latest` now denotes an official upstream release, so it is not the
discovery source for Daily. [Upstream publication](https://github.com/nightscout/nocturne/actions/runs/37895441854).

Published package versions and image digests are in each channel's `config.json`
and `provenance.json`; the runtime source and feature version are in
`rootfs/opt/nocturne-ha/version.json`. These files must agree before HA is updated.

Test B bevat **Hypo Duration** en **Hypo Events** in **Reports → Comparison**, naast de bestaande hyperinformatie. Deze testversie gebruikt [gemergede PR #2031](https://github.com/nightscout/nocturne/pull/2031), vastgezet op broncommit `ef8850840` en upstream main `ef8850840`. De exacte bron en checksum staan in `upstream-test-b.json`.

De **1.x**-pakketreeks gebruikt vooraf gebouwde GitHub-images voor AMD64 en ARM64. Home Assistant downloadt de geteste image; lokaal compileren is niet nodig.

Vergelijk twee periodes van gelijke lengte. Hypo Duration toont de totale geregistreerde tijd onder bereik in uren; Hypo Events gebruikt de bestaande episode-definitie. Een overgang tussen laag en zeer laag binnen één episode telt één keer. Een periode zonder metingen toont **No data** in plaats van nul en een berekend verschil.

Controleer beide periodewaarden, het verschil, wisselen van periodes en de afdruk. [Installatie en volledige teststappen](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/nocturne_test_b/DOCS.md).

Test B behoudt zijn slug, standaardpoort **8452**, opties, data en cookie-namespace. Deze bron vervangt de vorige A1c-voorkeurentest uit PR #1977.
