# Personal maintenance experiment: CLI, terminal and guided recovery

Only **Nocturne Personal Release** includes this opt-in experiment. Official,
Latest, Stable, Main and Test A/B/C are unchanged. No Nocturne source, database,
passkeys or stored instance credentials are modified by installing it.

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
No authentication bypass, database SQL reset or development-only endpoint is
enabled.

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
the domain does not migrate passkeys. If no recovery code remains, use a linked
login provider or an authorized owner; this experiment does **not** implement
owner recovery without existing proof of access. A CLI cannot perform a browser's
WebAuthn ceremony. Restore backups only when needed, rather than deleting accounts.

## Test and decide

- Disabled: normal start and ingress work as before; maintenance is unavailable.
- Enabled: all three sections and the terminal work behind the password.
- Incorrect password and direct access to ingress/backend are rejected.
- Invalid `public_url` or missing/mismatching certificate stops Nocturne but leaves
  maintenance reachable. The failure remains visible; no silent authentication fallback.
- Recover on a disposable account/domain with a saved recovery code; confirm a
  replacement passkey works and records remain intact.
- Restart and cold restore; disable maintenance and confirm terminal access ends.

The maintenance host does not auto-restart a failed Nocturne process: diagnose it,
correct HA options, then restart the app. Its UI can remain available while the
API is stopped. If the container itself or Home Assistant is down, ingress cannot
provide recovery; use the Hyper-V/HAOS console or restore a backup.
