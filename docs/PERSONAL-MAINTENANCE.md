# Personal maintenance experiment: CLI, terminal and guided recovery

Only **Nocturne Personal Release** includes this opt-in experiment. Official,
Latest, Stable, Main and Test A/B/C are unchanged. No Nocturne source, schema,
passkeys or stored instance credentials are modified by installing it. The explicit
owner-recovery command does add a recovery-code hash to the existing database.

## Enable and compare

1. Make a full Home Assistant backup of Personal, including its private data.
2. Upgrade only Personal. Its local source build needs substantial RAM; do not
   build other channels simultaneously.
3. In Personal's HA configuration set `maintenance_enabled: true` and set
   `maintenance_password` to a unique password of 16–256 characters. Restart.
4. Open Personal's HA web interface and select **Personal onderhoud**. If the
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
2. Check DNS, trusted HTTPS and tenant/share hostnames if used; restart Personal.
3. Open Nocturne's `/auth/recovery` page **outside HA ingress**.
4. Use an unused Nocturne recovery code and register a replacement passkey there.
5. Test logout/login and retain new recovery codes before retiring the old domain.

Nocturne recovery sessions are restricted to passkey enrollment. Merely changing
the domain does not migrate passkeys. A CLI cannot perform a browser's WebAuthn
ceremony; the replacement passkey is created on the working HTTPS origin.

### All Nocturne login details and recovery codes lost

This situation is supported through **local HA administrator authority**, without
an existing Nocturne login, passkey, recovery code or remembered username:

1. Back up Personal through HA. Configure a working HTTPS domain/certificate in
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
5. The CLI prints the username, new recovery code and code ID once. Open
   `https://YOUR-WORKING-DOMAIN/auth/recovery`, enter username/code, register a
   replacement passkey, then sign in with it. This restores access to the existing
   owner account and its records; it does not create a second owner.
6. Once login works, review/remove obsolete passkeys and generate/store fresh
   recovery codes in Nocturne. Disable maintenance and restart if no longer needed.

The code is native, single-use and stored only as a salted PBKDF2 hash. The CLI
output is sensitive; it is not copied to app logs or command history. A private
receipt in `/data/maintenance` stores the selected account and code ID, never the
code. The code **does not automatically expire**. Revoke an unused code with:

```sh
nocturne-ha owner-recovery revoke --code-id CODE_ID --write
```

The command rejects inactive, system, demo and non-owner accounts. It never
changes owner roles, existing passkeys or existing recovery codes. The database
mutation is transactional and rechecks eligibility. Only the currently pinned
Personal Nocturne source is supported: an unreviewed source change disables this
command rather than guessing a new schema/hash format. Generic CLI API access
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
