# Verification results

Final runtime/test candidate: `89357c4a1fd463bbe5ee2ae9dac074180513eace`. Exact executed revisions remain attached to retained earlier bundles.

## Local gates

`python3 tools/quality_gate.py quality`: exit0, 2,377 tests passed, 18 existing skips, 37 architecture tests, six import contracts, 732 source files typechecked. Tested isolated tree at8819d5d3 plus the two frozen credential helper/test changes was byte-identical to committed89357c4a; the commit occurred after this gate. Independent commit reviewer confirmed hashes. `local-verification.json` records protected complete log checksum.

Quality fixes:21focusedPASS including actualPester. Mutation reporting:49tests/6fail RED,98focusedPASS GREEN,2,375fullPASS. Cookie helper:6tests/3fail RED,6PASS GREEN,2,377fullPASS. RC1S07 six mocked prerequisite modules:122PASS,zero skips/failures/errors. Local results establish local quality, not browser/live/Sonar success.

## WSL managed target

Clean1bd3 fresh managed installation/reset plus baseline/reconcile: each25live+7API with no failures/errors/skips. Independent review retains unchanged runtime applicability. Atbdd: genuine image update/repeat/recovery, real failed rollout and recovery, service replacement, worker recovery and all-managed-node cold restart were executed; post-success25+7 and persistent job/build/artifact/configuration/volume/credential/identity comparisons passed.

Final893 affected worker rerun: actual stopped→running, converged/executedtrue, unchanged repeatno_op/executedfalse,25+7PASS. Both final-source credential transitions passed with actual source/application/session invalidation/reapply/consumer restart/restoration checks and postrestore25+7. Earlier failed login/observation/deployment attempts remain separate in the phase ledger.

Windowsbridge/preflight and nine routedHTTPS endpoints checked from actual Windows client with exactpublicCA; no systemtrust mutation. DefaultWindowsTrustFailure and unavailable revocation remain explicit. Actual selected TSW-RC1-Isolated distribution restart on893passed: changed PID1ticks/PIDnamespace, shared bootID and primary Ubuntu identity/interoperability preserved; same provider identities. Readiness8PASS at127.202seconds≤600, first warming failure retained separately. Real seeded Jenkins SUCCESSbuild1/archived artifact/job/configuration/private-key contents preserved before/after and again after99.956second25+7PASS. Isolate returned to its original stopped/disabled baseline with data retained and shared network released. Primary Ubuntu normal startup restored all original nodes: platformverify and8readiness passed on attempt3 at116.957seconds≤600; first two warming failures remain separate. Full25+7 passed in66.477seconds and original Jenkins fixture/configuration/volume/master-key/credentials/provider/Swarm identity comparisons passed. Final nine Windows HTTPS routes passed using the exact current public CA; no trust-store mutation. Bridge/80/443 and unrelated host listeners preserved. Selected primary WSL evidence is frozen under portable/wsl-primary/.

## Native Linux

Protected original custom operator input first failed sync because three non-secret reference names were absent. Canonically prepared input retained original credentials and passed setup/verify/25+7, before separate fresh reset; reset does not hide that diagnosis. Cleanbdd scoped destroy→observedemptyinventory→freshinstall→three newUUIDs passed with immediate formal25+7.

Final893 canonical14-operation chain LIVE_VERIFIED: all exits0, four8/8readiness suites and four25+7authenticated suites with zero failures/errors/skips. Genuine distinct imageupdate/recovery plus unchanged update repeatno_op passed. Additional exit73 fault classified rollout_failed and retained LIVE_FAILED_AFTER_MUTATION; canonical recovery converged and25+7passed. Worker convergence/repeat observed; both final-source credential cases LIVE_VERIFIED with complete restoration. Actual host reboot also LIVE_VERIFIED: changed boot ID, first platformverify6PASS, readiness8PASS within189.814seconds of conservative before-request anchor, postrestart25+7zero failures/errors/skips. All recorded identity/spec/config/credential/original-input/unrelated-container comparisons passed; native is healthy. First reboot did not seed/compare application content. Independent audit requires representative persistent application-data continuity under #299; a second actual reboot with a recorded Jenkins job/SUCCESS build#1/archived artifact fixture now passed. Actual content, job inventory/configuration and Jenkins home configuration/master key matched before/after and after final authentication. Initial warming readiness failed and remains separate; bounded unchanged retry passed8/8 at162.761047seconds≤600, then25+7zero failures/errors/skips. Native ends healthy with18continuous services and one completed bootstrap task. A missing reboot-cleared /tmp external helper caused an exit2 test invocation; unchanged helper restoration and successful subsequent qualification are separate evidence.

## Attribution / external checks

Source review: `documentation/evidence/issue-363-final-source-applicability-20261003.md`. Scenario map: `rc1_applicability.md`. No historical failed invocation is upgraded by a later successful retry. No new hosted CI, SonarQube or RC1 release acceptance is claimed.

## Portable evidence checks

Root verified all native checksum levels, all isolated WSL manifest entries, and primary WSL selected files against the frozen protected manifest. The native public ledger replaces seven operator-specific absolute paths with protected placeholders and records the original protected ledger checksum. Raw credentials, cookies, forms, environment inputs, database backup, private credential fingerprints and logs are excluded.

Original primary restore attestation field startup_readiness_seconds=186.04 was misnamed: helper source measures total observation/authentication/continuity elapsed. The portable aggregate correctly records actual readiness at116.957seconds. The ambiguous original stays protected and is referenced by checksum, not republished as readiness duration. Isolated UTC wall readings and monotonic operation durations differ slightly; both measurements are retained without assigning an unverified cause.

Documentation-only verification: git diff --check and JSON/checksum/traceability validation. No duplicate full Python gate for final evidence edits: runtime/test bytes remain unchanged from the independently reviewed893candidate.
