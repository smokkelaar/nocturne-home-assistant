# Nocturne Official en Latest naast elkaar

## Main synchronization — 2026-10-14

The common upstream base is `2efc0d66e12ff9ad1dc10767075092eca78efb32`
(2026-10-14T20:21:30Z), including the AAPS temporary-basal fix #2033 and A1c
display preferences #1977. Later translation-only commits skip image publication;
the installers use the newest verified published main ancestor.

Official and Latest both use the official Nightscout main API/web image pair,
without Personal source changes. The functional wrapper remains **0.1.13**.
HA package versions are separate and become available only after both native
architectures, runtime/upgrade checks and anonymous image verification pass.

| Channel | Source | Upstream base | Additional code |
|---|---|---|---|
| Official / Latest | Approved official main | `2efc0d6` | None |
| Personal 0.3.37 | Exact approved Personal source | `2efc0d6` | Personal extensions and the additional relative-field reporting guard |
| Test A / B / C | Same source as Personal | `2efc0d6` | Same Personal extensions, isolated data and cookies |

Images are resolved through the immutable `main-2efc0d6` tags and OCI digests.
`latest` denotes upstream's official release and is not the Daily discovery tag.
[Upstream publication](https://github.com/nightscout/nocturne/actions/runs/38631381085).
Published package versions and image digests are in each channel's `config.json`
and `provenance.json`; runtime source and feature versions are in
`rootfs/opt/nocturne-ha/version.json`. These files must agree before HA is updated.

Na één keer toevoegen van deze repository toont Home Assistant twee losse apps:

| Eigenschap | Nocturne Official Release | Nocturne Latest Release |
|---|---|---|
| Doel | Officiële main in de bestaande Official-installatie | Dezelfde geverifieerde upstream `main` |
| HA-slug / gegevensidentiteit | `nocturne_local` — bestaande 0.1.x-installaties blijven hier | `nocturne_latest` — volledig eigen `/data` |
| Standaard hostpoort | 8448 | 8449 |
| Standaard URL | `https://homeassistant.local:8448` | `https://homeassistant.local:8449` |
| Upstream-selectie | Dezelfde goedgekeurde main-lock als Latest | Exacte geteste `main`-commit |
| Imagegebruik | Officiële API/web op exacte OCI-digests | Dezelfde officiële API/web op exacte OCI-digests |
| Repository-update | Volgt de goedgekeurde Latest-bron via `main-rollout.json` | Dagelijkse controle; auto-merge uitsluitend na verplichte tests |
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

De effectieve Official-main-bron volgt `upstream-latest.json` via de expliciete
main-policy. `upstream.json` bewaart de oude releasebasis voor de generator;
de gepubliceerde `provenance.json` en runtimeversie tonen de werkelijk gebruikte main-bron.

Latest controleert dagelijks of upstream `main` een nieuwer commit heeft waarvoor de officiële `build-and-push`-job volledig is geslaagd. De updater controleert de API-broncommit, kiest precies één linux/amd64-manifest, zet API en web vast op digest en sluit races met veranderende tags uit. Daarna moeten unit-tests, beide container-smoketests en een vorige-Latest-naar-kandidaat-herstelproef slagen. Branchbeveiliging blokkeert auto-merge zolang verplichte controles niet groen zijn.

De Home Assistant app-storebeschrijving toont bij Latest de korte commitcode plus de exacte upstream-committijd in UTC. Beide worden door dezelfde dagelijkse promotie bijgewerkt, zodat de zichtbare datum bij de werkelijk vastgezette code blijft horen.

Een Latest-update kan ondanks deze technische tests functioneel onvolledig zijn of een niet-terugdraaibare databasemigratie bevatten. Houd Latest-data vervangbaar, maak koude back-ups en gebruik hem niet voor behandelbeslissingen, alarmen of automatische dosering.

[Installatie](INSTALLATIE.md) · [Updatebeleid](UPDATES.md) · [Testbereik](TESTING.md)
