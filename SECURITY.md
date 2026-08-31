# Security and privacy

This is an experimental wrapper, not a security-audited or medically validated product. Only the latest wrapper release is maintained. No security response SLA is offered.

Please use GitHub's **Report a vulnerability** feature under the Security tab for credential disclosure, authentication bypass, data isolation or similar issues. If private reporting is unavailable, open a minimal issue requesting a private reporting channel **without exploit details or personal data**.

Do not attach databases, health data, API/gateway tokens, HA credentials, session cookies, passkey recovery codes, private keys or full diagnostics to any public report.

The app uses a mandatory gateway password in addition to Nocturne authentication, read-only TLS files, least-privilege database roles and private loopback API/database listeners. These are defense-in-depth measures, not a guarantee of safe internet exposure. Do not forward its ports publicly during testing.

If a gateway code was exposed in a screenshot, rotate **only that gateway credential** in a controlled maintenance procedure; do not delete `secrets.json` or regenerate the instance/database keys. A supported rotation UI is not implemented yet.
