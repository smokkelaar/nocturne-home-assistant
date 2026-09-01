# Nederlandse snelstart

**Wil je alle klikstappen, afbeeldingen en controlepunten? Open de [volledige visuele installatiehandleiding](INSTALLATIE.md).** Voor certificaat, DNS en Windows is er de [uitgewerkte HTTPS-handleiding](HTTPS-EN-DNS.md).

Dit is een aparte, openbare Nocturne-repository voor de **Home Assistant-appwinkel**. Het is geen HACS-integratie. Anderen kunnen via Issues en pull requests meewerken.

Voor een **nieuwe testinstallatie**:

1. Voeg `https://github.com/smokkelaar/nocturne-home-assistant` toe bij de repositories van de appwinkel.
2. Kies **Nocturne Official Release** (handmatig bevorderde officiële Nocturne-release, poort 8448) of **Nocturne Latest Release** (dagelijks geteste upstream-`main`, aparte data, poort 8449). Je kunt beide geïnstalleerd houden. [Vergelijk de kanalen](CHANNELS.md).
3. Stel per gekozen app je vaste HTTPS-domeinnaam, juiste poort en vertrouwde certificaatbestanden in; zie [Official-documentatie](../nocturne_local/DOCS.md) of [Latest-documentatie](../nocturne_latest/DOCS.md).
4. Start de app en open de webinterface voor status, link en extra toegangscode. Nocturne zelf opent in een aparte tab en gebruikt daarna zijn eigen passkey-account.

Gebruik eerst een lege testomgeving zonder Nightscout/CGM/pomp-koppeling. Dit is geen medisch gevalideerd systeem.

## Twee updatekanalen

Official wordt uitsluitend gecontroleerd nadat een beheerder de handmatige workflow start. De API en webinterface worden samen vastgezet, gebouwd en getest; de beheerder beoordeelt en publiceert bewust.

Latest controleert dagelijks upstream `main`. Alleen een volledig herleidbaar API/web-paar wordt op exacte commit en digests vastgezet. Na container-, upgrade- en verplichte repositorytests kan uitsluitend de Latest-wijziging automatisch worden samengevoegd.

HA kan per app updates automatisch installeren. Laat dit bij Official uit. Bij Latest kun je het later bewust aanzetten voor dagelijkse doorstroming, maar alleen als Latest-testdata vervangbaar is en herstel is geoefend. Ook Latest downloadt bij start geen ongecontroleerde zwevende tag: iedere aangeboden versie bevat exacte digests.

## Je huidige lokale installatie

De bestaande lokale app wordt niet automatisch omgezet. De GitHub-versie heeft een andere interne HA-identiteit en gegevensmap. **Verwijder de werkende lokale app niet.** Voeg de repository gerust toe, maar migreer pas na een apart geteste back-up-/herstelprocedure. Zie [Migratie](MIGRATION.md).

Er gaan geen persoonlijke configuraties, toegangscodes, certificaten of medische gegevens mee in deze repository.
