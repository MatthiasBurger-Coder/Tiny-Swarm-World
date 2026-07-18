# Workflow: SonarCloud remediation baseline and bounded S3415 pilot

Version: `workflow-sonarcloud-remediation-v2.0.0`
Workflow ID: `workflow-sonarcloud-remediation-20260718`
Branch: `fix/workflow-sonarcloud-remediation-20260718`
Baseline: `main@e91ca5824e823fbd2ae547c23080e8847ef55ccb`
Status: `READY_FOR_EXECUTION`

## Executive Summary

This workflow replaces the stale S3415-only mass-repair plan. It first records a reproducible SonarCloud baseline and then repairs at most 20 unambiguous `python:S3415` findings in a single pilot batch. It deliberately does not attempt a bulk repair of all open SonarCloud issues.

The verified baseline on 2026-07-18 reported 329 open issues: 214 `python:S3415`, 94 `python:S5778`, and 21 issues across eleven other rules. The exact URL filter provided by the requester returned 84 issues. Counts are remote observations, not a completion claim; Slice 01 must refresh them before any source edit.

## Requirement Clarification Gate

| Field | Decision |
|---|---|
| Original request | Create a safe workflow after the previous 1,580-S3415 workflow was found stale and too broad. |
| Interpreted intent | Establish a verifiable, incremental SonarCloud-remediation process rather than a blind mass change. |
| Change type | Quality-debt triage and test-maintenance pilot. |
| Affected process strand | Python test quality and workflow governance. |
| Affected architecture area | Tests only; production hexagonal boundaries are not in scope. |
| Explicit requirements | Small independently verified slices; no mass modification; quality gate per implementation slice. |
| Implicit requirements | Preserve assertion expressions/messages; do not weaken tests, suppress rules, alter the quality profile, or run live infrastructure. |
| Assumptions | SonarCloud public issue data remains available and the pilot contains at least one unambiguous S3415 finding. |
| Non-goals | Fixing all 329 issues; S5778 changes; product-code refactors; SonarCloud configuration changes; exclusions/suppressions. |
| Risks | Remote issue state can change; a location can be ambiguous; an assertion may use a custom helper with different semantics. |
| Open questions | None for the bounded baseline-and-pilot workflow. |
| Blocking questions | A missing/inconsistent remote baseline, no safely mappable pilot candidates, or an invalid local quality gate blocks execution. |
| Confidence level | 92% |
| Decision | `READY_FOR_WORKFLOW` |

## Target Picture

- A committed, reviewable snapshot identifies the actual SonarCloud issue set and its rule distribution at execution time.
- One pilot batch has no more than 20 `python:S3415` issues, each mapped to a concrete unittest assertion call before editing.
- Every accepted change preserves compared expressions and optional message, passes targeted tests and the full local quality gate, and receives remote SonarCloud confirmation after branch analysis.
- A follow-on workflow can use the evidence to plan the next bounded batch or a separate `python:S5778` remediation stream.

## Scope and Constraints

Allowed production behavior changes: none.

Allowed write scope during execution:

- `tests/**/*.py`, limited to files named in the Slice 01 baseline manifest and selected by the Slice 02 pilot manifest;
- `.tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**`;
- `.codex/evidence/slice-01-*` and `.codex/evidence/slice-02-*`;
- `documentation/workflow/**` only for execution results and status.

Forbidden areas: `src/**`, `infra/**`, CI and SonarCloud configuration, quality-profile settings, suppressions, test exclusions, live infrastructure, and unrelated test cleanup.

Architecture constraints: retain the existing hexagonal architecture; do not change production imports, runtime wiring, ports, adapters, or domain behavior. No ADR is required because the workflow only governs test-maintenance planning. Arc42 quality and technical-debt documentation were checked and need no update for the planned behavior.

## Python Automation and Frontend Assessment

- Python automation: required only for deterministic issue inventory and AST mapping; no source mutation may be performed by an unreviewed text replace.
- Frontend: not applicable. This repository has no verified browser frontend module in scope; no React or browser role is permitted.
- Runtime/DevOps: no live command, deployment, provider, Docker, or network operation is allowed. SonarCloud branch analysis is external CI evidence, not local runtime validation.

## Requirement Matrix and Evidence

Requirement matrix path: `.tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/requirement_matrix.md`

Required evidence files: `requirement_matrix.md`, `sonar_baseline.json`, `sonar_baseline.md`, `pilot_manifest.md`, `implementation_summary.md`, `changed_files.md`, `test_results.md`, `remaining_risks.md`, and `acceptance_checklist.md`.

Requirement Lead review: Senior Requirement Engineer. System Architect Reviewer review: Senior System Architect. Test / Evidence Reviewer review: Senior Tester. Issue Completion Auditor review is required before a slice or workflow is called `DONE`.

DONE blocking rule: any open or unverified requirement makes the result `INCOMPLETE`, `BLOCKED`, or `FAILED`; it must never be reported as `DONE`.

## Test Strategy

1. Slice 01 retrieves the current public SonarCloud issue inventory with the project key, records query parameters and response timestamp, and produces a rule/count baseline without credentials.
2. Slice 02 selects at most 20 open S3415 issues from that fixed baseline, maps every issue to an AST assertion call, and records before/after argument expressions and optional messages.
3. Run only the changed unittest modules first with `PYTHONPATH=src`, then `python3 tools/quality_gate.py quality` and `git diff --check` in WSL.
4. After branch analysis is uploaded, re-query the exact pilot issue keys. A local pass cannot claim a remote SonarCloud resolution.

## Ordered Slices

### Slice 01: Refresh baseline and create bounded pilot manifest

Purpose: replace stale counts with a reproducible inventory and choose only unambiguous candidates for the pilot.

```yaml
slice_id: "01"
profile: "FULL_PATH"
owner: "Senior Requirement Engineer"
secondary_reviewers:
  - "Senior System Architect"
  - "Senior Python Automation Developer"
  - "Senior Tester"
affected_files:
  - ".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**"
  - ".codex/evidence/slice-01-*"
  - "documentation/workflow/**"
affected_modules: []
affected_contracts:
  - "SonarCloud issue inventory query and issue-key baseline"
dependencies: []
parallel_group: "serial-01"
file_locks:
  - ".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**"
  - "documentation/workflow/**"
contract_locks:
  - "remote issue baseline"
architecture_locks:
  - "no production or infrastructure changes"
quality_gates:
  targeted:
    - "JSON schema/parse validation of saved baseline"
    - "git diff --check"
  required:
    - "git diff --check"
documentation:
  arc42: "checked; no update required"
  adr: "not required"
stop_conditions:
  - "SonarCloud query cannot be reproduced or returns an inconsistent project key"
  - "pilot candidate lacks a unique source location or assertion-call mapping"
  - "more than 20 pilot issues are selected"
```

Done criteria: the evidence package contains the complete returned issue inventory and rule/count summary, with secrets and host data excluded; `pilot_manifest.md` lists no more than 20 S3415 issue keys, source files, locations, expected/actual expressions, optional messages, and selection rationale; all non-S3415 findings and unselected S3415 findings are explicitly deferred, not ignored.

### Slice 02: Repair and verify the bounded S3415 pilot

Purpose: repair only the assertions named by the Slice 01 manifest, with expression-preservation review and full local verification.

```yaml
slice_id: "02"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "tests/**/*.py (only paths and lines named in pilot_manifest.md)"
  - ".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**"
  - ".codex/evidence/slice-02-*"
  - "documentation/workflow/**"
affected_modules: []
affected_contracts:
  - "unittest actual-before-expected assertion convention"
  - "preservation of assertion expressions and optional messages"
dependencies:
  - "01"
parallel_group: "serial-02"
file_locks:
  - "tests/**/*.py paths named in pilot_manifest.md"
  - ".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**"
  - "documentation/workflow/**"
contract_locks:
  - "pilot assertion expressions and messages"
architecture_locks:
  - "tests only; no production imports or runtime behavior"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest <each changed test module>"
    - "AST expression/message preservation comparison against pilot manifest"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
    - "git diff --check"
    - "SonarCloud branch analysis for every pilot issue key"
documentation:
  arc42: "checked; no update required"
  adr: "not required"
stop_conditions:
  - "a changed assertion is not a manifest-listed S3415 issue"
  - "an expected/actual expression or optional message would change"
  - "a custom assertion helper makes argument semantics uncertain"
  - "any required local quality gate fails"
  - "remote branch analysis is unavailable or does not confirm the pilot result"
```

Done criteria: only the two assertion arguments for manifest-listed calls change; targeted modules, full local quality, and diff checks pass; remote analysis confirms that each pilot issue key is resolved or reports a documented external blocker. A blocker prevents a `DONE` status.

## Dependency Graph

```text
Slice 01 (baseline + manifest)
  -> Slice 02 (<=20 S3415 pilot repairs + verification)
```

## Deferred Follow-on Work

No deferred work may be executed through this workflow. A successor workflow must use the committed baseline and pilot evidence to define its own bounded scope and branch.

- Remaining S3415 issues: batches of at most 20, each on a dedicated workflow branch and with a fresh issue-key manifest.
- S5778 issues: separate manual test-semantics workflows, at most 10 issues per batch, because exception-invocation refactoring can alter test behavior.
- Every other rule family: separate triage and design decision before a repair workflow; complexity or production-code changes require architecture review.

## Parallel Execution

- Can this workflow run in parallel? No.
- Conflicting workflows: any SonarCloud remediation workflow targeting the same test file or baseline branch.
- Shared files: workflow evidence and potentially several test modules.
- Shared infrastructure: remote SonarCloud analysis state.
- Requires isolated worktree: yes.
- Requires serialized live validation: remote branch analysis is serialized; no live infrastructure validation is allowed.
- Merge-order constraints: Slice 01 evidence must be committed before Slice 02; Slice 02 may not begin until the baseline manifest is accepted.

## Automatic Work Distribution Policy

During `workflow execute`, Codex must inspect each slice for safe specialist distribution and create `.codex/evidence/slice-<number>-distribution.md` before implementation plus `.codex/evidence/slice-<number>-consolidation.md` after it. Codex remains final integration owner.

Stream map: requirement/documentation review belongs to the Requirement Lead; architecture review to the System Architect; AST mapping and repair to the Python Automation Developer; test and quality evidence to the Senior Tester; remote analysis handling to the quality stream. Frontend, runtime, security, and backend streams are not applicable unless evidence contradicts the stated test-only scope.

Both slices are sequential. They share the baseline/manifest contract and potentially the same test files. Do not parallelize overlapping files, ambiguous assertion semantics, contradictory requirements, shared evidence, generated artifacts, unclear secrets handling, weakened safety guards, or a Three Amigos decision that marks the work unsafe. If real subagents are not available, record the explicit role-based fallback in both evidence files.

## Git Worktree Execution Rule

Execute only in an isolated worktree on `fix/workflow-sonarcloud-remediation-20260718`. No worker may write on `main` or merge directly to an integration branch. Any future parallel stream must use a distinct `<workflow-branch>-slice-<number>-<stream>` branch and worktree only after S3D verifies disjoint locks.

## Quality, Documentation, and Escalation

Quality commands are authoritative from `QUALITY.md`; run them through WSL. The full local quality gate is mandatory for Slice 02. Slice 01 is documentation/evidence-only and requires `git diff --check`; skipping full quality for it must be recorded as justified, not claimed as passed.

Arc42 check status: `documentation/arc42/10_quality_requirements.adoc` and `documentation/arc42/11_risks_and_debt.adoc` were checked. No behavior, architecture, or accepted-decision change is planned, so no arc42/ADR update is required.

Stop and escalate to the Root Architect if the baseline cannot be verified, the workflow branch/worktree is wrong or dirty, an issue maps ambiguously, a change would leave the test-only scope, a local gate fails, remote confirmation cannot be obtained, or a new architecture decision is needed.

## Definition of Done

- Slice 01 has a reproducible evidence package and approved <=20-issue pilot manifest.
- Slice 02 repairs only manifest-listed assertions and preserves expressions and messages.
- Required targeted checks, `python3 tools/quality_gate.py quality`, and `git diff --check` pass.
- SonarCloud branch analysis confirms every pilot issue key is resolved.
- Three Amigos and Issue Completion Auditor evidence are present. Any open or unverifiable requirement yields `INCOMPLETE`, `BLOCKED`, or `FAILED`.

## Handoff to workflow execute

Run `workflow execute` only after verifying this branch, the clean worktree, the context pack hashes, and the active workflow path. It authorizes execution of this bounded two-slice workflow only; it does not authorize deferred Sonar issues or a mass repair.
