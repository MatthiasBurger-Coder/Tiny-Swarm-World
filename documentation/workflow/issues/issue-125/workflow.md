# Workflow: Issue #125 — Live Green-Path Evidence Contract

Workflow id: `issue-125-live-evidence-contract-20260812`

Issue: [#125](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/125)

Authoring branch: `docs/workflow-public-beta-roadmap-20260812`

Planned execution branch: `docs/issue-125-live-evidence-contract-20260812`

Execution branch: `docs/issue-125-live-evidence-contract-20260812`

Status: `IN_PROGRESS`

## Executive Summary

Define the canonical, redacted and reviewable evidence bundle for future live
validation without executing live commands now. The contract prepares the
Public-Beta Green-Path but is not itself a Green-Path pass.

## Requirement Clarification Gate

- Original request: execute #125 after #124 and after the final feature state.
- Interpreted intent: create the four evidence-contract documents, define
  phase/result/status/checksum/review semantics and prepare future manual runs.
- Change type: live-evidence governance documentation.
- Affected process strand: consent -> preflight -> apply -> readiness ->
  redaction/checksum -> independent review.
- Affected architecture area: live-operation surfaces, provider/deployment
  evidence, Service Access/Traefik and verification-state policy.
- Explicit requirements: create `live-greenpath-evidence-contract.md`,
  `live-run-template.md`, `redaction-rules.md`, `live-smoke-checklist.md`;
  include required evidence categories and non-pass states.
- Implicit requirements: no raw secrets/tokens/env/command dumps/private data;
  native Linux and WSL2 plus fresh/re-run/update scenarios can be represented;
  evidence is checksummed and independently reviewed.
- Assumptions: #121 and #124 provide evidence/traceability vocabulary; local
  evidence roots remain governed by current verification policy.
- Non-goals: live commands, fake evidence, committing local `.tiny-swarm*`
  evidence, claiming Green-Path success.
- Risks: overbroad evidence capture, secret leakage, ambiguous second-run
  semantics and treating resource-gated as pass.
- Open/blocking questions: exact Public-Beta issue identity and run host
  matrix remain blockers for the later gate, not for this contract.
- Confidence: 94%.
- Decision: `READY_FOR_WORKFLOW`.

## Target Picture

```text
explicit consent -> bounded phases -> redacted evidence + checksums
                                  -> readiness/result states -> review decision
```

## Verified Baseline, Scope and Assessments

`documentation/evidence/` is absent in the verified baseline. Existing live
operation docs/tests are inputs only. Python/frontend are not applicable unless
a safe evidence validator is separately approved. Resilience means retries,
partial apply, reset/update, blocked/refused/resource-gated/failed-to-verify
states and cleanup are documented without hiding failures.

## Ordered Slices

### Slice 01 — Matrix, phase model and redaction contract

```yaml
slice_id: S125-01
profile: EVIDENCE_DESIGN
owner: Live Evidence Validation Expert
secondary_reviewers: [Senior Requirement Engineer, ISMS-light Security Governance Expert, Traceability Engineer, Senior Tester]
affected_files: [.tiny-swarm/evidence/issue-125/requirement_matrix.md, documentation/process/verification-state-policy.md]
affected_modules: [live evidence governance]
affected_contracts: [phase result, redaction, checksum and review model]
dependencies: [S124-02]
parallel_group: SERIAL-125
file_locks: [.tiny-swarm/evidence/issue-125/requirement_matrix.md]
contract_locks: [live-evidence-status-contract, redaction-contract]
architecture_locks: [explicit-live-consent, no-live-default]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: review live-operation/runtime evidence references
  adr: review explicit live-consent ADR
stop_conditions: [raw sensitive output, ambiguous pass state, missing consent evidence, no cleanup/retry semantics]
```

Done: every required evidence category/status/redaction/review field is mapped.

### Slice 02 — Contract files, template and smoke checklist

```yaml
slice_id: S125-02
profile: EVIDENCE_DESIGN
owner: Live Evidence Validation Expert
secondary_reviewers: [ISMS-light Security Governance Expert, Senior Documentation Engineer, Acceptance Checks, Senior Tester]
affected_files: [documentation/evidence/live-greenpath-evidence-contract.md, documentation/evidence/live-run-template.md, documentation/evidence/redaction-rules.md, documentation/evidence/live-smoke-checklist.md]
affected_modules: [live evidence documentation]
affected_contracts: [manual live-run bundle, smoke/readiness checklist, redaction/checksum/review]
dependencies: [S125-01]
parallel_group: SERIAL-125
file_locks: [documentation/evidence/]
contract_locks: [live-run-template-contract, live-smoke-contract]
architecture_locks: [evidence-not-runtime-success]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: link only verified live-operation surfaces
  adr: no new ADR unless evidence ownership changes
stop_conditions: [fake result, secret/token/raw output inclusion, must not claim live success, missing checksum/review field]
```

Done: four files are reusable, redacted and connected to #121/#124; the future
Green-Path is still explicitly `PLANNED` until an authorized run supplies data.

## Dependency Graph

`S124-02 -> S125-01 -> S125-02`

## Parallel Execution

No implementation parallelism because phase/status/redaction schemas are shared.
Isolated worktree required. Live validation is not performed; any later live
run is serialized and needs explicit consent. Conflicts: evidence policy and
live-operation docs.

## Automatic Work Distribution Policy

Use standard distribution/consolidation evidence. Evidence, security,
traceability, documentation and test reviews may be separated after S125-01;
do not parallelize status/redaction/checksum semantics or any live run.

## Git Worktree Execution Rule

Use isolated worktree `docs/issue-125-live-evidence-contract-20260812`. No live
commands or local evidence capture are allowed during normal execution.

## Issue Completion Discipline

- Requirement matrix path: `.tiny-swarm/evidence/issue-125/requirement_matrix.md`.
- Required evidence path: `.tiny-swarm/evidence/issue-125/`.
- Required evidence files: matrix, implementation summary, changed files,
  test results, remaining risks and acceptance checklist.
- Requirement Lead review: S125-01 and final.
- System Architect Reviewer review: S125-01/S125-02 and final.
- Test / Evidence Reviewer review: S125-02 and final.
- Issue Completion Auditor review: required before `DONE`.
- DONE blocking rule: any missing evidence-contract requirement forces
  `INCOMPLETE`, `BLOCKED` or `FAILED`; contract existence is not live success.

## Quality, Documentation and Handoff

Run `git diff --check`; do not run live infrastructure. Handoff the canonical
bundle model to the separately refined Public-Beta gate, including the required
native Linux/WSL2 A/B/C matrix, service readiness, browser state, checksums and
redaction review. Commit only issue-scoped contract docs.

Definition of Done: the contract is complete, redaction-safe, status-honest,
reviewable and independent of any unexecuted live claim.

Arc42 Check Status: live-operation and verification-state references reviewed;
no runtime architecture change expected.

## Scope

Only the canonical live-evidence contract, reusable template, redaction rules,
smoke checklist and issue evidence are in scope.

## Target Outcome

An explicitly consented future live run can produce a reproducible, checksummed,
redacted and independently reviewable evidence bundle.

## Architecture Constraints

Evidence contracts do not mutate infrastructure or replace application/runtime
verification; live consent and verification-state policy remain authoritative.

## Python Automation Assessment

Not applicable unless a safe evidence-format validator is separately approved;
the contract itself is documentation.

## Frontend Assessment

No frontend implementation. Browser checks are a future evidence category only.

## Test Strategy

Verify phase/categories/statuses/redaction/checksum/review fields and run
`git diff --check`; do not execute live commands.

## Resilience Requirements

The contract must represent retry, partial apply, cleanup, reset/update,
resource-gated, blocked, refused and failed-to-verify outcomes explicitly.

## Role and Ownership Map

Live Evidence expert owns the contract; ISMS owns redaction; Traceability maps
requirements; Tester checks completeness; Acceptance Checks defines observable
criteria; Auditor reviews completion.

## Commit and Push Plan

One issue-scoped contract commit; no local runtime evidence or raw output is
committed and no live run is performed.

## Handoff to workflow execute

Promote after #124 evidence is stable; pass the contract to the separately
refined Public-Beta Green-Path issue, which remains blocked until identified.

## Arc42 Check Status

Live-operation and verification-state references were reviewed; no runtime
architecture change is expected.
