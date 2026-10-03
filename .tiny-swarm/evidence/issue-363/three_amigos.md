# Three Amigos review

## Requirement Lead

Issue #363's goal, three target environments, nine lifecycle operations and
six acceptance criteria are represented by R363-01 through R363-15. No live
requirement is waived. Decision: requirement coverage recorded; acceptance open.

## System Architect Reviewer

This issue changes the Classic live runner's state classification, restores
the WSL2 preflight resource floor without lowering native Linux's floor, and
corrects Jenkins image initialization-file permissions after fresh-install
authentication failed.
Architecture gates passed on the final branch diff. Live validation must use
the supported Classic/Incus profile, preserve
the current candidate commit, and avoid reset or cleanup on an unowned target.
Decision: local architecture fit supported; live compatibility unverified.

## Test / Evidence Reviewer

The focused regression set and canonical quality gate passed (2,343 tests,
18 skipped). The native 14-operation chain passed after browser dependencies
were provisioned, as did controlled restart, post-restart authentication and
confirmed destroy. A corrected Jenkins image passed 9 browser and 7 API checks
after guarded update from the failed fresh-install state. The earlier skipped
browser run remains failed. Earlier live results
predate refactor commits. Decision: local evidence accepted; live and E2E
acceptance open. Independent issue-completion audit is required before DONE.

## Optional gate applicability

| Gate | Applicability | Protected behavior | Result |
|---|---|---|---|
| Installation and lifecycle | `APPLICABLE_LIVE` | Current Classic install, setup, reconcile, update, recovery, restart and cleanup on owned hosts | WSL2 deployment apply failed after preflight pass; native full chain, controlled restart, destroy, managed-state reinstall and corrected Jenkins image update passed |
| Authenticated browser E2E | `APPLICABLE_LIVE` | Current deployed routes, credentials and secret bootstrap | WSL2 not reached; native baseline, reconcile, update, recovery, post-restart and post-Jenkins-fix authenticated checks passed with zero skips |
| Deterministic unit/integration/contract | `APPLICABLE_LOCAL` | CLI, installer, lifecycle, evidence and architecture contracts | Focused Python 3.14 and 3.12 tests PASS; final full gate PASS, 2,343 tests with 18 skips |
| SonarQube external gate | `NOT_APPLICABLE` | No external publication or merge is being attempted | `EXTERNAL_GATE_NOT_APPLICABLE` for this local validation; no green claim |

General live consent was provided in the user reply “Ja mach das wie immer”.
The first live summary's after-mutation state was an observed runner defect;
its redacted artifact is retained. The corrected rerun proves the resource
gate occurred before mutation with a `resource_gated` nested result. The WSL2
preflight regression was then corrected and passed live at the original host
setting. WSL2 deployment and missing WSL2 browser evidence remain open. The
test/evidence perspective rejects issue DONE until those failures and the
unrun lifecycle steps are resolved.
