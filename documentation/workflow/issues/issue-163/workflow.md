# Workflow: Issue #163 — Sonar S1313 Test-Fixture Remediation

Workflow ID: `issue-163-20260809`

Workflow version: `issue-163-v1.0.0`

Status: `READY_FOR_WORKFLOW`

Authoring branch: `feature/workflow-issue-chain-163-156-197-152-144-146-147-148-145-151-153-20260809`

Source: [GitHub Issue #163](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/163)

## Executive Summary

Remediate the three consolidated Sonar `python:S1313` findings in
`tests/domain/network/test_port_forwarding_plan.py` with one focused,
readable test-fixture change. The workflow is test-only: it must not change
runtime configuration, deployment behavior or host/network defaults.

## Target Picture

Named, safe test values replace raw hard-coded address literals where that
removes the findings without obscuring the test intent. The focused unittest
passes, the local quality gate is executed or its blocker is evidenced, and
external Sonar state is reported separately as `EXTERNAL_GATE_UNAVAILABLE`,
`EXTERNAL_GATE_FAILED` or `EXTERNAL_GATE_VERIFIED` only when observable.

## Requirement Clarification Record

- Original request: create the first workflow in the supplied chain.
- Interpreted intent: fully plan Issue #163 before the next issue #156 starts.
- Change type: quality/test-fixture remediation.
- Affected process strand: `workflow-create-to-workflow-execute`.
- Affected architecture area: test fixtures only; domain/runtime architecture
  is explicitly unchanged.
- Explicit and implicit requirements: see [requirement matrix](requirement-matrix.md).
- Assumptions: the current GitHub issue body and active Sonar EPIC are the
  authority; no remote Sonar success is assumed.
- Non-goals: runtime config, production code, live infrastructure, blanket
  suppressions, test exclusions and bulk replacements.
- Risks: changing a fixture can reduce readability or accidentally touch
  unrelated address literals.
- Open/blocking questions: none at authoring; any new Sonar key or runtime
  impact blocks execution.
- Confidence: 94%; decision `READY_FOR_WORKFLOW`.

## Verified Baseline

- Baseline commit: `b8c64eaa50839fcbf4581ca819286ad13ee88300`.
- The target test contains the three issue-referenced literals and nearby
  tests contain other fixture addresses that must not be changed incidentally.
- `documentation/epics/sonarcloud-remediation.md` is the matching EPIC and
  requires bounded rule-specific remediation with remote evidence for EPIC
  completion.

## Scope and Non-Goals

In scope: requirement matrix, finding inventory, named constants/fixture
design, the focused test edit, targeted/full local checks, external-state
classification and issue evidence.

Out of scope: all `src/`, `infra/`, live Sonar, Docker, Incus, networking,
browser and unrelated test changes.

## Python Automation and Frontend Assessment

- Python automation: `NO_PRODUCTION_CHANGE`; only Python unittest fixtures are
  writable.
- Frontend/browser: `NOT_APPLICABLE`; browser React review is forbidden.
- Console/status UI: `NOT_APPLICABLE`.

## Architecture, Resilience and Evidence Constraints

Preserve the Linux/WSL test baseline and avoid host-specific defaults. Do not
use a global suppression or change the production safety validators. The issue
evidence must distinguish local test/quality results from remote Sonar state;
missing remote access is not a pass.

## Ordered Slices

### Slice 01 — Freeze findings and requirement matrix

Purpose: capture the exact three findings, target lines, issue criteria, EPIC
trace and allowed test-only write scope.

Prerequisites: Issue #163 body, clean workflow branch and current baseline.

Allowed write scope: only `.tiny-swarm/evidence/issue-163/` and slice evidence.

```yaml
slice_id: I163-S01
profile: FULL_PATH
owner: Senior Requirement Engineer
secondary_reviewers: [Senior System Architect, Senior Python Automation Developer, Senior Tester]
affected_files: [tests/domain/network/test_port_forwarding_plan.py, documentation/epics/sonarcloud-remediation.md, .tiny-swarm/evidence/issue-163/requirement_matrix.md]
affected_modules: [test fixture quality, Sonar S1313]
affected_contracts: [test-only remediation scope, external Sonar state classification]
dependencies: []
parallel_group: SERIAL-BASELINE
file_locks: [.tiny-swarm/evidence/issue-163/**]
contract_locks: [I163-finding-inventory, I163-test-only-boundary]
architecture_locks: [no-runtime-change]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: reviewed; no architecture update expected
  adr: none
stop_conditions: [dirty branch, missing issue criteria, unmatched Sonar keys, runtime scope discovered]
```

Done criteria: every issue sentence and acceptance criterion is in the matrix;
all three keys and source locations are recorded; no production file is
assigned to an implementation slice.

Verification/evidence: `requirement-matrix.md`, finding inventory and changed
files allow-list under `.tiny-swarm/evidence/issue-163/`.

### Slice 02 — Design safe named test values

Purpose: choose the narrowest named constants or fixture helper that satisfies
Sonar while keeping the address-validation intent obvious.

Prerequisites: I163-S01. Allowed writes: target test and its unit test support
only; no blanket suppression without System Architect approval.

```yaml
slice_id: I163-S02
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Senior Tester]
affected_files: [tests/domain/network/test_port_forwarding_plan.py, tests/support/**]
affected_modules: [network port-forwarding tests]
affected_contracts: [readable safe fixture values]
dependencies: [I163-S01]
parallel_group: SERIAL-DESIGN
file_locks: [tests/domain/network/test_port_forwarding_plan.py, tests/support/**]
contract_locks: [I163-safe-fixture-contract]
architecture_locks: [test-only-no-host-default]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: no change
  adr: none
stop_conditions: [fixture meaning becomes unclear, suppression is broader than the three findings, non-test file needed]
```

Done criteria: the selected representation is explicit, local, reviewable and
does not alter the validation behavior being tested.

Verification/evidence: design note, source diff preview and mapping to
REQ-163-01 through REQ-163-04.

### Slice 03 — Apply the focused fixture change

Purpose: replace only the issue-scoped raw literals and keep all test behavior
and assertions intact.

Prerequisites: I163-S02. Allowed writes: the target test and directly required
test support file only.

```yaml
slice_id: I163-S03
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Tester, Senior System Architect]
affected_files: [tests/domain/network/test_port_forwarding_plan.py, tests/support/**]
affected_modules: [port forwarding domain tests]
affected_contracts: [Sonar S1313 remediation, unchanged validation semantics]
dependencies: [I163-S02]
parallel_group: SERIAL-IMPLEMENTATION
file_locks: [tests/domain/network/test_port_forwarding_plan.py, tests/support/**]
contract_locks: [I163-safe-fixture-contract]
architecture_locks: [no-src-or-infra-change]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.domain.network.test_port_forwarding_plan]
  required: []
documentation:
  arc42: no change
  adr: none
stop_conditions: [test intent changes, unrelated literal edits, production/config diff]
```

Done criteria: all three mapped findings are addressed by one focused change;
the target test passes; the diff remains test-only.

Verification/evidence: focused unittest output and `changed_files.md`.

### Slice 04 — Local quality and external-state verification

Purpose: run the focused test and full local gate, then classify the actual
remote Sonar result without conflating it with local success.

Prerequisites: I163-S03. Allowed writes: issue evidence only.

```yaml
slice_id: I163-S04
profile: FULL_PATH
owner: Senior Tester
secondary_reviewers: [Senior Requirement Engineer, Senior Python Automation Developer]
affected_files: [.tiny-swarm/evidence/issue-163/test_results.md, .tiny-swarm/evidence/issue-163/remaining_risks.md]
affected_modules: [local quality gate, Sonar external state]
affected_contracts: [QUALITY.md command contract, verification-state policy]
dependencies: [I163-S03]
parallel_group: SERIAL-QUALITY
file_locks: [.tiny-swarm/evidence/issue-163/**]
contract_locks: [I163-verification-state]
architecture_locks: [no-live-mutation]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.domain.network.test_port_forwarding_plan]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: quality section reviewed
  adr: none
stop_conditions: [focused test failure, quality failure without classification, unavailable external evidence presented as pass]
```

Done criteria: exact command results are recorded; local completion and remote
Sonar state are separate; no live infrastructure was started.

Verification/evidence: `test_results.md`, `remaining_risks.md` and external
state record under `.tiny-swarm/evidence/issue-163/`.

### Slice 05 — Evidence package and independent completion audit

Purpose: map every requirement to implementation/check evidence and obtain the
independent Issue Completion Auditor decision before #156 is released.

Prerequisites: I163-S04. Allowed writes: required issue evidence files only.

```yaml
slice_id: I163-S05
profile: FULL_PATH
owner: Issue Completion Auditor
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Senior Tester]
affected_files: [.tiny-swarm/evidence/issue-163/requirement_matrix.md, .tiny-swarm/evidence/issue-163/implementation_summary.md, .tiny-swarm/evidence/issue-163/changed_files.md, .tiny-swarm/evidence/issue-163/test_results.md, .tiny-swarm/evidence/issue-163/remaining_risks.md, .tiny-swarm/evidence/issue-163/acceptance_checklist.md]
affected_modules: [issue completion evidence]
affected_contracts: [issue completion discipline, three-amigos completion gate]
dependencies: [I163-S04]
parallel_group: SERIAL-AUDIT
file_locks: [.tiny-swarm/evidence/issue-163/**]
contract_locks: [I163-completion-decision]
architecture_locks: [auditor-independent-from-implementer]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: final reviewed/no-change status
  adr: none
stop_conditions: [open requirement, missing evidence file, incomplete role review, unverified external claim]
```

Done criteria: the auditor returns `PASS`, `INCOMPLETE` or `BLOCKED` with no
hidden requirements. Only `PASS` permits the chain to proceed to #156.

Verification/evidence: complete `.tiny-swarm/evidence/issue-163/` package and
`.codex/evidence/slice-05-consolidation.md`.

## Dependency Graph

```text
I163-S01 -> I163-S02 -> I163-S03 -> I163-S04 -> I163-S05
```

## Parallel Execution

- Can this workflow run in parallel? No; the five slices share one focused
  test contract and the user supplied a serial cross-issue chain.
- Conflicting workflows: any Sonar test-remediation workflow touching the same
  fixture or the active EPIC baseline.
- Shared files: target test, issue evidence, EPIC trace and quality state.
- Shared infrastructure: none; external Sonar state is read-only and optional.
- Requires isolated worktree: yes, for every slice.
- Requires serialized live validation: live validation is not applicable by
  default; any external check is serialized.
- Merge-order constraints: S01 through S05 in order; S05 precedes #156.

## Automatic Work Distribution Policy

`workflow execute` must analyze each slice for backend, frontend, tests,
runtime, documentation, quality, architecture and security stream work; use
real Codex subagents where supported and an explicit role-based fallback when
not. It must create `.codex/evidence/slice-<number>-distribution.md` before
implementation and `.codex/evidence/slice-<number>-consolidation.md` after an
implemented slice. Codex remains final integration owner.

Stream map: backend is test-fixture Python only; frontend is forbidden; tests
own unittest/quality evidence; runtime is not applicable; documentation owns
the EPIC/evidence wording; quality owns local/external state; architecture
owns test-only boundary; security owns S1313 interpretation and redaction.
Do not parallelize overlapping files, unclear requirements, contradictory
criteria, generated evidence, missing secrets classification or weakened
guards.

## Git Worktree Execution Rule

Every slice uses an isolated worktree and a branch derived from
`feature/workflow-issue-chain-163-156-197-152-144-146-147-148-145-151-153-20260809`.
Workers verify branch ownership and locks, write only the declared scope, and
never merge directly. Codex consolidates after evidence and tests.

## Issue Completion Discipline

- Requirement matrix path: `documentation/workflow/issues/issue-163/requirement-matrix.md` before implementation; `.tiny-swarm/evidence/issue-163/requirement_matrix.md` during execution.
- Required evidence path: `.tiny-swarm/evidence/issue-163/`.
- Required evidence files: `requirement_matrix.md`, `implementation_summary.md`, `changed_files.md`, `test_results.md`, `remaining_risks.md`, `acceptance_checklist.md`.
- Requirement Lead review: I163-S01 and I163-S05.
- System Architect Reviewer review: I163-S02/I163-S03 and I163-S05.
- Test / Evidence Reviewer review: I163-S04 and I163-S05.
- Issue Completion Auditor review: I163-S05, independent of implementation.
- DONE blocking rule: any open, guessed, conflicting or unverified requirement forces `INCOMPLETE`, `BLOCKED` or `FAILED`.

## Quality-Gate Expectations

Use only `QUALITY.md`: focused unittest, `python3 tools/quality_gate.py
quality` and `git diff --check`. No live or external success is inferred.

## Documentation Synchronization and Arc42 Check Status

The Sonar EPIC and arc42 quality sections were reviewed. No arc42 or ADR
update is expected because this workflow changes only test fixtures. If the
implementation discovers runtime drift, stop and route it to a successor
workflow.

## Stop Conditions and Uncertainty Escalation

Stop on an unclear Sonar key, runtime/config impact, unrelated test scope,
missing quality authority, missing evidence, external-state ambiguity or any
request to weaken the test/architecture guards. Route requirement ambiguity to
the Requirement Engineer, architecture ambiguity to the System Architect and
quality failure to the Senior Tester.

## Definition of Done

All matrix rows have implementation and verification evidence, all required
evidence files exist, the independent auditor decides `PASS`, the local gate
result is classified, and the branch is ready for the next indexed workflow.

## Handoff to workflow execute

Promote only `issue-163-20260809` explicitly, run S3/S3D preflight, execute
I163-S01 through I163-S05 in order, and do not begin #156 unless I163-S05 is
`PASS`.

