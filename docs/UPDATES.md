# Update policy

This repository exposes two independent Home Assistant apps. Their update policies deliberately differ:

| Channel | Upstream source | Discovery | Merge | Recommended HA setting |
|---|---|---|---|---|
| **Nocturne Official Release** | Latest numbered, non-prerelease Nocturne release | Maintainer starts the workflow manually | Maintainer reviews and merges manually | Automatic update off |
| **Nocturne Latest Release** | Current upstream `main`, only after its paired image build succeeded | Daily at 06:53 UTC and on demand | Auto-merge may complete only after required checks | Optional, only for replaceable test data |

Both channels use immutable source commits and OCI digests in the version that Home Assistant builds. Neither app downloads a floating `latest` image at startup. [Identity, port and data separation](CHANNELS.md).

## Official: deliberate release promotion

The **Check Official Nocturne release manually** workflow has no schedule. A maintainer starts it with **Run workflow**. The updater:

1. Reads the latest non-draft, non-prerelease release from `nightscout/nocturne`.
2. Requires a newer numeric three-part version; it rejects equal-version retags and downgrades.
3. Resolves both API and web images, validates blobs, linux/amd64 availability and the API source commit.
4. Updates `upstream.json` and only the `nocturne_local` package as one proposal.
5. Runs offline checks, candidate smoke tests and a baseline-to-candidate/cold-restore rehearsal.
6. Opens or refreshes `automation/nocturne-official` and explicitly dispatches the required Validate workflow.

The workflow never requests auto-merge. A maintainer must review upstream release notes, schema/authentication/licensing changes, CI evidence and the recovery plan before merging. Stable image mutation under an unchanged release number is not silently adopted.

Read-only local check:

```sh
python tools/update_upstream.py --check-upstream
```

Prepare the same proposal locally:

```sh
python tools/update_upstream.py --update
```

## Latest: daily tested snapshot

The **Check Latest Nocturne main daily** workflow runs daily and can also be started manually. It does not trust a moving tag as an install input. The updater:

1. Reads the exact current commit of upstream `main`.
2. Finds an upstream `docker-publish.yml` run whose **build-and-push** job succeeded for that commit. Another unrelated job in that upstream workflow may have failed; API and web still must originate from the same successful paired build job.
3. Resolves exactly one linux/amd64 API and web manifest. The API image's embedded `GIT_COMMIT` must equal `main`.
4. Repeats the main/API lookup after resolving web so a moving tag cannot mix two publications.
5. Writes the exact commit, workflow run and image digests to `upstream-latest.json` and changes only `nocturne_latest` version/build metadata.
6. Runs all unit checks, both updater consistency checks, a real Latest container smoke test and a previous-Latest-to-candidate cold-restore rehearsal.
7. Opens or refreshes `automation/nocturne-latest`, dispatches the required Validate workflow and requests squash auto-merge.

The pull request is restricted to the Latest lock and package metadata/build files. Branch protection keeps it open until **Unit tests** and **Container smoke test** pass. The repository setting **Allow auto-merge** must be enabled; bypassing checks or allowing direct main pushes is not a substitute.

If upstream main has no complete promotable paired build, patch signatures changed, provenance is ambiguous or any test fails, no new app version is offered. This is an expected safe no-op/failure, not a reason to fall back to `:latest`.

Read-only local check:

```sh
python tools/update_latest.py --check-upstream
```

Prepare the same candidate locally:

```sh
python tools/update_latest.py --update
```

Latest remains highly experimental. Automated technical tests do not prove dashboard completeness, passkey behavior on every client, connector compatibility or safe real-data migrations.

## Delivery to Home Assistant

Merging a changed package version into `main` lets the HA app store offer that channel's update after a repository refresh. The two app versions and HA's **Automatic update** switches are independent:

- An Official merge never changes or restarts Latest.
- A Latest merge never changes or restarts Official.
- GitHub does not remotely install or restart either app.
- Supervisor performs the local image build when the user installs/updates.

For Official, keep HA automatic updates off and update after a reviewed backup/checkpoint. For Latest, daily end-to-end delivery is possible only if the user explicitly enables automatic updates on **Nocturne Latest Release**. Leave Official's switch off. A cold backup remains necessary; an old image is not a rollback for a migrated database.

## Repository setup and monitoring

- Enable Actions to create pull requests and enable repository auto-merge for the protected Latest PR path.
- Protect `main` with successful **Unit tests** and **Container smoke test** checks and conversation resolution before merge.
- Keep the Official workflow manual and the Latest workflow restricted to its own package paths.
- Watch scheduled-workflow failures. GitHub schedules can be delayed or disabled after prolonged public-repository inactivity; this is not a guaranteed always-on service.
- Dependabot proposes GitHub Actions dependency updates separately. PostgreSQL, Node/base OS and other wrapper dependencies remain maintainer-reviewed.
- Canonical-repository guards prevent forks from unexpectedly running publisher workflows.

References: [GitHub workflow triggering](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow), [scheduled events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule), [HA app repositories](https://developers.home-assistant.io/docs/apps/repository/).
