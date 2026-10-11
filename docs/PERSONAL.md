# Nocturne Personal Release

## Contextual documentation — Personal 0.3.30

Personal adds searchable in-app documentation to the approved upstream main base
`5ad70cbffb8e9cf5f4e9e03133a3c68718b90dca`. Latest and Test A/B/C keep their existing
source pins; Official / Stable remains on its existing release.

Use the book beside Nocturne to switch between your page and its guide. Help
replaces the normal page area and uses the existing sidebar; there is no popup
or duplicate menu. Click the book again or press Escape to return to your
original page, filters and scroll position. Steps,
Heart Rate, Connectors & Apps, Google Health and Appearance have starter content.
The library icon is the default. An optional help bar and hiding/restoring help
can be configured under
**Settings → Appearance → Documentation & help**. The visibility preference is
saved per browser. The collapsed sidebar keeps both controls accessible; hidden
help does not flash before the saved preference is loaded.

The functional HA wrapper remains **0.1.13**. Personal keeps its existing slug,
port, options, cookie namespace and private data. HA package versions become
available once the AMD64 and ARM64 images have been built and published. This
repository offers an update; it does not restart a running HA installation.

The Google Health instructions below describe functionality now present upstream,
not an additional Personal extension.

Personal is an independent Home Assistant app that builds the Personal source fork
on the approved Nocturne Daily base. It has its own database, configuration, sessions
and backups. Installing or updating Personal does not migrate Official or Latest.

| App | Default host port | Source |
| --- | --- | --- |
| Official | 8448 | Official Nocturne release |
| Latest | 8449 | Approved upstream Daily commit |
| Personal | 8450 | Personal fork on the approved Daily base |

## Features in Personal 0.3.11-2

### Google Health

Open **Settings -> Connectors & Apps -> Server Connectors -> Google Health**.
Create your own Google Cloud OAuth Web application client, enable the Google Health
API, and register the callback URL shown in Nocturne. This upstream preview uses
`/settings/connectors/google-health/callback`. Replace the former
`/personal/google/callback` registration before reconnecting Google.

The current connector stores configuration through Nocturne's connector framework
and writes directly to its native health histories. Older Personal previews used
different connector configuration. Updating from 0.3.7 through 0.3.10 to 0.3.11 does not
require disconnecting Google or deleting imported data.

Choose **Import data from**, save the settings and sign in to Google. Review the
inventory of known data types before choosing **Save selection and import**. The
table shows whether data was found, whether permission was granted, the Nocturne
destination, and the saved import status. Unsupported types can be inspected but
cannot be selected for import. Checking a box alone does not enable its import.

| Google Health data | Nocturne destination |
| --- | --- |
| Steps | Existing step history |
| Heart rate | Existing heart-rate history |
| Weight | Existing body-weight history |
| Sleep | Existing sleep sessions and stages |

Nocturne follows result pages from the selected start date, with a 10,000-page safety
limit per data type and operation. Exceeding it produces a technical error instead
of silently reporting a complete import. Large histories take longer and require
more resources. Automatic synchronization starts
after the selection is confirmed, runs approximately every 15 minutes, and reconciles
the configured date range. Use **Sync now** for a manual retry. Disconnect before
editing the history start date or OAuth settings; imported records are preserved
unless you explicitly delete the imported Google data.

Errors retain a technical code and, where available, an HTTP status. Match the code
and attempt time to the API server log. Google account access and available source
data still require testing with your own account; automated tests do not sign in to
Google. Keep client secrets and tokens out of issues, chats and Git.

[Google Cloud and connector setup](https://github.com/smokkelaar/nocturne-personal/blob/review/google-health-final/docs/google-health.md).

Version 0.3.9 also fixes a reproduced 0.3.8 sleep reimport regression that attempted
to change an existing session's database primary key. This does not establish the
cause of failures observed on earlier releases. API console logging remains enabled
when OpenTelemetry is disabled by the HA wrapper. Automated browser and database
tests do not establish that a real Google account import completes on HAOS.

Version 0.3.10 fixes a failure identified in an actual import log: after native
writes and reconciliation completed, parsing an existing `lastSyncedTo` watermark
threw `ArgumentException` because incompatible `DateTimeStyles` flags were combined.
The same parser also prevented scheduled imports from resuming. Both paths now
normalize timestamps to UTC with compatible options. Regression tests cover repeat
imports, UTC and offset timestamps, and older backfills preserving a newer watermark.
No reconnect or deletion of imported data is required; use **Sync now** after updating.

Version 0.3.11 fixes `invalid_google_filter` for sleep. Google requires sleep
queries to use `sleep.interval.end_time`, not the start time. Inventory, imports,
local range checks and reconciliation now use the same end-time window: inclusive
lower bound and exclusive upper bound. Nights that start before the range but end
inside it are included with their stages intact. Other sources, tenants and sessions
ending outside the window are preserved during reconciliation.

After updating, open Google Health and click **Refresh inventory**, select
**Sleep sessions and stages**, then **Save selection and import**. Keep your other
desired data types selected. No Google reconnect or data deletion is needed. Tests
cover the outgoing filters, pagination, date boundaries, repeated imports and
relational reconciliation; a real Google sleep import still requires account access.

## Install or update

### Steps or Heart Rate shows `each_key_duplicate`

Personal delivery `0.3.26-9` fixes the shared actogram renderer when the profile's
lower and upper glucose target values are equal, including two zero values.
Update Personal and hard-refresh the browser (`Ctrl+Shift+R`). Existing imported
readings and profile values are preserved; do not delete data, reconnect Google
or reimport history to address this rendering error.

1. Refresh the Home Assistant app store for the repository
   `https://github.com/smokkelaar/nocturne-home-assistant`, then install or update
   **Nocturne Personal Release**.
2. For a new installation, configure a certificate matching your own hostname and
   use Personal's separate host port:

   ```yaml
   public_url: https://nocturne.example.net:8450
   certificate: fullchain.pem
   private_key: privkey.pem
   gateway_auth: true
   ```

   The container port remains `8448/tcp`, mapped to host port 8450. Local access
   does not require a new router port forward. Do not expose database, API or ingress
   ports. See the [gateway instructions](GATEWAY.md) for initial access setup.
3. Wait for the prebuilt image download and update to finish, then start Personal and open its HA web
   interface. For a new installation, create the instance and account there;
   Official/Latest logins are not imported.
4. Confirm sign-in, reload and restart work, then check the connector and report.

GitHub compiles the API, web application and native alert library from the pinned
source. Home Assistant downloads the prebuilt image. Build progress and the seven
source-build phases are visible in GitHub Actions, rather than in Supervisor logs.

## Versions and release checks

The HA interface distinguishes the wrapper version, Personal feature version, and
approved Nocturne Daily commit. HA packages add a delivery suffix, such as
`0.3.27-p1`. These hyphenated package numbers are historical examples from before prebuilt distribution; current packages use the separate plain 1.0.x series. The `p` identifies Personal, like `a`, `b` and `c` for the test
channels. The package base is temporarily ahead of the actual Personal feature
version: feature `0.3.26` is delivered as package `0.3.27-p1` to rank above the
installed `0.3.26-9` and the failed same-base `0.3.26-p11` migration.
Subsequent deliveries keep this published base and increment `p1` â†’ `p2`.
When the feature reaches `0.3.27`, the counter continues; it must not reset to p1.
Only a feature version above the current package base starts a new base at p1.
Legacy numeric suffixes are read only as migration input and trigger a one-time
base bump. Source pins and the actual feature version stay unchanged for this fix.
Official and Latest keep their own package versions.

For a clean main baseline, the fork's `personal` branch has the same file tree as
upstream main. No `.personal/version.json` is needed or added. The resolver verifies
the tree, uses the canonical approved main source and carries the previous numeric
Personal version for delivery compatibility; that number does not imply extensions.
While the branch remains a clean baseline, promotion can follow a newer approved
Daily source without restoring former Personal code.

Future extension commits with a different file tree require `.personal/version.json`
to identify their feature version and approved Daily base. Those source commits
must descend from that base. The HA lock records their exact source commit,
archive SHA-256 and approved runtime image digests in `upstream-personal.json`.
A release tag alone does not publish an HA update.

HA Personal promotion runs at 07:43 UTC and can also be started manually. The old
Personal source-sync workflow was removed when the fork returned to upstream main.

The HA update proposal must pass **Unit tests** and **Container smoke test** before
protected automatic merge. For Personal changes, validation builds the pinned source,
checks application startup and features, tests cold restore and upgrade from the
previous Personal package, and checks session isolation across the three apps. HA
can offer the new version after the proposal is merged and the repository refreshed.
Automatic installation requires enabling automatic updates for Personal in HA.

## Isolation and recovery

Personal uses slug `nocturne_personal`, its own `/data`, encryption keys and
`NocturnePersonal_` session cookies. Do not copy databases, passkeys or keys between
the three apps. Make a cold backup of the correct app before updating; reverting
the container alone does not undo a database migration.

Experimental; not for clinical use. CI does not verify a real HA installation,
Google consent, passkey ceremony or medical accuracy.

## Development

Application features belong in the source fork; HA packaging and its tests belong
here. `python tools/update_personal.py --update` regenerates only
`upstream-personal.json` and `nocturne_personal` from the selected source.
`python tools/update_personal.py --check` verifies those generated files without
network or live HA access. Update the generator before regenerating its files.

Dependencies and source are pinned. The app does not download changing application
source when it starts. The HA host builds the combined container locally; this
repository distributes the build recipe rather than combined Personal images.
