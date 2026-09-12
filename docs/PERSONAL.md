# Nocturne Personal Release

Personal is an independent Home Assistant app that builds the Personal source fork
on the approved Nocturne Daily base. It has its own database, configuration, sessions
and backups. Installing or updating Personal does not migrate Official or Latest.

| App | Default host port | Source |
| --- | --- | --- |
| Official | 8448 | Official Nocturne release |
| Latest | 8449 | Approved upstream Daily commit |
| Personal | 8450 | Personal fork on the approved Daily base |

## Features in Personal 0.3.11

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

[Google Cloud and connector setup](https://github.com/smokkelaar/nocturne-personal/blob/personal/PERSONAL_USAGE.md).

#### Import diagnostics

On the Google Health settings page, open **Import diagnostics**. This is inside
Nocturne, not in Home Assistant's Supervisor logs. The page refreshes status every
two seconds while open, including after reopening during an import. Progress is
based on data-type stages, not a record-count percentage or time estimate.

The log records the run ID and source commit, requested ranges, page requests and
responses, native write batches and durations, reconciliation, saved watermarks,
and completion or failure. It shows processed record counts and the latest written
record timestamp. These counts can include updates to existing records; they are
not a count of net-new rows. A recent timestamp alone does not prove that all types
or pages completed successfully.

Use **Download diagnostics** to retain the JSON run log before restarting. The current run and
up to four previous runs are held in bounded memory for up to 24 hours, with at most
256 events per run; restart or cache eviction removes them. Diagnostics omit tokens,
client secrets, raw provider responses and measurement values, but dates and counts
are still sensitive. Review an export before sharing it.

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

### Year overview color focus

Open **Reports -> Year Overview** and select a metric. TDD, bolus, basal,
carbohydrates and Time in Range have two adjustable color bounds. Values outside
those bounds use the endpoint colors, increasing contrast within the selected range.

Average glucose has four movable boundaries on its continuous color bar, plus
numeric inputs in the selected mg/dL or mmol/L units. **Reset** restores the default
glucose color scale. Settings are remembered per metric, user and tenant in the
current browser. They change display colors only: glucose targets, Time in Range
calculations and measured values are unchanged.

Personal remains the HA app's name. There is no separate Personal menu or medication/
GLP-1 feature in Nocturne; the connector and report use the normal application areas.

## Install or update

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
3. Wait for the local build to finish, then start Personal and open its HA web
   interface. For a new installation, create the instance and account there;
   Official/Latest logins are not imported.
4. Confirm sign-in, reload and restart work, then check the connector and report.

Personal compiles the API, web application and native alert library locally. This
takes more time, memory and temporary storage than installing the other channels.
Home Assistant Supervisor may keep **Installing (0%)** visible throughout this build.
The wrapper cannot make that native percentage advance evenly.

Open **Settings -> System -> Logs -> Supervisor** and look for
`Nocturne build phase X/7`: build tools, source unpacking, web dependencies and bridge,
API compilation, alert engine, API publishing, and web application build. These are
named build stages, not equal-duration percentage estimates; container assembly and
installation can continue after phase 7.

## Versions and release checks

The HA interface distinguishes the wrapper version, Personal feature version, and
approved Nocturne Daily commit. HA packages add a delivery suffix, such as
`0.3.0-1`. A new source commit with the same feature version increments that suffix.
Official and Latest keep their own package versions.

The source fork's `personal` branch and `.personal/version.json` identify the feature
version and approved Daily base. The HA promotion records the exact source commit,
archive SHA-256 and approved runtime image digests in `upstream-personal.json`.
Both API and web are built from that pinned source; a release tag alone does not
publish an HA update.

Source synchronization checks the approved Daily base at 07:13 UTC, and HA promotion
runs at 07:43 UTC. Both workflows can also be started manually; scheduled runs may
be delayed. Conflicts stop source synchronization instead of discarding fork changes.
Source tests cover Google Health behavior and browser interactions, but do not replace
the HA build checks.

Personal promotion is driven by `.personal/version.json` on the fork's `personal`
branch, not by the upstream contribution branch alone.

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
