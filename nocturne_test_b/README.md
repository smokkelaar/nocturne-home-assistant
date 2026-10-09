# Nocturne Test B

## Main synchronization — 2026-10-09

The common compiled upstream base is `df000c33e15d3809591261d78a22135bb0176ffd` (2026-10-09T09:16:08Z).
It includes dashboard/chart refresh fixes (#2019), v3 deletion/history fixes
(#1825), and temporary basal uploader-origin handling (#1570), in addition to
the previously merged clock-face and hypo-comparison changes.
Upstream's later `d106f6085` commit only synchronizes translations and skips
image publication. Daily therefore selects the newest verified published main
ancestor; all five channels use that same compiled base.

Official remains Nocturne **0.2.7**. The functional wrapper remains **0.1.13**.
HA package versions are separate and become available only after both native
architectures, runtime/upgrade checks and anonymous image verification pass.

| Channel | Source | Upstream base | Additional code |
|---|---|---|---|
| Daily / Latest | `df000c3` | `df000c3` | None |
| Personal 0.3.28 | `51e2c1d` | `df000c3` | Personal extensions, including Google Health and HbA1c method comparison |
| Test A | `dd2b027` | `df000c3` | Google Health PR #1293, still unmerged |
| Test B | `df000c3` | `df000c3` | Hypo comparison PR #2031 is merged into main |
| Test C | `df000c3` | `df000c3` | Clock-face settings PR #2007 are merged into main |

Images are resolved through the immutable `main-df000c3` tags and OCI digests.
`latest` denotes upstream's official release and is not the Daily discovery tag.
[Upstream publication](https://github.com/nightscout/nocturne/actions/runs/37910180933).
Published package versions and image digests are in each channel's `config.json`
and `provenance.json`; runtime source and feature versions are in
`rootfs/opt/nocturne-ha/version.json`. These files must agree before HA is updated.

Test B bevat **Hypo Duration** en **Hypo Events** in **Reports → Comparison**, naast de bestaande hyperinformatie. Deze testversie gebruikt [gemergede PR #2031](https://github.com/nightscout/nocturne/pull/2031), vastgezet op broncommit `df000c33e` en upstream main `df000c33e`. De exacte bron en checksum staan in `upstream-test-b.json`.

De **1.x**-pakketreeks gebruikt vooraf gebouwde GitHub-images voor AMD64 en ARM64. Home Assistant downloadt de geteste image; lokaal compileren is niet nodig.

Vergelijk twee periodes van gelijke lengte. Hypo Duration toont de totale geregistreerde tijd onder bereik in uren; Hypo Events gebruikt de bestaande episode-definitie. Een overgang tussen laag en zeer laag binnen één episode telt één keer. Een periode zonder metingen toont **No data** in plaats van nul en een berekend verschil.

Controleer beide periodewaarden, het verschil, wisselen van periodes en de afdruk. [Installatie en volledige teststappen](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/nocturne_test_b/DOCS.md).

Test B behoudt zijn slug, standaardpoort **8452**, opties, data en cookie-namespace. Deze bron vervangt de vorige A1c-voorkeurentest uit PR #1977.
