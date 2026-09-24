# 0.3.25-b5

Restores the missing eHbA1c and lab-result labels in production tooltips. PR #1361 commit `2b480c6` includes both labels in all 11 supported language catalogs, with English as the source language. A regression test reproduces production translation and verifies every language in CI. The earlier line-boundary fix remains included.

# 0.3.25-b4

Pinned Test B to PR #1361 follow-up commit `7dfdd53`. Lab-only markers outside glucose-estimate coverage no longer extend the eHbA1c line; the regression test covers a lab result before the first estimate. Test B's identity, options, port, data mount, and cookie namespace remain unchanged.

# 0.3.25-b3

Pinned Test B to PR #1361 merge commit `dacd76c`, including the resolved upstream `main` conflict. The HA app identity, options, port, data mount, and cookie namespace are unchanged.

# 0.3.25-b2

Klikbare broninformatie voor PR #1293, het testscenario en actuele systeemresources op de Home Assistant-statuspagina.

# 0.3.25-b1

Test B pinned to PR #1293 (Google Health connector), review follow-up commit `22e4a759f`; source `22e4a759fb4b176b2aba2fdc7ccf68cbe52b94c7`; Daily base `3e30bf504a7d04cb49178edd6e67fc561b58b035`. Temporary isolated instance for manual verification only; Personal and Test A remain in use for other testing.
