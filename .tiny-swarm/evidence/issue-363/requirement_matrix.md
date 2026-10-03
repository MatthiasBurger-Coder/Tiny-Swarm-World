# ARCH-03.20 requirement matrix

Source: GitHub issue #363, parent #313; baseline `2a74134e`.
Status: INCOMPLETE pending full live evidence. Operator consent was given on
2026-10-03. WSL2 and native Linux preflight pass on the current candidate;
the WSL2 chain has a deployment failure, while the native chain and the
post-Jenkins-fix authenticated rerun pass. The final local quality gate passes
with 2,343 tests and 18 skips. The candidate is the
baseline plus the branch diff; native testing
uses an isolated archive snapshot with a local provenance commit.

| ID | Requirement | Type | Likely evidence | Verification | Status |
|---|---|---|---|---|---|
| R363-01 | Prove the architectural refactor preserves supported behavior across real lifecycle scenarios. | Goal | current source commit and scenario results | compare supported contracts with executed results | PARTIAL: native live chain and Jenkins correction verified; WSL2 chain fails in deploy |
| R363-02 | Validate install and bootstrap. | Live lifecycle | guarded installation run, phase summary | redacted exits and readiness | PARTIAL: native installer from empty managed state passed after LXD conflict was resolved; WSL2 deployment phase failed; factory-clean host unrun |
| R363-03 | Validate deploy and status. | Live lifecycle | deployment and status results | redacted state and service checks | PARTIAL: native setup, platform verify and post-deploy E2E passed; WSL2 apply failed |
| R363-04 | Validate reconcile and restart. | Live lifecycle | rerun and restart results | stable identity and health | PARTIAL: native reconcile and authenticated E2E passed; Jenkins task replaced, service 1/1 and post-restart auth passed; WSL2 unrun |
| R363-05 | Validate update where supported. | Live lifecycle | controlled update result | version and readiness observations | PARTIAL: native controlled Jenkins update and E2E passed; WSL2 unrun |
| R363-06 | Validate recovery and destroy/cleanup. | Live lifecycle | controlled failure/recovery and scoped cleanup results | final state and retained failure evidence | PARTIAL: native update recovery and E2E passed; confirmed destroy converged and removed managed nodes; WSL2 unrun |
| R363-07 | Relevant unit, integration, E2E and live tests pass. | Acceptance | test and live reports | exact commands, counts and non-success states | PARTIAL: 2,343 full local tests pass with 18 skips; native live chain and post-Jenkins-fix E2E pass; WSL2 chain fails in deploy |
| R363-08 | Classic Docker Swarm profile remains operational. | Acceptance | Classic readiness, browser and service checks | current-host live evidence | PARTIAL: native complete 14-operation chain `LIVE_VERIFIED`; WSL2 deployment remains failed |
| R363-09 | WSL2 supported flows remain operational. | Acceptance | WSL2 scenario bundle | host-classified current results | PARTIAL: preflight passes at original 20 GB WSL setting; setup fails in deployment apply |
| R363-10 | Native Linux supported flows remain operational. | Acceptance | native Linux scenario bundle | host-classified current results | PARTIAL: complete native chain, controlled restart, destroy and managed-state reinstall passed; corrected Jenkins image passed authenticated E2E; no factory-clean host |
| R363-11 | Secret bootstrap remains compatible. | Acceptance | credential bootstrap and authenticated checks | redacted test and live results | PARTIAL: native authenticated browser/API phases passed; WSL2 Infisical sync failed |
| R363-12 | CLI contracts remain compatible. | Acceptance | CLI regression results and live exits/output | comparison to documented contracts | PARTIAL: native setup, reconcile, update, recover and destroy CLI passed; WSL2 apply failed |
| R363-13 | Rerun any RC1/live evidence invalidated by the refactor. | Acceptance | evidence applicability and commit provenance audit | fresh run for each invalidated scenario | OPEN |
| R363-14 | Report failures truthfully without reclassifying them as success. | Acceptance | run summaries and state classification | review skipped, partial, failed and blocked outcomes | VERIFIED for observed preflight, deployment and browser blockers; original inaccurate artifact retained as defect evidence |
| R363-15 | Preserve WSL2 preflight at the operator's existing 20 GB configuration. | User clarification | host-specific resource profile and live preflight | 16 GiB WSL2 minimum, 20 GiB native minimum, real WSL2 preflight exit 0 | VERIFIED: WSL2 preflight passes without WSL restart or memory-cap change |

Live and external result states follow `documentation/process/verification-state-policy.md`. Prior runs on other commits are historical evidence; they do not automatically verify the current integrated candidate.
