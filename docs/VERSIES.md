# Eén wrapperversie, twee Nocturne-keuzes

De functionaliteit van deze Home Assistant-verpakking heeft vanaf **0.1.4 één
gedeeld versienummer**. Alleen de meegeleverde upstream-Nocturne-code verschilt:

| Keuze in HA | Wrapperfunctionaliteit | Meegeleverde Nocturne |
|---|---|---|
| Nocturne Official Release | 0.1.5 | Officiële release 0.2.4 |
| Nocturne Latest Release | 0.1.5 | Vastgezette daily/main-build, met commitcode en UTC-datum/tijd |

De code voor opstarten, HTTPS, toegangscontrole, opslag en status is identiek.
Accounts, gegevens en instellingen blijven afzonderlijk; beide apps hebben
bewust een andere naam, slug en standaard hostpoort.

## Waarom toont HA ook 0.1.4-1?

Home Assistant heeft een veranderend **pakketversienummer** nodig om een nieuwe
build aan te bieden. Daarom bestaat dat uit wrapperversie plus leveringsnummer:

- `0.1.4-1`: eerste pakketbuild van wrapper 0.1.4.
- `0.1.4-2`: volgende upstream-build, nog steeds exact wrapper 0.1.4.
- `0.1.5-1`: pas bij een wijziging aan onze eigen functionaliteit.

De statuspagina toont **HA-wrapper 0.1.5** prominent. Het volledige HA-pakketnummer
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
