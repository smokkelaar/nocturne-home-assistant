# Open punten: concrete oplossingen en een veilige volgorde

**Voorstellen, geen reeds geïmplementeerde functies.** Dit document vult de gaten uit [de testmatrix](TESTING.md), [migratiewaarschuwing](MIGRATION.md) en [installatiehandleiding](INSTALLATIE.md) in met afgebakende ontwikkelstappen. Het is geen toestemming om een bestaande installatie te wijzigen of gegevens te wissen.

## Eerst onderscheid maken

| Soort gat | Oplossing in deze documentatieronde | Wat daarmee nog niet is opgelost |
|---|---|---|
| Onvindbare of te korte handleiding | Een prominente Nederlandse instaplink, acht stappen, vier schema's en controlepunten | Geen technische installatiewizard |
| Onduidelijke HTTPS/DNS-voorbereiding | Certificaatroute, Windows-test, DNS-uitleg en onderscheid tussen naam, adres en poort | Geen automatische DNS-inrichting of certificaatherlading |
| Verwarring over inloggen | HA-account, gatewaycode en Nocturne-passkey apart uitgelegd | Geen vereenvoudiging van de werkelijke authenticatie |
| Onzeker of iets echt werkt | Concrete eindtest en tabel met bekende foutmeldingen | Geen garantie voor back-upherstel, upgrades, medische functies of lange-termijnstabiliteit |

Een handleiding kan een technische beperking zichtbaar maken, maar kan deze niet wegschrijven. Gebruik daarom bij ieder voorstel onderstaande acceptatietest.

## Aanbevolen prioriteit

| Prioriteit | Werkpakket | Waarom eerst / later? | Bewijs dat het klaar is |
|---|---|---|---|
| **P0** | Back-up en herstel aantonen | Noodzakelijke vangrail voor iedere migratie of upgrade | Een nieuwe lege omgeving herstelt dezelfde testdata en bijbehorende sleutels |
| **P0** | Lokale app naar repository-app migreren | Nodig om de huidige lokale gebruiker veilig repository-updates te geven | Bestaand account werkt op de doelapp, bron en back-up blijven recoverable |
| **P1** | Installatiecontrole in de app | Voorkomt de meeste hostname/poort/certificaatfouten vóór accountaanmaak | Elke misconfiguratie geeft een gerichte fout, zonder valse groenmelding |
| **P1** | Certificaten automatisch herladen | Voorkomt handmatig app-herstarten na iedere vernieuwing | Nieuwe geldige certificaatketen wordt geladen zonder databasestop |
| **P1** | Echte versie-upgrade testen | Verse boot/restart is niet hetzelfde als een databasemigratie | Vorige ondersteunde release → kandidaat → verificatie; herstelroute apart bewezen |
| **P2** | Gatewaycode veilig roteren | Een gedeelde screenshot mag geen permanente toegang geven | Alleen gatewaycode verandert; account/database blijven intact |
| **P2** | IPv6, andere apparaten en stroomuitval | Dezelfde UI moet meer dan alleen de ontwikkel-pc overleven | Expliciete matrix met IPv4/IPv6, Windows/Android en herstartscenario's |
| **P3** | Connectors, HA-integratie en embedding | Pas zinvol als identiteit, herstel en updates betrouwbaar zijn | Afzonderlijke functionele en beveiligingstests per uitbreiding |

## 1. Back-up en herstel: maak eerst de reddingsroute aantoonbaar

**Huidig gat:** het manifest vraagt een koude back-up en data/sleutels staan samen in `/data`, maar een volledige HA-herstelproef is nog niet vastgelegd. De huidige CI bewijst alleen dat dezelfde containerdata een normale stop/start overleven.

**Voorstel:** begin met een aparte testinstallatie zonder medische gegevens. Maak daar herkenbare testinstellingen en een klein testrecord. Maak een HA-back-up van uitsluitend die testapp, bewaar een versleutelde kopie buiten HA en herstel in een schone testomgeving met dezelfde ondersteunde appidentiteit. Verifieer een niet-geheime controlewaarde van de data en vergelijk sleutelvingerafdrukken alleen lokaal; publiceer de sleutels niet.

Voeg daarna een reproduceerbare, gedocumenteerde restore-test toe. Een aanvullende logische PostgreSQL-export kan nuttig worden, maar alleen `pg_dump` is **geen volledige Nocturne-back-up**: instance/authenticatiesleutels, rollen en opties horen bij dezelfde herstelset. Zie ook [PostgreSQL's back-upmethoden](https://www.postgresql.org/docs/17/backup.html).

**Acceptatie:** testdata, accountinstellingen en sleutelidentiteit komen terug; login wordt handmatig gecontroleerd. Ontbrekende of beschadigde onderdelen geven een duidelijke stop, geen automatische reset. Documenteer ook waar de HA-back-upherstelsleutel bewaard moet worden.

## 2. Migratie: een expliciete, eenmalige overdracht

**Huidig gat:** `local_nocturne_local` en de repository-app hebben verschillende Supervisor-identiteiten en `/data`-mappen. Een nieuw geïnstalleerde app kan daarom keurig werken maar toch leeg zijn.

**Voorstel:** maak een onderhoudstool voor een **gecoördineerde export/import**, niet voor blind kopiëren naar een draaiende database. Ontwerp die eerst rond exact bekende compatibele Nocturne- en PostgreSQL-versies. Het pakket bevat database, bijbehorende sleutels, relevante opties en een manifest met versies en integriteitscontroles; nooit onversleuteld in GitHub of een openbaar issue.

De doeltool moet:

1. Alleen in expliciete onderhoudsmodus en met bevestiging van de beheerder werken.
2. Een bronback-up en geslaagde herstelproef vereisen.
3. Import in een al gevulde doelinstallatie weigeren.
4. PostgreSQL-/Nocturne-compatibiliteit en de ongewijzigde publieke hostname/origin controleren.
5. Database en sleutels als één set overnemen, met correcte bestandsrechten.
6. De bron gestopt maar **niet verwijderd** laten; nooit twee instanties met dezelfde identiteit/poort tegelijk laten werken.

De exacte overdracht via Supervisor/back-upformaat of een app-eigen exportfunctie moet eerst worden onderzocht en getest; er is nu geen bewezen knop die een bestaande lokale back-up naar een andere repository-identiteit omzet.

**Acceptatie:** bestaande instantie en passkey-account werken na doel-herstart. Een terugweg is getest vóór definitieve ingebruikname. Na nieuwe gegevensinvoer in de doelapp kan de oude bron achterlopen: terugschakelen mag die nieuwe gegevens niet stilzwijgend verliezen.

## 3. Een installatiecontrole in de HA-statuspagina

**Huidig gat:** de huidige pagina rapporteert vooral processen/listeners. “HTTPS gereed” betekent nog niet dat de browser de juiste server met een vertrouwd certificaat bereikt.

**Voorstel:** voeg een aparte **Controleer installatie**-sectie toe met drie duidelijk gescheiden kolommen:

| App kan zelf controleren | Browser/apparaat moet controleren | Mens bevestigt |
|---|---|---|
| URL-syntax, certificaatbestanden, sleutel/certificaat-match, SAN-hostnaam en verloopdatum | Werkelijk gebruikte DNS-route, certificaatvertrouwen en beschikbaarheid van WebAuthn | Accountlogin geslaagd en herstelcodes veilig bewaard |
| API-gereedheid en web-respons via de eigen gateway | Werkelijke origin/poort van de geopende tab | Herstarttest geslaagd |

Toon bijvoorbeeld **certificaat geldig tot …**, **naam komt overeen**, **browsercontrole nog niet uitgevoerd**, in plaats van alles groen te kleuren zodra een socket luistert. Een server kan niet bewijzen welke DNS-cache, CA-vertrouwenslijst of passkeyvoorziening een telefoon gebruikt.

Gebruik gerichte foutcodes met een link naar de juiste handleidingstap. Een voorbeeld: `CERT_HOSTNAME_MISMATCH → controleer public_url en certificaat`. Geen gevoelige headers, tokens of private sleutels in diagnostiek. Dit kan zonder nieuwe HA-API-rechten; de bestaande ingresspagina is voldoende voor een eerste versie.

**Acceptatie:** fixtures voor verkeerde hostnaam, verlopen certificaat, ontbrekende sleutel, onbereikbare backend en niet-uitgevoerde browsercontrole. Alleen werkelijk uitgevoerde controles kunnen “geslaagd” tonen.

## 4. Certificaatvernieuwing zonder app-/databasestop

**Huidig gat:** DuckDNS kan de certificaatbestanden vernieuwen, maar nginx gebruikt het ingelezen certificaat tot een herstart/herlaadactie.

**Voorstel:** laat de wrapper wijzigingen aan het ingestelde certificaat/sleutelpaar detecteren. Wacht tot beide bestanden stabiel en passend zijn, controleer de hostnaam/geldigheid en voer de nginx-configuratietest uit. Herlaad daarna uitsluitend nginx met zijn ondersteunde reloadmechanisme; laat PostgreSQL, API en web draaien. [nginx documenteert deze gecontroleerde herlaadroute](https://nginx.org/en/docs/control.html).

Bij onvolledige of ongeldige vernieuwing: niet herladen, huidig proces laten draaien, een duidelijke fout/verloopwaarschuwing tonen en geen sleutelmateriaal loggen. De wrapper hoeft zelf geen certificaten aan te vragen of schrijfrechten op `/ssl` te krijgen.

**Acceptatie:** een geldige nieuwe certificaatketen verschijnt in een nieuwe TLS-verbinding, het account blijft werken en de database stopt niet. Een mismatch, halfgeschreven bestand of ongeldig certificaat wordt geweigerd. Controleer ook herstel nadat later alsnog een geldig paar verschijnt.

## 5. Upstream-updates: ook de overgang testen

**Huidig gat:** de bot bouwt en test een nieuwe versie in een lege omgeving. Dat bewijst niet dat een bestaande database veilig naar die versie migreert.

**Voorstel:** breid CI uit met een upgradeproef:

1. Start de laatst ondersteunde release met een lege, disposable database.
2. Maak niet-gevoelige testdata en bewaar een herstelset.
3. Stop netjes en start de kandidaatversie met diezelfde gegevens.
4. Controleer schema/instellingen/data en bestaande authenticatie-identiteit.
5. Test daarna **restore van de oude back-up naar de oude release**, niet alleen “oude image over nieuwe database starten”.

Voor accountflows kan een aparte browsertest met een virtuele passkey-authenticator en een correct vertrouwde test-HTTPS-host worden toegevoegd. Houd daarnaast een echte Windows/Android-handtest: gesimuleerde WebAuthn is geen bewijs dat alle apparaten werken.

Pas na betrouwbare herstel-/upgradeproeven is optionele, strikter geautomatiseerde vrijgave te overwegen. Een patchnummer alleen zegt niet dat een release geen databasemigratie bevat. Houd handmatige beoordeling voor onbekende migraties, grote wijzigingen en niet-ondersteunde versie-overgangen.

**Acceptatie:** de update-PR verwijst naar bewijs voor zowel verse installatie als vorige-versie-upgrade en herstel. Een mislukte overgang blokkeert publicatie, zonder productiegegevens te gebruiken.

## 6. Gatewaycode roteren zonder identiteitsverlies

**Huidig gat:** de code is zichtbaar op de HA-statuspagina en kan per ongeluk in een screenshot terechtkomen. Er is nog geen ondersteunde rotatieknop.

**Voorstel:** een expliciete onderhoudsactie **Vernieuw alleen gatewaycode**. Verander atomair uitsluitend het veld `gateway`, werk het htpasswd-bestand en de weergegeven code bij en herlaad de gateway gecontroleerd. Laat `instance`, PostgreSQL-, migrator-, API- en websleutels identiek. Bescherm de actie tegen ongeautoriseerde toegang en onbedoelde GET/CSRF-aanroepen; alleen “de knop staat in HA” is niet voldoende als autorisatieontwerp.

**Acceptatie:** de oude Basic-code werkt niet meer bij een nieuwe aanvraag, de nieuwe wel, en dezelfde Nocturne-passkey/database blijven werken na herstart. Een gefaalde rotatie houdt een coherente, herstelbare toestand; nooit `secrets.json` verwijderen.

## 7. IPv6, andere apparaten en herstartscenario's

**Huidig gat:** een IPv4-oplossing op één Windows-pc bewijst geen ondersteuning voor AAAA-routes, telefoons of de volledige HA-hostpoortketen.

**Voorstel:** test eerst afzonderlijk DNS A/AAAA, de containerlistener, Supervisor/Docker-poortpublicatie en de browserroute. Voeg pas een IPv6-listener toe als het platformpad echt werkt; alleen `listen [::]` toevoegen aan nginx is onvoldoende bewijs. Houd interne database/API/web-listeners privé. Vermijd `host_network` of brede firewallversoepeling als snelle oplossing.

Maak daarnaast een korte matrix voor Windows/Android, lokale DNS versus de tijdelijke hosts-regel, app-restart, HA/VM-herstart en uitval tijdens opstarten. Een abrupte uitvaltest hoort uitsluitend op wegwerpdata en een herstelbare testmachine.

**Acceptatie:** beide ondersteunde IP-routes tonen hetzelfde geldige certificaat en dezelfde instantie; niet-ondersteunde routes worden eerlijk gedocumenteerd. Herstel na uitval veroorzaakt geen stille herinitialisatie of gewijzigde sleutels.

## 8. Later: connectors, HA-entiteiten en ingebedde UI

- **Connectors:** de gateway verwijdert inkomende Authorization en vereist extra Basic-authenticatie. Onderzoek per Nocturne-client het officiële authenticatiemechanisme en ontwerp een beperkte, expliciet beveiligde API-route. Verwijder niet alle gatewaybeveiliging om één client te laten werken. Begin met niet-gevoelige synthetische gegevens, minimale rechten en tests voor ongeautoriseerde toegang.
- **HA-integratie:** begin met technische, read-only entiteiten zoals appversie, bereikbaarheid en certificaatverloop. Exporteer niet standaard gezondheidsmetingen. Bepaal eerst welke veilige lokale status-API daarvoor beschikbaar moet zijn; HACS is een mogelijke distributieroute voor zo'n latere integratie, niet voor de database-app zelf.
- **Ingebedde Nocturne-interface:** houd voorlopig de aparte vertrouwde HTTPS-tab. Onderzoek origin/passkey-, cookie-, CSP- en iframe-beperkingen voordat volledige HA-ingress-embedding wordt beloofd. “Het scherm past in een iframe” bewijst geen werkende login.
- **Prebuilt images en meer architecturen:** kunnen installatie versnellen, maar vragen bron-/licentiecontrole, per-architectuur runtime-tests en supply-chainbeheer. Los eerst de in [UPSTREAM.md](../UPSTREAM.md) genoemde licentie-/herkomstvragen op voordat gecombineerde binaries publiek worden verspreid.

## Voorstel voor de eerstvolgende ronde

**Eén afgebakend resultaat: een herstelde lege testinstantie aantoonbaar terugkrijgen uit een back-up.** Lever daarvoor een exacte procedure en testverslag op, zonder de huidige installatie te vervangen. Daarna kan de migratietool verantwoord worden ontworpen. Installatiechecks en certificaatherlading kunnen als afzonderlijke kleine wijzigingen volgen, elk met eigen tests en release-notities.

Dit volgt het principe: eerst gegevens kunnen terughalen, dan verplaatsen, daarna updates verder automatiseren. De bestaande werkende installatie blijft tot die tijd het uitgangspunt, niet het proefobject voor destructieve tests.
