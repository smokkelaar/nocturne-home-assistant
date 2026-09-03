# Nocturne Personal Release

Een derde, onafhankelijke HA-app voor persoonlijke uitbreidingen. De bestaande
**Nocturne Official Release** en **Nocturne Latest Release** behouden hun namen,
instellingen, pakketversies, poorten en gegevens. Personal is geen migratie.

| App | Standaardpoort | Inhoud |
| --- | --- | --- |
| Official | 8448 | Officiële Nocturne-release |
| Latest | 8449 | Goedgekeurde dagelijkse Nocturne-bronversie |
| Personal | 8450 | Dezelfde Daily-basis, met de broncode uit de Personal-fork |

## Installeren

1. Vernieuw de HA app-store bij de al toegevoegde repository
   `https://github.com/smokkelaar/nocturne-home-assistant`.
2. Installeer **Nocturne Personal Release**. Laat de andere apps geïnstalleerd.
   Deze app bouwt ook Nocturne zelf uit broncode; dat kost meer tijd, geheugen en
   tijdelijke opslag dan de twee bestaande pakketten. Wacht tot de bouw klaar is.
3. Gebruik dezelfde geldige certificaatbestandsnamen als bij de andere apps,
   maar stel voor Personal een eigen URL met poort **8450** in:

   ```yaml
   public_url: https://nocturne.example.net:8450
   certificate: fullchain.pem
   private_key: privkey.pem
   gateway_auth: true
   ```

   Vervang de voorbeeldhostnaam door je eigen certificaatnaam. Er is geen nieuwe
   router-portforward nodig voor lokaal gebruik. Publiceer geen database-, API-
   of ingress-poorten. De containerpoort blijft `8448/tcp`, de hostpoort is 8450.
4. Start uitsluitend Personal. Open zijn HA-webinterface en wacht op gereedheid.
5. Open Nocturne vanuit die pagina. Gebruik zo nodig de gatewaycode van **Personal**.
   Maak een eigen instantie, account/passkey en herstelcodes aan. Begin zonder
   echte gezondheidsdata. Bestaande aanmeldingen worden niet geïmporteerd.
6. Test aanmelden, afmelden, herladen en een herstart van uitsluitend Personal.
   Controleer dat Official/Latest hun eigen aanmelding behouden.

De optie `gateway_auth: false` kan pas na de bestaande veilige eerste inrichting,
net als bij de andere apps. [Gateway-instructies](GATEWAY.md).

## Google Health en medicatie vanaf Personal 0.2.0

Log in als beheerder en kies **Personal** in het Nocturne-menu:

| Onderdeel | Wat werkt in deze eerste uitbreiding |
| --- | --- |
| Google Health | Google-login, zelf stappen/hartslag/gewicht kiezen, import ongeveer elke 15 minuten, meetgeschiedenis, ontkoppelen en import wissen |
| Medicatielogboek | Middel en werkzame stof, werkelijke hoeveelheid in mg/microgram, tijdstip, toegediend/overgeslagen, plaats en notities, wijzigen/verwijderen |

**[Stap-voor-stap functiehandleiding](https://github.com/smokkelaar/nocturne-personal/blob/personal/PERSONAL_USAGE.md)**
met de eenmalige Google Cloud-clientinstellingen. Gebruik de callback-URL uit je
eigen Personal-scherm; deel het client-secret niet in issues of chats.

De metingen staan in de eigen Personal-weergave, nog niet in alle bestaande
Nocturne-rapporten. Niet-ondersteunde typen blijven zichtbaar maar niet selecteerbaar.
Google Health is geen toegang op afstand tot de lokale Android Health Connect-database.
Echte Google-toestemming en bronbeschikbaarheid vragen nog een proef met jouw account.

Het medicatielogboek is geschikt om bijvoorbeeld Mounjaro te noteren, niet om de
dosis of een opbouwschema te bepalen. Het verandert geen insuline-/IOB-berekeningen.
Begin met een herkenbare testregistratie en controleer bewaren, wijzigen en wissen.

Personal begint met dezelfde Nocturne-basis als de goedgekeurde Daily, maar
compileert API, web en de native alertbibliotheek zelf. Daardoor worden toekomstige
wijzigingen aan de Personal-broncode werkelijk meegenomen. Het is niet alleen
een andere naam op de ongewijzigde Daily-binaries.

## Drie herkenbare versies

- **HA-wrapper**: de technische HA-basis, aanvankelijk 0.1.5.
- **Personal**: de eigen uitbreidingsversie, nu 0.2.0.
- **Nocturne**: de goedgekeurde Daily-broncommit met datum/tijd.

HA gebruikt voor deze aparte app de Personal-versie met leveringsnummer, zoals
`0.2.0-1`. Een nieuwe Daily-/Personal-broncommit verhoogt alleen het leveringsnummer
als de uitbreidingsversie gelijk blijft. Een wijziging in Personal verhoogt niet
de pakketversie van Official of Latest.

## Automatisch bijblijven

Broncode: [smokkelaar/nocturne-personal](https://github.com/smokkelaar/nocturne-personal),
standaardbranch `personal`. `.personal/version.json` vermeldt de uitbreidingsversie
en Daily-basis. Gezondheidsdata, OAuth-tokens en wachtwoorden horen nooit in Git.

1. De bronfork controleert dagelijks om 07:13 UTC de al goedgekeurde Daily-pin
   in de HA-repository. Hij volgt niet blind de allernieuwste upstream-main.
2. Een normale merge behoudt persoonlijke commits. Conflicten stoppen de
   synchronisatie. De bron-PR passeert metadata-/afstammingscontroles en de Personal
   OAuth-, import-, medicatie- en rechtencontroles; dit is nog
   geen geslaagde runtimebouw of HA-publicatie.
3. Om 07:43 UTC controleert de HA-repository de Personal-bron, legt commit en
   archiefchecksum vast en opent een uitsluitend Personal betreffend updatevoorstel.
4. De verplichte **Container smoke test** bouwt bij Personal-wijzigingen zowel
   API als web uit dezelfde bron, test opstarten en voert een koude herstelproef
   en, indien aanwezig, een vorige-Personal-upgrade uit. Bij de eerste versie is
   alleen een herstelproef met dezelfde versie mogelijk.
5. Alleen na verplichte controles mag het updatevoorstel automatisch samenvoegen.
   Daarna kan HA de update aanbieden. Automatisch installeren vereist dat jij
   **Automatisch bijwerken** voor alleen Personal inschakelt.

De containerproef controleert vanaf 0.2.0 ook de echte PostgreSQL-migraties,
versleutelde clientinstellingen, afgeschermde Personal-routes, medicatie-invoer,
wijzigconflicten, verwijderen en behoud na een herstart. De Google-antwoorden
worden in aparte unit-tests nagebootst; CI logt niet in op Google.

GitHub-planningen kunnen vertraagd zijn. Als Daily later klaar is dan deze
controles, kan Personal een cyclus achterlopen. Een workflow kan ook handmatig
worden gestart. Geen nieuwe versie zonder nieuwe bron en geslaagde controles.

Nocturne-bron en bouwafhankelijkheden zijn vastgezet. De app downloadt bij het
starten geen veranderlijke broncode. De HA-host bouwt de container lokaal; deze
repository publiceert geen nieuwe samengestelde Personal-binaries. De bestaande
upstream-runtime vormt de OS/.NET-basis, niet de te gebruiken Personal-appcode.

## Veiligheid en herstel

- Eigen slug `nocturne_personal`, eigen `/data`, database, sleutels, opties en back-ups.
- Eigen sessiecookies met `NocturnePersonal_`. Alleen een andere poort was daarvoor
  niet voldoende; de Personal-gateway verwerkt de eigen cookienamen.
- Kopieer geen database, passkeys of sleutels tussen de drie apps.
- Een mislukte bouw verandert de aangeboden Personal-versie niet. Een eerdere
  container terugplaatsen draait een databasemigratie niet vanzelf terug.
- Maak vóór updates een koude back-up van de juiste app. Behandel Personal als
  testomgeving, niet als basis voor medicatie, alarmen of automatische dosering.
- Geautomatiseerde tests bewijzen geen echte passkey-ceremonie, HA-installatie,
  medische juistheid of geschiktheid voor alle upstream-wijzigingen.

## Ontwikkelen

Productuitbreidingen komen in de bronfork. HA-verpakking en zijn tests blijven in
de HA-repository. Houd wijzigingen klein en versieer uitbreidingen in
`.personal/version.json`. De bestaande AGENTS.md-codeconventies blijven gelden.

`tools/update_personal.py --update` schrijft uitsluitend `upstream-personal.json`
en `nocturne_personal`. `--check` controleert de gegenereerde bestanden zonder
netwerk of live HA-toegang. Wijzigingen aan het bron-/wrappercontract moeten
expliciet worden beoordeeld; wijzig niet ongemerkt de twee bestaande pakketten.
