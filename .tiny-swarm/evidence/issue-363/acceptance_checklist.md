# Acceptance checklist

- [x] Issue #363 goal, target environments, lifecycle phases and six acceptance
  criteria extracted into the requirement matrix.
- [x] Focused local regression tests passed (292 tests).
- [x] Final canonical local quality gate passed (2,343 tests; 18 skipped).
- [x] Operator consent recorded; WSL2 protected path and owned test target
  qualified.
- [x] WSL2 preflight passed with the original 20 GB host setting. Earlier
  resource-gated attempts remain recorded as non-success with a corrected,
  tested before-mutation classification.
- [x] Native Linux 14-operation Classic chain passed with authenticated
  browser/API checks; earlier browser skips remain recorded as non-success.
- [x] Native controlled Jenkins restart, post-restart authentication and
  confirmed managed-platform destroy passed.
- [x] Native guarded installer rebuilt the platform from empty managed state
  after an idle conflicting LXD daemon was stopped.
- [x] Fresh-install Jenkins authorization failure was reproduced, corrected
  in the image, and rechecked with 9 browser and 7 API checks on native Linux.
- [ ] Relevant current-host E2E and live tests pass with redacted evidence.
- [ ] Classic profile operational on current candidate.
- [ ] WSL2 install, bootstrap, deploy, status, reconcile, restart, supported
  update, recovery and scoped cleanup verified.
- [ ] Native factory-clean first install verified; managed-state reinstall
  is recorded separately.
- [ ] Secret bootstrap and CLI contracts verified in current live flows.
- [ ] All invalidated RC1/live scenarios rerun on current candidate.
- [x] Unexecuted and skipped checks are classified as non-success.
- [ ] Independent issue completion audit returns PASS.

Overall status: **INCOMPLETE**, not DONE. The issue's full live acceptance
remains open after current-candidate failures on both hosts.
