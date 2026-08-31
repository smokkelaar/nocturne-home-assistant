## 0.1.1

- Validate TLS SAN/hostname, leaf validity and matching private key before startup; reject invalid pairs with safe error codes. Browser trust is still a separate test.
- Stage immutable private certificate copies; automatically check renewed source files and reload only nginx after validation. Reject partial/mismatched renewals and verify the served leaf before accepting a change.
- HA status now distinguishes server checks from unverified browser DNS/trust/passkey checks, shows certificate expiry, and checks a real web HTTP response.
- Add disposable cold-data restore, baseline 0.1.0-to-candidate upgrade, and missing-identity refusal tests. The upstream updater tests its current-main baseline before proposing a candidate.
- Bound the certificate-generation and cold-copy subprocesses themselves (15/90 seconds), inside the existing Docker/workflow limits; regression tests cover both bounds.
- Nocturne remains 0.2.4. No automatic local-to-repository migration, Supervisor backup importer, real-account upgrade proof or live installation changes.
- **Before updating:** confirm your configured certificate is currently valid, covers `public_url` in a DNS SAN and matches its unencrypted key. Invalid/expired certificates now block startup rather than merely causing browser warnings. Keep a coordinated app backup.

## 0.1.0

- First public repository release, based on the locally tested `0.1.0-test2` wrapper.
- Nocturne API/web 0.2.4, pinned by digest; PostgreSQL 17; amd64 only.
- Shared lock/version metadata, daily stable-upstream update proposals, regression checks and disposable container smoke testing.
- Generic installation, migration, architecture and contributor documentation; no personal configuration included.
- Runtime design remains experimental. Repository installation does not migrate an existing local app's data.
