# Extra gatewaycode en de controle daarop instellen

Deze instellingen zijn beschikbaar in **alle zes varianten**: Official, Latest, Personal en Test A/B/C.

Wrapper **0.1.4** herstelt de optie om bij een **bestaande, volledig ingerichte Nocturne-instantie** de extra HTTP Basic-popup te verwijderen. Je blijft daarna aanmelden met je eigen Nocturne-passkey; Nocturne-authenticatie wordt niet uitgeschakeld.

De eerdere startcontrole vertrouwde op `settings.requireAuthentication`.
Upstream main gebruikt dat alleen nog als oud compatibiliteitsveld en zet het
op `false`, ook bij een private instantie. Daardoor kon Latest ten onrechte
stoppen vóór het openen van de webinterface. De nieuwe controle vereist een
geladen, niet-demo-instantie met `anonymousReadAccess: false` én een echte
anonieme gegevensaanvraag die met HTTP `401` wordt geweigerd. Er worden geen
account- of servicesleutels aan de test toegevoegd en geen gegevensinhoud gelezen.

## Bewust overslaan vanaf wrapper 0.1.10

Wil je Nocturne zelf laten bepalen wanneer anoniem lezen of een publieke deel-link is toegestaan? Zet in de configuratie van de bedoelde app **Extra gebruikersnaam/wachtwoord-popup** uit en **Gatewaycontrole bewust overslaan** aan. Behoud je andere instellingen:

```yaml
gateway_auth: false
skip_gateway_check: true
```

**Opslaan en alleen deze app herstarten.** Je moet beide bij elkaar passende certificaatbestanden blijven instellen. De statuspagina en het app-log tonen prominent `GATEWAY_SKIPPED`. De knop **Open Nocturne** opent het basisadres, zodat de hulp niet vooraf een aanmelding afdwingt.

Dit slaat alleen de private-instantiecontrole van de wrapper over. Het schakelt geen Nocturne-rechten, accounts of passkeys uit en geeft zelf geen anonieme lees- of schrijfrechten. Stel de bedoelde toegangs- en deelrechten in Nocturne zelf in. TLS-, certificaat-, domein- en headercontroles blijven actief. De ondersteunde deeladressen hangen ook af van de Nocturne-versie en de hostroutering van het gekozen kanaal.

`skip_gateway_check` staat standaard **uit**. Met `gateway_auth: true` wordt de skip-optie genegeerd: de extra gatewaycode blijft vereist. Zet `skip_gateway_check: false` en herstart om de private controle te herstellen.

**Bestaande Test A-configuraties:** de oude zichtbare `verify_native_auth`-optie is vervangen door dezelfde `skip_gateway_check`-optie als in alle andere varianten. Gebruikte je `verify_native_auth: false`? Zet na de update in **Configuratie** `skip_gateway_check: true`, verwijder de oude `verify_native_auth`-regel uit de YAML, sla op en herstart. Een nieuw standaardveld van Supervisor kan anders de private controle weer inschakelen. Gebruik `skip_gateway_check: false` om de controle te herstellen. Er is nog maar één zichtbare schakelaar. Oude ruwe opties worden alleen intern gelezen wanneer het nieuwe veld ontbreekt; een expliciet nieuw veld heeft altijd voorrang.

De omschakelstappen hieronder beschrijven de standaardmodus **met** private controle.

## Voorwaarden

- Maak eerst een HA-back-up waarin deze app is opgenomen.
- Het Nocturne-eigenaarsaccount en de passkey bestaan al; uitloggen en opnieuw aanmelden werkte eerder.
- `public_url` gebruikt de vaste HTTPS-hostnaam en de browser vertrouwt het ingestelde certificaat.
- De app draait niet op een publiek doorgestuurde routerpoort. Deze instelling geeft geen toestemming of veiligheidsbewijs voor internetpublicatie.

Een nieuwe lege instantie moet eerst met `gateway_auth: true` worden ingericht. De app weigert native modus wanneer setup/herstel nog niet klaar is, anoniem lezen aanstaat, demo/een onbekende toestand is geladen of anonieme toegang tot beschermde gegevens niet met `401` wordt geweigerd.

## Omschakelen in Home Assistant

1. Werk de repository-app bij naar wrapper **0.1.4** (HA-pakket **0.1.4-1** of hoger) en controleer dat de bestaande instantie nog normaal opent.
2. Open **Instellingen → Apps → de bedoelde Nocturne-variant → Configuratie**. Kies de bedoelde instantie.
3. Zet **Ongebruikte optionele configuratieopties tonen** aan als `gateway_auth` niet zichtbaar is.
4. Zet **Extra gebruikersnaam/wachtwoord-popup** (`gateway_auth`) uit en laat `skip_gateway_check` uit. Laat `public_url`, `certificate`, `private_key` en de hostpoort ongewijzigd.
5. Klik **Opslaan** en herstart alleen de Nocturne-app.

In de YAML-editor is de relevante extra regel:

```yaml
gateway_auth: false
skip_gateway_check: false
```

Na een geslaagde start toont de HA-statuspagina geen gatewaycode meer. **Open Nocturne** gaat rechtstreeks naar Nocturne's eigen aanmeldpagina. Een browser die de oude Basic-popup heeft onthouden kan een oude tab cachen; sluit die tab en open opnieuw via de HA-statuspagina.

## Meteen controleren

1. Open Nocturne via exact dezelfde vaste HTTPS-hostnaam.
2. Controleer dat de browser geen extra gebruikersnaam/wachtwoord-popup toont.
3. Meld aan met de bestaande passkey en controleer dat hetzelfde dashboard/account verschijnt.
4. Meld af en opnieuw aan.
5. Herstart de app nog eenmaal en controleer opnieuw dezelfde accounttoegang.

Dit zijn handmatige acceptatietests. De automatische test bewijst de configuratie- en afwijzingsgrenzen, niet jouw browser/passkey of gegevens.

## Veilig terugzetten

Start de app niet, of zie je een `GATEWAY_...`-fout in de app-log?

| Fout | Betekenis / actie |
|---|---|
| `GATEWAY_SETUP` | Eigenaarsaccount nog niet afgerond. Eerst inrichten met de gateway aan. |
| `GATEWAY_RECOVERY` | Nocturne vraagt herstel van een bestaand account. Herstel met de gateway aan; wis geen account of gegevens. |
| `GATEWAY_AUTH` | Private status of echte HTTP-401-weigering niet bevestigd. Extra gateway weer aan, meld alleen de foutcode en versies. |
| `GATEWAY_STATUS` | Statusaanvraag gaf een onverwachte HTTP-code. Extra gateway weer aan en onderzoek die code. |
| `GATEWAY_TLS` | Beide certificaatbestanden moeten expliciet ingesteld zijn. Vertrouwen controleer je daarnaast in de browser. |

1. Zet `gateway_auth` terug op `true`.
2. Sla op en herstart alleen deze app.
3. Gebruik daarna weer gebruiker `nocturne` plus de bestaande gatewaycode op de HA-statuspagina.

De instelling wist of roteert niets: database, account, passkey, instantie- en databasesleutels en de oude gatewaycode blijven behouden. Verwijder `secrets.json` of de appgegevens niet om een toegangsprobleem op te lossen.

[Terug naar installatie](INSTALLATIE.md) · [Security](../SECURITY.md) · [Testbereik](TESTING.md)

## Home Assistant via OAuth vanaf wrapper 0.1.6

In de hierboven beschreven native modus (`gateway_auth: false`) kan een externe
OAuth-client zijn eigen Bearer-token meesturen. Wrapper 0.1.5 verwijderde dat
token en stuurde v4-gegevensaanvragen naar de webinterface. Daardoor kon het
toestemmingsscherm wel slagen, terwijl de HACS-integratie daarna HTTP 401 kreeg.

Wrapper 0.1.6 stuurt zulke v4-aanvragen naar de API. Nocturne controleert daar
nog steeds het token, de vervaldatum, de instantie en de verleende rechten.
Browseraanvragen zonder Bearer-token blijven via de bestaande sessieverwerking
lopen. De standaardmodus met extra Basic-popup blijft een afzonderlijke poort;
die kan niet met een Bearer-token worden overgeslagen.

Werk de bedoelde Nocturne-app bij en probeer de bestaande HA-koppeling opnieuw.
Gebruik als Instance URL het HTTPS-adres van die Nocturne-app, inclusief haar
poort; de OAuth-callback gebruikt het HTTPS-adres van Home Assistant zelf.
Een HACS-client moet zelf de Authorization-header verzenden. Deze wrapper-update
herstelt geen fouten in externe integratiecode. Andere legacy/API-secret-clients
en echte passkey-/OAuth-aanmelding blijven afzonderlijke acceptatietests.
