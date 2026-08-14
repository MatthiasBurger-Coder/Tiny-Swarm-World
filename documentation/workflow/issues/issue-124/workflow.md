# Workflow: Issue #124 — Requirement-to-Test-to-Evidence Traceability

Workflow id: `issue-124-traceability-matrix-20260812`

Issue: [#124](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/124)

Authoring branch: `docs/workflow-public-beta-roadmap-20260812`

Planned execution branch: `docs/issue-124-traceability-matrix-20260812`

Status: `AUTHORED_INDEXED`

## Executive Summary

Create the repository-level traceability structure after the principal feature
work is stable. It maps requirements to architecture, implementation, tests,
quality gates and evidence, and explicitly marks missing evidence open. It must
not fabricate tests or live results.

## Requirement Clarification Gate

- Original request: execute #124 after #150 and before #125/#129.
- Interpreted intent: create the four required traceability documents and
  populate them from verified requirements and current repository artifacts.
- Change type: documentation/quality traceability.
- Affected process strand: requirement -> architecture -> implementation ->
  test -> quality gate -> evidence.
- Affected architecture area: arc42, ADRs, source/tests, quality policy and
  live evidence references; no runtime behavior.
- Explicit requirements: create `requirements.md`, `traceability-matrix.md`,
  `test-coverage-map.md`, `live-evidence-map.md`; uniquely identify required
  controls and mark missing evidence open.
- Implicit requirements: include Linux/WSL, Swarm-first, live consent,
  secrets/redaction, architecture, default gate, readiness and routing
  requirements; link #121 and #150 evidence.
- Assumptions: preceding issue outputs exist or are explicitly marked planned;
  tests and paths are inspected rather than inferred.
- Non-goals: runtime changes, fake tests/evidence, live commands and generated
  local evidence committed to Git.
- Risks: stale links after later docs changes and status drift.
- Open/blocking questions: no authoring blocker; all missing evidence remains
  open in the matrix.
- Confidence: 93%.
- Decision: `READY_FOR_WORKFLOW`.

## Target Picture

```text
requirement -> arc42/ADR -> source/config -> test -> QUALITY.md -> evidence
```

## Verified Baseline, Scope and Assessments

`documentation/traceability/` is absent in the verified baseline. Scope is four
documents and short navigation links. Python/frontend are not applicable unless
an executable matrix validator is separately justified. Resilience means
missing/blocked/unverifiable evidence remains visible and never becomes a
pass; links must be path-checked.

## Ordered Slices

### Slice 01 — Matrix requirements and source inventory

```yaml
slice_id: S124-01
profile: TRACEABILITY
owner: Senior Requirement Engineer
secondary_reviewers: [Traceability Engineer, Senior System Architect, Senior Tester]
affected_files: [.tiny-swarm/evidence/issue-124/requirement_matrix.md, documentation/workflow/issues/issue-124/workflow.md]
affected_modules: [traceability governance]
affected_contracts: [requirement IDs, source/evidence status vocabulary]
dependencies: [S150-03]
parallel_group: SERIAL-124
file_locks: [.tiny-swarm/evidence/issue-124/requirement_matrix.md]
contract_locks: [traceability-id-contract]
architecture_locks: [arc42-and-ADR-source-authority]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: inspect relevant sections and record paths
  adr: inspect relevant decisions and record paths
stop_conditions: [requirement cannot be sourced, path guessed, missing evidence marked passed]
```

Done: all issue and project requirements have stable IDs, sources and initial
implementation/test/evidence state.

### Slice 02 — Traceability documents and verification map

```yaml
slice_id: S124-02
profile: TRACEABILITY
owner: Traceability Engineer
secondary_reviewers: [Senior Documentation Engineer, Senior Tester, Live Evidence Validation Expert, Senior System Architect]
affected_files: [documentation/traceability/requirements.md, documentation/traceability/traceability-matrix.md, documentation/traceability/test-coverage-map.md, documentation/traceability/live-evidence-map.md]
affected_modules: [traceability documentation]
affected_contracts: [requirement-to-evidence matrix, test coverage map, live evidence map]
dependencies: [S124-01]
parallel_group: SERIAL-124
file_locks: [documentation/traceability/]
contract_locks: [traceability-matrix-contract]
architecture_locks: [verified-source-mapping]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: links must resolve or be marked planned/missing
  adr: links must be verified
stop_conditions: [fake coverage, ambiguous status, missing requirement, sensitive local evidence]
```

Done: every requirement maps to architecture, implementation, test/check and
evidence or is explicitly open; live gaps feed #125 and the Green-Path gate.

## Dependency Graph

`S150-03 -> S124-01 -> S124-02`

## Parallel Execution

No implementation parallelism: all maps share requirement IDs and statuses.
Isolated worktree required; no live validation. Read-only path inventory may
parallelize. Merge in order.

## Automatic Work Distribution Policy

Run standard distribution/consolidation evidence. Documentation, architecture,
testing and live-evidence reviews may be advisory in parallel after S124-01,
but ID/status ownership is serialized. No fake evidence or scope expansion.

## Git Worktree Execution Rule

Use isolated worktree `docs/issue-124-traceability-matrix-20260812`. Verify #121,
#150 and path sources before writing.

## Issue Completion Discipline

- Requirement matrix path: `.tiny-swarm/evidence/issue-124/requirement_matrix.md`.
- Required evidence path: `.tiny-swarm/evidence/issue-124/`.
- Required evidence files: matrix, implementation summary, changed files,
  test results, remaining risks and acceptance checklist.
- Requirement Lead review: S124-01 and final.
- System Architect Reviewer review: S124-01/S124-02 and final.
- Test / Evidence Reviewer review: S124-02 and final.
- Issue Completion Auditor review: required before `DONE`.
- DONE blocking rule: any open/unverified trace row forces `INCOMPLETE`,
  `BLOCKED` or `FAILED`; missing evidence may not be hidden.

## Quality, Documentation and Handoff

Run path/reference checks and `git diff --check`; run the full Python gate only
if tooling or implementation changes. Handoff to #125 provides the exact live
evidence gaps and required categories. Handoff to #129 provides canonical
navigation targets. Commit only issue-scoped docs/evidence.

Definition of Done: four traceability documents are populated from verified
sources, open gaps are explicit and the independent auditor returns `PASS`.

Arc42 Check Status: arc42/ADR source paths reviewed; no runtime change expected.

## Scope

Only the four traceability documents, verified source links and issue evidence
are in scope.

## Target Outcome

Every selected requirement has a visible architecture, implementation, test,
quality and evidence path or an explicit open status.

## Architecture Constraints

Use arc42/ADR and verified implementation as sources; never infer runtime
behavior from plans, labels or generated summaries.

## Python Automation Assessment

Not applicable by default. A validator would require separate approval, typed
implementation, tests and the normal quality gate.

## Frontend Assessment

Not applicable; traceability may reference conditional browser evidence but
does not create a frontend.

## Test Strategy

Path-check all references, review each matrix row and run `git diff --check`.
Missing evidence remains open and feeds #125.

## Resilience Requirements

Trace rows preserve blocked, missing, refused and failed-to-verify states so
later audit/release decisions cannot silently become green.

## Role and Ownership Map

Requirement Engineer owns IDs; Traceability Engineer owns matrices; Architect
owns design links; Tester owns test mapping; Live Evidence expert owns live
rows; Auditor decides completion.

## Commit and Push Plan

One issue-scoped documentation commit after #150 evidence is stable; no fake
test/evidence or local sensitive artifact is committed.

## Handoff to workflow execute

Promote after #150 completion evidence and isolated branch checks; pass the
open live rows and canonical IDs to #125.

## Arc42 Check Status

Arc42 and ADR source paths were reviewed; no runtime change is expected.
