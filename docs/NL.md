# Nederlandse snelstart

Dit is een aparte, openbare Nocturne-repository voor de **Home Assistant-appwinkel**. Het is geen HACS-integratie. Anderen kunnen via Issues en pull requests meewerken.

Voor een **nieuwe testinstallatie**:

1. Voeg `https://github.com/smokkelaar/nocturne-home-assistant` toe bij de repositories van de appwinkel.
2. Installeer **Nocturne (experimental)**. De eerste containerbuild duurt enkele minuten.
3. Stel je eigen vaste HTTPS-domeinnaam en vertrouwde certificaatbestanden in; zie [Documentatie](../nocturne_local/DOCS.md).
4. Start de app en open de webinterface voor status, link en extra toegangscode. Nocturne zelf opent in een aparte tab en gebruikt daarna zijn eigen passkey-account.

Gebruik eerst een lege testomgeving zonder Nightscout/CGM/pomp-koppeling. Dit is geen medisch gevalideerd systeem.

## Automatische updates

GitHub controleert dagelijks op een nieuwe stabiele Nocturne-versie. De API en webinterface worden samen vastgezet, gebouwd en getest. Bij succes wordt automatisch een updatevoorstel aangemaakt. De beheerder beoordeelt onder andere de databasemigratie en keurt het voorstel goed. Daarna ziet HA bij het verversen van de appwinkel de hogere appversie.

HA kan die update desgewenst automatisch installeren via zijn app-instelling, maar laat dat tijdens deze experimentele fase uit totdat back-up/terugzetten en upgrades zijn getest. Het is dus **automatische ontdekking en voorbereiding, met bewuste goedkeuring vóór publicatie**; geen ongecontroleerde `latest`-download bij iedere herstart.

## Je huidige lokale installatie

De bestaande lokale app wordt niet automatisch omgezet. De GitHub-versie heeft een andere interne HA-identiteit en gegevensmap. **Verwijder de werkende lokale app niet.** Voeg de repository gerust toe, maar migreer pas na een apart geteste back-up-/herstelprocedure. Zie [Migratie](MIGRATION.md).

Er gaan geen persoonlijke configuraties, toegangscodes, certificaten of medische gegevens mee in deze repository.
