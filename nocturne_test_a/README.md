# Nocturne Test A

Pinned build of [Nocturne PR #1293](https://github.com/nightscout/nocturne/pull/1293), with API and web compiled from the same checksum-verified source. Default host port 8451, separate data and cookies.

Version 0.3.26-a5 uses PR commit `7bf77f155` on main `637eab7` and fixes missing PostgreSQL credentials in Google Health's coordinator sessions. API warning/error logging remains enabled; no remote OTLP export is configured. Test A retains its app identity, settings and storage. This PR build replaces the Personal source and does not include Personal-only extensions.

[Installation and updates](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/PERSONAL.md).
