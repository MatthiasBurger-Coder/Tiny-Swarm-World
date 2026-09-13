# RC1-R03 Test Results

| Actual scenario | Result |
|---|---|
| Hosted fresh WSL lifecycle 34725969899 | LIVE_VERIFIED, all 14 phases and four 25+7 authenticated suites; full artifacts in issue-301 |
| Controlled failing update, WSL/native | Expected typed rollout_failed; canonical recovery, preservation, complete authentication and repeated no-op recovery pass; issue-297 and native package |
| WSL worker loss 20260913T001909Z | Stop observed; canonical reconcile recovers in 4.714 seconds; same three provider identities; 25+7 authentication passes |
| Native worker loss 20260912T234009Z | Stop observed; recovery 3.036 seconds; identity and 25+7 authentication pass |
| First WSL restart | LIVE_PARTIAL, failed full acceptance and endpoint gap retained |
| Targeted Pulsar recovery | Full 25+7 authentication passes in 87.811 seconds; identity/configuration/data preserved |
| Second planned WSL restart | LIVE_VERIFIED; startup 133.629 seconds, authentication 87.931 seconds; no post-start repair |
| Actual native VM reboot | LIVE_VERIFIED; SSH observed after 38.279 seconds; startup verifier 100.427 seconds, authentication 60.164 seconds; changed boot ID |
| Representative prerequisite fixtures | PASS, 116 tests, zero skips; six exact test modules/cases and log hash in prerequisite-fixtures.json |

Every successful authenticated phase has eight before/nine browser/eight after
checks plus seven API checks, zero errors/failures/skips. Initial startup readiness
failures remain individual attempts within the declared bound. The first WSL
failed cycle is separate and is never converted into PASS.

Canonical platform verification checks the managed Docker/Swarm state; a high-level
reconcile mutation label can be no_op even when its provider lifecycle started a
stopped worker. The recorded provider stop/start observations are the authority.

The already executed full candidate quality passed 2066 tests with 18 explicit
live/optional skips. This evidence-only publication runs diff, verification-policy,
JSON assertions, manifest/redaction and link checks; a duplicate full runtime suite
is omitted under QUALITY.md because source/configuration/tests are unchanged.
PR-specific quality/compatibility/Sonar must pass before merge.
