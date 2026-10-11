# Selective HA builds

Run **Actions → Validate → Run workflow**. The `channels` field accepts:

| Input | Builds |
| --- | --- |
| `changed` | Only channels whose image inputs changed; none for docs or CI-only edits |
| `personal` | Personal only |
| `official,latest,personal,test-c` | Those four channels only |
| `all` | All six channels |

Names are `official`, `latest`, `personal`, `test-a`, `test-b`, `test-c`.
Explicit names always build the requested channels, even when unchanged. The
`force` option with `changed` keeps the legacy behavior of rebuilding all six.
Invalid names fail before any image build or registry request.

Leave `publish` disabled to validate. Enable it to publish tested images and
prepare the HA-appstore promotion. Both AMD64 and ARM64 remain required: one
channel means two native jobs, four means eight, and all six means twelve.

Each selected image is built once, with build cache, and checked for startup,
owner recovery, cold restore and upgrade from its published predecessor.
Maintenance tests use the same selection. The separate always-running Test A,
Test C and serial core builds have been removed. Unit tests still cover all
channels because they are quick and check shared app identities and generators.

Session isolation uses already-published peer images instead of rebuilding
unselected channels. During publication, all selected Official/Latest/Personal
images are checked together before the appstore promotion; unselected peers
retain their published versions. A failed check prevents the store update.

PRs no longer force all six channels. Runtime fingerprints include package
files, source/version metadata, licenses, runtime/toolchain pins and publication
policy. Docs and orchestration changes do not cause image updates. Existing
fingerprints are verified against their recorded builder commit so this change
does not force a one-time rebuild. For material changes to generated image
content, bump `publication.json`'s `format`.

Examples using GitHub CLI:

```sh
gh workflow run validate.yml --ref main -f channels=personal
gh workflow run validate.yml --ref main -f channels=official,latest,personal,test-c
gh workflow run validate.yml --ref main -f channels=all -f publish=true
```

This reduces duplicate builds and runner queues. Nocturne compilation, tests and
registry transfers still take time; this change does not promise a fixed duration.
