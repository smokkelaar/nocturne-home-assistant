# Nocturne Test A

Pinned build of [Nocturne PR #1293](https://github.com/nightscout/nocturne/pull/1293), with API and web compiled from the same checksum-verified source. Default host port 8451, separate data and cookies.

Version 0.3.26-a7 uses PR commit `7c05a8183` on main `637eab7`, with all 21 PR checks passed and no code findings in the current balanced Copilot review. Final human review is still recommended. Test A now preserves public URL ports in generated links and offers an explicit verify_native_auth startup-check override; verification remains enabled by default. API diagnostics, Nocturne authorization, TLS, app identity, settings and storage are retained. This PR build does not include Personal-only extensions.

[Installation and updates](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/PERSONAL.md).
