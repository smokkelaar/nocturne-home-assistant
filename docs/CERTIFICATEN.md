# Certificaatcontrole en automatische herlading

Vanaf wrapper **0.1.1** controleert de app het certificaat vóór het starten en controleert zij daarna iedere 15 seconden de ingestelde bestanden. Nocturne zelf blijft in deze release **0.2.4**.

## Wat je ziet in Home Assistant

Open de app → **Webinterface openen** → **Installatiecontrole**.

| Onderdeel | Betekenis |
|---|---|
| Publiek adres | De ingestelde `public_url`; de URL-syntax is gecontroleerd |
| Geladen certificaat | DNS SAN past bij de hostnaam, privésleutel past, begin- en einddatum gecontroleerd; einddatum in UTC |
| BINNENKORT VERLOPEN | Minder dan 14 hele dagen over; controleer DuckDNS of je eigen certificaatvernieuwer |
| Certificaatvernieuwing | Bestanden ongewijzigd, stabiliteitscontrole bezig, nieuwe versie geladen of gerichte foutcode |
| Nocturne Web | Een echt HTTP-antwoord of lokale omleiding ontvangen, niet uitsluitend een open poort |
| HTTPS | Het via een nieuwe lokale TLS-verbinding aangeboden leaf-certificaat komt overeen met de geaccepteerde kopie |
| Nog op jouw browser te controleren | DNS-route, vertrouwen in de certificaatketen, passkey-login, tweede apparaat en geplande herstart; **niet automatisch geslaagd** |

Ververs de pagina om de laatste controles te zien. De server bewijst niet of je telefoon de juiste DNS gebruikt, of jouw browser de CA vertrouwt. Controleer daarom altijd het vaste HTTPS-adres in een aparte tab zonder beveiligingswaarschuwing.

## Hoe vernieuwing werkt

1. DuckDNS of jouw bestaande certificaatbeheerder vernieuwt de bestanden in `/ssl`. De Nocturne-app vraagt zelf geen certificaten aan en schrijft niet naar `/ssl`.
2. De app verlangt twee identieke waarnemingen, minimaal tien seconden uit elkaar. Normaal duurt detectie en verwerking ongeveer 15–45 seconden; bij problemen langer.
3. Het paar wordt naar een private tijdelijke map onder `/run/nocturne/tls` gekopieerd. Alle controles en nginx lezen diezelfde onveranderde kopie; niet half bijgewerkte bronbestanden.
4. OpenSSL controleert DNS SAN, hostnaam, sleutelmatch en de geldigheid van het leaf-certificaat. nginx test de volledige configuratie en laadbaarheid van het PEM-paar.
5. Alleen de nginx-master krijgt een herlaadsignaal. Database, API en web worden niet herstart.
6. Een nieuwe lokale TLS-verbinding moet het verwachte leaf-certificaat tonen. Zonder bevestiging wordt de vorige configuratie teruggezet; een volgende controle kan opnieuw proberen.

De bestaande nginx-workers handelen bestaande verbindingen af. Dit volgt het [gedocumenteerde nginx-herlaadmechanisme](https://nginx.org/en/docs/control.html). Het is geen garantie voor alle langlopende clientverbindingen; test jouw browser ook na vernieuwing.

**Bij een ongeldig nieuw paar blijft de laatst geaccepteerde kopie actief.** Dat verlengt de geldigheidsduur niet: ook het oude certificaat kan verlopen. Bij een volledige app-herstart moet het ingestelde bronpaar geldig zijn; `/run` is geen permanente herstelopslag. De oorspronkelijke `/ssl`-bestanden worden nooit door deze app gecorrigeerd of gewist.

## Foutcodes en jouw volgende actie

| Code | Controle |
|---|---|
| `CERT_FILES` | Bestaan beide bestanden direct in `/ssl`, zijn ze leesbaar en elk maximaal 1 MiB? Vul alleen bestandsnamen in. |
| `CERT_PARSE` | Gebruik PEM-certificaat en bijpassende, onversleutelde PEM-privésleutel. Deel de sleutel niet. |
| `CERT_SAN` | Laat een certificaat met DNS Subject Alternative Name voor je vaste domeinnaam uitgeven. Alleen Common Name is onvoldoende. |
| `CERT_HOSTNAME` | Controleer `public_url` en DNS SAN. Wijzig een bestaande passkey-hostnaam niet zomaar om een verkeerd certificaat passend te maken. |
| `CERT_KEY_MISMATCH` | Wacht bij actieve vernieuwing even; blijft dit staan, controleer of certificaat en sleutel uit dezelfde uitgifte komen. |
| `CERT_NOT_YET_VALID` | Controleer systeemtijd en ingangsdatum van het certificaat. |
| `CERT_EXPIRED` | Controleer vernieuwing bij DuckDNS/eigen uitgever; geen browserbeveiliging uitschakelen. |
| `CERT_RELOAD` | De herlading kon niet worden bevestigd. Bekijk een geschoonde app-log en controleer de status opnieuw. Herstart niet blind met een ongeldig bronpaar. |
| `WEB_RESPONSE` / `TLS_RESPONSE` | De web- of TLS-antwoordcontrole faalde; een draaiend proces alleen is onvoldoende. Controleer de appstatus en relevante geschoonde logs. |

Bij een ongeldig startcertificaat stopt de app met de foutcode in **Logboeken**; de statuspagina kan dan nog niet beschikbaar zijn. Database en identiteitsbestanden worden niet opnieuw aangemaakt ter reparatie van een certificaatfout.

## Wat is getest en wat nog niet?

Unit-tests gebruiken echte, tijdelijke OpenSSL-certificaten: verkeerd domein, ontbrekende SAN, verkeerde sleutel, verlopen/nog-niet-geldige periode, onleesbaar certificaat en herstel na een afgewezen paar. Linux-container-CI laat eerst alleen het certificaat veranderen, bewijst dat het oude paar blijft werken, levert daarna de juiste sleutel en controleert het nieuwe aangeboden leaf-certificaat plus ongewijzigde PostgreSQL-starttijd.

Dit test het mechanisme met synthetische testcertificaten. Een echte DuckDNS/Let's Encrypt-vernieuwing op HA, de volledige CA-keten op jouw apparaten en een bestaande Nocturne-passkey moeten nog in een geplande gebruikersproef worden bevestigd. De app controleert geen intrekkingslijsten/OCSP en bewijst niet zelfstandig browservertrouwen.

[Terug naar installatie](INSTALLATIE.md) · [HTTPS en DNS](HTTPS-EN-DNS.md) · [Testmatrix](TESTING.md)
