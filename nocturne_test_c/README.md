# Nocturne Test C

Isolated Nocturne main build with a personal pre-PR branch of the Google Health connector (heart-rate per-minute aggregation, day-chunked backfill) for manual verification before it is sent to PR #1293. Default host port 8453, separate data and cookies.

This test combines the approved Nocturne runtime basis with that personal source overlay. It covers read-only Google Health imports for steps, heart rate, weight and sleep; it makes no dosing advice or insulin/IOB changes.

[Installation and updates](https://github.com/smokkelaar/nocturne-home-assistant/blob/main/docs/UPDATES.md).
