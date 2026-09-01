# Security and privacy

This is an experimental wrapper, not a security-audited or medically validated product. Only current wrapper releases are maintained. **Nocturne Latest Release** has extra upstream-development risk and is not a security-hardening channel. No security response SLA is offered.

Please use GitHub's **Report a vulnerability** feature under the Security tab for credential disclosure, authentication bypass, data isolation or similar issues. If private reporting is unavailable, open a minimal issue requesting a private reporting channel **without exploit details or personal data**.

Do not attach databases, health data, API/gateway tokens, HA credentials, session cookies, passkey recovery codes, private keys or full diagnostics to any public report.

The app uses a gateway password in addition to Nocturne authentication by default, plus read-only TLS files, least-privilege database roles and private loopback API/database listeners. From wrapper 0.1.2 an existing configured instance may explicitly set `gateway_auth: false`. Startup then requires configured TLS, forces Nocturne authentication, verifies the loaded non-demo instance reports authentication as mandatory and verifies anonymous protected-data access is denied. This removes only the extra Basic prompt, not Nocturne's passkey login. These are defense-in-depth measures, not a security audit or a guarantee of safe internet exposure. Do not forward its ports publicly during testing.

If a gateway code was exposed in a screenshot, setting `gateway_auth: false` is not credential rotation. Either return to `gateway_auth: true` and rotate **only that gateway credential** in a controlled maintenance procedure, or keep the native mode only after its documented checks. Do not delete `secrets.json` or regenerate the instance/database keys. A supported rotation UI is not implemented yet.

Official and Latest are separate Supervisor apps. Never copy their `/data`, `secrets.json`, databases, passkeys, recovery material or backups across channels. Different default host ports prevent a bind conflict; they do not make simultaneous exposure or real medical use safe. Keep Latest data disposable and do not enable public port forwarding for either channel.
