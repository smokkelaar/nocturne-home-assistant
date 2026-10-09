# Nocturne Latest Release

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

**[Nederlandse visuele installatiehandleiding: van repository tot dashboard](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/INSTALLATIE.md)**

The frequently updated upstream-`main` channel: self-contained Nocturne API/web + PostgreSQL 17 + HTTPS gateway for Home Assistant OS on amd64. It has its own `nocturne_latest` identity, private data and default host port 8449.

Do not restore an Official backup into Latest or treat Latest as a rollback path. Development snapshots can introduce unfinished features and irreversible database migrations.

Use the **Documentation** tab before installing. This is an unofficial experimental app, not a HACS integration or a medically validated service.

The HA web interface is a protected status/launcher page. The actual Nocturne UI opens separately using your configured HTTPS hostname and Nocturne's own authentication.

Source, issues and contributions: https://github.com/smokkelaar/nocturne-home-assistant
