# Nocturne Test B

Isolated Test B build pinned to the exact PR #1361 commit, including its merge with upstream main. Use it to verify the eHbA1c lab-result chart tooltips and confirm the upstream report metadata is retained. Default host port 8452; Test B keeps its separate data and cookie namespace.

The update changes the app image and package version only. It does not change Test B's slug, HTTPS port, HA options, or cookie namespace, and it contains no data-reset step. No clinical use.

[Installation and updates](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/PERSONAL.md).
