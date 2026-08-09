# Workflow: Issue #189 — Centralize LXC Backend CLI Mapping and Shared Utilities

Workflow ID: `issue-189-20260809`

Workflow version: `issue-189-v1.0.0`

Status: `ACTIVE_EXECUTION`

Workflow set: `solid-refactor-chain-20260809`

Authoring branch: `feature/centralize-lxc-shared-utilities-solid`

Workflow authoring source branch: `feature/workflow-solid-refactor-chain-20260809`

Execution branch: `feature/centralize-lxc-shared-utilities-solid`

Implementation branch: `feature/centralize-lxc-shared-utilities-solid`

Promotion: Issue #189 promoted from the indexed workflow set for execution.

Chain position: 01 of 07; predecessor: none; successor: #184.

## Executive Summary

Create one dependency-safe LXC backend CLI resolver and centralize only the
shared command, diagnostics, manager-IP, path/quote and structured parsing
utilities that have multiple verified consumers. Preserve Incus/LXD command
values, adapter-owned failure policy, safe diagnostics, compatibility imports
and the existing hexagonal boundary. This is a refactor plan only.

## Requirement Clarification Record

- Original Request: `workflow create` for `#189 -> #184 -> #191 -> #187 -> #190 -> #192 -> #186`.
- Interpreted Intent: execute the first promoted indexed issue workflow; do not execute later chain issues before #189 completion.
- Change Type: issue-driven Python infrastructure refactor and architecture guard with evidence and regression gates.
- Affected Process Strand: `workflow-create-to-workflow-execute`.
- Affected Architecture Area: LXC command utilities, infrastructure adapters, diagnostics and composition wiring.
- Explicit Requirements: [Issue #189 requirement matrix](../../.tiny-swarm/evidence/solid-lxc-shared-utilities/requirement_matrix.md).
- Implicit Requirements: no domain/application imports, no circular imports, stable `ManagedLxcBackend` mapping, redacted diagnostics, explicit evidence, and no live infrastructure mutation in default verification.
- Assumptions: issue text is the source because no matching EPIC exists; #238's current LXC package is the implementation baseline; existing shared utilities are retained when behavior is already correct.
- Non-Goals: node-provider decomposition (#184), typed evidence builders (#191), preflight registry (#187), stack strategies (#190), service wrappers (#192), DI redesign (#186), Java/Maven/Spring, React and live deployment.
- Risks: centralization could blur ownership, change shell quoting, duplicate the #238 service boundary or expose raw output.
- Open Questions: exact utility placement and which JSON/YAML helper is truly shared; Slice 01 resolves these from verified consumers.
- Blocking Questions: none for authoring; any unknown consumer or circular dependency blocks execution.
- Confidence Level: 85%.
- Decision: `PROCEED_WITH_ACCEPTED_ASSUMPTIONS`.

## Verified Baseline and Target Picture

Baseline commit: `004fd6c3f0a01b9bcf2bcb011b88e43a069399f9` on clean `main` before
authoring. Current LXC code still contains `_BACKEND_CLI` in
`lxc_node_provider.py` and `lxc_swarm_runtime.py`; #238 already introduced
`lxc/command/`, `lxc/services/` and `lxc/swarm/` packages. The target is one
authoritative backend resolver with small shared utilities and no high-level
runtime imports.

## Scope and Architecture Constraints

In scope: backend resolver, verified shared utility extraction, consumer
migration, focused tests, an architecture/static duplicate guard, before/after
inventory, and planned-vs-implemented Arc42 synchronization.

The resolver and utilities remain in infrastructure. `composition.py` may wire
them, but application and domain packages remain unaware of LXC CLI mechanics.
Adapter policy, retries, failure classification and public application-port
behavior remain at their owning adapters. No live Incus/LXD/Docker/Swarm or
service command is permitted in default checks.

## Python, Frontend, Test and Resilience Assessment

This is Python infrastructure work; use typed protocols/value objects where
useful and preserve Python 3.12 compatibility. Frontend and Console/status UI
impact are `NOT_APPLICABLE`; browser React review is forbidden. Tests use
fakes/mocks and must cover Incus/LXD mapping, diagnostics, path handling,
manager-IP failure and import boundaries. Timeouts, retries and redaction stay
bounded and adapter-owned. Optional live/browser and external checks are
classified per verification-state policy and are never implied by a local pass.

## Ordered Slices

### Slice 01 — Consumer inventory and Three-Amigos contract

Purpose: inventory duplicate mappings/utilities and freeze ownership before
source edits. Create the issue-required Three-Amigos note during execution.

Prerequisites: indexed workflow promoted and #188 active baseline unchanged.

```yaml
slice_id: S189-01
profile: FULL_PATH
owner: Senior Requirement Engineer
secondary_reviewers: [Senior System Architect, Senior Python Automation Developer, Senior Tester]
affected_files: [.tiny-swarm/evidence/solid-lxc-shared-utilities/requirement_matrix.md, .tiny-swarm-world/evidence/solid-lxc-shared-utilities/three-amigos.md, .tiny-swarm-world/evidence/solid-lxc-shared-utilities/duplicate-inventory-before.md]
affected_modules: [infrastructure.adapters.clients.lxc.command, infrastructure.adapters.clients.lxc.services]
affected_contracts: [ManagedLxcBackend CLI mapping, safe diagnostics]
dependencies: []
parallel_group: SERIAL-CHAIN
file_locks: [.tiny-swarm/evidence/solid-lxc-shared-utilities/**, .tiny-swarm-world/evidence/solid-lxc-shared-utilities/**]
contract_locks: [lxc-backend-cli-resolution, lxc-shared-utility-boundary]
architecture_locks: [infrastructure-only-lxc-utilities]
quality_gates:
  targeted: [git diff --check]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: reviewed; planned only
  adr: none unless a new public boundary is discovered
stop_conditions: [unknown consumer, ambiguous stable value, circular-import risk, incomplete matrix]
```

### Slice 02 — Shared resolver/utilities and consumer migration

Purpose: add the authoritative resolver and only the utilities justified by
Slice 01; migrate LXC consumers while preserving adapter policy and imports.

Prerequisites: `S189-01` READY with no blocking contract question.

```yaml
slice_id: S189-02
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior System Architect, Senior Tester, Senior Security Sandbox Engineer]
affected_files: [src/tiny_swarm_world/infrastructure/adapters/clients/lxc/command/**, src/tiny_swarm_world/infrastructure/adapters/clients/lxc_node_provider.py, src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py, src/tiny_swarm_world/infrastructure/composition.py, tests/infrastructure/adapters/clients/lxc/**, tests/infrastructure/adapters/clients/test_lxc_swarm_runtime.py]
affected_modules: [infrastructure.adapters.clients.lxc, infrastructure.composition]
affected_contracts: [ManagedLxcBackend, LXC command diagnostics, manager IP resolution]
dependencies: [S189-01]
parallel_group: SERIAL-CHAIN
file_locks: [src/tiny_swarm_world/infrastructure/adapters/clients/lxc/command/**, src/tiny_swarm_world/infrastructure/adapters/clients/lxc_node_provider.py, src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py, src/tiny_swarm_world/infrastructure/composition.py, tests/infrastructure/adapters/clients/lxc/**, tests/infrastructure/adapters/clients/test_lxc_swarm_runtime.py]
contract_locks: [lxc-backend-cli-resolution, lxc-shared-utility-boundary]
architecture_locks: [infrastructure-only-lxc-utilities, composition-root-wiring]
quality_gates:
  targeted: [python3 tools/quality_gate.py lint, python3 tools/quality_gate.py typecheck, python3 tools/quality_gate.py test, python3 tools/quality_gate.py arch-lint, python3 tools/quality_gate.py arch-tests]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: planned boundary only until evidence
  adr: required only for a new public cross-layer contract
stop_conditions: [duplicate mapping remains, public behavior drift, raw secret diagnostics, domain/application import]
```

### Slice 03 — Regression, architecture guard and audit handoff

Purpose: prove no command drift, record the after-inventory, synchronize Arc42
planned status, and hand off to the issue completion auditor before #184.

Prerequisites: `S189-02` implementation and focused tests pass.

```yaml
slice_id: S189-03
profile: FULL_PATH
owner: Senior Tester
secondary_reviewers: [Senior System Architect, Senior Requirement Engineer, Senior Documentation Engineer]
affected_files: [tests/architecture/**, tests/infrastructure/adapters/clients/lxc/**, .tiny-swarm-world/evidence/solid-lxc-shared-utilities/**, documentation/arc42/**]
affected_modules: [architecture validation, LXC evidence, Arc42 quality/risk documentation]
affected_contracts: [issue acceptance, evidence package, local quality gate]
dependencies: [S189-02]
parallel_group: SERIAL-CHAIN
file_locks: [tests/architecture/**, tests/infrastructure/adapters/clients/lxc/**, .tiny-swarm-world/evidence/solid-lxc-shared-utilities/**, documentation/arc42/**]
contract_locks: [lxc-backend-cli-resolution]
architecture_locks: [lxc-duplicate-mapping-guard]
quality_gates:
  targeted: [git diff --check, python3 tools/quality_gate.py arch-tests, python3 tools/quality_gate.py test]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: update only verified planned/implemented status
  adr: review existing LXC ADRs; no invented decision
stop_conditions: [missing evidence, unverified requirement, failed local gate, inaccessible external result claimed green]
```

## Parallel Execution

- Can this workflow run in parallel? No; it locks shared LXC command and
  composition surfaces and is the first chain dependency.
- Conflicting workflows: #184, #192 and any workflow touching LXC command
  utilities or composition.
- Shared files: `lxc_node_provider.py`, `lxc_swarm_runtime.py`, composition and
  LXC tests.
- Shared infrastructure: none may be mutated by local verification.
- Requires isolated worktree: yes, for this workflow and every future stream.
- Requires serialized live validation: yes; live validation is optional and
  serialized if separately authorized.
- Merge-order constraints: complete #189 before #184; preserve its resolver
  contract.

## Automatic Work Distribution Policy

`workflow execute` must analyze every slice for safe backend, frontend, tests,
runtime, documentation, quality, architecture and security streams; use real
Codex subagents where supported; otherwise record explicit role-based fallback
review. Because the global slice evidence names are occupied by historical
workflows, this workflow uses `.codex/evidence/issue-189-20260809/` and must
create `slice-<number>-distribution.md` there before implementation and
`slice-<number>-consolidation.md` there after an implemented slice. Overlapping files/contracts, unclear architecture,
contradictory requirements, mandatory ordering, generated-file conflicts,
unclear secrets or weakened safety guards are not parallelizable. Codex is the
final integration owner.

## Execution Evidence Paths

- S189-01 distribution: `.codex/evidence/issue-189-20260809/slice-01-distribution.md`.
- S189-01 consolidation: `.codex/evidence/issue-189-20260809/slice-01-consolidation.md`.
- S189-02 distribution: `.codex/evidence/issue-189-20260809/slice-02-distribution.md`.
- S189-02 consolidation: `.codex/evidence/issue-189-20260809/slice-02-consolidation.md`.
- S189-03 distribution: `.codex/evidence/issue-189-20260809/slice-03-distribution.md`.
- S189-03 consolidation: `.codex/evidence/issue-189-20260809/slice-03-consolidation.md`.

## Git Worktree Execution Rule

Every execution uses an isolated worktree. Any approved stream branch must be
named `<workflow-branch>-slice-<number>-<stream>`. Workers verify the branch
before edits, never modify `main` or the authoring branch directly, and never
merge. Codex consolidates only after distribution, tests and evidence pass.

## Role and Ownership Map

| Responsibility | Owner |
|---|---|
| requirement matrix and drift | Senior Requirement Engineer |
| boundary and import safety | Senior System Architect |
| Python implementation | Senior Python Automation Developer |
| tests and quality gates | Senior Tester |
| Arc42 and handoff docs | Senior Documentation Engineer |
| lock/order validation | Senior Execution Orchestrator |

## Issue Completion Discipline

- Requirement matrix path: `.tiny-swarm/evidence/solid-lxc-shared-utilities/requirement_matrix.md`.
- Required evidence path: `.tiny-swarm/evidence/solid-lxc-shared-utilities/`.
- Required evidence files: `requirement_matrix.md`, `implementation_summary.md`, `changed_files.md`, `test_results.md`, `remaining_risks.md`, `acceptance_checklist.md`, plus issue-required Three-Amigos and inventory files under `.tiny-swarm-world/evidence/solid-lxc-shared-utilities/`.
- Requirement Lead review: required after S189-01 and before audit.
- System Architect Reviewer review: required after S189-02.
- Test / Evidence Reviewer review: required after S189-03.
- Issue Completion Auditor review: required before #184 is promoted.
- DONE blocking rule: any open or unverified requirement forces `INCOMPLETE`,
  `BLOCKED` or `FAILED`; skipped live/external evidence cannot be called green.

## Quality-Gate Expectations

Use only commands in `QUALITY.md`: targeted gates during implementation,
`python3 tools/quality_gate.py quality` before completion, and `git diff --check`
for authoring/docs. Sonar or browser checks are external/live state checks,
not implied by local quality.

## Documentation Synchronization, Stop Conditions and Definition of Done

Update Arc42 only to reflect verified planned or implemented responsibility.
Stop on a missing consumer, behavior drift, circular dependency, ambiguous
evidence, failed required gate, unverified external result, or need for an
unrecorded architecture decision.

The workflow is complete when all matrix rows have implementation and
verification evidence, the issue-required evidence exists, local quality is
green, the auditor records PASS, and the handoff explicitly declares #184
unblocked. No live success claim is required.

## Handoff to `workflow execute`

This workflow is promoted from the indexed set on
`feature/centralize-lxc-shared-utilities-solid`. Run S3/S3D preflight before
write-capable work, preserve the chain order, and do not call `workflow create`
backwards.

## Arc42 Check Status

Existing LXC-native and process-runner ADR/Arc42 material was reviewed. This
workflow adds a planned chain note only; no architecture decision is invented.
