# Workflow: Issue #191 — Typed Verification Evidence Builders

Workflow ID: `issue-191-20260809`

Workflow version: `issue-191-v1.0.0`

Status: `COMPLETED_LOCAL_AUDITED`

Authoring branch: `feature/workflow-solid-refactor-chain-20260809`

Implementation branch: `feature/typed-verification-evidence-solid`

Chain position: 03 of 07; predecessor: #184; successor: #187.

## Executive Summary

Inventory and centralize distributed verification-evidence construction using
typed constants, value objects or builders where they protect the stable
serialized contract. Preserve all externally consumed keys and classification
values, keep policy in lifecycle/preflight/deployment owners, and stop if an
evidence consumer is unknown.

## Requirement Clarification Record

- Original Request: workflow creation for the ordered issue chain.
- Interpreted Intent: author the third indexed workflow; implementation waits
  for audited #184 completion.
- Change Type: evidence-contract-sensitive Python infrastructure refactor.
- Affected Process Strand: `workflow-create-to-workflow-execute`.
- Affected Architecture Area: node lifecycle, teardown, preflight and
  deployment evidence creation and tests.
- Explicit Requirements: [Issue #191 matrix](../../../.tiny-swarm/evidence/solid-typed-evidence/requirement_matrix.md).
- Implicit Requirements: schema compatibility, deterministic serialization,
  safe values, no generic builder owning runtime policy, and complete consumer
  inventory.
- Assumptions: #184 establishes extraction boundaries; the current evidence
  dictionaries are the compatibility baseline; issue bodies remain the source
  without a matching EPIC.
- Non-Goals: renaming public evidence keys, changing lifecycle semantics,
  live infrastructure/browser runs, React, service extraction or DI redesign.
- Risks: an unknown consumer or implicit key can be broken by typing; broad
  builders can recreate the original large-module problem.
- Open Questions: which fields are externally consumed and whether enums or
  small value objects best preserve string serialization.
- Blocking Questions: unknown evidence consumer is a hard execution blocker.
- Confidence Level: 85%.
- Decision: `PROCEED_WITH_ACCEPTED_ASSUMPTIONS`.

## Verified Baseline and Target Picture

The current `lxc_node_provider.py` constructs broad dictionaries through
helpers such as `_evidence`, `_profile_evidence` and
`_resource_resolution_evidence`; preflight and deployment paths also emit
classification strings. #238 has already introduced separate LXC modules but
not a verified typed evidence contract. The target keeps serialized output
backward compatible and makes construction explicit and testable.

## Scope, Constraints and Assessments

In scope: consumer/key inventory, typed evidence primitives/builders,
incremental caller migration, compatibility tests, architecture guard and
evidence audit. Domain/application contracts are not redesigned. Frontend and
Console/status UI impact are `NOT_APPLICABLE`; browser React review is
forbidden. Python and architecture work uses deterministic mocks and the full
local quality gate. No live infrastructure, credentials, Selenium or external
success claim is implied. Evidence values and logs remain sanitized.

## Ordered Slices

### Slice 01 — Evidence consumer and schema inventory

```yaml
slice_id: S191-01
profile: FULL_PATH
owner: Senior Requirement Engineer
secondary_reviewers: [Senior System Architect, Senior Python Automation Developer, Senior Tester]
affected_files: [.tiny-swarm/evidence/solid-typed-evidence/requirement_matrix.md, .tiny-swarm-world/evidence/solid-typed-evidence/three-amigos.md, .tiny-swarm-world/evidence/solid-typed-evidence/evidence-key-inventory-before.md]
affected_modules: [node lifecycle, teardown, preflight, deployment evidence consumers]
affected_contracts: [serialized verification evidence, classification values]
dependencies: []
parallel_group: SERIAL-CHAIN
file_locks: [.tiny-swarm/evidence/solid-typed-evidence/**, .tiny-swarm-world/evidence/solid-typed-evidence/**]
contract_locks: [verification-evidence-serialization]
architecture_locks: [evidence-builder-policy-boundary]
quality_gates:
  targeted: [git diff --check]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: reviewed; planned only
  adr: none unless evidence is a new external contract
stop_conditions: [unknown consumer, omitted key/classification, inconsistent baseline]
```

### Slice 02 — Typed builders and gradual caller migration

```yaml
slice_id: S191-02
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior System Architect, Senior Tester, Senior Security Sandbox Engineer]
affected_files: [src/tiny_swarm_world/infrastructure/adapters/clients/lxc/node/**, src/tiny_swarm_world/infrastructure/adapters/clients/lxc_node_provider.py, src/tiny_swarm_world/infrastructure/adapters/preflight/**, src/tiny_swarm_world/infrastructure/composition.py, tests/infrastructure/adapters/clients/lxc/**, tests/infrastructure/adapters/preflight/**, tests/application/**]
affected_modules: [typed evidence builders and existing evidence producers]
affected_contracts: [verification evidence keys, classifications, operator actions]
dependencies: [S191-01]
parallel_group: SERIAL-CHAIN
file_locks: [src/tiny_swarm_world/infrastructure/adapters/clients/lxc/node/**, src/tiny_swarm_world/infrastructure/adapters/clients/lxc_node_provider.py, src/tiny_swarm_world/infrastructure/adapters/preflight/**, src/tiny_swarm_world/infrastructure/composition.py, tests/infrastructure/adapters/clients/lxc/**, tests/infrastructure/adapters/preflight/**, tests/application/**]
contract_locks: [verification-evidence-serialization]
architecture_locks: [evidence-builder-policy-boundary, issue-184-lxc-node-boundary]
quality_gates:
  targeted: [python3 tools/quality_gate.py lint, python3 tools/quality_gate.py typecheck, python3 tools/quality_gate.py test, python3 tools/quality_gate.py arch-lint, python3 tools/quality_gate.py arch-tests]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: planned typed evidence boundary until verified
  adr: required only if serialized contract intentionally changes
stop_conditions: [serialized key/value drift, broad builder policy leakage, raw sensitive values, untyped bypass remains in guarded scope]
```

### Slice 03 — Compatibility, architecture and evidence audit

```yaml
slice_id: S191-03
profile: FULL_PATH
owner: Senior Tester
secondary_reviewers: [Senior System Architect, Senior Requirement Engineer, Senior Documentation Engineer]
affected_files: [tests/architecture/**, tests/infrastructure/**, tests/application/**, .tiny-swarm-world/evidence/solid-typed-evidence/**, documentation/arc42/**]
affected_modules: [evidence compatibility and architecture validation]
affected_contracts: [before/after evidence schema, local quality gate]
dependencies: [S191-02]
parallel_group: SERIAL-CHAIN
file_locks: [tests/architecture/**, tests/infrastructure/**, tests/application/**, .tiny-swarm-world/evidence/solid-typed-evidence/**, documentation/arc42/**]
contract_locks: [verification-evidence-serialization]
architecture_locks: [evidence-builder-policy-boundary]
quality_gates:
  targeted: [git diff --check, python3 tools/quality_gate.py test, python3 tools/quality_gate.py arch-tests]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: synchronize verified status only
  adr: review existing evidence/safety decisions
stop_conditions: [missing consumer coverage, open matrix row, failed compatibility test, external result not observable]
```

## Slice Dependency Graph

```text
S191-01 -> S191-02 -> S191-03
```

Cross-workflow prerequisite: #184 must complete its lifecycle extraction and
evidence compatibility audit first.

## Parallel Execution

- Can this workflow run in parallel? No; evidence construction is shared by
  node, preflight and deployment paths and follows #184.
- Conflicting workflows: #184, #187, #190 and any evidence-schema change.
- Shared files: lifecycle evidence, preflight/deployment evidence and tests.
- Shared infrastructure: none in local verification.
- Requires isolated worktree: yes.
- Requires serialized live validation: yes, if separately authorized.
- Merge-order constraints: #184 -> #191 -> #187.

## Automatic Work Distribution Policy

`workflow execute` automatically analyzes backend, frontend, tests, runtime,
documentation, quality, architecture and security streams for every slice.
Real Codex subagents are used where supported; unavailable subagents require
explicit role-based fallback. Distribution evidence is required before edits
and consolidation evidence after implemented slices under
`.codex/evidence/issue-191-20260809/slice-<number>-{distribution,consolidation}.md`.
Historical global slice evidence is preserved. Shared evidence contracts,
overlapping files, unclear consumers, mandatory ordering, generated
conflicts, unclear secrets or weakened guards forbid parallelization. Codex is
the final integration owner.

## Execution Evidence Paths

- S191-01 distribution: `.codex/evidence/issue-191-20260809/slice-01-distribution.md`.
- S191-01 consolidation: `.codex/evidence/issue-191-20260809/slice-01-consolidation.md`.
- S191-02 distribution: `.codex/evidence/issue-191-20260809/slice-02-distribution.md`.
- S191-02 consolidation: `.codex/evidence/issue-191-20260809/slice-02-consolidation.md`.
- S191-03 distribution: `.codex/evidence/issue-191-20260809/slice-03-distribution.md`.
- S191-03 consolidation: `.codex/evidence/issue-191-20260809/slice-03-consolidation.md`.

## Git Worktree Execution Rule

All execution uses isolated worktrees and stream branches named
`<workflow-branch>-slice-<number>-<stream>`. Workers verify branch ownership,
stay within locks, and do not merge. Codex consolidates after tests and
evidence.

## Role and Ownership Map

Requirement: Senior Requirement Engineer. Architecture: Senior System
Architect. Implementation: Senior Python Automation Developer. Tests/evidence:
Senior Tester. Docs: Senior Documentation Engineer. Order/locks: Senior
Execution Orchestrator.

## Issue Completion Discipline

- Requirement matrix path: `.tiny-swarm/evidence/solid-typed-evidence/requirement_matrix.md`.
- Required evidence path: `.tiny-swarm/evidence/solid-typed-evidence/`.
- Required evidence files: `requirement_matrix.md`, `implementation_summary.md`, `changed_files.md`, `test_results.md`, `remaining_risks.md`, `acceptance_checklist.md`, plus Three-Amigos and before/after key inventories under `.tiny-swarm-world/evidence/solid-typed-evidence/`.
- Requirement Lead review: S191-01.
- System Architect Reviewer review: S191-02.
- Test / Evidence Reviewer review: S191-03.
- Issue Completion Auditor review: before #187 promotion.
- DONE blocking rule: every key/value requirement must have implementation
  and verification evidence; open/unverified rows force `INCOMPLETE`,
  `BLOCKED` or `FAILED`.

## Quality-Gate Expectations

The default authority is `python3 tools/quality_gate.py quality` plus focused
tests and architecture checks from `QUALITY.md`. Live/browser/external states
must be recorded separately and never inferred from local output.

## Documentation, Stop Conditions, Definition of Done and Handoff

Arc42 may record the typed evidence boundary only after verification. Stop on
an unknown consumer, schema drift, unsafe evidence, failed gate or missing
decision. Done requires schema-compatible output, complete inventory,
focused/regression/architecture tests, required evidence, full local quality,
and an independent auditor PASS. These conditions are satisfied locally;
promote #187 as the next serialized target.

## Completion Record

- Decision: `PASS` — locally complete and independently audited.
- Requirement matrix: all `REQ-191-001` through `REQ-191-006` are
  `VERIFIED_LOCAL`.
- Local quality: `python3 tools/quality_gate.py quality` passed with `1685`
  tests passed and `28` skipped.
- Live, browser and external quality-system checks: not run and not claimed.
- Handoff: Issue #187, `feature/preflight-service-probe-registry-solid`.

## Arc42 Check Status

Current Arc42 evidence-safety and quality sections were reviewed. The typed
construction boundary is verified locally and preserves the existing schema;
no live or external result is claimed.
