## 0.2.0-3

Personal 0.2.0; source `b79ea61b8b8f4a23e295e56136c120ba75371804`; Daily base `3b7514591f854f4794deeeb75d43e33d979d1ee4`.

## 0.2.0-2

- Wrapper 0.1.6 forwards external OAuth Bearer tokens in guarded native mode and routes authenticated v4 requests directly to the API.
- Browser session routing, TLS, tenant checks, Basic gateway mode, cookie isolation and internal-header filtering remain enforced.
- Upstream pins, database schema, stored accounts and keys are unchanged. Existing Home Assistant OAuth clients can retry after updating this app.

# 0.2.0-1

Personal 0.2.0; source `752ebf65017a41508b76346090778d8965c87f9a`; Daily base `3b7514591f854f4794deeeb75d43e33d979d1ee4`.

- Google Health OAuth, selectable steps/heart rate/weight, periodic read-only import and history.
- Encrypted credentials, partial-consent handling, disconnect and explicit import deletion.
- Separate medication log: actual/skipped, explicit units, notes, edits and deletion; no dosing advice.
- New Personal database migrations; take a cold Personal backup before updating.
- Real Google client/consent remains a user setup/test. Official and Latest are unchanged.

# 0.1.0-1

Personal 0.1.0; source `fdf290aab0e5ab5eccedfb15026622a94a0f2d56`; Daily base `3b7514591f854f4794deeeb75d43e33d979d1ee4`.
