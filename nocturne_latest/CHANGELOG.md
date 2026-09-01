## 0.1.0

- First separately installable **Nocturne Latest Release** channel.
- Pin API and web images from upstream `main` commit `3b7514591f854f4794deeeb75d43e33d979d1ee4` by immutable digest; HA never builds from a floating image reference.
- Use slug `nocturne_latest`, a separate private data directory and default host port 8449. Official data, accounts, passkeys and keys are not copied.
- Include the same guarded TLS, gateway/passkey, health and persistence wrapper as the Official channel.
- Daily automation may promote newer tested `main` snapshots. Schema changes can be frequent and rollback is not guaranteed; keep cold backups.
