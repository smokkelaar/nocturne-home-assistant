# Verification and known limitations

## Automated evidence

The current **Validate** GitHub Actions run is the authority for this commit's automated results. Do not interpret a README badge as certification of clinical use.

- Python regression checks: options, secret persistence/failure handling, ingress isolation, proxy auth/headers, database privileges, process shutdown and guarded web patches.
- Node fixtures: real ESM resolution/evaluation, dependency path isolation and the runtime UID guard.
- Update checks: strict stable versions, paired image pins, source/digest/platform validation, downgrade rejection, version consistency and refusal to write on unexpected build signatures.
- Linux amd64 container smoke: build, empty first boot, API readiness, TLS gateway 401 without credentials, authenticated setup HTML, direct-ingress rejection, clean stop and same-version restart with persistent keys/database row.

CI uses only a disposable empty database plus a non-health test row. No private HA connection, real account, passkey or medical data is used. The smoke test intentionally does not publish raw runtime logs or secrets on failure.

## User-reported prototype verification

Before publication, the `0.1.0-test2` prototype was run on amd64 HA OS in Hyper-V. The operator confirmed trusted-hostname HTTPS, Nocturne setup, dashboard access, passkey re-login and continued access after restarting the app. These are manual operator reports, not independently recorded automated browser tests. The public package adds repository/update metadata and tests around that runtime baseline.

## Still to verify / not supported

- Complete HA cold-backup restore and local-app → repository-app migration.
- Cross-version upgrades with real schema migrations and rollback/restore.
- Certificate renewal/reload automation (currently restart the app after renewal).
- Full HA/VM reboot, failures under resource pressure and long-running reliability.
- IPv6 host-port publication, all client DNS configurations and all passkey platforms.
- ARM64 builds; the upstream images supporting ARM does not prove this wrapper does.
- Full Nocturne dashboard embedded through HA ingress.
- External Nightscout/CGM/pump connectors, API token clients, health-data import and clinical/alarms/dosing behavior.
- Public internet exposure, multi-user security assessment and penetration testing.

No false-ready state, missing data, unavailable connector or unverified feature should be described as working. Report the exact scope of a test, especially “same-version restart” versus “upgrade”.
