# Pinned main rollout

`main-rollout.json` makes the Official installation use the same verified
official Nightscout main API/web images as Latest. The exact commit, publisher
run and immutable image digests come from `upstream-latest.json`. No Personal
source changes are included in either installation.

Personal and Test A/B/C compile the same approved Personal commit and archive
checksum. The three test source locks must equal `upstream-personal.json`.
Each installation retains its own options, port, cookie namespace and private
data directory. Candidate metadata, provenance and source notices identify the
effective source.

Updating the approved main pin changes both official image fingerprints.
Both native architectures and the existing startup, recovery, upgrade and
isolation gates must pass before the store advertises a new package.
