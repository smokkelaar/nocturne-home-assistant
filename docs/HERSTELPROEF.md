# Geautomatiseerde herstel- en upgradeproef

Deze ontwikkelaarstest gebruikt **alleen nieuw gemaakte Docker-volumes en synthetische testdata**. Hij accepteert geen bestaande container, gebruikersvolume of HA-pad. Het is geen migratieknop en geen hulpmiddel om een HA-back-uparchief te importeren.

## De bewijsvoering

| Fase | Uitvoering | Controle |
|---|---|---|
| Baseline | Start de bekende vorige wrapper op lege data; voeg een herkenbare testwaarde toe | API, beschermde setup, sleutelidentiteit |
| Koude kopie | Stop de app netjes; kopieer de volledige `/data` naar een apart back-upvolume | Schone exit; geen PostgreSQL PID-bestand; databasecontrolebestand en sleutels aanwezig |
| Upgrade | Start de kandidaat met de oorspronkelijke data | Zelfde sleutels, testwaarde, beschermde setup en API |
| Herstel | Kopieer de **vooraf gemaakte** back-up naar nog een leeg volume en start de **oude** image | Zelfde testwaarde en sleutels komen terug |
| Onvolledige set | Verwijder alleen op een aparte wegwerpkopie het sleutelbestand | De identiteitslader weigert nieuwe sleutels te maken; databasecontrolebestand blijft intact |

De volledige PostgreSQL-cluster, inclusief WAL, rollen en bestandsrechten, wordt samen met opties en sleutels gekopieerd. Bron en doel staan tijdens het kopiëren stil. Dit volgt de voorwaarden voor een [PostgreSQL-bestandsback-up](https://www.postgresql.org/docs/17/backup-file.html).

**Terugrollen betekent hier herstellen van de oude back-up naar de oude versie.** Het betekent niet dat je veilig een oude image op een al gemigreerde database kunt starten.

## Wat GitHub automatisch uitvoert

- **Validate / Container smoke test:** verse installatie, certificaatherlading en herstart van de kandidaat; daarna wrapper **0.1.0** (immutable broncommit `24c93193bc73a36e8ffd52e3d18a8e1419bc4884`) → kandidaat → herstel naar 0.1.0.
- **Check Nocturne updates:** bouwt daarnaast de versie die vóór de update in `HEAD`/main stond. Die vormt de baseline voor de voorgestelde upstream-update. Een mislukte proef verhindert dat de bot het updatevoorstel publiceert.
- De publieke logs tonen alleen versiemetadata en PASS/foutmeldingen, geen sleutels, ruwe app-logs of data-export. Tijdelijke containers en volumes worden na afloop opgeruimd.

De CI-run van de concrete commit is leidend; alleen aanwezigheid van dit script is geen geslaagde proef. De bron is gepind, maar OS-pakketten worden tijdens de build opnieuw opgehaald. Dit is dus geen bit-identieke reproductie van een historische image.

## Zelf uitvoeren — uitsluitend ontwikkelomgeving

Na het bouwen van beide images in een eigen Docker-ontwikkelomgeving:

```sh
python tools/recovery_smoke.py --image nocturne-ha:candidate --baseline nocturne-ha:baseline
```

De scriptinterface biedt bewust geen bestaande volumeparameter. Gebruik deze opdracht niet als productieback-upinstructie en geef geen bestaande HA-volumes mee via een aangepaste scriptversie.

## Grenzen: nog geen volledige gebruikersherstelproef

Er is geen echt account, passkey, herstelcode, medische meting of connector toegevoegd. De eerste proef 0.1.0 → 0.1.1 gebruikt aan beide kanten Nocturne 0.2.4: zij test een **wrapper-upgrade**, geen gewijzigde upstream-databasemigratie. Toekomstige botproeven gebruiken de werkelijke vorige en nieuwe upstream-versies, maar de fixtures blijven beperkt.

Nog met de gebruiker te doen:

1. Een afzonderlijke niet-medische HA-testinstallatie kiezen en backup-/herstelsleutel veilig bewaren.
2. Via HA een koude back-up maken en buiten HA bewaren.
3. Die met de ondersteunde HA-herstelroute in een lege testomgeving met dezelfde appidentiteit herstellen.
4. Bestaand testaccount, passkey, opties, tweede apparaat en herstart controleren.
5. Pas daarna een overdracht tussen `local_nocturne_local` en de repository-app ontwerpen/testen. Die hebben verschillende Supervisor-identiteiten.

Geen productie-installatie verwijderen of overschrijven. Na ingebruikname van een nieuwere instantie kan de oude bron achterlopen; terugschakelen mag nieuwe gegevens niet stilzwijgend verliezen.

[Migratiegrenzen](MIGRATION.md) · [Testmatrix](TESTING.md) · [Updatebeleid](UPDATES.md)
