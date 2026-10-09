# Nocturne Personal Release

## Main synchronization — 2026-10-09

The common compiled upstream base is `df000c33e15d3809591261d78a22135bb0176ffd` (2026-10-09T09:16:08Z).
It includes dashboard/chart refresh fixes (#2019), v3 deletion/history fixes
(#1825), and temporary basal uploader-origin handling (#1570), in addition to
the previously merged clock-face and hypo-comparison changes.
Upstream's later `d106f6085` commit only synchronizes translations and skips
image publication. Daily therefore selects the newest verified published main
ancestor; all five channels use that same compiled base.

Official remains Nocturne **0.2.7**. The functional wrapper remains **0.1.13**.
HA package versions are separate and become available only after both native
architectures, runtime/upgrade checks and anonymous image verification pass.

| Channel | Source | Upstream base | Additional code |
|---|---|---|---|
| Daily / Latest | `df000c3` | `df000c3` | None |
| Personal 0.3.28 | `51e2c1d` | `df000c3` | Personal extensions, including Google Health and HbA1c method comparison |
| Test A | `dd2b027` | `df000c3` | Google Health PR #1293, still unmerged |
| Test B | `df000c3` | `df000c3` | Hypo comparison PR #2031 is merged into main |
| Test C | `df000c3` | `df000c3` | Clock-face settings PR #2007 are merged into main |

Images are resolved through the immutable `main-df000c3` tags and OCI digests.
`latest` denotes upstream's official release and is not the Daily discovery tag.
[Upstream publication](https://github.com/nightscout/nocturne/actions/runs/37910180933).
Published package versions and image digests are in each channel's `config.json`
and `provenance.json`; runtime source and feature versions are in
`rootfs/opt/nocturne-ha/version.json`. These files must agree before HA is updated.

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
`0.3.27-p1`. The `p` identifies Personal, like `a`, `b` and `c` for the test
channels. The package base is temporarily ahead of the actual Personal feature
version: feature `0.3.26` is delivered as package `0.3.27-p1` to rank above the
installed `0.3.26-9` and the failed same-base `0.3.26-p11` migration.
Subsequent deliveries keep this published base and increment `p1` → `p2`.
When the feature reaches `0.3.27`, the counter continues; it must not reset to p1.
Only a feature version above the current package base starts a new base at p1.
Legacy numeric suffixes are read only as migration input and trigger a one-time
base bump. Source pins and the actual feature version stay unchanged for this fix.
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
