# Workflow: Issue #120 — Roadmap Reassessment and Closure

Workflow id: `issue-120-roadmap-reassessment-20260812`

Issue: [#120](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/120)

Authoring branch: `docs/workflow-public-beta-roadmap-20260812`

Planned execution branch: `docs/issue-120-roadmap-reassessment-20260812`

Status: `BLOCKED` (Public-Beta Green-Path is not live-verified)

## Executive Summary

Close the audit-remediation roadmap only after all selected child issues are
complete, the Public-Beta Green-Path has independently passed, findings are
reassessed on `main`, and no major finding remains untreated. This workflow is
the final governance gate; document presence, local quality or a single
successful installation cannot close #120.

## Requirement Clarification Gate

- Original request: execute #120 last after #121, #122, #123, #128, #126,
  #150, #124, #125, #129 and the Public-Beta Green-Path.
- Interpreted intent: reconcile child issue/audit evidence, review the complete
  fresh-install/reconcile/update evidence, run a new full maturity/audit pass
  on `main`, and close only if acceptance criteria are met.
- Change type: final audit/release-governance decision with authorized live
  evidence intake, not a product refactor.
- Affected process strand: child completion -> live evidence -> re-audit ->
  roadmap disposition.
- Affected architecture area: whole repository governance, deployment/runtime
  evidence and arc42/quality/security documentation; no unplanned feature.
- Explicit requirements: all major findings closed or risk-accepted; minor
  findings owned/planned; reproducible live evidence; QMS/ISMS and
  traceability linked; security/dependency risks governed; follow-up audit
  reasonably supports target maturity.
- Implicit requirements: #127's closed result is verified; #150 is secured and
  evidenced; Green-Path covers native Linux and WSL2, fresh/re-run/update; all
  results are redacted and state-classified; auditor is independent.
- Assumptions: the Green-Path will be refined into a concrete issue/workflow
  before this workflow is executed; explicit live consent and prerequisites
  will exist; `main` is the reassessment baseline.
- Non-goals: closing from plans alone, changing findings to pass without
  evidence, bypassing QMS/ISMS/quality/security gates or running live commands
  without explicit authorization.
- Risks: incomplete child issue evidence, non-reproducible live state,
  environmental drift, false green status and audit ownership conflict.
- Open/blocking questions: Green-Path issue identity, host/prerequisite matrix,
  exact evidence bundle and operator consent are unresolved.
- Confidence: 76% for authoring; execution decision is `REQUIRES_REFINEMENT`
  until the Green-Path gate is specified.
- Decision: `PROCEED_WITH_ACCEPTED_ASSUMPTIONS` for this indexed plan;
  `REQUIRES_REFINEMENT` for execution.

## Target Picture

```text
child issue evidence -> Green-Path A/B/C on Linux + WSL2
          -> redaction/review -> fresh audit on main
          -> major finding disposition -> #120 PASS/INCOMPLETE/BLOCKED
```

## Verified Baseline, Scope and Assessments

The roadmap issue defines ten work packages; #127 is already closed and the
remaining requested child workflows are indexed here. The Public-Beta gate has
no concrete issue artifact and no live evidence in this baseline. Scope is
final evidence reconciliation, re-audit and disposition. Python/frontend are
not the default scope; any live run uses existing guarded application paths and
must not be improvised. Resilience requires rollback/recovery and explicit
failure states for all three run scenarios.

## Ordered Slices

### Slice 01 — Child issue evidence and requirement reconciliation

```yaml
slice_id: S120-01
profile: FULL_PATH
owner: Issue Completion Auditor
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Senior Tester, Audit Evidence Manager]
affected_files: [.tiny-swarm/evidence/issue-120/requirement_matrix.md, documentation/audit/findings-register.md, documentation/audit/evidence-matrix.md, documentation/audit/remediation-plan.md]
affected_modules: [roadmap audit evidence]
affected_contracts: [child completion matrix, finding disposition, evidence status]
dependencies: [S129-02]
parallel_group: SERIAL-120
file_locks: [.tiny-swarm/evidence/issue-120/requirement_matrix.md, documentation/audit/]
contract_locks: [roadmap-closure-contract, finding-disposition-contract]
architecture_locks: [independent-completion-audit]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: verify final references only
  adr: review all decision references touched by findings
stop_conditions: [missing child evidence, open requirement claimed done, major finding silently downgraded, #127 inconsistency]
```

Done: every child issue has an auditor decision and every finding has current
status, owner, treatment and evidence link.

### Slice 02 — Public-Beta Green-Path evidence intake and independent review

```yaml
slice_id: S120-02
profile: FULL_PATH_WITH_APPROVED_LIVE_GATE
owner: Live Evidence Validation Expert
secondary_reviewers: [Acceptance Checks, Senior DevOps, ISMS-light Security Governance Expert, Senior Tester, Issue Completion Auditor]
affected_files: [documentation/evidence/live-greenpath-evidence-contract.md, .tiny-swarm/evidence/issue-120/acceptance_checklist.md, .tiny-swarm/evidence/issue-120/test_results.md, .tiny-swarm/evidence/issue-120/remaining_risks.md]
affected_modules: [Public-Beta acceptance, live evidence review]
affected_contracts: [native Linux/WSL2 A-B-C run matrix, redacted live bundle, readiness review]
dependencies: [S120-01]
parallel_group: SERIAL-LIVE-GATE
file_locks: [.tiny-swarm/evidence/issue-120/]
contract_locks: [public-beta-greenpath-contract]
architecture_locks: [explicit-live-consent, no-live-default]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: update only with observed evidence and verified runtime statements
  adr: review provider/Traefik/consent decisions
stop_conditions: [missing issue identity, missing explicit consent, missing host scenario, raw secret, failed/blocked state presented as pass, no second successful run]
```

Done: the separately approved Green-Path produces complete redacted evidence
for native Linux and WSL2, fresh/re-run/update, readiness/browser checks and a
second successful run; otherwise the issue remains blocked.

### Slice 03 — Fresh maturity audit on main and roadmap disposition

```yaml
slice_id: S120-03
profile: AUDIT_CLOSURE
owner: Senior System Architect
secondary_reviewers: [Audit Evidence Manager, Senior Requirement Engineer, Senior Tester, QMS-light Governance Expert, ISMS-light Security Governance Expert]
affected_files: [documentation/audit/audit-register.md, documentation/audit/findings-register.md, documentation/audit/remediation-plan.md, .tiny-swarm/evidence/issue-120/implementation_summary.md, .tiny-swarm/evidence/issue-120/changed_files.md]
affected_modules: [final roadmap audit]
affected_contracts: [maturity reassessment, major/minor finding closure, release baseline]
dependencies: [S120-02]
parallel_group: SERIAL-120-FINAL
file_locks: [documentation/audit/, .tiny-swarm/evidence/issue-120/]
contract_locks: [audit-reassessment-contract, roadmap-status-contract]
architecture_locks: [main-baseline-reassessment]
quality_gates:
  targeted: [git diff --check]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: required when verified maturity/runtime/deployment statements change
  adr: record reviewed decisions and unresolved risks
stop_conditions: [child issue open, major finding untreated, Green-Path missing, failed quality gate, independent auditor not PASS]
```

Done: a fresh audit on `main` is recorded; #120 is `DONE` only if all criteria
are evidenced and the independent auditor returns `PASS`. Otherwise report
`INCOMPLETE` or `BLOCKED` with exact open requirements.

## Dependency Graph

`S129-02 -> S120-01 -> PUBLIC-BETA-GREENPATH -> S120-02 -> S120-03`

`PUBLIC-BETA-GREENPATH` is an external named gate, not an executable slice in
this authoring branch. It must be refined into a concrete issue/workflow before
S120-02 can start.

## Parallel Execution

No implementation parallelism. Child evidence, live validation and audit
disposition are strictly serialized. Isolated worktree required for audit
documentation; live validation requires an approved isolated/serialized
environment. Conflicts: any roadmap, finding register, release baseline or
live-evidence workflow.

## Automatic Work Distribution Policy

Use standard distribution/consolidation evidence for S120-01/S120-03. The live
gate must use explicit live-evidence distribution and reviewer evidence. No
subagent may declare #120 complete; Codex integrates, and the independent
Issue Completion Auditor makes the final decision.

## Git Worktree Execution Rule

Use isolated worktree `docs/issue-120-roadmap-reassessment-20260812`. The
re-audit baseline must be a verified `main` commit; no completion decision may
be made from a stale child branch or unreviewed local state.

## Issue Completion Discipline

- Requirement matrix path: `.tiny-swarm/evidence/issue-120/requirement_matrix.md`.
- Required evidence path: `.tiny-swarm/evidence/issue-120/`.
- Required evidence files: matrix, implementation summary, changed files,
  test results, remaining risks and acceptance checklist.
- Requirement Lead review: S120-01 and S120-03.
- System Architect Reviewer review: all slices and final.
- Test / Evidence Reviewer review: S120-02/S120-03 and final.
- Issue Completion Auditor review: mandatory final authority and must be
  independent of implementation.
- DONE blocking rule: any open or unverified child, finding, live scenario,
  quality gate or evidence requirement forces `INCOMPLETE`, `BLOCKED` or
  `FAILED`; no roadmap closure by inference.

## Quality, Documentation and Handoff

Use the canonical verification-state policy. Run `git diff --check` and the full
local quality gate where required; live/browser/external checks require consent,
prerequisites and evidence. Handoff to release/baseline governance occurs only
after the audit decision. Commit/push/merge actions remain guarded and issue
scoped; no PR merge is implied by this plan.

Definition of Done: child issues, Green-Path, finding dispositions, fresh audit,
quality evidence and independent completion audit all pass. Otherwise the final
status is explicitly not `DONE`.

Arc42 Check Status: relevant architecture, runtime, deployment, quality and
risk sections must be rechecked on `main` during S120-03; planned statements
must not be promoted to implemented behavior.

## Scope

Only final child-evidence reconciliation, explicitly authorized Green-Path
evidence intake, fresh audit/reassessment and roadmap disposition are in scope.

## Target Outcome

#120 is `DONE` only when every requirement, finding and Public-Beta scenario is
verified, evidenced and independently audited; otherwise a non-DONE status is
reported with exact blockers.

## Architecture Constraints

Do not bypass provider, consent, evidence, redaction, quality or hexagonal
architecture rules during the final acceptance run.

## Python Automation Assessment

No new Python implementation is planned. Existing guarded automation may be
used only by a separately approved live workflow; local quality remains the
default code authority.

## Frontend Assessment

No frontend implementation. Browser/readiness checks are conditional evidence
within the Green-Path and cannot be inferred from static route files.

## Test Strategy

Audit every child matrix and evidence package, review native Linux/WSL2 A/B/C
live results, run the required local quality gate and perform an independent
fresh audit on `main`.

## Resilience Requirements

Fresh install, reconcile/re-run and update must all be exercised where approved;
partial failure, recovery, rollback, drift and failed verification remain
explicit non-pass states.

## Role and Ownership Map

Requirement Lead reconciles scope; Live Evidence expert reviews runs; QMS/ISMS
experts review quality/security findings; Architect owns final architecture
assessment; Tester reviews checks; Issue Completion Auditor decides #120.

## Commit and Push Plan

Only an issue-scoped evidence/reassessment commit may be prepared after the
Green-Path and fresh audit. No roadmap closure, PR merge or release claim is
allowed while a blocker remains.

## Handoff to workflow execute

Do not promote for execution until the Public-Beta gate has a concrete issue,
explicit consent, host/scenario matrix, evidence root, rollback plan and
independent reviewer. Then execute S120-01 through S120-03 serially.

## Arc42 Check Status

Architecture, runtime, deployment, quality and risk sections must be rechecked
on `main` during the final reassessment; planned statements stay planned.
