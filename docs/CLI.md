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

From wrapper 0.1.13 all six channels include the opt-in maintenance terminal,
guided recovery, and enhanced CLI. `api` accepts only local `/api/...` paths,
defaults to GET and follows no redirects. Mutations require `--write`; powerful
instance-service credentials require the separate `--service` flag. Responses
are capped at 2 MB and can contain private data. Inspect output locally and
do not publish it unredacted.

Start lost-credential recovery with `nocturne-ha owner-recovery check`, then
`nocturne-ha owner-recovery list`. A build whose recovery contract is unknown
cannot issue or revoke owner-recovery codes. Unrelated new source commits are
accepted automatically when their complete recovery contract is unchanged.
Follow the [step-by-step maintenance guide](PERSONAL-MAINTENANCE.md).
No channel exposes a public debug endpoint or Docker/host access.
