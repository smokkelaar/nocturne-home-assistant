# Verification and known limitations

## Automated evidence

The current **Validate** GitHub Actions run is the authority for this commit's automated results. Do not interpret a README badge as certification of clinical use.

- Python regression checks: options, secret persistence/failure handling, ingress isolation, proxy auth/headers, database privileges, process shutdown, dedicated `/health` probing and guarded web patches.
- Node fixtures: real ESM resolution/evaluation, dependency path isolation and the runtime UID guard.
- Node cookie adapter tests: separate namespaces, preserved cookie attributes/deletions, legacy/foreign/duplicate rejection and non-authoritative UI-hint handling.
- Two-app cookie test: real Official/Latest containers, a same-host cookie jar, synthetic refresh-token fixtures, SSR/API renewal, isolated logout/restart and anonymous denial. [Details and manual acceptance](COOKIES.md). This does not perform a real passkey ceremony.
- Official update checks: strict stable versions, paired image pins, source/digest/platform validation, downgrade rejection, version consistency and refusal to write on unexpected build signatures.
- Latest update checks: exact upstream-main commit, one successful paired build job, API revision proof, amd64 manifest selection, double-read race closure, immutable digests, isolated file writes and refusal of incomplete/ambiguous publications.
- TLS regression checks: real OpenSSL pairs, SAN/hostname, key match, validity dates, staged renewals, rejected configuration and rollback without touching the source files.
- Linux amd64 container smoke: both Official and Latest build independently. Each gets empty first boot, API readiness, TLS gateway 401 without credentials, authenticated setup HTML, exact `/health` response without dashboard access, direct-ingress rejection, a separate unpublished-loopback nginx check without Basic auth, mismatched-then-corrected TLS renewal with unchanged database start time, clean stop and same-version restart with persistent keys/database row.
- Recovery container rehearsal: the previous published Official wrapper → Official candidate, plus the previous Latest package → each generated Latest candidate. It performs a full cold `/data` copy, restore into another empty volume using the matching old channel image, matching keys/test row, and refusal to recreate identity in an incomplete restore. [Exact scope](HERSTELPROEF.md).

CI uses only its own disposable database, non-health test row and a synthetic owner fixture. No private HA connection, real account, working passkey or medical data is used. The smoke test intentionally does not publish raw runtime logs or secrets on failure.

The native-gateway checks cover fresh and configured states. The first proves fresh setup is refused and checks a separate unpublished nginx listener. The second creates a synthetic tenant/owner through the setup API, inserts a deliberately nonfunctional credential fixture in that disposable database, then restarts the **real container entrypoint** with `gateway_auth: false` twice. It checks real upstream authorization, no Basic challenge, canonical-host rejection and persistent keys. It requires the orchestrator's disposable marker and an initially empty tenant table; it is not shipped in the HA image. This catches incompatible upstream status fields that mocked tests miss. It does **not** prove real passkey enrollment/login, account migration or clinical use; those remain manual acceptance tests after backup, per installed channel.

## User-reported prototype verification

Before publication, the `0.1.0-test2` prototype was run on amd64 HA OS in Hyper-V. The operator confirmed trusted-hostname HTTPS, Nocturne setup, dashboard access, passkey re-login and continued access after restarting the app. These are manual operator reports, not independently recorded automated browser tests. The public package adds repository/update metadata and tests around that runtime baseline.

## Still to verify / not supported

For remaining proposals and the implemented subset, see [the improvement plan (Dutch)](OPLOSPLAN.md).

- Complete HA cold-backup restore and local-app → repository-app migration.
- Upgrades of populated real-account instances with upstream schema migrations; prior wrapper-only rehearsals on Nocturne 0.2.4 are not changed-upstream schema evidence. Latest's synthetic previous-to-candidate test remains narrower than real account/data use.
- Real HA/DuckDNS certificate renewal and client trust after renewal; the synthetic container reload mechanism is tested, not every real certificate authority/client combination.
- Full HA/VM reboot, failures under resource pressure and long-running reliability.
- IPv6 host-port publication, all client DNS configurations and all passkey platforms.
- ARM64 builds; the upstream images supporting ARM does not prove this wrapper does.
- Full Nocturne dashboard embedded through HA ingress.
- External Nightscout/CGM/pump connectors, API token clients, health-data import and clinical/alarms/dosing behavior.
- Public internet exposure, multi-user security assessment and penetration testing.

No false-ready state, missing data, unavailable connector or unverified feature should be described as working. Report the exact scope of a test, especially “same-version restart” versus “upgrade”.
