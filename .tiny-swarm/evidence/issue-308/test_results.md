# RC1-R07 Test Results

| Executed check | Result |
|---|---|
| PR307 reinspection | Merged 2026-09-11, 3998dde7930da9ad1736f2c4c6337e5d4e04d0f5 |
| WSL fresh journey, hosted 34725969899 at 8eb (exact c921 tree) | LIVE_VERIFIED; 14 phases, four complete authenticated suites; setup 1723.846 seconds |
| Native fresh journey at c921 | LIVE_VERIFIED; 14 phases, four complete authenticated suites; setup 1476.238 seconds |
| Planned WSL distribution restart | R03 PASS, 133.629-second readiness and 87.931-second 25+7 authentication |
| Actual native VM reboot | R02 PASS, changed boot ID, 100.427-second readiness and 60.164-second 25+7 authentication |
| Installation, usage, arc42 and system AsciiDoc rendering | PASS, pinned Linux renderer, --failure-level WARN, read-only source and network none |
| Current manual local links and explicit AsciiDoc anchors | PASS; developer workflow link corrected |
| Diff, verification-policy, JSON evidence and current-doc review | PASS |
| Existing legacy-documentation and canonical update CLI regressions | PASS, 20 tests, zero skips |

The first render command mistakenly named documentation/system.adoc; the corrected
path documentation/system/system.adoc and all four outputs rendered successfully.
A second render after the current arc42 corrections also passed with no warning.
The exact renderer digest and latest output hashes are retained in render-20260913.json.

The current source has a passing 2066-test full quality result with 18 declared
live/optional skips. These documentation/evidence changes use the appropriate
narrow checks under QUALITY.md; no duplicate full-suite execution is claimed.
Exact-head hosted quality, compatibility and Sonar are observed before merge.
