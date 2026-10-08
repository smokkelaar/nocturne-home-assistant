# Vooraf gebouwde Nocturne-images — de nieuwe 1.x-aanpak

De nieuwe HA-pakketreeks **1.0.x** geldt voor alle zes varianten: Official,
Latest, Personal, Test A, Test B en Test C. Deze nummers staan los van de
Nocturne-versie, Personal-featureversie en functionele wrapperversie.
Iedere nieuwe pakketversie moet volgens HA's AwesomeVersion strikt hoger
zijn dan de aangeboden/geïnstalleerde eerdere versies, inclusief alle oude
`-9`, `-10`, `-p`, `-a`, `-b` en `-c`-reeksen.

## Wat verandert op jouw HAOS?

HAOS downloadt een complete geteste container uit GHCR. .NET, Rust en de
webapp worden op GitHub gecompileerd. Geen lokale builds of compilatiepieken
meer bij installeren/updaten. Het normale geheugengebruik van de draaiende
apps blijft bestaan.

De bestaande repository-URL blijft hetzelfde. Slugs, hostpoorten,
opties/defaults, cookie-namespaces en private `/data`-mappen blijven behouden.
Je hoeft de apps niet te verwijderen of een andere repository toe te voegen.
Maak een volledige HA-back-up, vernieuw de appstore en voer de gewone update uit
zodra de 1.x-versie gepubliceerd is. De eerste overgang gebruikt dezelfde
Nocturne-bronpins: geen Nocturne-upgrade wordt met deze distributiewijziging vermengd.

| Variant | Slug | HTTPS-hostpoort | Architecturen |
|---|---|---:|---|
| Official | nocturne_local | 8448 | AMD64 en ARM64 |
| Latest | nocturne_latest | 8449 | AMD64 en ARM64 |
| Personal | nocturne_personal | 8450 | AMD64 en ARM64 |
| Test A | nocturne_test_a | 8451 | AMD64 en ARM64 |
| Test B | nocturne_test_b | 8452 | AMD64 en ARM64 |
| Test C | nocturne_test_c | 8453 | AMD64 en ARM64 |

HA noemt ARM64 `aarch64`; Docker noemt het `arm64`. De native GitHub-runner
en architectuurspecifieke SDK/Rust/runtime-pins worden daarop afgestemd.
De PostgreSQL-versie blijft 17. Cross-architecture migratie van een bestaande
database is niet onderdeel van deze omschakeling; restore wordt per architectuur getest.

## Bouwen, testen, publiceren, daarna aanbieden

1. Bronpromoties wijzigen de vastgezette bron en buildinformatie, maar verhogen
   de zichtbare HA-versie nog niet. `publication.json` activeert deze scheiding.
2. `tools/prebuilt_publish.py prepare` maakt losse kandidaten en een matrix van
   zes varianten × twee native architecturen. Een source fingerprint selecteert
   alleen gewijzigde varianten; een force-run en PR-validatie testen alles.
3. Native runners bouwen met digest-pins en buildcache. Ze controleren opstart,
   gatewaybeveiliging, eigenaarherstel, de TOTP-knop en native passkeyherstel.
4. Cold restore en upgrade worden per variant/architectuur getest. Bij de eerste
   AMD64-publicatie wordt ook de bestaande lokale-build-receptuur als baseline
   gebouwd; ARM64 heeft nog geen oude installatie en gebruikt een cold restore
   van de kandidaat. De bestaande gecombineerde cookie-isolatietests blijven behouden.
5. Alleen een vertrouwde publicatierun mag de exact geteste image pushen.
   Een bestaand versietag wordt nooit overschreven. PR-runs krijgen geen
   package-schrijfbevoegdheid.
6. Pas na succes van alle vereiste jobs controleert de promotie **anoniem**
   beide GHCR-images, platform, bronrevision en HA-labels. Bij een ontbrekende,
   private of verkeerde image verandert geen enkele appstoreconfiguratie.
7. De promotie-PR voegt het eigen `image`-veld en de nieuwe 1.x-versie toe aan
   de bestaande appconfiguraties. `provenance.json` bewaart de bron en image-digests.

Versies combineren een 1.x-basis met een oplopende publicatieteller. De bestaande
storeversie blijft een minimum bij workflow-tellerresets; retries krijgen een
ander versienummer. De eerste concrete publicatie hoeft daarom niet exact
`1.0.0` te zijn, maar blijft herkenbaar in de nieuwe **1.0.x**-reeks.

## GHCR en automatische publicatie

Nieuwe GHCR-packages kunnen aanvankelijk private zijn. Maak alle twaalf
architectuurpackages publiek; de promotie weigert anders een HA-update aan te bieden.
Er is geen GitHub-token op HAOS nodig. Het GITHUB_TOKEN van Actions krijgt alleen
package-schrijfbevoegdheid in de vertrouwde publicatiejobs.

Na bronupdates op main en ieder uur start `prebuilt-auto.yml` een publicatierun.
Ongewijzigde bronfingerprints leveren geen nieuwe images op. Official's bronrelease
blijft een handmatig beoordeelde promotie; deze pipeline kiest geen nieuwe
Official-Nocturne-versie op eigen initiatief. De dagelijkse Latest/Personal-bronchecks
blijven bestaan. Containerpublicatie en storepromotie gebeuren daarna afzonderlijk.

`Validate` kan handmatig worden gestart met `publish=true`; `force=true` bouwt
alle zes opnieuw. Beide architecturen moeten slagen. Een mislukking laat de
laatst gepubliceerde HA-versie beschikbaar. Runtime/download op echte HAOS en
echte browserauthenticators blijven aanvullend te controleren.

## Broncode en licenties

Iedere image bevat de AGPL-3.0-only-licentietekst en `corresponding-source.json`
met de exacte wrapper- en Nocturne-broncommits en de Nocturne-bronarchive-URL.
Nocturne en afhankelijkheden behouden hun auteursrechten en licenties; Ubuntu,
PostgreSQL, .NET en JavaScript-package-notices worden niet bewust verwijderd.
De registry-verificatie is gebaseerd op de upstream HA-publicatieaanpak, met
behoud van de bestaande ontwikkelvarianten en onderhoudsfuncties.
