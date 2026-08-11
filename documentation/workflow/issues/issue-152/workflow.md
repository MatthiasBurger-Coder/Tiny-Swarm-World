# Workflow: Issue #152 — Shared Performance Evidence Contract

Workflow ID: `issue-152-20260809`

Workflow version: `issue-152-v1.0.0`

Status: `READY_FOR_WORKFLOW`

Authoring branch: `feature/workflow-issue-chain-163-156-197-152-144-146-147-148-145-151-153-20260809`

Source: [GitHub Issue #152](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/152)

## Executive Summary

Create a small, human-readable and Git-friendly performance evidence contract
that Issues #144–#148 can reuse for timings, retries, call counts, subprocess
counts, file reads and phase durations. This workflow creates the contract and
helper/template only; it does not implement the optimizations.

## Target Picture

Every performance slice records a stable issue/workflow identifier, segment,
environment summary, duration/timestamps, optional counters, baseline/new
values and measurement limitations under one documented schema. Serialization
is deterministic, optional values are explicit, and local timing is never
treated as globally absolute.

## Requirement Clarification Record

- Upstream dependency: `I197-S06` must be `PASS`.
- Requirement matrix: [matrix](requirement-matrix.md).
- Change type: governance/observability support with a small typed helper.
- Architecture area: new evidence value object/helper location selected from
  verified domain/application boundaries in S152-S02.
- Non-goals: heavyweight benchmarking, external services and #144–#148
  optimization code.
- Risks: schema drift, sensitive environment data, unstable timestamps and
  accidental coupling to live infrastructure.
- Confidence: 91%; decision `READY_FOR_WORKFLOW`.

## Verified Baseline

The repository has typed sanitized evidence and local evidence repositories but
no verified shared performance measurement module. Existing evidence paths can
host issue-local artifacts; the implementation slice must choose the smallest
compatible value object/helper and add no external dependency.

## Scope and Assessments

In scope: schema, helper/template, serialization, docs, unit tests and issue
evidence. Python automation is `FULL_PATH`; frontend is `NOT_APPLICABLE`; live
and external checks are `NOT_APPLICABLE` for the contract itself.

## Ordered Slices

### Slice 01 — Freeze shared contract and matrix

Purpose: normalize all #144–#148 measurement needs and define stable fields,
identifiers, limitations and allowed evidence roots.

```yaml
slice_id: I152-S01
profile: FULL_PATH
owner: Senior Requirement Engineer
secondary_reviewers: [Senior System Architect, Senior Python Automation Developer, Senior Tester]
affected_files: [documentation/workflow/issues/issue-152/requirement-matrix.md, documentation/process/issue-completion-discipline.md]
affected_modules: [performance evidence governance]
affected_contracts: [shared measurement schema, evidence identity, limitations]
dependencies: [I197-S06]
parallel_group: SERIAL-BASELINE
file_locks: [.tiny-swarm/evidence/issue-152/**]
contract_locks: [I152-schema-v1]
architecture_locks: [no-optimization-in-contract-issue]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: review quality/evidence sections
  adr: none
stop_conditions: [missing measurement field, sensitive environment requirement, optimization scope leakage]
```

Done criteria: all five related issues can name the schema fields they need;
limitations and external-service prohibition are explicit.

### Slice 02 — Implement the typed measurement value object

Purpose: choose a verified package boundary and implement immutable, typed
measurement data with validation for IDs, duration/counters and redaction.

```yaml
slice_id: I152-S02
profile: FULL_PATH
owner: Senior System Architect
secondary_reviewers: [Senior Python Automation Developer, Senior Requirement Engineer, Senior Tester]
affected_files: [src/tiny_swarm_world/domain/performance/**, src/tiny_swarm_world/domain/sanitized_evidence.py, tests/domain/performance/**]
affected_modules: [performance value object, sanitized evidence]
affected_contracts: [I152-schema-v1, safe environment summary, optional fields]
dependencies: [I152-S01]
parallel_group: SERIAL-CONTRACT
file_locks: [src/tiny_swarm_world/domain/performance/**, src/tiny_swarm_world/domain/sanitized_evidence.py, tests/domain/performance/**]
contract_locks: [I152-measurement-value]
architecture_locks: [domain-free-of-filesystem-and-clock-side-effects]
quality_gates:
  targeted: [python3 tools/quality_gate.py test]
  required: []
documentation:
  arc42: no change unless a new crosscutting concept is verified
  adr: none
stop_conditions: [domain imports infrastructure, raw host/secret data allowed, fields cannot serialize deterministically]
```

Done criteria: the value object supports single/multi-node context, optional
values and safe deterministic serialization.

### Slice 03 — Add helper/adapter or Git-friendly template

Purpose: make recording a measurement lightweight and reusable without adding
benchmark infrastructure or slowing installation materially.

```yaml
slice_id: I152-S03
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior System Architect, Senior Tester]
affected_files: [src/tiny_swarm_world/application/ports/repositories/port_performance_evidence_repository.py, src/tiny_swarm_world/infrastructure/adapters/repositories/performance_evidence_local_repository.py, documentation/process/performance-evidence-contract.md, tests/infrastructure/adapters/repositories/test_performance_evidence_local_repository.py]
affected_modules: [performance evidence writer/template]
affected_contracts: [shared evidence location/schema, deterministic Markdown/JSON projection]
dependencies: [I152-S02]
parallel_group: SERIAL-ADAPTER
file_locks: [src/tiny_swarm_world/application/ports/repositories/port_performance_evidence_repository.py, src/tiny_swarm_world/infrastructure/adapters/repositories/performance_evidence_local_repository.py, documentation/process/performance-evidence-contract.md, tests/infrastructure/adapters/repositories/test_performance_evidence_local_repository.py]
contract_locks: [I152-evidence-writer]
architecture_locks: [application-port-before-infrastructure-adapter]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: update quality/evidence concept only after implementation review
  adr: none
stop_conditions: [new external dependency, non-Git-friendly output, persistent secret/host identity]
```

Done criteria: a helper or template can record all required fields and emits
stable human-readable plus structured output where useful.

### Slice 04 — Integrate contract into issue/workflow evidence paths

Purpose: define how #144–#148 attach segment evidence without changing their
runtime behavior or creating ad hoc locations.

```yaml
slice_id: I152-S04
profile: FULL_PATH
owner: Senior Workflow Architect
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Senior Tester]
affected_files: [documentation/workflow/workflow.index.md, documentation/workflow/issues/issue-144/workflow.md, documentation/workflow/issues/issue-146/workflow.md, documentation/workflow/issues/issue-147/workflow.md, documentation/workflow/issues/issue-148/workflow.md, documentation/workflow/issues/issue-145/workflow.md]
affected_modules: [indexed workflow evidence contract]
affected_contracts: [issue-to-segment evidence mapping, baseline/new semantics]
dependencies: [I152-S03]
parallel_group: SERIAL-WORKFLOW-SYNC
file_locks: [documentation/workflow/issues/issue-144/**, documentation/workflow/issues/issue-146/**, documentation/workflow/issues/issue-147/**, documentation/workflow/issues/issue-148/**, documentation/workflow/issues/issue-145/**]
contract_locks: [I152-consumer-contract]
architecture_locks: [planned-vs-implemented]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: no architecture change expected
  adr: none
stop_conditions: [consumer workflow invents incompatible schema, evidence path ambiguous, planned behavior presented as implemented]
```

Done criteria: each related workflow points to the shared schema, segment
identity and limitation rules.

### Slice 05 — Serialization/template tests and documentation review

Purpose: prove stability, optional-field handling, comparison guidance and
single/multi-node compatibility.

```yaml
slice_id: I152-S05
profile: FULL_PATH
owner: Senior Tester
secondary_reviewers: [Senior Python Automation Developer, Senior System Architect, Senior Documentation Engineer]
affected_files: [tests/domain/performance/**, tests/infrastructure/adapters/repositories/test_performance_evidence_local_repository.py, documentation/process/performance-evidence-contract.md, .tiny-swarm/evidence/issue-152/test_results.md]
affected_modules: [performance contract tests]
affected_contracts: [serialization stability, limitations, optional values]
dependencies: [I152-S04]
parallel_group: SERIAL-QUALITY
file_locks: [tests/domain/performance/**, tests/infrastructure/adapters/repositories/test_performance_evidence_local_repository.py, documentation/process/performance-evidence-contract.md, .tiny-swarm/evidence/issue-152/**]
contract_locks: [I152-tested-schema]
architecture_locks: [no-heavy-benchmarking]
quality_gates:
  targeted: [python3 tools/quality_gate.py test]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: quality/evidence wording checked
  adr: none
stop_conditions: [serialization instability, missing optional values fail unexpectedly, timing described as absolute]
```

Done criteria: all matrix requirements have test/docs evidence and the shared
contract is ready for #144.

### Slice 06 — Evidence package and independent completion audit

Purpose: confirm this issue did not implement downstream optimizations and
release the contract to the next indexed workflow.

```yaml
slice_id: I152-S06
profile: FULL_PATH
owner: Issue Completion Auditor
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Senior Tester, Senior Documentation Engineer]
affected_files: [.tiny-swarm/evidence/issue-152/**]
affected_modules: [issue completion evidence]
affected_contracts: [I152-completion-decision]
dependencies: [I152-S05]
parallel_group: SERIAL-AUDIT
file_locks: [.tiny-swarm/evidence/issue-152/**]
contract_locks: [I152-completion-decision]
architecture_locks: [auditor-independent-from-implementer]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: final reviewed status
  adr: final status
stop_conditions: [open requirement, missing contract test, downstream optimization diff, evidence ambiguity]
```

Done criteria: independent audit is `PASS`; otherwise the next workflow is
blocked or incomplete.

## Dependency Graph

```text
I197-S06 -> I152-S01 -> I152-S02 -> I152-S03 -> I152-S04 -> I152-S05 -> I152-S06
```

## Parallel Execution

- Can this workflow run in parallel? No; schema, writer, consumers and tests
  are contract-ordered.
- Conflicting workflows: any evidence schema, quality-policy or performance
  measurement workflow.
- Shared files: workflow consumer docs and evidence conventions.
- Shared infrastructure: none; external services prohibited.
- Requires isolated worktree: yes for every slice.
- Requires serialized live validation: not applicable.
- Merge-order constraints: S06 precedes #144.

## Automatic Work Distribution Policy

Analyze backend, frontend, tests, runtime, docs, quality, architecture and
security streams for each slice; use subagents or explicit fallback evidence;
require distribution/consolidation artifacts. Frontend/runtime live streams
are normally not applicable. Codex owns final integration and schema decisions.
Do not parallelize shared schema/writer/docs, generated evidence, unclear
redaction or any scope that implements #144–#148 early.

## Git Worktree Execution Rule

Every slice uses an isolated worktree, verifies the indexed workflow branch and
locks, and does not merge directly.

## Issue Completion Discipline

- Requirement matrix path: `documentation/workflow/issues/issue-152/requirement-matrix.md`; execution copy `.tiny-swarm/evidence/issue-152/requirement_matrix.md`.
- Required evidence path: `.tiny-swarm/evidence/issue-152/`.
- Required evidence files: standard six plus schema/template and consumer mapping evidence.
- Requirement Lead review: S01/S04/S06.
- System Architect Reviewer review: S02/S03/S06.
- Test / Evidence Reviewer review: S05/S06.
- Issue Completion Auditor review: S06.
- DONE blocking rule: open or unverified requirements force `INCOMPLETE`, `BLOCKED` or `FAILED`.

## Quality-Gate Expectations

Use `git diff --check`, targeted serialization/template tests and the full
`python3 tools/quality_gate.py quality`; no benchmark or live claim.

## Documentation Synchronization and Arc42 Check Status

Arc42 quality/evidence sections were reviewed. S03/S05 update a process
document and, if needed, a quality section only from verified behavior; no ADR
is inferred.

## Stop Conditions and Uncertainty Escalation

Stop for schema ambiguity, redaction risk, external dependency, missing
consumer mapping or downstream implementation leakage. Escalate architecture
to the System Architect and evidence semantics to the Senior Tester.

## Definition of Done

The shared contract, helper/template, consumer references, serialization tests,
limitations guidance and required evidence exist; S06 is `PASS`.

## Handoff to workflow execute

Promote #152 only after I197-S06. Execute S01–S06 serially and require the
shared schema before starting #144.
