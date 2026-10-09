# Eén wrapperversie, twee Nocturne-keuzes

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

De functionaliteit van deze Home Assistant-verpakking heeft vanaf **0.1.4 één
gedeeld versienummer**. Alleen de meegeleverde upstream-Nocturne-code verschilt:

| Keuze in HA | Wrapperfunctionaliteit | Meegeleverde Nocturne |
|---|---|---|
| Nocturne Official Release | 0.1.13 | Officiële release 0.2.7 |
| Nocturne Latest Release | 0.1.13 | Vastgezette daily/main-build, met commitcode en UTC-datum/tijd |

De code voor opstarten, HTTPS, toegangscontrole, opslag en status is identiek.
Accounts, gegevens en instellingen blijven afzonderlijk; beide apps hebben
bewust een andere naam, slug en standaard hostpoort.

## Historische pakketnummers vóór de prebuilt 1.x-reeks

Home Assistant heeft een veranderend **pakketversienummer** nodig om een nieuwe
build aan te bieden. Daarom bestaat dat uit wrapperversie plus leveringsnummer:

- `0.1.4-1`: eerste pakketbuild van wrapper 0.1.4.
- `0.1.4-2`: volgende upstream-build, nog steeds exact wrapper 0.1.4.
- `0.1.5-1`: pas bij een wijziging aan onze eigen functionaliteit.

De huidige statuspagina toont **HA-wrapper 0.1.13**. De onderstaande 0.1.x-leveringsnummers zijn historische voorbeelden; de huidige prebuilt pakketreeks is 1.0.x. Het volledige HA-pakketnummer
staat onder **Technische pakketgegevens**. Official en Latest mogen verschillende
leveringsnummers hebben zonder dat hun wrapperfunctionaliteit verschilt.
De HA-appwinkel kan dit technische versienummer niet vervangen door twee losse velden.

De Latest-datum is de committijd van de **werkelijk opgenomen code**, niet het
tijdstip van onze dagelijkse controle en niet een belofte dat elke nieuwe
main-commit al beschikbaar is. Mislukte of onvolledige upstream-builds worden niet aangeboden.

## Updates

Latest wordt dagelijks gecontroleerd; een nieuwe, geslaagde kandidaat verhoogt
alleen zijn leveringsnummer. Zet **Automatisch bijwerken** alleen bij Latest aan
als je dat wilt. Official blijft een handmatig gestarte controle en beoordeelde
publicatie. Een wijziging in onze wrapper wordt voor beide kanalen uitgebracht.
Een repository-update installeert of herstart zelf niets in jouw HA.

## Voor bijdragers

`wrapper.json` is de bron voor het functionele versienummer.
`version.json.app` wordt daarvan afgeleid; `version.json.package`, de
HA-manifestversie en Docker `BUILD_VERSION` bevatten hetzelfde leveringsnummer.
De updaters verhogen alleen de teller, nooit zelfstandig de wrapperversie.
CI weigert afwijkende wrapperversies of uiteenlopende gedeelde runtimecode.

Bij een wrapperwijziging: verhoog `wrapper.json`, zet beide manifestversies op
`<nieuwe-versie>-1`, regenereer beide metadata via de functies
`tools/update_upstream.py:render` en `tools/update_latest.py:render`,
werk beide changelogs bij en voer alle tests uit. Verhoog nooit alleen één
kanaal naar een andere wrapperfunctionaliteit.

[Kanalen](CHANNELS.md) · [Updatebeleid](UPDATES.md)
