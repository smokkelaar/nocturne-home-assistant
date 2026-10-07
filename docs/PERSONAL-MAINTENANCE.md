# Onderhoud en herstel — alle zes Nocturne HA-varianten

Vanaf wrapper **0.1.13** hebben Official, Latest, Personal en Test A/B/C dezelfde
onderhoudsoptie. Hij staat standaard uit en vereist een eigen wachtwoord per app.
Controleer altijd welke variant je opent: iedere app heeft eigen accounts, data,
poorten en sleutels. Alleen een bewuste terminalopdracht wijzigt herstelgegevens.
De oude documentnaam blijft behouden zodat bestaande links blijven werken.

## Snel kiezen wat je nodig hebt

- **Nog een ongebruikte Nocturne-herstelcode?** Gebruik die op
  `https://JOUW-NOCTURNE-DOMEIN/auth/recovery`. Registreer een nieuwe passkey.
  Je hoeft geen nieuwe code via onderhoud te maken.
- **Nieuw domein of certificaat?** Pas eerst `public_url`, DNS en
  `certificate`/`private_key` aan in HA. Herstart de app. Open Nocturne op het
  juiste, vertrouwde HTTPS-domein buiten HA Ingress. Een passkey voor het oude
  domein werkt doorgaans niet op het nieuwe domein.
- **Alle Nocturne-inloggegevens kwijt?** Volg de accountselectie en stappen in
  de herstelwizard. Je hebt nog wel HA-beheerderstoegang nodig.
- **Nocturne start niet?** Herstel eerst de HA-appconfiguratie en herstart.
  De terminal kan werken terwijl de database gestopt is; eigenaarherstel niet.

## Nieuwe builds en automatische compatibiliteitscontrole

Iedere imagebuild controleert de exact vastgezette Nocturne-bronbestanden voor
herstelcodes, account-/tenantgegevens, herstelverificatie en sleutelconfiguratie.
Het volledige stel fingerprints moet bij één gecontroleerd profiel passen.
De uitslag wordt gekoppeld aan bronrepository/commit en de gecompileerde
Nocturne-assemblies van die image. Runtime hoeft daarvoor niet op internet.

Een nieuwe commit met dezelfde herstelbestanden blijft automatisch bruikbaar.
Een gewijzigd bestand, onbereikbare broncontrole, ontbrekend manifest of
ander binair bestand blokkeert alleen nieuwe eigenaarherstelcodes. Dit is bewust
conservatief: ook een onschuldige wijziging binnen een gecontroleerd bronbestand
kan een nieuwe beoordeling vereisen. Een nieuwe softwareversie stopt daardoor
niet de terminal, diagnose, normale Nocturne-login of bestaande herstelcodes.

Vóór eigenaarherstel worden ook de echte databasekolommen en typen gecontroleerd.
Official 0.2.7 gebruikt HMAC met de installatiesleutel; de andere huidige builds
gebruiken PBKDF2. Je kiest dat niet zelf. Veranderde herstelbestanden worden niet
automatisch als veilig aangemerkt. Een ontwikkelaar beoordeelt eerst de wijziging
en voegt een nieuw profiel toe, gevolgd door de native CI-herstelproef.

Bij onbekende builds controleert CI dat eigenaarherstel blokkeert. Bij bekende
profielen maakt CI op een wegwerpaccount werkelijk een code, laat Nocturne die
accepteren, weigert een tweede gebruik, registreert een vervangende passkey,
meldt ermee aan en controleert intrekking. Dat bewijst de serverroute, geen echte
browser-/apparaatceremonie of Supervisor-back-upherstel op jouw installatie.

## Alle inloggegevens kwijt: stappen die je zelf doorloopt

1. Open **de juiste app** in HA. Controleer de variant en maak een volledige
   HA-back-up inclusief appgegevens. Download hem en bewaar de herstelinformatie.
   Verwijder de app niet en maak geen nieuwe eigenaar of lege installatie aan.
2. Zet **Experimenteel onderhoud inschakelen** aan. Geef een uniek wachtwoord van
   16–256 tekens op, sla op en herstart. Dit staat los van Nocturne-inloggegevens.
3. Open de HA-webinterface en **Onderhoud**. Log in als `maintenance` met dat
   wachtwoord. Kies in de wizard het bestaande account dat je wilt herstellen.
   Selecteren leest alleen gegevens; er wordt nog geen code gemaakt.
4. Als de wizard meldt dat de build of database niet geschikt is: volg de uitleg.
   Controleer eventueel in de terminal met `nocturne-ha owner-recovery check`.
   Stop bij twijfel; gebruik geen losse SQL en zet geen controle uit.
5. Kopieer de door de wizard ingevulde opdracht naar de terminal. De opties
   `--backup-confirmed --write` bevestigen bewust de back-up en de wijziging.
   Je voegt één code aan je bestaande account toe. Als het account geen
   gebruikersnaam heeft, legt de wizard uit hoe je er expliciet één toewijst.
6. Alleen als je ook je authenticator kwijt bent: voeg `--reset-totp` toe.
   Dat verwijdert de tweede factor voor het geselecteerde account, ook als dat
   account tot meerdere tenants behoort. Anders blijft TOTP actief.
7. Gebruik de velden `username` en `code` uit de terminaluitvoer op het
   Nocturne-hersteladres. Bewaar ook `code_id` tijdelijk privé. Plak codes niet
   in deze wizard, een GitHub-issue, app-log of gedeelde schermafbeelding.
8. Registreer op het werkende HTTPS-domein een nieuwe passkey. Meld af en weer
   aan. Controleer dat je het oorspronkelijke account en de bestaande gegevens ziet.
9. Stel TOTP opnieuw in als die gereset is. Verwijder alleen oude passkeys die je
   niet meer gebruikt en bewaar nieuwe Nocturne-herstelcodes veilig.
10. Heb je de nieuwe code niet gebruikt? Trek hem in met
    `nocturne-ha owner-recovery revoke --code-id CODE_ID --write`, met de ID uit
    de uitvoer. Ongebruikte codes verlopen niet automatisch. Zet daarna onderhoud
    uit in HA en herstart; controleer dat de terminal niet meer bereikbaar is.

## Enable and compare

1. Make a full Home Assistant backup of the selected app, including its private data.
2. Upgrade that app. Local source builds need substantial RAM; do not
   build other channels simultaneously.
3. In that app's HA configuration set `maintenance_enabled: true` and set
   `maintenance_password` to a unique password of 16–256 characters. Restart.
4. Open that app's HA web interface and select **Onderhoud**. If the
   application failed to start, ingress opens maintenance automatically.
5. The browser asks for user **maintenance** and the configured password.
   Keep the HA connection protected by HTTPS or use a trusted local connection.
6. Compare the three sections: CLI, real interactive terminal, and recovery wizard.

The terminal is an actual ttyd/xterm.js shell, with root privileges **inside this
app only**. It can read secrets and modify/delete app data. HA authentication and
the independent maintenance password protect access. `panel_admin` restricts the
sidebar presentation, not backend authorization. The proxy accepts only HA's
Supervisor ingress address, never a forwarded client-IP header. No new host port,
Docker socket, Supervisor token, host PID namespace or protection-mode change is
used. A random per-start terminal URL guards WebSocket requests against blind
cross-site initiation. Do not share its URL or credentials. Browser Basic-auth
credentials may be cached: disable maintenance and restart to end access.

## 1. CLI

```sh
nocturne-ha --help
nocturne-ha doctor
nocturne-ha status
nocturne-ha recover
nocturne-ha recover --url https://new.example.net:8450
nocturne-ha api /api/v4/status
nocturne-ha api --help
nocturne-ha owner-recovery check
nocturne-ha owner-recovery list
nocturne-ha owner-recovery --help
```

`doctor` checks wrapper options, DNS, the configured certificate/key and local
API reachability. DNS resolution is not proof that the browser can reach the
site; certificate validation is not proof that the browser trusts its issuer.
`recover` produces a plan; it does not consume recovery codes or mint a login.

The generic API client always connects to the local API on 127.0.0.1:8080 and
does not follow redirects. `--service` explicitly uses the existing powerful
instance-service credential internally. It is not a user login and cannot
promise authorization for every endpoint. Mutating requests require `--write`;
JSON comes from `--body-file filename` or `--body-file -` (stdin), keeping
secrets out of argv. API output may contain private data: do not publish it.
New compatible API endpoints are usable without adding a wrapper command.
No public authentication bypass or development-only endpoint is enabled. The
separate local owner-recovery command below uses HA administrator authority.

## 2. Terminal

Use `nocturne-ha` or the installed shell tools. For example `ps`, `df -h` and
`/usr/lib/postgresql/17/bin/pg_isready` assist diagnosis. Commands are not centrally
recorded and shell history is disabled. Output is still visible in your browser.
Two concurrent terminal sessions are allowed. Closing a tab disconnects its shell;
do not start unmanaged background services. This is not a terminal on the HA host
or inside a different Nocturne app. Changes outside `/data` disappear on upgrade.

## 3. Guided recovery

The wizard displays the same diagnosis and prepares steps for the current or a
new HTTPS URL. It intentionally leaves durable configuration changes in HA's
configuration screen, so Supervisor and the runtime retain the same settings.

1. Back up; configure the new `public_url` and matching certificate/private_key.
2. Check DNS, trusted HTTPS and tenant/share hostnames if used; restart the app.
3. Open Nocturne's `/auth/recovery` page **outside HA ingress**.
4. Use an unused Nocturne recovery code and register a replacement passkey there.
5. Test logout/login and retain new recovery codes before retiring the old domain.

Nocturne recovery sessions are restricted to passkey enrollment. Merely changing
the domain does not migrate passkeys. A CLI cannot perform a browser's WebAuthn
ceremony; the replacement passkey is created on the working HTTPS origin.

### All Nocturne login details and recovery codes lost

This situation is supported through **local HA administrator authority**, without
an existing Nocturne login, passkey, recovery code or remembered username:

1. Back up the selected app through HA. Configure a working HTTPS domain/certificate in
   HA and restart. PostgreSQL must be running; maintenance alone does not start it
   after an invalid app configuration stops the database.
2. Enable maintenance and set a new maintenance password through HA if needed.
   Alternatively use the local container console as root. No Nocturne login is needed.
3. Run `nocturne-ha owner-recovery list` to find the existing owners, usernames,
   tenant IDs and subject IDs. Select the correct tenant and owner explicitly.
4. Run:

   ```sh
   nocturne-ha owner-recovery issue --tenant TENANT_ID --subject SUBJECT_ID --backup-confirmed --write
   ```

   If an OIDC-only owner has no username, also supply `--username recovery-owner`
   to assign one to that existing account. Existing usernames are not changed.
   If the second-factor authenticator is also lost, explicitly add `--reset-totp`.
   This removes TOTP only from the selected account, which may belong to multiple
   tenants. Reconfigure two-factor authentication after recovery. Without this flag,
   existing TOTP remains active and a replacement passkey still requires that factor.
5. The CLI prints the username, new recovery code and code ID once. Open
   `https://YOUR-WORKING-DOMAIN/auth/recovery`, enter username/code, register a
   replacement passkey, then sign in with it. This restores access to the existing
   owner account and its records; it does not create a second owner.
6. Once login works, review/remove obsolete passkeys and generate/store fresh
   recovery codes in Nocturne. Disable maintenance and restart if no longer needed.

The code is native, single-use and stored only as the build's compatible HMAC or salted PBKDF2 hash. The CLI
output is sensitive; it is not copied to app logs or command history. A private
receipt in `/data/maintenance` stores the selected account and code ID, never the
code. The code **does not automatically expire**. Revoke an unused code with:

```sh
nocturne-ha owner-recovery revoke --code-id CODE_ID --write
```

The command rejects inactive, system, demo and non-owner accounts. It never
changes owner roles, existing passkeys or existing recovery codes. TOTP is removed
only with the explicit `--reset-totp` option. The database
mutation is transactional and rechecks eligibility. The build's checked source
contract and actual database must match a reviewed recovery profile. An unknown
contract disables this command rather than guessing a new schema/hash format. Generic CLI API access
remains available for other compatible endpoints.

If access to HA **and** the container/Hyper-V console is also lost, this wrapper
cannot establish administrator authority; restore HA access or a trusted backup
first. Losing Nocturne credentials alone does not prevent this recovery.

## Test and decide

- Disabled: normal start and ingress work as before; maintenance is unavailable.
- Enabled: all three sections and the terminal work behind the password.
- Incorrect password and direct access to ingress/backend are rejected.
- Invalid `public_url` or missing/mismatching certificate stops Nocturne but leaves
  maintenance reachable. The failure remains visible; no silent authentication fallback.
- Recover on a disposable account/domain with a saved recovery code; confirm a
  replacement passkey works and records remain intact.
- Lose all Nocturne credentials on that disposable account; issue a fresh code
  through HA, enroll a replacement passkey and confirm the same owner/data remain.
- Confirm native code consumption is single-use, unused codes can be revoked,
  and a non-owner or wrong tenant cannot receive a code.
- Restart and cold restore; disable maintenance and confirm terminal access ends.

The maintenance host does not auto-restart a failed Nocturne process: diagnose it,
correct HA options, then restart the app. Its UI can remain available while the
API is stopped. If the container itself or Home Assistant is down, ingress cannot
provide recovery; use the Hyper-V/HAOS console or restore a backup.
