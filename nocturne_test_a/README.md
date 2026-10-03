# Nocturne Test A

Pinned build of [Nocturne PR #1293](https://github.com/nightscout/nocturne/pull/1293), with API and web compiled from the same checksum-verified source. Default host port 8451, separate data and cookies.

Version 0.3.26-a10 uses PR commit `ed84340a4` on main `d21c2fb81`. The merge preserves Google Health sleep-session identities and creation times while retaining main's concurrent-import locking and protection for manually deleted sessions. It also retains both sets of translation messages in all eleven languages. Main adds database columns for sleep deletion and heart-rate/step types, plus non-unique original-ID indexes; these migrations do not delete existing records.

After taking a backup, retest recent and historical Google Health imports, repeated sleep imports, sleep stages, and deletion followed by synchronization. A manually deleted sleep session should stay deleted. Also check disconnect/reconnect and continuation after restart with real Google credentials. Automated checks and review results are linked from the delivery pull request; they cannot validate your Google account's consent or data.

The writer skips manually deleted sleep sessions while continuing the import. Sessions absent from a non-empty Google response are soft-deleted as system deletions, so a later reimport can restore them. Explicit purge remains the operation that permanently removes Google's records and reserved import keys.

Shared wrapper 0.1.10 provides `skip_gateway_check` (default false, only effective with `gateway_auth: false`) and preserves public URL ports. API diagnostics, Nocturne authorization, TLS, app identity, settings and storage are retained. This PR build does not include Personal-only extensions.

[Installation and updates](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/PERSONAL.md).
