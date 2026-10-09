# Nocturne Test A

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

Pinned build of [Nocturne PR #1293](https://github.com/nightscout/nocturne/pull/1293), with API and web compiled from the same checksum-verified source. Default host port 8451, separate data and cookies.

The current source is `dd2b027746cc956be9a6f5564d805f0bdc76c64d` on main `df000c33e15d3809591261d78a22135bb0176ffd`; see the published config for the HA package version. The merge preserves Google Health sleep-session identities and creation times while retaining main's concurrent-import locking and protection for manually deleted sessions. It also retains both sets of translation messages in all eleven languages. Main adds database columns for sleep deletion and heart-rate/step types, plus non-unique original-ID indexes; these migrations do not delete existing records.

After taking a backup, retest recent and historical Google Health imports, repeated sleep imports, sleep stages, and deletion followed by synchronization. A manually deleted sleep session should stay deleted. Also check disconnect/reconnect and continuation after restart with real Google credentials. Automated checks and review results are linked from the delivery pull request; they cannot validate your Google account's consent or data.

The writer skips manually deleted sleep sessions while continuing the import. Sessions absent from a non-empty Google response are soft-deleted as system deletions, so a later reimport can restore them. Explicit purge remains the operation that permanently removes Google's records and reserved import keys.

Shared wrapper 0.1.13 provides `skip_gateway_check` (default false, only effective with `gateway_auth: false`) and preserves public URL ports. API diagnostics, Nocturne authorization, TLS, app identity, settings and storage are retained. This PR build does not include Personal-only extensions.

[Installation and updates](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/PERSONAL.md).
