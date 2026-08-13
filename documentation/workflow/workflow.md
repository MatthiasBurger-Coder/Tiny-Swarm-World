# Workflow: Issue #122 — QMS-light Documentation

Workflow id: `issue-122-qms-light-20260812`

Issue: [#122](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/122)

Authoring branch: `docs/workflow-public-beta-roadmap-20260812`

Planned execution branch: `docs/issue-122-qms-light-20260812`

Execution branch: `docs/issue-122-qms-light-20260812`

Status: `COMPLETED`

## Executive Summary

Create a lightweight, evidence-driven quality management structure without
claiming ISO 9001 certification or weakening `QUALITY.md`. It consumes the
canonical audit evidence vocabulary from #121 and defines measurable quality
objectives, CAPA, change control and internal audits.

## Requirement Clarification Gate

- Original request: implement issue #122 after #121.
- Interpreted intent: create the five QMS files and connect quality decisions
  to branches, PRs, quality gates, reviews, evidence and baselines.
- Change type: documentation/governance.
- Affected process strand: quality objective -> change/CAPA -> audit -> evidence.
- Affected architecture area: process governance only; no runtime boundary.
- Explicit requirements: create `qms-light.md`, `quality-objectives.md`,
  `capa-process.md`, `change-control.md`, `internal-audit-process.md`; define
  measurable objectives, CAPA triggers/effectiveness, branch/PR/gate/review
  control and audit cadence.
- Implicit requirements: reference #121 registers; never turn skipped or
  missing evidence into a pass; preserve Linux/WSL and no-live-default rules.
- Assumptions: #121 exists or its paths are linked as planned during a safe
  sequential execution.
- Non-goals: certification, runtime changes, live commands and quality-gate
  weakening.
- Risks: objectives without evidence sources and CAPA closure without
  effectiveness review.
- Open/blocking questions: none for authoring; #121 completion is a runtime
  dependency for execution.
- Confidence: 94%.
- Decision: `READY_FOR_WORKFLOW`.

## Target Picture

```text
quality objectives -> change control -> quality gate/review evidence
        |                    |
        v                    v
     CAPA triggers -> effectiveness -> internal audit cadence
```

## Verified Baseline, Scope and Assessments

`documentation/qms/` is absent in the verified baseline. Scope is the five
issue-required documents plus direct navigation links. Python and frontend work
are not applicable. Resilience means CAPA preserves failed/blocked states and
requires objective effectiveness evidence before closure. Architecture remains
hexagonal and documentation remains subordinate to verified repository
behavior.

## Ordered Slices

### Slice 01 — Matrix and QMS control model

```yaml
slice_id: S122-01
profile: DOCS_GOVERNANCE
owner: Senior Requirement Engineer
secondary_reviewers: [QMS-light Governance Expert, Senior System Architect, Senior Tester]
affected_files: [.tiny-swarm/evidence/issue-122/requirement_matrix.md, documentation/workflow/issues/issue-122/workflow.md]
affected_modules: [QMS governance]
affected_contracts: [quality objective IDs, CAPA status and closure semantics]
dependencies: [S121-02]
parallel_group: SERIAL-122
file_locks: [.tiny-swarm/evidence/issue-122/requirement_matrix.md]
contract_locks: [qms-control-model]
architecture_locks: [quality-governance-authority]
quality_gates:
  targeted: [git diff --check]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: check quality requirements links
  adr: none expected
stop_conditions: [conflict with QUALITY.md, non-measurable objective, CAPA closure without evidence]
```

Done: each requirement maps to a QMS section, evidence source and review
owner; #121 dependency is explicit.

### Slice 02 — QMS documents and navigation

```yaml
slice_id: S122-02
profile: DOCS_GOVERNANCE
owner: QMS-light Governance Expert
secondary_reviewers: [Senior Documentation Engineer, Senior Tester, Audit Evidence Manager]
affected_files: [documentation/qms/qms-light.md, documentation/qms/quality-objectives.md, documentation/qms/capa-process.md, documentation/qms/change-control.md, documentation/qms/internal-audit-process.md, documentation/README.adoc]
affected_modules: [QMS documentation]
affected_contracts: [quality objectives, CAPA process, change-control and audit cadence]
dependencies: [S122-01]
parallel_group: SERIAL-122
file_locks: [documentation/qms/, documentation/README.adoc]
contract_locks: [qms-documentation-contract]
architecture_locks: [QUALITY.md-authority]
quality_gates:
  targeted: [git diff --check]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: update only verified quality-governance links
  adr: none expected
stop_conditions: [certification claim, quality gate weakening, undocumented owner, stale link]
```

Done: five files are internally consistent, measurable objectives have metric,
target, source, cadence and owner, CAPA has effectiveness/closure rules and
required evidence exists.

## Dependency Graph

`S121-02 -> S122-01 -> S122-02`

## Parallel Execution

No implementation parallelism: #121 paths and shared documentation navigation
are dependencies. Isolated worktree required; no live validation. Conflicts are
other QMS/quality-policy changes. Merge in slice order.

## Automatic Work Distribution Policy

`workflow execute` must perform the standard documentation, quality, architecture
and test distribution analysis, create per-slice distribution/consolidation
evidence and keep Codex as final integrator. Do not parallelize shared QMS,
QUALITY.md, audit links or contradictory quality rules.

## Git Worktree Execution Rule

Use an isolated worktree on `docs/issue-122-qms-light-20260812`; verify branch,
locks and predecessor evidence before writing.

## Issue Completion Discipline

- Requirement matrix path: `.tiny-swarm/evidence/issue-122/requirement_matrix.md`.
- Required evidence path: `.tiny-swarm/evidence/issue-122/`.
- Required evidence files: all six files required by the indexed workflow
  contract: matrix, implementation summary, changed files, test results,
  remaining risks and acceptance checklist.
- Requirement Lead review: S122-01 and final.
- System Architect Reviewer review: S122-01 and final.
- Test / Evidence Reviewer review: S122-02 and final.
- Issue Completion Auditor review: required before `DONE`.
- DONE blocking rule: open/unverified requirements force `INCOMPLETE`,
  `BLOCKED` or `FAILED`.

## Quality, Documentation and Handoff

Run `git diff --check` and the full WSL/Linux quality gate required by the
original issue. The gate is local evidence only; it is not live, browser or
external-service evidence.
Keep `QUALITY.md` authoritative, update only verified navigation and do not
claim certification. Commit only issue-scoped files; hand off after S3/S3D,
predecessor evidence and independent audit are ready.

Definition of Done: QMS documents, measurable objectives, CAPA effectiveness,
change-control and audit cadence are complete and independently evidenced.

Arc42 Check Status: quality requirements reviewed; no runtime architecture
change expected.

## Scope

Only the five QMS documents and directly required navigation/evidence are in
scope.

## Target Outcome

Quality objectives, CAPA, change control and internal audits have measurable,
evidence-backed governance without certification overclaim.

## Architecture Constraints

`QUALITY.md` remains authoritative; QMS documents cannot weaken gates or change
application/domain/infrastructure boundaries.

## Python Automation Assessment

Not applicable for documentation-only execution; executable quality changes
require a new scoped slice and Python review.

## Frontend Assessment

Not applicable; no browser or React module is in scope.

## Test Strategy

Check required files, objective fields, CAPA closure/effectiveness, links and
`git diff --check`.

## Resilience Requirements

Failed gates and audit findings remain CAPA triggers until effectiveness is
verified; skipped evidence cannot close an action.

## Role and Ownership Map

Requirement Engineer owns scope; QMS expert owns objectives/CAPA; Tester checks
evidence; Documentation Engineer checks links; Architect reviews authority;
Auditor decides completion.

## Commit and Push Plan

One issue-scoped documentation commit on the planned branch after predecessor
evidence and governance checks; no live or CI-setting mutation.

## Handoff to workflow execute

Promote only after #121 evidence is available, S3/S3D passes and the QMS matrix
is created in the isolated worktree.

## Arc42 Check Status

Quality-governance references were reviewed; update only verified behavior.
