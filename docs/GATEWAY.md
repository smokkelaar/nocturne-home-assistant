# Extra gebruikersnaam/wachtwoord-popup uitschakelen

Wrapper **0.1.4** herstelt de optie om bij een **bestaande, volledig ingerichte Nocturne-instantie** de extra HTTP Basic-popup te verwijderen. Je blijft daarna aanmelden met je eigen Nocturne-passkey; Nocturne-authenticatie wordt niet uitgeschakeld.

De eerdere startcontrole vertrouwde op `settings.requireAuthentication`.
Upstream main gebruikt dat alleen nog als oud compatibiliteitsveld en zet het
op `false`, ook bij een private instantie. Daardoor kon Latest ten onrechte
stoppen vóór het openen van de webinterface. De nieuwe controle vereist een
geladen, niet-demo-instantie met `anonymousReadAccess: false` én een echte
anonieme gegevensaanvraag die met HTTP `401` wordt geweigerd. Er worden geen
account- of servicesleutels aan de test toegevoegd en geen gegevensinhoud gelezen.

## Voorwaarden

- Maak eerst een HA-back-up waarin deze app is opgenomen.
- Het Nocturne-eigenaarsaccount en de passkey bestaan al; uitloggen en opnieuw aanmelden werkte eerder.
- `public_url` gebruikt de vaste HTTPS-hostnaam en de browser vertrouwt het ingestelde certificaat.
- De app draait niet op een publiek doorgestuurde routerpoort. Deze instelling geeft geen toestemming of veiligheidsbewijs voor internetpublicatie.

Een nieuwe lege instantie moet eerst met `gateway_auth: true` worden ingericht. De app weigert native modus wanneer setup/herstel nog niet klaar is, anoniem lezen aanstaat, demo/een onbekende toestand is geladen of anonieme toegang tot beschermde gegevens niet met `401` wordt geweigerd.

## Omschakelen in Home Assistant

1. Werk de repository-app bij naar wrapper **0.1.4** (HA-pakket **0.1.4-1** of hoger) en controleer dat de bestaande instantie nog normaal opent.
2. Open **Instellingen → Apps → Nocturne Official Release / Nocturne Latest Release → Configuratie**. Kies de bedoelde instantie.
3. Zet **Ongebruikte optionele configuratieopties tonen** aan als `gateway_auth` niet zichtbaar is.
4. Zet alleen **Extra gebruikersnaam/wachtwoord-popup** (`gateway_auth`) uit. Laat `public_url`, `certificate`, `private_key` en de hostpoort ongewijzigd.
5. Klik **Opslaan** en herstart alleen de Nocturne-app.

In de YAML-editor is de relevante extra regel:

```yaml
gateway_auth: false
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
