# Pinned main rollout

`main-rollout.json` selects the exact maintained fork-main commit and archive
checksum compiled for Official, Latest and Test A/B/C. These app names retain
their existing storage slots; their effective runtime is a main snapshot rather
than the upstream release previously assigned to that slot. Personal keeps its
own pinned extension branch.

The publisher reuses the source compiler for both API and web. It keeps each
slot's options, port, cookie namespace and private data directory. Candidate
runtime metadata, image descriptions, provenance and corresponding-source
notices identify the effective source. The original upstream lock files remain
the base-package inputs, not a claim that those binaries are the delivered API.

Changing the main pin changes the image fingerprint. Both native architectures
and the existing startup, recovery, upgrade and isolation gates are still
required before the store advertises a new package. Removing the rollout file
also changes the fingerprint and restores the channel's normal source policy on
its next reviewed build. Do not enable write-back before verifying the deployed
temporary-basal JSON shape.
