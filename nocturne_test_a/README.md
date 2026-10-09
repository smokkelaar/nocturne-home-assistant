# Nocturne Test A

## Main synchronization — 2026-10-09

All development sources now include upstream main `ef8850840c349fa9519a7f3022599ec9adddff82` (2026-10-09 06:48:03 UTC).
Official remains Nocturne **0.2.7** because no newer release exists.
The functional wrapper remains **0.1.13**. HA package versions are generated only
after both native architectures pass publication checks; source versions are separate.

| Channel | Source | Upstream base | Additional code |
|---|---|---|---|
| Daily / Latest | `ef88508` | `ef88508` | None |
| Personal 0.3.27 | `6ec88de` | `ef88508` | Personal extensions, including Google Health and HbA1c method comparison |
| Test A | `4e2ec5c` | `ef88508` | Google Health PR #1293, still unmerged |
| Test B | `ef88508` | `ef88508` | Hypo comparison PR #2031 is already merged into main |
| Test C | `ef88508` | `ef88508` | Clock-face settings PR #2007 is already merged into main |

Main images come from the immutable `main-ef88508` publication tags and verified
OCI digests. `latest` now denotes an official upstream release, so it is not the
discovery source for Daily. [Upstream publication](https://github.com/nightscout/nocturne/actions/runs/37895441854).

Published package versions and image digests are in each channel's `config.json`
and `provenance.json`; the runtime source and feature version are in
`rootfs/opt/nocturne-ha/version.json`. These files must agree before HA is updated.

Pinned build of [Nocturne PR #1293](https://github.com/nightscout/nocturne/pull/1293), with API and web compiled from the same checksum-verified source. Default host port 8451, separate data and cookies.

The current source is `4e2ec5cdbb32922e4fb390dc7b2a85b622913627` on main `ef8850840c349fa9519a7f3022599ec9adddff82`; see the published config for the HA package version. The merge preserves Google Health sleep-session identities and creation times while retaining main's concurrent-import locking and protection for manually deleted sessions. It also retains both sets of translation messages in all eleven languages. Main adds database columns for sleep deletion and heart-rate/step types, plus non-unique original-ID indexes; these migrations do not delete existing records.

After taking a backup, retest recent and historical Google Health imports, repeated sleep imports, sleep stages, and deletion followed by synchronization. A manually deleted sleep session should stay deleted. Also check disconnect/reconnect and continuation after restart with real Google credentials. Automated checks and review results are linked from the delivery pull request; they cannot validate your Google account's consent or data.

The writer skips manually deleted sleep sessions while continuing the import. Sessions absent from a non-empty Google response are soft-deleted as system deletions, so a later reimport can restore them. Explicit purge remains the operation that permanently removes Google's records and reserved import keys.

Shared wrapper 0.1.13 provides `skip_gateway_check` (default false, only effective with `gateway_auth: false`) and preserves public URL ports. API diagnostics, Nocturne authorization, TLS, app identity, settings and storage are retained. This PR build does not include Personal-only extensions.

[Installation and updates](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/PERSONAL.md).
