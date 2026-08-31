# Extra gebruikersnaam/wachtwoord-popup uitschakelen

Wrapper **0.1.2** kan bij een **bestaande, volledig ingerichte Nocturne-instantie** de extra HTTP Basic-popup verwijderen. Je blijft daarna aanmelden met je eigen Nocturne-passkey. Dit is niet wachtwoordloos en schakelt Nocturne-authenticatie niet uit.

## Voorwaarden

- Maak eerst een HA-back-up waarin deze app is opgenomen.
- Het Nocturne-eigenaarsaccount en de passkey bestaan al; uitloggen en opnieuw aanmelden werkte eerder.
- `public_url` gebruikt de vaste HTTPS-hostnaam en de browser vertrouwt het ingestelde certificaat.
- De app draait niet op een publiek doorgestuurde routerpoort. Deze instelling geeft geen toestemming of veiligheidsbewijs voor internetpublicatie.

Een nieuwe lege instantie moet eerst met `gateway_auth: true` worden ingericht. De app weigert native modus wanneer setup nog niet klaar is, Nocturne authenticatie niet verplicht meldt, demo/een onbekende toestand is geladen of anonieme toegang tot beschermde gegevens niet met `401` wordt geweigerd.

## Omschakelen in Home Assistant

1. Werk de repository-app bij naar wrapper **0.1.2** en controleer dat de bestaande instantie nog normaal opent.
2. Open **Instellingen → Apps → Nocturne (experimental) → Configuratie**.
3. Zet **Ongebruikte optionele configuratieopties tonen** aan als `gateway_auth` niet zichtbaar is.
4. Zet alleen `gateway_auth` uit. Laat `public_url`, `certificate`, `private_key` en de hostpoort ongewijzigd.
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

Start de app niet, of zie je `GATEWAY_SETUP`, `GATEWAY_AUTH` of `GATEWAY_TLS` in de app-log?

1. Zet `gateway_auth` terug op `true`.
2. Sla op en herstart alleen deze app.
3. Gebruik daarna weer gebruiker `nocturne` plus de bestaande gatewaycode op de HA-statuspagina.

De instelling wist of roteert niets: database, account, passkey, instantie- en databasesleutels en de oude gatewaycode blijven behouden. Verwijder `secrets.json` of de appgegevens niet om een toegangsprobleem op te lossen.

[Terug naar installatie](INSTALLATIE.md) · [Security](../SECURITY.md) · [Testbereik](TESTING.md)
