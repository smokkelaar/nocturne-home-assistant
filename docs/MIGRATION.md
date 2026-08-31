# Existing local prototype: read before switching

The original prototype was installed from HA's local app directory, with a Supervisor identity such as `local_nocturne_local`. This repository keeps the app slug `nocturne_local`, but **Supervisor adds a different repository prefix**. It is consequently a separate installation with a separate private `/data` directory.

Adding this GitHub repository does **not** automatically adopt the existing database, gateway code, instance keys, passkeys or account. An empty setup page in a new installation is not evidence that the old data was migrated.

## Safe current choice

Keep the working local app installed. You can add the repository now to see it in the store, but do not uninstall the old app or start two instances on the same host port. Ordinary local-app restarts should continue to use the existing data.

For collaborators without an existing installation, use the normal fresh-installation instructions.

## Alternative: deliberately start empty

If the operator explicitly does **not** need the prototype's data/account, a fresh repository installation avoids migration entirely. A backup still provides a fallback; leave the prototype installed until the replacement has been tested.

1. Preserve the backup outside HA and note the existing `public_url`, certificate and private-key **filenames**. Do not share private keys or gateway passwords.
2. Install a published, tested repository version. Do not start it while the prototype uses the same HTTPS host port.
3. Before cutover, turn off the prototype's start-on-boot/watchdog options if enabled and stop **only the prototype app**. It remains installed with its old data intact.
4. Configure the new app with the intended stable HTTPS URL and existing certificate filenames. Keep automatic updating off during initial tests.
5. Start the repository app. Its database is empty and it has a **new gateway code** in its own HA web interface; the prototype's gateway code does not transfer.
6. Sign out of the old Nocturne session before cutover, or use a fresh/private browser window for initial setup. Create a new instance/account/passkey and save its new recovery codes. Existing prototype passkeys are not imported by this route.
7. Verify dashboard access, sign-out/sign-in and an app restart before retiring the prototype. For fallback, stop the new app first, then start the old app; never run both on the same host port. New data in the replacement is not present in the old app.

This is a **new installation**, not a test of backup restoration or account migration. It is inappropriate if the old account or data needs to be retained.

## Migration is not implemented yet

Do not treat the following checklist as a tested copy/paste migration procedure:

1. Make a cold backup of the current app, including its **complete database and matching keys**, plus its options. Save the backup outside HA and verify recovery access.
2. Rehearse recovery on a disposable installation. A repository-prefix change may require explicit supported backup/data migration tooling; this repository does not provide it yet.
3. Preserve the exact public hostname/origin and instance identity. Changing them can invalidate passkey expectations.
4. Stop the source instance before any coordinated data transfer. Do not merge independently initialized databases/key files or delete keys to make startup succeed.
5. Verify the destination version, login, settings, database contents and restart behavior before retiring the source. Keep the original and its backup recoverable until this is proven.

Source-code updates in the local prototype directory are a different, manual workflow; they do not subscribe that app to this GitHub repository. There is no promise that HA's normal restore UI automatically maps backups across different repository identities.

**Do not uninstall the local app as a migration step before a verified backup/restore plan exists.** A future migration tool must be non-destructive, explicitly authorized and covered by restore tests.
