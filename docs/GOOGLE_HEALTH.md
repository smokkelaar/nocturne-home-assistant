# Google Health / Health Connect naar Nocturne

**Kanaalkeuze bijgewerkt:** de gebruiker wil deze uitbreidingen uitsluitend in
de aparte **Nocturne Personal Release**. De bestaande Official- en Daily-apps en
hun installatieopties blijven ongewijzigd. [Personal](PERSONAL.md).

**Status: technisch ontwerp, nog niet gebouwd of gekoppeld.** Onderzocht op
2 september 2026, voor HA-wrapper 0.1.5. Dit document verandert geen installatie,
toestemmingen of gezondheidsgegevens. Het is geen installatiehandleiding voor
een al beschikbare functie.

**Gewenste eindervaring, door de gebruiker verduidelijkt:** Google-login → zelf
gegevens aanvinken/toestemming geven → automatisch ophalen en zichtbaar in
Nocturne. Geen handmatige exports, API-tokens plakken of vaste beperking tot
alleen stappen, hartslag en gewicht.

**Acceptatieregel:** ieder meettype dat de koppeling als aanvinkbaar aanbiedt,
moet een volledige werkende route hebben van bron tot opslag en weergave.
Een succesvolle Google-login mag nooit suggereren dat niet-ondersteunde
metingen ook worden verwerkt. De eerste drie typen hieronder vormen een
technische proef, niet het gewenste maximum van de uiteindelijke koppeling.

## 1. Advies in het kort

Voeg een optionele **Health Bridge** toe aan uitsluitend de Personal HA-app. Deze leest
gekozen metingen en schrijft ze, na toestemming, naar de eigen Nocturne-omgeving.
Eerst een alleen-lezen proef, daarna gecontroleerde import. Geen Google-wachtwoord
in Home Assistant en geen rechtstreekse databasewijzigingen.

Bouw nieuwe ondersteuning op de **Google Health API**, niet op de oude Google Fit
API. Google ondersteunt de Fit-API's volgens de huidige planning tot eind 2026.
Voor gegevens die uitsluitend op Android staan, is **Health Connect** de andere
route. Google Health-cloudgegevens en lokale Health Connect-gegevens zijn niet
automatisch dezelfde verzameling. [Google: migratieroutes](https://developer.android.com/health-and-fitness/health-connect/migration/fit).

| Waar staan de gegevens? | Voorgestelde route | Extra onderdeel |
| --- | --- | --- |
| Beschikbaar via Google Health, bijvoorbeeld vanuit een gesynchroniseerde Fitbit/Pixel Watch | Google Health API → Health Bridge → Nocturne | Eenmalige Google Cloud/OAuth-configuratie en toestemming |
| Alleen in Android Health Connect, bijvoorbeeld vanuit andere telefoon-apps | Android-koppeling → Health Bridge → Nocturne | Een Android-app met expliciete Health Connect-leestoestemming |
| Alleen in de oude Google Fit-app/historie | Eerst onderzoeken welke gegevens via een opvolger beschikbaar zijn | Geen volledige migratie of toegang veronderstellen |

Een gewone webapp op Home Assistant kan Health Connect op een telefoon niet
rechtstreeks uitlezen. De Android-route is een afzonderlijk bouwtraject; dit
ontwerp beweert niet dat er al een geschikte Nocturne-telefoonapp beschikbaar is.

## 2. Uitbreidbare gegevenscatalogus

De bridge krijgt geen hardgecodeerd scherm met slechts drie schakelaars, maar
een catalogus met per type: naam, bron, Google-recht, eenheid, synchronisatiemethode,
Nocturne-doel, weergave en geteste upstreamversies. Nieuwe typen worden via een
adapter toegevoegd. Aanvinkbaar worden ze pas als de hele route is getest.
Niet-ondersteunde typen krijgen een expliciete status, geen werkende schakelaar.

Het streven is alle door de gebruiker gewenste, via de gekozen bron leesbare
typen te ondersteunen. Waar Nocturne nog geen passend model of scherm heeft,
hoort daar een upstream-uitbreiding bij. Alleen een ruwe kopie bewaren in de
bridge telt niet als beschikbaar in Nocturne.

| Gegeven | Eerste doel | Bijzonderheden |
| --- | --- | --- |
| Stappen | Aantallen en tijdstippen naar Nocturne | Overlappende telefoon-/horlogebronnen niet optellen; dagtotalen niet naast dezelfde deelintervallen importeren |
| Hartslag | Tijdreeks in slagen per minuut | Alleen werkelijk ontvangen metingen; geen ontbrekende minuten invullen |
| Gewicht | Metingen in kg, eerst alleen voorbeeldweergave | Nocturne heeft opslag; beperkte schrijfrechten moeten nog worden opgelost, zie §5 |
| Vetpercentage | Later, gekoppeld aan een echte gewichtsmeting als bron/tijdstip dat toelaten | Alleen aangeleverde waarden; niet afleiden uit gewicht |
| Slaap | Tweede uitbreidingsstap | Eerst sessies, slaapfasen en tijdzones passend maken; niet alleen een aantal uren als willekeurige notitie opslaan |
| Afstand, energieverbruik, SpO₂, HRV en andere metingen | Per type onderzoeken | Beschikbaarheid bij Google bewijst nog geen passend Nocturne-opslagveld of grafiek |

Google documenteert onder meer stappen, hartslag, gewicht, lichaamsvet en slaap.
Beschikbaarheid hangt af van bron, synchronisatie en verleende rechten. De
koppeling kan geen metingen ophalen die de bron niet heeft opgeslagen.
[Google: gegevenstypen](https://developers.google.com/health/data-types).

Nocturne heeft modellen en API's voor de drie hoofdtypen. Dat is nog geen bewijs
dat iedere gewenste grafiek in beide webversies zichtbaar is: opslag, API-uitlezing
en dashboardweergave krijgen afzonderlijke acceptatietests.

## 3. Zo moet de bediening eruitzien

Een nieuwe sectie **Gezondheidskoppelingen** op de beschermde HA-pagina van iedere
Personal-app. Dit zijn voorgestelde knoppen, geen bestaande instellingen:

1. **Google verbinden**: openen in de normale browser; Google verzorgt het
   inloggen. Geen wachtwoordveld voor Google in onze app en geen token kopiëren.
2. **Gegevens kiezen en toestemming geven**: kies de gewenste beschikbare typen
   uit de catalogus. Google bevestigt de benodigde toegang; extra typen kunnen
   later om aanvullende toestemming vragen zonder een nieuw account te maken.
   Als de bron uitsluitend Health Connect is, leg uit waarom daarvoor de
   afzonderlijke Android-route nodig is in plaats van een misleidende Google-login.
3. **Selectie bevestigen**: toon welke gekozen typen echt naar Nocturne gaan en
   welke niet beschikbaar zijn. Slaap en overige typen zijn geen permanente
   uitsluiting, maar komen pas vrij na hun volledige implementatie en tests.
4. **Voorbeeld ophalen**: maximaal de afgelopen 24 uur, lokaal en alleen-lezen.
   Toon per type bron, aantal records, periode en eventuele ontbrekende rechten.
   Geen gewichtsmeting in die periode is een geldige lege uitkomst; de gebruiker
   kan bewust een ruimere voorbeeldperiode kiezen.
5. **Nocturne toestemming geven**: autoriseer de bridge voor deze omgeving.
6. **Import inschakelen**: expliciete bevestiging van doelomgeving, gegevenstypen
   en terugkijkperiode. Standaard één omgeving, niet beide tegelijk.
7. **Nu synchroniseren**, **Pauzeren** en **Verbinding verbreken** blijven beschikbaar.

De bestaande Nocturne-knop **Add device** hoort bij het autoriseren van een externe
app. Hij is niet zelf een Google-koppeling. Een bridge kan hiervoor een eigen
Nocturne-apparaatcode aanvragen, nadat zij correct als OAuth-client is geregistreerd.
De Google-toestemming en Nocturne-toestemming zijn twee verschillende stappen.
[Nocturne OAuth-controller](https://github.com/nightscout/nocturne/blob/3b7514591f854f4794deeeb75d43e33d979d1ee4/src/API/Nocturne.API/Controllers/Authentication/OAuthController.cs).

Presenteer beide binnen één begeleide verbindingsprocedure. Hergebruik waar
mogelijk de bestaande ingelogde Nocturne-sessie voor de expliciete goedkeuring;
laat de gebruiker geen technische tokens opzoeken. Google toont rechten op
categorieniveau, niet noodzakelijk één vakje per meettype. Toon daarom precies
welke metingen onze selectie omvat. Een brede Google-toestemming is geen reden
om niet-geselecteerde gegevens te lezen of gekozen gegevens stilzwijgend weg te laten.

Status mag nooit alleen één groen vinkje zijn. Toon apart:

- Google verbonden / opnieuw toestemming nodig.
- Per type: toestemming, laatste ophaalpoging, laatste geslaagde synchronisatie en
  het tijdstip van de nieuwste bronmeting.
- Nocturne verbonden / import gepauzeerd / schrijfrecht ontbreekt.
- Aantallen toegevoegd, bijgewerkt, overgeslagen en afgewezen, zonder ruwe data in logs.
- Duidelijk verschil tussen **geen metingen ontvangen**, **geen toestemming** en
  **ophalen mislukt**. Een ontbrekende waarde is geen nul.

## 4. Inpassing in deze repository

Voorkeur: een kleine, apart draaiende helper binnen de nieuwe Personal-container.
De derde HA-app en bronfork bieden plaats aan de noodzakelijke Nocturne-uitbreidingen.
De twee bestaande apps krijgen deze gezondheidskoppeling niet. De bridge zelf is
nog niet geïmplementeerd.

| Onderdeel | Verantwoordelijkheid |
| --- | --- |
| Google-adapter | Toestemming, tokenvernieuwing en alleen-lezen API-verzoeken |
| Normalisatielaag | Eenheden, tijdstippen, bronidentiteit, correcties en ontdubbelen |
| Nocturne-adapter | Geauthenticeerde verzoeken naar uitsluitend de eigen Nocturne-API |
| Synchronisatiewerker | Planning, herpogingen en hervatten na herstart |
| HA-beheerpagina | Instellen, toestemmen, voorbeeldweergave en status |

Alleen Personal krijgt deze implementatie. Ondersteuning wordt gecontroleerd
voor zijn vastgezette Daily-basis. De interface mag niets beloven over
Google-ondersteuning in Official of Latest.

Elke omgeving bewaart haar eigen configuratie, tokens en voortgang in de eigen
private `/data`. Nooit automatisch tokens of meetgegevens tussen Official en
Latest kopiëren. Als het gekozen doel uitstaat: wachten of een foutstatus tonen,
niet naar de andere omgeving uitwijken.

### Bestaande beveiligingsgrens behouden

De huidige gateway verwijdert de externe `Authorization`-header in
[`settings.py`](../nocturne_local/rootfs/opt/nocturne-ha/settings.py).
Een willekeurige externe synchronisatiedienst met een Bearer-token door deze
gateway sturen, werkt dus niet zonder aanvullend ontwerp.

De voorgestelde helper benadert de API via de interne loopbackverbinding met een
**eigen, door de gebruiker goedgekeurd Nocturne OAuth-token**. Ook intern blijven
tenant- en scopecontroles gelden. Geen instance-key, beheerderssleutel of directe
PostgreSQL-toegang als alternatief. Correcte host/tenant-resolutie en OAuth-client-
registratie moeten eerst in wegwerpcontainers worden bewezen.

Beheer blijft achter HA-ingress. Voor Google komt alleen een exact afgebakende
OAuth-terugkeerroute, met eenmalige state, korte geldigheid, kanaalbinding en PKCE
waar ondersteund. De route verleent zelf geen toegang tot meetgegevens. Geen brede
auth-uitzondering voor een nieuwe map en geen globale Bearer-doorvoer.

Voor een persoonlijke, periodiek ophalende proef is geen nieuwe router-
portforward nodig: de helper maakt uitgaande Google-verzoeken en de browser
moet de ingestelde HTTPS-terugkeerroute kunnen bereiken. Een publieke webhook
is een ander ontwerp en valt niet onder deze eerste proef.

## 5. Nocturne-contract en rechten

Onderzochte bronversies:

- Official: Nocturne v0.2.4, commit `66c35837d3719b592fa25e0aa09bb5f1c33c14a5`.
- Latest-pin bij dit onderzoek: `3b7514591f854f4794deeeb75d43e33d979d1ee4`.

Deze inventarisatie is gebaseerd op broncode, niet op geslaagde live imports.

| Type | Schrijfroute | Belangrijk verzoekformaat | Recht in onderzochte Latest |
| --- | --- | --- | --- |
| Hartslag | `POST /api/v4/heartrate` | Array; `timestamp`, `bpm`, `device`, `app`, `dataSource`, `syncIdentifier` | `heartrate.readwrite` |
| Stappen | `POST /api/v4/stepcount` | Array; `timestamp`, `metric`, `source`, `device`, `app`, `dataSource`, `syncIdentifier` | `stepcount.readwrite` |
| Gewicht | `POST /api/v4/body-weight` | Eén object; onder meer `created_at`, `weightKg`, `data_source`, `syncIdentifier` | `therapy.readwrite` via de gedeclareerde write-scope |

Let op het verschil tussen `dataSource` in de hartslag-/stappenverzoeken en
`data_source` in het gewichtsmodel. Hergebruik niet blind dezelfde JSON voor alle
routes. De stapbron gebruikt een bitvlag voor absolute totalen; `source: 0` hoort
bij delta's. Dit is niet hetzelfde als een leverancier-ID.

Bronnen: [hartslagverzoek](https://github.com/nightscout/nocturne/blob/3b7514591f854f4794deeeb75d43e33d979d1ee4/src/API/Nocturne.API/Models/Requests/V4/UpsertHeartRateRequest.cs),
[stappenverzoek](https://github.com/nightscout/nocturne/blob/3b7514591f854f4794deeeb75d43e33d979d1ee4/src/API/Nocturne.API/Models/Requests/V4/UpsertStepCountRequest.cs),
[stappenmodel](https://github.com/nightscout/nocturne/blob/3b7514591f854f4794deeeb75d43e33d979d1ee4/src/Core/Nocturne.Core.Models/StepCount.cs),
[gewichtmodel](https://github.com/nightscout/nocturne/blob/3b7514591f854f4794deeeb75d43e33d979d1ee4/src/Core/Nocturne.Core.Models/BodyWeight.cs),
[gewichtcontroller](https://github.com/nightscout/nocturne/blob/3b7514591f854f4794deeeb75d43e33d979d1ee4/src/API/Nocturne.API/Controllers/V4/Health/BodyWeightController.cs).

### Gewicht: belangrijke open keuze

De onderzochte Latest vraagt voor gewicht bredere therapie-schrijfrechten dan
deze koppeling nodig zou moeten hebben. Voorkeur: upstream een aparte
`bodyweight.readwrite`-scope toevoegen en de ondersteuning daarvan testen.
Die scope **bestaat nog niet** in de onderzochte code. Een andere afgebakende,
upstream-goedgekeurde importmogelijkheid kan ook worden onderzocht.

Tot die tijd kan de proef gewicht bij Google lezen en lokaal tonen, zonder het
naar Nocturne te schrijven. Een tijdelijke test met `therapy.readwrite` mag
alleen na expliciete toestemming voor dat bredere recht, op een testomgeving.
Niet ongemerkt `health.readwrite`, een wildcard of een beheerdersaccount kiezen.

De Official-gewichtcontroller heeft andere autorisatiecode. Het ontbreken van
dezelfde controllerannotatie bewijst geen veilig beperkt recht; controleer ook de
middleware en effectieve rechten. Hartslag en stappen declareren in beide
onderzochte versies hun specifieke schrijfscope. Voer desondanks dezelfde
contract- en isolatietests op beide versies uit. De readwrite-scopes bieden meer
dan alleen toevoegen; de bridge gebruikt uitsluitend de afgesproken bewerkingen.

## 6. Google-toestemming en delen met anderen

Voor een persoonlijke eerste proef: eigen Google Cloud-project, Google Health
API inschakelen, OAuth-webclient configureren, exacte terugkeer-URL registreren
en het eigen account als testgebruiker toevoegen. Clientgegevens worden lokaal
ingevoerd, nooit gedeeld in deze repository.

**Belangrijk:** in Google's OAuth-testmodus verlopen refresh-tokens na zeven
dagen. Zo'n proef is dus niet meteen een onderhoudsvrije permanente koppeling.
Een productieconfiguratie en eventuele Google-verificatie zijn een aparte stap;
ook daarna moet intrekken/verlopen van toegang worden afgehandeld.
[Google: Cloud en OAuth instellen](https://developers.google.com/health/setup).

Voorgestelde Google-leesrechten:

| Geselecteerde gegevens | Scope |
| --- | --- |
| Stappen | `https://www.googleapis.com/auth/googlehealth.activity_and_fitness.readonly` |
| Hartslag en/of gewicht | `https://www.googleapis.com/auth/googlehealth.health_metrics_and_measurements.readonly` |
| Slaap, pas in een latere fase | `https://www.googleapis.com/auth/googlehealth.sleep.readonly` |

Deze categorieën zijn ruimer dan één meting. Vraag de kleinst beschikbare
categorieën en haal binnen een categorie uitsluitend de geselecteerde typen op.
Verwerk gedeeltelijke toestemming: weigering van slaap mag stappen niet blokkeren.
Geen Google-schrijfrechten, locatie-, Gmail- of Drive-toegang aanvragen.
[Google: scopes](https://developers.google.com/health/scopes).

De gewenste Google-login kan pas werken nadat de OAuth-client voor de installatie
of distributie is ingericht. Verberg deze beheervereiste niet achter een knop die
niets doet. Een eigen client betekent een eenmalige beheerhandeling; daarna
hoort de dagelijkse bediening uitsluitend via verbinden en aanvinken te lopen.

Voor algemene verspreiding zijn privacybeleid, gegevensbeheer en toepasselijke
Google-verificatie nodig. Een openbare GitHub-repository levert niet automatisch
een goedgekeurde Google OAuth-app op. Eerst een persoonlijke client ondersteunen;
een centraal beheerde client is een afzonderlijke product-/beheerkeuze.
[Google: developer checklist](https://developers.google.com/health/developer-checklist).

## 7. Synchronisatie zonder dubbele of verzonnen gegevens

Onderstaande intervallen en grenzen zijn ontwerpkeuzes voor de proef, geen
toezegging over de snelheid of beschikbaarheid van Google-data.

- Begin met 24 uur voorbeeldgegevens. Na akkoord maximaal zeven dagen initiële
  import; langere historie alleen als aparte, hervatbare opdracht.
- Voorstel: stappen/hartslag iedere 15 minuten ophalen, gewicht/slaap ieder uur.
  Dit is geen realtime meetverbinding. Nieuwe data zijn afhankelijk van bron-sync.
- Gebruik één samengestelde bron of een expliciet gekozen primaire bron voor
  overlappende stappen. Geen telefoonstappen bij horlogestappen optellen zonder
  een bewezen ontdubbelregel.
- Bewaar een stabiele bronidentiteit per account, type en bronrecord, plus een
  wijzigingsvingerafdruk. Koppel die aan Nocturne `dataSource`/`syncIdentifier` en
  het ontvangen doel-ID. Gewijzigde meetwaarden veranderen niet de recordidentiteit.
- Test idempotentie werkelijk: opnieuw ophalen of crash/herstart mag niet tot
  extra records leiden. Veronderstel niet dat een veldnaam dit alleen garandeert.
- Bewaar UTC-tijd plus de relevante lokale offset/daggrens. Test zomertijd en
  nachten over middernacht. Verdeel dagtotalen nooit over verzonnen tijdstippen.
- Stappenintervallen passen niet verliesloos in een enkel Nocturne-tijdstempel.
  Bewaar de bronintervalgrenzen in het beperkte synchronisatiejournaal; stel de
  projectieregel en grafiekinterpretatie vast voordat import wordt ingeschakeld.
- Converteer gewicht alleen met een expliciete bron-eenheid naar kg. Ontbrekend
  vetpercentage blijft leeg. Verzin geen hartslag-accuracyscore.
- Lees alle pagina's. Sla voortgang pas op nadat de doelrecords duurzaam bevestigd
  zijn; behandel afgebroken batches en herhaalde pagina's zonder dubbel schrijven.
- Bij HTTP 429: respecteer `Retry-After`; bij tijdelijke fouten begrensde herpogingen
  met toenemende wachttijd. Bij ingetrokken toestemming stoppen en herverbinden vragen.
- Vernieuw tokens op aanvraag met één gelijktijdige vernieuwing per account.
  Maak onderscheid tussen Google- en Nocturne-toegangsfouten.
- Herlees een begrensd overlappend venster voor late correcties. Oudere correcties
  vragen een expliciete hersynchronisatie; beloof geen onbeperkte wijzigingsdetectie.
- Wis nooit gebruikersmetingen buiten de bridge. Verwijderingen uit de bron niet
  stilzwijgend doorzetten in de eerste proef; leg later een expliciet beleid vast.

Google documenteert paginering, gegevensafhankelijke venstergrenzen en vertraagde
beschikbaarheid na synchronisatie. Pas verzoekgrootte daarop aan en houd tests
per endpoint bij. [Google: query- en synchronisatiegrenzen](https://developers.google.com/health/data-types).

## 8. Privacy en veilige opslag

- Alleen de expliciet gekozen brongegevens gaan naar de eigen HA/Nocturne-
  omgeving. Geen meetgegevens, accountsleutels of tokens naar GitHub of AI-tools.
- Tokens apart van gewone opties opslaan, met beperkte bestandsrechten en encryptie.
  Een sleutel op dezelfde host beschermt niet tegen volledige hostovername;
  gebruik ook versleutelde back-ups en aparte toegang tot herstelmateriaal.
- Een ontkoppeling stopt de werker en verwijdert lokale toegangsmiddelen. Google-
  en Nocturne-toestemming waar mogelijk intrekken; een mislukte intrekking melden.
  Bestaande geïmporteerde historie blijft bewaard, tenzij de gebruiker apart kiest
  om alleen de door deze bridge gemaakte records te verwijderen.
- Tijdelijke voorbeeldgegevens niet loggen en niet standaard op schijf bewaren.
  Synchronisatiejournalen bevatten zo weinig mogelijk gegevens en krijgen een
  begrensde bewaartermijn; retentie moet ontdubbeling na herimport blijven ondersteunen.
- Eén gebruiker/Nocturne-tenant per connectorconfiguratie in de eerste versie.
  Geen automatische koppeling op alleen een weergavenaam.
- Geen glucose-, medicatie-, pomp- of behandelinstellingen wijzigen. Dit is
  gegevensoverdracht, geen klinisch gevalideerde monitoring of doseerfunctie.

## 9. Kleine opleveringen met duidelijke stopmomenten

| Stap | Concreet resultaat | Voorwaarde om verder te gaan |
| --- | --- | --- |
| A. Offline prototype | Adapterscheidingen, synthetische fixtures en tests voor eenheden/tijden/ontdubbelen | Geen accounts of echte gezondheidsdata nodig |
| B. OAuth- en API-contracttest | Wegwerp-Nocturne voor beide pins; beperkte rechten, tenantkeuze en herstart getest | Geen productievolume gebruiken; ontbrekende scopes niet omzeilen |
| C. Persoonlijke Google-leesproef | Lokaal voorbeeld van stappen, hartslag en gewicht; nog geen import | Gebruiker kiest bron en geeft Google-toestemming |
| D. Eerste import | Stappen/hartslag naar één expliciet gekozen testomgeving | Gebruiker controleert voorbeeld, bron/dagtotalen, periode en doel; herstelmogelijkheid aanwezig |
| E. Gewicht en slaap | Gewicht na rechtenbesluit; slaap na aparte mappingtest | Geen brede rechten zonder expliciet akkoord |
| F. Deelbare app-update | Handleiding, statuspagina, hersteltests en updatepad voor beide kanalen | CI plus menselijke browser-/toestemmingsproef; Google-publicatievoorwaarden gecontroleerd |

Tests vóór een werkende koppeling mag worden geclaimd:

- Alle aanvinkbare typen doorlopen ophalen, opslaan en zichtbare weergave;
  geen type stilzwijgend overslaan omdat de Nocturne-versie iets mist.
- Gedeeltelijke toestemming, leeg resultaat, ingetrokken/zevendaags verlopen token.
- Dubbele records, correcties, mislukte doelbatch en hervatten na herstart.
- Meerdere apparaten met overlappende stappen; ontbrekende versus echte nulwaarden.
- Tijdzonewissel, zomertijd, gewichtseenheden en geen verzonnen aanvullende waarden.
- Token van verkeerde omgeving/tenant geweigerd; stoppen van één omgeving raakt
  de andere niet. Bestaande 0.1.5-cookie-/login-isolatie blijft werken.
- Afwijzing van te brede/ontbrekende rechten; onbevoegde toegang tot beheer,
  callbackmisbruik en onbedoelde publieke API-toegang getest.
- Geïmporteerde gegevens via Nocturne teruggelezen én in de bedoelde webweergave
  gecontroleerd. Een succesvol HTTP-antwoord alleen is onvoldoende.
- Back-up/herstel inclusief tokens en voortgang getest zonder live data te wissen.

## 10. Open punten voor implementatie en de eerste echte proef

Het gewenste gebruik is vastgesteld: Google-login en zelf gegevens aanvinken.
Dat is voldoende om de catalogus, begeleide verbinding en offline tests te
ontwerpen. Voor een echte bronproef moet nog blijken welke typen in het Google-
account aanwezig zijn. Als verwachte metingen ontbreken, controleer dan pas in
welke app/bron ze wel zichtbaar zijn en of Health Connect nodig is. Deel hiervoor
geen gezondheidswaarden of wachtwoorden.

Daarna pas: Google-toestemming, gewenste historie en akkoord voor een concrete
testdoelomgeving. Tot die tijd kunnen offline tests en de afgebakende
containercontracttests worden voorbereid. Er is met dit ontwerp nog niets naar
GitHub gepubliceerd en geen nieuwe pakketversie uitgebracht.
