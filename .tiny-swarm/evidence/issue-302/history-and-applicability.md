# History and candidate applicability

The authoritative qualification candidate is `69f040a75fa8a7bc9b9c01bf5eb62f53abeb6a6e`; product behavior is
`c921e69533450fba86d908e2990c106bef87769a`. Exact compared inputs are in candidate-provenance.json.

| History | Recorded closure / earlier scope | Current disposition |
|---|---|---|
| #252 | closed/completed 2026-08-29; previous acceptance lacked current results | Preserve history; all body/CI requirements are re-audited here; #294 is successor |
| #271 / #272 / #273 / #274 / #275 | closed/not_planned 2026-08-29 | WSL #299, native #298, update #297, Sonar #300, hosted #301 provide actual replacement evidence |
| #285 and merged PR #293 | closed 2026-09-09; partial historical credential matrix | Retain old runs; #295/#296 and current both-host c921 chains close the remaining acceptance scope |
| #277 | full 25-row requirement/independent audit remains committed; current REST returns HTTP 410 (deleted) | Audit original snapshot and unchanged requirement matrix; document deletion instead of attempting a misleading GitHub update |
| #295 | baseline/restart authentication at d254b769 | Actual current c921 fresh/reconcile/update/recovery/restart suites supersede affected authentication scope |
| #296 | four source-precedence transitions at 81443e80; independently approved | Reuse only unchanged resolver/consumer behavior with explicit related-change review; restore missing issue entrypoints |
| #310 / PR #332 | actual Poincare/Faraday independent maintenance review | Retain that review; #329/#331 are owned nonblocking extraction work, not waived functional defects |

The 1,913-test old baseline included 19 skips; it never meant 1,913 live or
executed successes. Current local results report discovered tests and skips
separately. Four authenticated phases per fresh host chain each contain 25 live
tests (8 readiness before + 9 browser routes + 8 readiness after) and 7 API checks.

Affected update behavior was repaired in PRs #333/#334/#335: preserve the original
recovery plan, use observed runtime source/convergence, isolate selected-stack
image update and retry only typed observation races. Both-host full chains and
fault/repeat/no-op tests were rerun. Scoped native bedb0c9f proofs differ only in
documentation/evidence from c921; their actual SHAs remain in R01 provenance.
8eb5db33 hosted execution has identical whole-tree content to c921.

The first WSL restart genuinely failed due to a missing container overlay endpoint.
Its explicit targeted repair and subsequent authentication remain recorded. The
separate approved planned restart quiesced node Docker before terminating only
the owned distribution; that complete cycle passed without post-start repair.
This qualifies the documented planned boundary, not hard power loss or global
WSL shutdown. Native whole-VM reboot passed without post-start repair.

Native DNS collision and the initial fresh WSL bridge/PATH configuration failure
occurred before the qualifying empty-target retries. Operator prerequisites were
corrected, documented and the complete fresh paths rerun. Failed evidence was
retained. The final source scan covers dependency/configuration checks; it does
not certify built-image packages vulnerability-free. R08 records explicit risk
owners and bounded access assertions. No known functional acceptance blocker is
silently converted to maintenance debt.

## Current credential-parent row cross-check

Some historical parent entries cite an untracked/missing issue-279 package.
That absence is not used as implementation evidence. The current catalog,
resolver, installer, documentation and actual #295/#296/c921 results below
directly establish each requirement. Original dated independent reviews remain
historical, and the missing CRED-09 entrypoints have been restored.

| Parent ID | Current verification route |
|---|---|
| E02-01 | domain/configuration/internal_test_credentials.py; tests/domain/configuration/test_internal_test_credentials.py; current both-host full authentication; source alias review preserves exact values |
| E02-02 | domain/configuration/internal_test_credentials.py; tests/domain/configuration/test_internal_test_credentials.py; current both-host full authentication; source alias review preserves exact values |
| E02-03 | domain/configuration/internal_test_credentials.py; tests/domain/configuration/test_internal_test_credentials.py; current both-host full authentication; source alias review preserves exact values |
| E02-04 | domain/configuration/internal_test_credentials.py; tests/domain/configuration/test_internal_test_credentials.py; current both-host full authentication; source alias review preserves exact values |
| E02-05 | domain/configuration/internal_test_credentials.py; tests/domain/configuration/test_internal_test_credentials.py; current both-host full authentication; source alias review preserves exact values |
| E02-06 | issue-280/282 implementation and deleted-path inventory; tests.test_simple_installer; canonical credential resolver; R03 prerequisite fixtures and current both-host fresh/reconcile |
| E02-07 | issue-280/282 implementation and deleted-path inventory; tests.test_simple_installer; canonical credential resolver; R03 prerequisite fixtures and current both-host fresh/reconcile |
| E02-08 | issue-280/282 implementation and deleted-path inventory; tests.test_simple_installer; canonical credential resolver; R03 prerequisite fixtures and current both-host fresh/reconcile |
| E02-09 | issue-280/282 implementation and deleted-path inventory; tests.test_simple_installer; canonical credential resolver; R03 prerequisite fixtures and current both-host fresh/reconcile |
| E02-10 | issue-280/282 implementation and deleted-path inventory; tests.test_simple_installer; canonical credential resolver; R03 prerequisite fixtures and current both-host fresh/reconcile |
| E02-11 | unchanged source/consumer files in credential-applicability.json; actual four CRED-09 transitions; current native/WSL full lifecycle and restart authentication |
| E02-12 | unchanged source/consumer files in credential-applicability.json; actual four CRED-09 transitions; current native/WSL full lifecycle and restart authentication |
| E02-13 | unchanged source/consumer files in credential-applicability.json; actual four CRED-09 transitions; current native/WSL full lifecycle and restart authentication |
| E02-14 | unchanged source/consumer files in credential-applicability.json; actual four CRED-09 transitions; current native/WSL full lifecycle and restart authentication |
| E02-15 | issue-282/284 current implementation/audits; documented credential-source-precedence contract; console/installer regressions in full2066-test gate; R07 manual review |
| E02-16 | issue-282/284 current implementation/audits; documented credential-source-precedence contract; console/installer regressions in full2066-test gate; R07 manual review |
| E02-17 | issue-282/284 current implementation/audits; documented credential-source-precedence contract; console/installer regressions in full2066-test gate; R07 manual review |
| E02-18 | issue-282/284 current implementation/audits; documented credential-source-precedence contract; console/installer regressions in full2066-test gate; R07 manual review |
| E02-19 | current full local gate; #295 authentication and current c921 suites; #296 four transition reports and source-applicability review |
| E02-20 | current full local gate; #295 authentication and current c921 suites; #296 four transition reports and source-applicability review |
| E02-21 | current full local gate; #295 authentication and current c921 suites; #296 four transition reports and source-applicability review |
| E02-22 | all preceding current rows; actual parent 25-row independent historical audit; R06 full requirement/architecture/QA fallback and preserved limitations |
| E02-23 | all preceding current rows; actual parent 25-row independent historical audit; R06 full requirement/architecture/QA fallback and preserved limitations |
| E02-24 | all preceding current rows; actual parent 25-row independent historical audit; R06 full requirement/architecture/QA fallback and preserved limitations |
| E02-25 | all preceding current rows; actual parent 25-row independent historical audit; R06 full requirement/architecture/QA fallback and preserved limitations |

## R09 review applicability

The independently reviewed preflight service, filesystem authorizer and their
two 57-test suite files are unchanged between reviewed320f11f8 and c921 (direct
Git comparison). Current full quality includes those suites. New update runtime
observation is separately covered by R01 and is not claimed to have been reviewed
by the earlier R09 reviewer.
