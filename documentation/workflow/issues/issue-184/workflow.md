# Workflow: Issue #184 — Split `LxcNodeProvider` Responsibilities

Workflow ID: `issue-184-20260809`

Workflow version: `issue-184-v1.0.0`

Status: `READY_FOR_EXECUTION_WITH_ACCEPTED_ASSUMPTIONS` (indexed; promote before execution)

Authoring branch: `feature/workflow-solid-refactor-chain-20260809`

Implementation branch: `feature/split-lxc-node-provider-solid`

Chain position: 02 of 07; predecessor: #189; successor: #191.

## Executive Summary

Decompose the verified responsibilities of `lxc_node_provider.py` into
dependency-safe command, node, profile and resource modules while keeping
`LxcNodeProvider` as lifecycle orchestration. Preserve public lifecycle
outcomes, serialized evidence classifications, compatibility imports and the
#189 backend resolver. This workflow does not authorize implementation during
authoring.

## Requirement Clarification Record

- Original Request: workflow creation for the ordered seven-issue chain.
- Interpreted Intent: author the second indexed workflow, executed only after
  the #189 contract is complete and audited.
- Change Type: Python infrastructure architecture refactor with compatibility
  and evidence regression gates.
- Affected Process Strand: `workflow-create-to-workflow-execute`.
- Affected Architecture Area: LXC node lifecycle adapter, command runner,
  profile/resource policy, teardown and verification evidence.
- Explicit Requirements: [Issue #184 matrix](../../../.tiny-swarm/evidence/solid-lxc-node-provider/requirement_matrix.md).
- Implicit Requirements: preserve verify/ensure/reset/destroy semantics,
  bounded async execution, no circular dependencies, and no public port drift.
- Assumptions: #189 supplies the sole backend mapping; existing evidence
  consumers are discovered in Slice 01; compatibility shims remain until
  consumers are migrated and tested.
- Non-Goals: new provider behavior, public application-port redesign, typed
  evidence contract redesign (#191), live LXC lifecycle, browser React or
  microservice extraction.
- Risks: extraction can change evidence shape, async timeout behavior, import
  seams or ownership of profile safety policy.
- Open Questions: exact split between node lifecycle evidence and #191 typed
  builders; Slice 01 must freeze the boundary.
- Blocking Questions: none for authoring; unclear evidence schema blocks
  execution as required by the issue.
- Confidence Level: 85%.
- Decision: `PROCEED_WITH_ACCEPTED_ASSUMPTIONS`.

## Verified Baseline and Target Picture

Baseline commit: `004fd6c3f0a01b9bcf2bcb011b88e43a069399f9`. The current module
contains `LxcNodeCommandResult`, async command execution, lifecycle methods,
`_ObservedNode`, profile/resource helpers and broad evidence builders. The
target package keeps the facade orchestration-only and moves mechanics into
`clients/lxc/{command,node,profile,resource}/`, preserving old imports.

## Scope and Architecture Constraints

In scope: responsibility inventory, command/node/profile/resource/teardown and
evidence extraction, compatibility exports, focused tests, architecture guard,
issue evidence and Arc42 planning status. The infrastructure adapter may
depend on application ports and domain value objects but never the reverse.
The composition root remains the concrete wiring owner. No live provider or
Swarm mutation is permitted in default verification.

## Assessments

Python infrastructure impact is `FULL_PATH`; use async protocols and typed
models without import-time side effects. Frontend/Console UI impact is
`NOT_APPLICABLE`; browser React review is forbidden. Tests must cover
verify/ensure/reset/destroy, evidence compatibility, timeout/failure mapping,
profile safety, resource resolution and old import paths. Existing retries,
live-consent guards and sanitized diagnostics remain bounded and adapter-owned.

## Ordered Slices

### Slice 01 — Responsibility and public-outcome inventory

```yaml
slice_id: S184-01
profile: FULL_PATH
owner: Senior Requirement Engineer
secondary_reviewers: [Senior System Architect, Senior Python Automation Developer, Senior Tester]
affected_files: [.tiny-swarm/evidence/solid-lxc-node-provider/requirement_matrix.md, .tiny-swarm-world/evidence/solid-lxc-node-provider/three-amigos.md, .tiny-swarm-world/evidence/solid-lxc-node-provider/responsibility-map-before.md]
affected_modules: [lxc_node_provider lifecycle, command, profile, resource and evidence responsibilities]
affected_contracts: [verify/ensure/reset/destroy outcomes, serialized evidence classifications]
dependencies: []
parallel_group: SERIAL-CHAIN
file_locks: [.tiny-swarm/evidence/solid-lxc-node-provider/**, .tiny-swarm-world/evidence/solid-lxc-node-provider/**]
contract_locks: [lxc-node-public-outcomes, evidence-schema-compatibility]
architecture_locks: [lxc-node-orchestration-boundary, issue-189-backend-resolver]
quality_gates:
  targeted: [git diff --check]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: reviewed; planned only
  adr: none unless evidence/public boundary is changed
stop_conditions: [unclear evidence schema, missing consumer, #189 contract not audited, cyclic split]
```

Purpose: create the issue-required Three-Amigos note and map every current
responsibility to extracted, retained or explicitly deferred ownership before
source edits.

### Slice 02 — Extract modules and preserve compatibility

```yaml
slice_id: S184-02
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior System Architect, Senior Tester, Senior Security Sandbox Engineer]
affected_files: [src/tiny_swarm_world/infrastructure/adapters/clients/lxc/command/**, src/tiny_swarm_world/infrastructure/adapters/clients/lxc/node/**, src/tiny_swarm_world/infrastructure/adapters/clients/lxc/profile/**, src/tiny_swarm_world/infrastructure/adapters/clients/lxc/resource/**, src/tiny_swarm_world/infrastructure/adapters/clients/lxc_node_provider.py, tests/infrastructure/adapters/clients/lxc/**, tests/infrastructure/adapters/clients/test_lxc_node_provider.py]
affected_modules: [infrastructure.adapters.clients.lxc.node_provider and extracted modules]
affected_contracts: [LxcNodeCommandRunner, PortNodeLifecycle, PortManagedNodeTeardown, evidence dictionaries]
dependencies: [S184-01]
parallel_group: SERIAL-CHAIN
file_locks: [src/tiny_swarm_world/infrastructure/adapters/clients/lxc/**, src/tiny_swarm_world/infrastructure/adapters/clients/lxc_node_provider.py, tests/infrastructure/adapters/clients/lxc/**, tests/infrastructure/adapters/clients/test_lxc_node_provider.py]
contract_locks: [lxc-node-public-outcomes, evidence-schema-compatibility, issue-189-backend-resolver]
architecture_locks: [lxc-node-orchestration-boundary]
quality_gates:
  targeted: [python3 tools/quality_gate.py lint, python3 tools/quality_gate.py typecheck, python3 tools/quality_gate.py test, python3 tools/quality_gate.py arch-lint, python3 tools/quality_gate.py arch-tests]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: planned boundary until evidence proves implementation
  adr: none unless public contract changes
stop_conditions: [behavior drift, old import break, direct policy leak, unbounded async command, duplicate backend map]
```

### Slice 03 — Regression, architecture and completion audit

```yaml
slice_id: S184-03
profile: FULL_PATH
owner: Senior Tester
secondary_reviewers: [Senior System Architect, Senior Requirement Engineer, Senior Documentation Engineer]
affected_files: [tests/architecture/**, tests/infrastructure/adapters/clients/lxc/**, .tiny-swarm-world/evidence/solid-lxc-node-provider/**, documentation/arc42/**]
affected_modules: [LXC lifecycle architecture and evidence verification]
affected_contracts: [public lifecycle behavior, compatibility imports, evidence schema]
dependencies: [S184-02]
parallel_group: SERIAL-CHAIN
file_locks: [tests/architecture/**, tests/infrastructure/adapters/clients/lxc/**, .tiny-swarm-world/evidence/solid-lxc-node-provider/**, documentation/arc42/**]
contract_locks: [lxc-node-public-outcomes, evidence-schema-compatibility]
architecture_locks: [lxc-node-orchestration-boundary]
quality_gates:
  targeted: [git diff --check, python3 tools/quality_gate.py arch-tests, python3 tools/quality_gate.py test]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: synchronize only verified responsibility status
  adr: review LXC-native provider ADR; no invented decision
stop_conditions: [missing regression evidence, open matrix row, failed quality gate, external success claimed without result]
```

## Slice Dependency Graph

```text
S184-01 -> S184-02 -> S184-03
```

Cross-workflow prerequisite: #189 must be audited and complete before S184-01
can freeze the command boundary.

## Parallel Execution

- Can this workflow run in parallel? No; it shares the LXC command package and
  `lxc_node_provider.py` with #189/#191 and must follow the chain.
- Conflicting workflows: #189, #191, #192 and any LXC node-provider change.
- Shared files: `lxc_node_provider.py`, `lxc/command/**`, LXC tests and evidence.
- Shared infrastructure: none in local quality checks.
- Requires isolated worktree: yes.
- Requires serialized live validation: yes, if separately authorized.
- Merge-order constraints: #189 first; #184 before #191.

## Automatic Work Distribution Policy

`workflow execute` must analyze backend, frontend, tests, runtime, documentation,
quality, architecture and security streams for every slice, use real Codex
subagents where available, or record role-based fallback. Distribution evidence
`.codex/evidence/slice-<number>-distribution.md` is required before edits and
consolidation evidence `.codex/evidence/slice-<number>-consolidation.md` after
implementation. Overlapping files, unclear architecture, contradictory
requirements, mandatory ordering, generated conflicts, unclear secrets and
weakened guards forbid parallelization. Codex integrates and decides final
acceptance.

## Git Worktree Execution Rule

Use an isolated worktree and stream branches named
`<workflow-branch>-slice-<number>-<stream>`. Workers verify branch ownership,
do not edit shared branches or merge, and remain within declared locks.

## Role and Ownership Map

Requirement: Senior Requirement Engineer. Architecture: Senior System
Architect. Implementation: Senior Python Automation Developer. Tests/evidence:
Senior Tester. Docs: Senior Documentation Engineer. Lock/order validation:
Senior Execution Orchestrator.

## Issue Completion Discipline

- Requirement matrix path: `.tiny-swarm/evidence/solid-lxc-node-provider/requirement_matrix.md`.
- Required evidence path: `.tiny-swarm/evidence/solid-lxc-node-provider/`.
- Required evidence files: `requirement_matrix.md`, `implementation_summary.md`, `changed_files.md`, `test_results.md`, `remaining_risks.md`, `acceptance_checklist.md`, plus the issue-required Three-Amigos, responsibility and E2E/live-state files where applicable.
- Requirement Lead review: after S184-01.
- System Architect Reviewer review: after S184-02.
- Test / Evidence Reviewer review: after S184-03.
- Issue Completion Auditor review: before #191 promotion.
- DONE blocking rule: open or unverified requirements force `INCOMPLETE`,
  `BLOCKED` or `FAILED`; no skipped live/browser/external check is success.

## Quality-Gate Expectations

Use only `QUALITY.md` commands. The full local gate is
`python3 tools/quality_gate.py quality`; docs use `git diff --check`. Live
LXC/browser and Sonar states must use the canonical policy.

## Documentation, Stop Conditions, Definition of Done and Handoff

Arc42 receives only verified status updates. Stop for unclear evidence schema,
behavior drift, import cycles, failed required gates, missing evidence or an
architecture decision not present in the repository. Done requires every
matrix row, compatibility test, lifecycle regression, architecture check,
evidence file and auditor PASS. Promote only after #189 is complete and the
indexed path is intentionally selected for execution.

## Arc42 Check Status

Existing LXC-native provider architecture and #238 responsibility split were
reviewed. This plan records a residual decomposition target; it does not claim
that #184 is implemented.
