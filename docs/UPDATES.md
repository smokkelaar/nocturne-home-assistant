# Update policy

There are two separate update systems: **Nocturne upstream → this wrapper repository**, and **this repository → a user's HA installation**.

## 1. Upstream discovery and preparation

The `Check Nocturne updates` GitHub workflow is scheduled daily at 06:23 UTC and can also be started with **Run workflow**. It uses the repository's built-in `GITHUB_TOKEN`; users do not need a Nocturne account, API key or personal GitHub token.

The updater:

1. Reads the latest non-draft, non-prerelease release from `nightscout/nocturne`.
2. Requires a newer numeric three-part version; rejects equal-version retags and downgrades.
3. Resolves **both** API and web images for that release and verifies manifest/blob digests, linux/amd64 availability and the API source commit.
4. Updates both pins, the upstream source record, wrapper patch version, launcher metadata and changelog together.
5. Runs offline tests, builds the proposed container and tests fresh boot, protected setup access, certificate renewal, clean stop, restart and same-version data/key persistence. It also builds the pre-update `HEAD` baseline, rehearses baseline → candidate, and restores the pre-upgrade cold data into another empty volume on that baseline. [Fixture scope and limits](HERSTELPROEF.md).
6. Opens or refreshes one `automation/nocturne-upstream` pull request **only if these checks pass**. It does not merge it.

Missing images, changed patch signatures, an unexpected API revision or failing runtime tests stop the workflow. In that case no release is offered; check the failed workflow and upstream notes. Stable-image mutations under the same release number are deliberately not adopted automatically.

The build/smoke checks run inside the updater itself. This avoids relying on a bot-created PR to trigger CI immediately: GitHub can require maintainer approval for those PR workflow runs. Approve the **Validate** runs when requested; do not bypass required checks.

## 2. Maintainer review and publication

Before merging an update:

- Read upstream release notes, schema migrations, authentication/routing and licensing changes.
- Review the CI baseline → candidate and cold-restore results. These use a setup-only instance and synthetic row. Additionally test a **disposable, backed-up** instance with a non-sensitive account and realistic settings: fixture persistence alone does not validate every upstream data migration.
- Verify passkey login and any supported connectors using non-sensitive test data.
- Confirm the updated wrapper version/changelog, required CI checks and rollback/restore plan.

Merging changes to `main` publishes the new app version to the app store repository. A GitHub Release tag can also be published for release notes/source archives; that alone does not update HA unless `main` contains the new app manifest. Do not merge an untested update into `main` merely to collect feedback: HA users might have auto-update enabled.

Automatic merging is intentionally disabled in this experimental repository. **Discovery and preparation are automatic; final release approval is not.** There is no guarantee that upstream releases become available immediately, or without maintainer attention.

## 3. Home Assistant delivery

HA must have installed the app **from this repository**, not from the old local directory. On its store refresh, it can detect a higher app version and offer an update. The user can choose the app's **Automatic update** option in HA, but it is optional and should remain off until backup/restore and upgrades have been verified for their deployment.

Users do not clone source, paste YAML changes or run the updater themselves for normal repository-app updates. Supervisor performs the local image build. It may take several minutes and require network access. No health data or settings are sent to GitHub by this workflow.

## Repository setup and monitoring

- Enable GitHub Actions and, under Actions → General → Workflow permissions, allow Actions to create pull requests. Individual workflows request their minimal required permissions.
- Keep `main` protected with successful **Unit tests** and **Container smoke test** checks before merge.
- Watch workflow failures and update PRs. GitHub schedules can be delayed and public-repository schedules can be disabled after 60 days without activity; this is not a guaranteed always-on update service.
- Dependabot proposes GitHub Actions dependency updates weekly. PostgreSQL major changes, Node/base OS pins and non-Nocturne system dependencies require separate review.
- Forks do not run the scheduled updater by default: its job checks the canonical repository name. A fork maintainer must deliberately change that guard and enable workflows.

Read-only local check:

```sh
python tools/update_upstream.py --check-upstream
```

Prepare a proposal in a clean contributor branch (writes local tracked files, not HA):

```sh
python tools/update_upstream.py --update
```

References: [GitHub workflow triggering](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow), [scheduled events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule), [HA app repositories](https://developers.home-assistant.io/docs/apps/repository/).
