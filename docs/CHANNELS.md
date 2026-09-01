# Nocturne Official en Latest naast elkaar

Na één keer toevoegen van deze repository toont Home Assistant twee losse apps:

| Eigenschap | Nocturne Official Release | Nocturne Latest Release |
|---|---|---|
| Doel | Handmatig bevorderde officiële Nocturne-release | Vaak bijgewerkte momentopname van upstream `main` |
| HA-slug / gegevensidentiteit | `nocturne_local` — bestaande 0.1.x-installaties blijven hier | `nocturne_latest` — volledig eigen `/data` |
| Standaard hostpoort | 8448 | 8449 |
| Standaard URL | `https://homeassistant.local:8448` | `https://homeassistant.local:8449` |
| Upstream-selectie | Semantische release, momenteel 0.2.4 | Exacte geteste `main`-commit |
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
