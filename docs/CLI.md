# Nocturne command-line diagnostics

All six app channels (Official, Latest, Personal, Test A, Test B and Test C)
package the same `nocturne-ha` command. Run it only inside the matching app
container, for example from an administrator-controlled container console:

```sh
nocturne-ha doctor
nocturne-ha status
nocturne-ha api /api/v3/version
nocturne-ha api /api/v4/status
```

`doctor` checks the configured URL, DNS resolution, the configured certificate
pair and whether the local API responds. These checks do not prove browser
reachability or certificate trust. `status` is an alias for `doctor`.

On Official, Latest and Test A/B/C, `api` accepts only local `/api/...` paths
and sends GET requests to the container's loopback API. It does not accept
external URLs, add service credentials, follow redirects, or perform writes.
Responses are capped at 2 MB. Some endpoints may still return private or
health-related information: inspect the output locally and do not publish it
unredacted.

Personal retains its separate opt-in maintenance terminal and the enhanced
`nocturne-ha api` and `owner-recovery` commands; those powerful options remain
Personal-only and are documented in [Personal maintenance](PERSONAL-MAINTENANCE.md).
No channel exposes a public debug endpoint or Docker/host access.
