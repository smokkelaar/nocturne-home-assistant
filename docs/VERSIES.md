# Eén wrapperversie, twee Nocturne-keuzes

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

De functionaliteit van deze Home Assistant-verpakking heeft vanaf **0.1.4 één
gedeeld versienummer**. Alleen de meegeleverde upstream-Nocturne-code verschilt:

| Keuze in HA | Wrapperfunctionaliteit | Meegeleverde Nocturne |
|---|---|---|
| Nocturne Official Release | 0.1.6 | Officiële release 0.2.4 |
| Nocturne Latest Release | 0.1.6 | Vastgezette daily/main-build, met commitcode en UTC-datum/tijd |

De code voor opstarten, HTTPS, toegangscontrole, opslag en status is identiek.
Accounts, gegevens en instellingen blijven afzonderlijk; beide apps hebben
bewust een andere naam, slug en standaard hostpoort.

## Waarom toont HA ook 0.1.4-1?

Home Assistant heeft een veranderend **pakketversienummer** nodig om een nieuwe
build aan te bieden. Daarom bestaat dat uit wrapperversie plus leveringsnummer:

- `0.1.4-1`: eerste pakketbuild van wrapper 0.1.4.
- `0.1.4-2`: volgende upstream-build, nog steeds exact wrapper 0.1.4.
- `0.1.5-1`: pas bij een wijziging aan onze eigen functionaliteit.

De statuspagina toont **HA-wrapper 0.1.6** prominent. Het volledige HA-pakketnummer
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
