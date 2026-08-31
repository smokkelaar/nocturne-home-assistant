# Existing local prototype: read before switching

The original prototype was installed from HA's local app directory, with a Supervisor identity such as `local_nocturne_local`. This repository keeps the app slug `nocturne_local`, but **Supervisor adds a different repository prefix**. It is consequently a separate installation with a separate private `/data` directory.

Adding this GitHub repository does **not** automatically adopt the existing database, gateway code, instance keys, passkeys or account. An empty setup page in a new installation is not evidence that the old data was migrated.

## Safe current choice

Keep the working local app installed. You can add the repository now to see it in the store, but do not uninstall the old app or start two instances on the same host port. Ordinary local-app restarts should continue to use the existing data.

For collaborators without an existing installation, use the normal fresh-installation instructions.

## Migration is not implemented yet

Do not treat the following checklist as a tested copy/paste migration procedure:

1. Make a cold backup of the current app, including its **complete database and matching keys**, plus its options. Save the backup outside HA and verify recovery access.
2. Rehearse recovery on a disposable installation. A repository-prefix change may require explicit supported backup/data migration tooling; this repository does not provide it yet.
3. Preserve the exact public hostname/origin and instance identity. Changing them can invalidate passkey expectations.
4. Stop the source instance before any coordinated data transfer. Do not merge independently initialized databases/key files or delete keys to make startup succeed.
5. Verify the destination version, login, settings, database contents and restart behavior before retiring the source. Keep the original and its backup recoverable until this is proven.

Source-code updates in the local prototype directory are a different, manual workflow; they do not subscribe that app to this GitHub repository. There is no promise that HA's normal restore UI automatically maps backups across different repository identities.

**Do not uninstall the local app as a migration step before a verified backup/restore plan exists.** A future migration tool must be non-destructive, explicitly authorized and covered by restore tests.
