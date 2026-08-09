# Workflow: Issue #190 — Stack Prerequisite Strategies

Workflow ID: `issue-190-20260809`

Workflow version: `issue-190-v1.0.0`

Status: `COMPLETED_LOCAL_AUDITED`

Authoring branch: `feature/workflow-solid-refactor-chain-20260809`

Implementation branch: `feature/stack-prerequisite-strategies-solid`

Chain position: 05 of 07; predecessor: #187; successor: #192.

## Executive Summary

Complete and verify strategy/registry dispatch for stack prerequisites and
asset transfer without duplicating the partial extraction already present in
`clients/lxc/swarm/` from #238. Preserve Traefik, SonarQube, Swagger and
default-stack behavior, command generation and safe failure semantics.

## Requirement Clarification Record

- Original Request: workflow creation for the ordered issue chain.
- Interpreted Intent: author the fifth indexed workflow; execute only after
  #187 completion.
- Change Type: Python Swarm/LXC runtime architecture refactor with residual
  scope reconciliation.
- Affected Process Strand: `workflow-create-to-workflow-execute`.
- Affected Architecture Area: `lxc/swarm` prerequisite, asset-transfer and
  runtime facade boundaries.
- Explicit Requirements: [Issue #190 matrix](../../../.tiny-swarm/evidence/solid-stack-prerequisites/requirement_matrix.md).
- Implicit Requirements: no generic runtime stack-name switch, deterministic
  default behavior, no live Docker/Swarm mutation and complete before/after
  special-case inventory.
- Assumptions: #238's current `StackPrerequisiteRegistry` and
  `StackAssetTransfer` are baseline candidates, not proof of issue completion;
  only residual gaps will be changed.
- Non-Goals: new stacks, deployment topology change, live Swarm execution,
  browser React, preflight registry or HTTP wrapper work.
- Risks: duplicating existing strategies, changing transfer order or
  prerequisite timing, and confusing registry dispatch with handler-local
  policy.
- Open Questions: whether each existing strategy satisfies the issue's
  protocol/coverage requirements and whether asset transfer needs further
  decomposition.
- Blocking Questions: incomplete current inventory or behavior coverage blocks
  implementation.
- Confidence Level: 85%.
- Decision: `PROCEED_WITH_ACCEPTED_ASSUMPTIONS`.

## Verified Baseline and Target Picture

Current source includes `stack_prerequisite_registry.py`,
`stack_asset_transfer.py` and `swarm_stack_runtime.py`; strategy classes still
contain stack-name branches. The target is a clear registry/strategy boundary
where generic runtime orchestration does not grow new stack conditionals, with
all current command and asset behavior preserved.

## Scope and Assessments

In scope: residual inventory, prerequisite/asset strategy contracts, handler
coverage, generic runtime delegation, focused/regression/architecture tests and
evidence. Infrastructure remains the adapter boundary; application/domain
ports do not absorb shell or Docker details. Python impact is `FULL_PATH`.
Frontend/Console UI is `NOT_APPLICABLE`; browser React review is forbidden.
Default gates are local and mocked; live Swarm and external checks are opt-in.

## Ordered Slices

### Slice 01 — Residual special-case inventory

```yaml
slice_id: S190-01
profile: FULL_PATH
owner: Senior Requirement Engineer
secondary_reviewers: [Senior System Architect, Senior Python Automation Developer, Senior Tester]
affected_files: [.tiny-swarm/evidence/solid-stack-prerequisites/requirement_matrix.md, .tiny-swarm-world/evidence/solid-stack-prerequisites/three-amigos.md, .tiny-swarm-world/evidence/solid-stack-prerequisites/special-case-inventory-before.md]
affected_modules: [LXC swarm stack runtime, prerequisite registry, asset transfer]
affected_contracts: [stack prerequisite behavior, stack asset transfer, command generation]
dependencies: []
parallel_group: SERIAL-CHAIN
file_locks: [.tiny-swarm/evidence/solid-stack-prerequisites/**, .tiny-swarm-world/evidence/solid-stack-prerequisites/**]
contract_locks: [stack-prerequisite-dispatch, stack-asset-transfer]
architecture_locks: [generic-stack-runtime-boundary]
quality_gates:
  targeted: [git diff --check]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: reviewed; planned residual status
  adr: none unless deployment behavior changes
stop_conditions: [duplicate existing extraction, unclassified special case, insufficient baseline tests]
```

### Slice 02 — Complete residual strategies and generic dispatch

```yaml
slice_id: S190-02
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior System Architect, Senior Tester, Senior Security Sandbox Engineer]
affected_files: [src/tiny_swarm_world/infrastructure/adapters/clients/lxc/swarm/**, src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py, tests/infrastructure/adapters/clients/lxc/swarm/**, tests/infrastructure/adapters/clients/test_lxc_swarm_runtime.py]
affected_modules: [stack prerequisite and asset transfer strategies]
affected_contracts: [StackPrerequisiteStrategy, StackPrerequisiteRegistry, deployment command generation]
dependencies: [S190-01]
parallel_group: SERIAL-CHAIN
file_locks: [src/tiny_swarm_world/infrastructure/adapters/clients/lxc/swarm/**, src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py, tests/infrastructure/adapters/clients/lxc/swarm/**, tests/infrastructure/adapters/clients/test_lxc_swarm_runtime.py]
contract_locks: [stack-prerequisite-dispatch, stack-asset-transfer]
architecture_locks: [generic-stack-runtime-boundary]
quality_gates:
  targeted: [python3 tools/quality_gate.py lint, python3 tools/quality_gate.py typecheck, python3 tools/quality_gate.py test, python3 tools/quality_gate.py arch-lint, python3 tools/quality_gate.py arch-tests]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: update only verified residual implementation
  adr: stop if deployment ownership changes
stop_conditions: [generic runtime conditionals remain, behavior drift, wrong asset path, live Docker call in tests]
```

### Slice 03 — Regression, architecture and completion audit

```yaml
slice_id: S190-03
profile: FULL_PATH
owner: Senior Tester
secondary_reviewers: [Senior System Architect, Senior Requirement Engineer, Senior Documentation Engineer]
affected_files: [tests/architecture/**, tests/infrastructure/adapters/clients/lxc/swarm/**, .tiny-swarm-world/evidence/solid-stack-prerequisites/**, documentation/arc42/**]
affected_modules: [stack strategy verification and evidence]
affected_contracts: [Traefik/SonarQube/Swagger behavior, generic runtime complexity]
dependencies: [S190-02]
parallel_group: SERIAL-CHAIN
file_locks: [tests/architecture/**, tests/infrastructure/adapters/clients/lxc/swarm/**, .tiny-swarm-world/evidence/solid-stack-prerequisites/**, documentation/arc42/**]
contract_locks: [stack-prerequisite-dispatch, stack-asset-transfer]
architecture_locks: [generic-stack-runtime-boundary]
quality_gates:
  targeted: [git diff --check, python3 tools/quality_gate.py test, python3 tools/quality_gate.py arch-tests]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: synchronize verified status
  adr: review existing Swarm/LXC decisions
stop_conditions: [missing behavior coverage, open matrix, failed gate, unobservable external result claimed]
```

## Parallel Execution

- Can this workflow run in parallel? No; it follows #187 and owns the shared
  LXC Swarm runtime used by #192.
- Conflicting workflows: #192 and any stack deployment/runtime change.
- Shared files: `lxc/swarm/**`, `lxc_swarm_runtime.py`, stack tests/evidence.
- Shared infrastructure: no live Docker/Swarm mutation in local gates.
- Requires isolated worktree: yes.
- Requires serialized live validation: yes, if authorized.
- Merge-order constraints: #187 -> #190 -> #192.

## Automatic Work Distribution Policy

`workflow execute` analyzes backend, frontend, tests, runtime, documentation,
quality, architecture and security streams per slice; uses real subagents or
records fallback role review. Distribution evidence precedes edits and
consolidation evidence follows implementation under `.codex/evidence/`. Shared
files/contracts, unclear residual scope, mandatory ordering, generated
conflicts, unclear secrets and weakened guards forbid parallelization. Codex
owns final integration.

## Execution Evidence Paths

- S190-01 distribution: `.codex/evidence/issue-190-20260809/slice-01-distribution.md`.
- S190-01 consolidation: `.codex/evidence/issue-190-20260809/slice-01-consolidation.md`.
- S190-02 distribution: `.codex/evidence/issue-190-20260809/slice-02-distribution.md`.
- S190-02 consolidation: `.codex/evidence/issue-190-20260809/slice-02-consolidation.md`.
- S190-03 distribution: `.codex/evidence/issue-190-20260809/slice-03-distribution.md`.
- S190-03 consolidation: `.codex/evidence/issue-190-20260809/slice-03-consolidation.md`.

## Git Worktree Execution Rule

Use isolated worktrees and `<workflow-branch>-slice-<number>-<stream>` branches.
Workers verify branch and locks, do not merge and remain inside allowed files.

## Role and Ownership Map

Requirement and drift: Senior Requirement Engineer. Architecture: Senior System
Architect. Python/runtime: Senior Python Automation Developer. Tests/evidence:
Senior Tester. Docs: Senior Documentation Engineer. Ordering/locks: Senior
Execution Orchestrator.

## Issue Completion Discipline

- Requirement matrix path: `.tiny-swarm/evidence/solid-stack-prerequisites/requirement_matrix.md`.
- Required evidence path: `.tiny-swarm/evidence/solid-stack-prerequisites/`.
- Required evidence files: `requirement_matrix.md`, `implementation_summary.md`, `changed_files.md`, `test_results.md`, `remaining_risks.md`, `acceptance_checklist.md`, plus Three-Amigos and before/after special-case inventory under `.tiny-swarm-world/evidence/solid-stack-prerequisites/`.
- Requirement Lead review: S190-01.
- System Architect Reviewer review: S190-02.
- Test / Evidence Reviewer review: S190-03.
- Issue Completion Auditor review: before #192 promotion.
- DONE blocking rule: open/unverified requirements force `INCOMPLETE`,
  `BLOCKED` or `FAILED`; local tests do not prove live Swarm success.

## Quality-Gate Expectations, Documentation, Stop Conditions and Handoff

Use the `QUALITY.md` full local gate and focused commands only. Arc42 updates
must distinguish #238 implemented portions from residual planned work. Stop on
duplication, behavior drift, unclassified special cases, missing evidence,
failed gates or unobservable external/live results. Done requires residual
scope closure, strategy tests, generic-runtime guard, evidence and auditor
PASS. These conditions are satisfied locally; promote #192 as the next
serialized target.

## Completion Record

- Decision: `PASS` — locally complete and independently audited.
- Requirement matrix: all `REQ-190-001` through `REQ-190-006` are
  `VERIFIED_LOCAL`.
- Local quality: `python3 tools/quality_gate.py quality` passed with `1691`
  tests passed and `28` skipped.
- Live, browser and external quality-system checks: not run and not claimed.
- Handoff: Issue #192, `feature/separate-lxc-service-wrappers-solid`.

## Arc42 Check Status

Current Arc42 records #238's LXC split and Swarm quality constraints. The #190
residual registry/strategy boundary is verified locally; no live Swarm result
is claimed.
