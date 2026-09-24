# Nocturne Test B

Isolated Test B build pinned to PR #1361 follow-up commit `7dfdd53`, including its merge with upstream main. Verify the eHbA1c lab-result tooltips and report metadata. In particular, a lab date before the first glucose estimate must remain a standalone marker and must not extend the estimate line back to that date. Default host port 8452; Test B keeps its separate data and cookie namespace.

The update changes the app image and package version only. It does not change Test B's slug, HTTPS port, HA options, or cookie namespace, and it contains no data-reset step. No clinical use.

[Installation and updates](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/PERSONAL.md).
