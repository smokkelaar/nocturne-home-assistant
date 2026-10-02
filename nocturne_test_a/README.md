# Nocturne Test A

Pinned build of [Nocturne PR #1293](https://github.com/nightscout/nocturne/pull/1293), with API and web compiled from the same checksum-verified source. Default host port 8451, separate data and cookies.

Version 0.3.26-a6 uses PR commit `7c05a8183` on main `637eab7`, with all 21 PR checks passed and no code findings in the current balanced Copilot review. Final human review is still recommended. This snapshot includes the credential, token-cache, authorization, parser and queued-import fixes. API warning/error logging remains enabled; no remote OTLP export is configured. Test A retains its app identity, settings and storage. This PR build does not include Personal-only extensions.

[Installation and updates](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/PERSONAL.md).
