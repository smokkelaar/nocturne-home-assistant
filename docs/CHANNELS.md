# Nocturne Official en Latest naast elkaar

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

Na één keer toevoegen van deze repository toont Home Assistant twee losse apps:

| Eigenschap | Nocturne Official Release | Nocturne Latest Release |
|---|---|---|
| Doel | Handmatig bevorderde officiële Nocturne-release | Vaak bijgewerkte momentopname van upstream `main` |
| HA-slug / gegevensidentiteit | `nocturne_local` — bestaande 0.1.x-installaties blijven hier | `nocturne_latest` — volledig eigen `/data` |
| Standaard hostpoort | 8448 | 8449 |
| Standaard URL | `https://homeassistant.local:8448` | `https://homeassistant.local:8449` |
| Upstream-selectie | Semantische release, momenteel 0.2.7 | Exacte geteste `main`-commit |
| Imagegebruik | API/web op exacte OCI-digests | `latest` alleen ontdekken; HA bouwt daarna op exacte OCI-digests |
| Repository-update | Alleen handmatig gestarte controle, review en merge | Dagelijkse controle; auto-merge uitsluitend na verplichte tests |
| HA-installatie-update | Handmatig aanbevolen | Kan automatisch als je alleen bij deze app **Automatisch bijwerken** aanzet |
| Risico | Experimenteel | Zeer experimenteel; onaf werk en frequente migraties mogelijk |

## Isolatie

Beide kanalen hebben vanaf 0.1.4 één gedeelde functionele **HA-wrapperversie**.
Het aparte Nocturne-versienummer of de main-commit bepaalt de meegeleverde
upstream-code. Alleen het technische leveringsnummer mag daarna per kanaal
oplopen. Zie [uitleg met voorbeelden](VERSIES.md).

De slugs bepalen afzonderlijke Supervisor-apps en afzonderlijke private gegevensmappen. Installeren van Latest leest, kopieert of migreert niets uit Official. Accounts, passkeys, herstelcodes, database en `secrets.json` zijn dus niet gedeeld.

De standaard hostpoorten verschillen, zodat beide geïnstalleerd kunnen blijven en zelfs een onbedoelde gelijktijdige start geen poortbotsing veroorzaakt. Gelijktijdig draaien is niet nodig en verdubbelt ongeveer de actieve database/API/web-belasting. Controleer altijd aan de appnaam, poort en statuspagina in welk kanaal je werkt.

Gebruik bij dezelfde hostnaam voor ieder kanaal zijn eigen URL met de juiste poort. Maak voor Latest een eigen Nocturne-account/passkey aan; probeer geen Official-database of sleutels te kopiëren. De twee passkeys kunnen in dezelfde browser zichtbaar zijn omdat de hostnaam gelijk is, dus geef ze herkenbare namen in je wachtwoord-/passkeybeheerder.

## Updategrenzen

Vanaf wrapper **0.1.5** scheidt de HTTPS-ingang de sessiecookies per kanaal, ook
bij één hostnaam met twee poorten. Na de update is eenmalig opnieuw aanmelden
nodig; accounts/passkeys blijven behouden. Displayvoorkeuren kunnen gedeeld
blijven. [Werking, grenzen en browsercontrole](COOKIES.md).
Oudere wrappers hebben deze scheiding niet: gebruik daarvoor aparte browserprofielen.

Official wijzigt alleen nadat iemand de workflow **Check Official Nocturne release manually** start, de gegenereerde wijziging controleert en samenvoegt.

Latest controleert dagelijks of upstream `main` een nieuwer commit heeft waarvoor de officiële `build-and-push`-job volledig is geslaagd. De updater controleert de API-broncommit, kiest precies één linux/amd64-manifest, zet API en web vast op digest en sluit races met veranderende tags uit. Daarna moeten unit-tests, beide container-smoketests en een vorige-Latest-naar-kandidaat-herstelproef slagen. Branchbeveiliging blokkeert auto-merge zolang verplichte controles niet groen zijn.

De Home Assistant app-storebeschrijving toont bij Latest de korte commitcode plus de exacte upstream-committijd in UTC. Beide worden door dezelfde dagelijkse promotie bijgewerkt, zodat de zichtbare datum bij de werkelijk vastgezette code blijft horen.

Een Latest-update kan ondanks deze technische tests functioneel onvolledig zijn of een niet-terugdraaibare databasemigratie bevatten. Houd Latest-data vervangbaar, maak koude back-ups en gebruik hem niet voor behandelbeslissingen, alarmen of automatische dosering.

[Installatie](INSTALLATIE.md) · [Updatebeleid](UPDATES.md) · [Testbereik](TESTING.md)
