# Architecture

```text
HA authenticated ingress ──> :8099 status/launcher (Supervisor peer only)
                                  │ HTTPS link (+ gateway code in default mode)
Browser ──trusted TLS ─────────────> host :8448 Official / :8449 Latest
                                      container :8448 nginx
             │ default: Basic auth; opt-in: native Nocturne auth only
                                  ├─> loopback :8000 Nocturne Web (UID 1655)
                                  └─> loopback :8080 Nocturne API (upstream app UID)
                                               │
                                      loopback :5432 PostgreSQL 17
                                               │
                                      persistent app-private /data
```

The Python supervisor starts PostgreSQL, bootstraps dedicated roles, starts the API, waits for usable status, starts web and then nginx. Any child exit stops the app. Shutdown stops clients first and PostgreSQL last. `/data` is never automatically deleted/reset.

An initial Nocturne `503 setup_required` status is a valid boot condition in default gateway mode. Other 503 responses do not count as ready. Web readiness uses upstream's dedicated `/health` route, so it does not render the dashboard or call protected chart endpoints. This proves process health, not an account/passkey login.

## State and privileges

`/data/secrets.json` holds six independently generated secrets: instance identity, PostgreSQL bootstrap, migration role, API role, web role and gateway. The database and these keys are one recovery unit. Incomplete bootstrap state fails closed. The database roles are not superusers and cannot bypass row-level security. PostgreSQL major versions other than 17 are refused.

The container's process supervisor/nginx master starts as root to initialize directories and drop child privileges. This is not a fully rootless container. PostgreSQL, API and web use separate OS users. No host network, privileged mode, Docker socket, HA API access or Supervisor API access is requested; the inherited Supervisor token is removed before starting children.

Only container HTTPS port 8448 is published to the host. Official maps it to host 8448; Latest maps it to host 8449 by default. HA ingress traffic on 8099 must originate from the Supervisor peer `172.30.32.2`; forwarded source headers are not trusted for this check. The gateway code is served only through that protected page with no-store headers. Do not publish the ingress port independently.

## Authentication and proxy behavior

TLS uses explicitly configured read-only `/ssl` files or a clearly marked temporary test certificate. By default nginx requires gateway Basic auth on all proxied paths. Wrapper 0.1.2 adds an explicit native mode (`gateway_auth: false`) for an already configured owner account. Before nginx starts, the wrapper forces and verifies Nocturne authentication and confirms an anonymous protected-data request receives `401`; a setup/demo/unknown response fails closed. Native mode also requires the canonical configured host and a real configured certificate. Both modes preserve the external hostname **including port**, set forwarded HTTPS headers, and strip incoming Authorization and internal instance-auth headers. No service/admin credential is injected into browser requests.

From 0.1.1, `tls.py` validates leaf SAN/hostname, validity and key match, then keeps a private immutable runtime snapshot. The watcher requires stable source bytes across two observations at least ten seconds apart. Renewal tests a candidate nginx configuration, atomically replaces its config, signals only nginx and verifies the served leaf fingerprint over loopback. Failed candidates retain/restore the previous config. It neither writes `/ssl` nor asserts trust in a client's CA store. Full chain parsing is checked by nginx; revocation and browser trust are outside this preflight. Runtime snapshots are not a persistent fallback after app restart.

Specific OIDC, OAuth, discovery and hub paths route to API; ordinary paths route to web. Dev/operator endpoints are blocked. External token-based clients/connectors are not validated through this gateway and may need a future deliberate authentication design. Do not fix them by removing authentication globally.

## Channel and data isolation

`nocturne_local` is the long-lived Official Supervisor slug so existing repository installs retain their identity and `/data`. `nocturne_latest` is a second Supervisor app with a separate private `/data`, account, passkey, keys, database, options and backup lifecycle. No runtime path reads from the other app. Different default host ports prevent a bind conflict if both are accidentally started.

Runtime/security files are intentionally duplicated because HA app packages are self-contained. Tests require those shared files to remain byte-identical. Channel metadata, Docker image pins, version, changelog, name, slug, default URL and published host port are allowed to differ. Never solve duplication by sharing or mounting one channel's private data into the other.

## Build coupling and limits

The API image is Ubuntu/glibc, so the Node binary is copied from a compatible Debian/glibc image, not Alpine. The pinned upstream web output is copied, guarded patches applied, then production dependencies are installed with its frozen lockfile. Dependency resolution/imports are checked as the real runtime UID, in both app and bridge module contexts.

PostgreSQL 17 is added using PGDG's Ubuntu noble repository. A future upstream base OS change can require a wrapper change even when upstream images exist. Tests intentionally stop publication when compatibility signatures change. Official tracks only manually promoted releases. Latest discovers upstream `main`, but converts it to an exact commit and paired immutable digests before any package is offered.
