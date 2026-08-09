# Requirement Matrix — Issue #217

Status: `EXECUTION_REVIEWED`; candidate decisions are recorded, but final
quality verification and guarded issue actions remain pending.

Source of truth: GitHub Issue #217 and the current bodies/comments of Issues
#156, #163 and #197, reviewed against the `main` baseline.

| ID | Requirement | Type | Planned evidence | Verification | Status |
|---|---|---|---|---|---|
| REQ-217-001 | Review Issues #156, #163 and #197 against current `main`; do not close any issue from historical assumptions or commit-message matching alone. | Functional / evidence | `baseline.md`, three issue review records | Current `main` SHA, source paths, tests and evidence are recorded | VERIFIED_LOCAL |
| REQ-217-002 | Run a Three-Amigos requirements review for each issue: Requirement Lead re-reads body/criteria; Developer/System Architect traces current implementation, production paths, configuration, tests, evidence and docs; Test/Quality Lead verifies tests and quality evidence. | Governance / quality | `three-amigos.md`, issue review records | Role perspectives and decision record recorded | VERIFIED_LOCAL |
| REQ-217-003 | Assign exactly one decision per issue: `COMPLETED`, `SUPERSEDED`, `REDUCE_SCOPE`, `KEEP_OPEN` or `BLOCKED`. | Functional / acceptance | Per-issue decision table | Decision value is one of the allowed enum values | VERIFIED_LOCAL |
| REQ-217-004 | For every decision record current implementation evidence, current test/evidence coverage, remaining gaps, recommended issue action and closing reason when applicable. | Evidence / traceability | `issue-156-review.md`, `issue-163-review.md`, `issue-197-review.md` | Required fields are populated or explicitly `unverified`/`not applicable` | VERIFIED_LOCAL |
| REQ-217-005 | For #156 verify central published-port resolution, image-specific internal targets, effective-model URLs/health checks, safe effective-port evidence and representative service tests. | Functional / architecture | #156 review and test result evidence | Static inventory and named tests; residual central-resolution gaps are explicit | VERIFIED_LOCAL_WITH_RESIDUALS |
| REQ-217-006 | For #163 verify the three original IP-literal findings are absent or narrowly justified, test intent remains readable, the targeted test passes and Sonar status is resolved or explicitly `unverified`. | Quality / security hygiene | #163 review and external-gate state | Literal scan, targeted unittest, Sonar state classification | VERIFIED_LOCAL_WITH_UNVERIFIED_EXTERNAL |
| REQ-217-007 | For #197 verify Socat process management is outside `composition.py`, remains infrastructure-only, preserves explicit live consent/fail-closed behavior, and covers no-op, missing consent, unavailable tool, existing process, success and failure. | Architecture / safety / testability | #197 review and targeted test result | Static ownership scan and composition tests; residual gaps are explicit | VERIFIED_LOCAL_WITH_RESIDUALS |
| REQ-217-008 | Keep scope limited to review and backlog decisions; do not implement unrelated refactors or run live Docker, LXC, Incus, Swarm, networking or Selenium checks without explicit consent. | Scope / safety | Workflow scope and command/evidence log | Diff scope and command safety preserved | VERIFIED_LOCAL |
| REQ-217-009 | Apply the correct issue action only after evidence: close completed/superseded issues with the correct reason, rewrite reduced-scope issues to residual work, and remove stale evidence/criteria from issues that remain open. | External coordination / functional | `issue-actions.md`, final issue snapshots | Four guarded evidence actions applied once; post-states re-read; no candidate qualified for closure | VERIFIED_LOCAL |
| REQ-217-010 | Prevent duplicate work by preserving supersession/duplicate relationships, using one canonical decision record, and refusing to repeat or overwrite an issue action after the remote state has changed. | Resilience / idempotency | `deduplication-guard.md`, issue action log | Stable keys, conflict policy, single application and post-state reads recorded; #159/#160 preserved | VERIFIED_LOCAL |
| REQ-217-011 | Create the required issue-completion evidence package and block `DONE` when any requirement is open, unverified, or dependent on unavailable external evidence. | Quality / evidence governance | `.tiny-swarm/evidence/issue-217-obsolescence-review/` | Candidate package, final action records and auditor review are required | PENDING_AUDITOR_REVIEW |

## Traceability note

The active `documentation/epics/sonarcloud-remediation.md` EPIC is the
repository-local authority for SonarCloud inventory-derived work. It is
applicable to #163's `python:S1313` test-fixture hygiene concern, but the
current external Sonar state and baseline assignment remain `UNVERIFIED`; this
workflow does not claim that the EPIC batch or #163 is complete. #156 and #197
have no matching EPIC under `documentation/epics`, so their issue bodies remain
the current requirement source. This distinction is recorded for traceability,
not used to infer completion.
