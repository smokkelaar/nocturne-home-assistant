# Verification and known limitations

## Automated evidence

The current **Validate** GitHub Actions run is the authority for this commit's automated results. Do not interpret a README badge as certification of clinical use.

- Python regression checks: options, secret persistence/failure handling, ingress isolation, proxy auth/headers, database privileges, process shutdown, dedicated `/health` probing and guarded web patches.
- Node fixtures: real ESM resolution/evaluation, dependency path isolation and the runtime UID guard.
- Update checks: strict stable versions, paired image pins, source/digest/platform validation, downgrade rejection, version consistency and refusal to write on unexpected build signatures.
- TLS regression checks: real OpenSSL pairs, SAN/hostname, key match, validity dates, staged renewals, rejected configuration and rollback without touching the source files.
- Linux amd64 container smoke: build, empty first boot, API readiness, TLS gateway 401 without credentials, authenticated setup HTML, exact `/health` response without dashboard access, direct-ingress rejection, a separate unpublished-loopback nginx check without Basic auth, mismatched-then-corrected TLS renewal with unchanged database start time, clean stop and same-version restart with persistent keys/database row.
- Recovery container rehearsal: immutable wrapper 0.1.1 baseline → candidate, full cold `/data` copy, restore into another empty volume using the old image, matching keys/test row, and refusal to recreate identity in an incomplete restore. [Exact scope](HERSTELPROEF.md).

CI uses only a disposable empty database plus a non-health test row. No private HA connection, real account, passkey or medical data is used. The smoke test intentionally does not publish raw runtime logs or secrets on failure.

The native-gateway container check proves generated nginx has no Basic challenge, rejects a wrong hostname, leaves fresh setup guarded and does not expose protected data. Because the disposable fixture has no owner account, it does **not** prove login with a real passkey. That remains a manual 0.1.2 acceptance test after backup.

## User-reported prototype verification

Before publication, the `0.1.0-test2` prototype was run on amd64 HA OS in Hyper-V. The operator confirmed trusted-hostname HTTPS, Nocturne setup, dashboard access, passkey re-login and continued access after restarting the app. These are manual operator reports, not independently recorded automated browser tests. The public package adds repository/update metadata and tests around that runtime baseline.

## Still to verify / not supported

For remaining proposals and the implemented subset, see [the improvement plan (Dutch)](OPLOSPLAN.md).

- Complete HA cold-backup restore and local-app → repository-app migration.
- Upgrades of populated real-account instances with upstream schema migrations; 0.1.1 → 0.1.2 is a wrapper upgrade on Nocturne 0.2.4, not a changed upstream schema.
- Real HA/DuckDNS certificate renewal and client trust after renewal; the synthetic container reload mechanism is tested, not every real certificate authority/client combination.
- Full HA/VM reboot, failures under resource pressure and long-running reliability.
- IPv6 host-port publication, all client DNS configurations and all passkey platforms.
- ARM64 builds; the upstream images supporting ARM does not prove this wrapper does.
- Full Nocturne dashboard embedded through HA ingress.
- External Nightscout/CGM/pump connectors, API token clients, health-data import and clinical/alarms/dosing behavior.
- Public internet exposure, multi-user security assessment and penetration testing.

No false-ready state, missing data, unavailable connector or unverified feature should be described as working. Report the exact scope of a test, especially “same-version restart” versus “upgrade”.
