# Workflow: Issue #186 — Explicit Composition Bindings

Workflow ID: `issue-186-20260809`

Workflow version: `issue-186-v1.0.0`

Status: `READY_FOR_EXECUTION_WITH_ACCEPTED_ASSUMPTIONS` (indexed; promote before execution)

Authoring branch: `feature/workflow-solid-refactor-chain-20260809`

Implementation branch: `feature/replace-global-di-service-locator-solid`

Chain position: 07 of 07; predecessor: #192; successor: none.

## Executive Summary

Audit the claimed global DI Service Locator scope and keep runtime dependency
resolution explicit through the composition root. The current baseline scan
found no `infra_core_container`, DI decorator package or
`infrastructure/dependency_injection` path, so the first slice must confirm
whether the issue is already absent or whether hidden residual usage remains.
If no residual scope exists, record bounded no-op evidence rather than
inventing a new container.

## Requirement Clarification Record

- Original Request: workflow creation for the ordered issue chain.
- Interpreted Intent: author the final indexed workflow; execute only after
  #192 is audited.
- Change Type: architecture/composition governance and possible Python DI
  residual refactor.
- Affected Process Strand: `workflow-create-to-workflow-execute`.
- Affected Architecture Area: `infrastructure/composition*.py` and any
  verified DI/annotation modules discovered by Slice 01.
- Explicit Requirements: [Issue #186 matrix](../../../.tiny-swarm/evidence/solid-di-container/requirement_matrix.md).
- Implicit Requirements: no global runtime resolve, deterministic lifetimes,
  explicit wiring, compatibility only when justified, and no scope invention.
- Assumptions: the read-only baseline scan is accurate enough to guide audit;
  current composition functions are the preferred wiring boundary; issue text
  is the source because no matching EPIC exists.
- Non-Goals: introduce a new service locator, change application ports without
  evidence, live infrastructure, browser React, microservices or unrelated
  composition cleanup.
- Risks: an incomplete repository-wide scan could miss hidden decorators;
  changing composition could affect all platform workflows.
- Open Questions: whether any generated/legacy surface is still in scope and
  whether explicit factory bindings are needed after audit.
- Blocking Questions: a discovered global runtime resolver or unclear lifetime
  contract blocks the no-op decision and requires architecture review.
- Confidence Level: 80%.
- Decision: `PROCEED_WITH_ACCEPTED_ASSUMPTIONS`.

## Verified Baseline and Target Picture

At authoring baseline `004fd6c3f0a01b9bcf2bcb011b88e43a069399f9`, a read-only
repository scan found no `infra_core_container`, `infra_core_di_*`, DI
decorators or dependency-injection package. `composition.py` and
`composition_lxc_runtimes.py` already construct concrete adapters explicitly.
The target is either verified explicit composition with a complete audit and
guard, or a minimal safe container used only for composition-time bindings if
the audit proves it is needed. Services must never call a global resolver.

## Scope and Assessments

In scope: complete usage inventory, composition binding decision, any strictly
necessary minimal binding implementation, explicit wiring tests, architecture
guard, evidence and Arc42 status. Python/architecture impact is `FULL_PATH`.
Frontend/Console UI is `NOT_APPLICABLE`; browser React review is forbidden.
Local quality is authoritative; no live infrastructure or external success is
implied.

## Ordered Slices

### Slice 01 — Repository-wide DI audit and decision

```yaml
slice_id: S186-01
profile: FULL_PATH
owner: Senior Requirement Engineer
secondary_reviewers: [Senior System Architect, Senior Python Automation Developer, Senior Tester]
affected_files: [.tiny-swarm/evidence/solid-di-container/requirement_matrix.md, .tiny-swarm-world/evidence/solid-di-container/three-amigos.md, .tiny-swarm-world/evidence/solid-di-container/dependency-map-before.md]
affected_modules: [composition, infrastructure wiring, repository-wide DI symbols]
affected_contracts: [explicit construction, binding/lifetime semantics, no global runtime resolve]
dependencies: []
parallel_group: SERIAL-CHAIN
file_locks: [.tiny-swarm/evidence/solid-di-container/**, .tiny-swarm-world/evidence/solid-di-container/**]
contract_locks: [explicit-composition-binding-contract]
architecture_locks: [composition-root-ownership, no-global-runtime-resolve]
quality_gates:
  targeted: [git diff --check]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: reviewed; planned/no-op status only
  adr: architecture review required if residual global resolver is found
stop_conditions: [hidden global resolve, unclear lifetime, missing usage inventory, composition ownership conflict]
```

### Slice 02 — Explicit composition or bounded residual implementation

```yaml
slice_id: S186-02
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior System Architect, Senior Tester, Senior Security Sandbox Engineer]
affected_files: [src/tiny_swarm_world/infrastructure/composition.py, src/tiny_swarm_world/infrastructure/composition_lxc_runtimes.py, src/tiny_swarm_world/infrastructure/**, tests/infrastructure/test_composition.py, tests/architecture/**]
affected_modules: [infrastructure composition and any verified residual DI module]
affected_contracts: [explicit adapter construction, deterministic binding/lifetime, compatibility imports]
dependencies: [S186-01]
parallel_group: SERIAL-CHAIN
file_locks: [src/tiny_swarm_world/infrastructure/composition.py, src/tiny_swarm_world/infrastructure/composition_lxc_runtimes.py, src/tiny_swarm_world/infrastructure/**, tests/infrastructure/test_composition.py, tests/architecture/**]
contract_locks: [explicit-composition-binding-contract]
architecture_locks: [composition-root-ownership, no-global-runtime-resolve]
quality_gates:
  targeted: [python3 tools/quality_gate.py lint, python3 tools/quality_gate.py typecheck, python3 tools/quality_gate.py test, python3 tools/quality_gate.py arch-lint, python3 tools/quality_gate.py arch-tests]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: only verified explicit wiring/no-op status
  adr: stop before a new container/boundary decision without ADR review
stop_conditions: [service-level resolve, eager singleton side effect, nondeterministic lifetime, broad unrelated composition rewrite]
```

### Slice 03 — Final architecture/evidence audit

```yaml
slice_id: S186-03
profile: FULL_PATH
owner: Senior Tester
secondary_reviewers: [Senior System Architect, Senior Requirement Engineer, Senior Documentation Engineer]
affected_files: [tests/architecture/**, tests/infrastructure/test_composition.py, .tiny-swarm-world/evidence/solid-di-container/**, documentation/arc42/**]
affected_modules: [composition architecture and DI evidence]
affected_contracts: [no global runtime resolve, explicit bindings, issue completion evidence]
dependencies: [S186-02]
parallel_group: SERIAL-CHAIN
file_locks: [tests/architecture/**, tests/infrastructure/test_composition.py, .tiny-swarm-world/evidence/solid-di-container/**, documentation/arc42/**]
contract_locks: [explicit-composition-binding-contract]
architecture_locks: [composition-root-ownership, no-global-runtime-resolve]
quality_gates:
  targeted: [git diff --check, python3 tools/quality_gate.py test, python3 tools/quality_gate.py arch-tests]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: synchronize verified final status
  adr: record any required decision reference; do not invent one
stop_conditions: [unverified audit, open matrix row, failed gate, false no-op claim, unobservable external result]
```

## Parallel Execution

- Can this workflow run in parallel? No; it is the final chain step and owns
  composition/architecture surfaces.
- Conflicting workflows: every workflow that changes composition or runtime
  dependency construction.
- Shared files: `composition.py`, `composition_lxc_runtimes.py`, infrastructure
  wiring and architecture tests.
- Shared infrastructure: none in local verification.
- Requires isolated worktree: yes.
- Requires serialized live validation: yes, if authorized.
- Merge-order constraints: #192 -> #186; no later chain step exists.

## Automatic Work Distribution Policy

`workflow execute` analyzes backend, frontend, tests, runtime, documentation,
quality, architecture and security streams per slice; uses real subagents or
records role fallback and requires distribution/consolidation evidence under
`.codex/evidence/`. Overlapping files, unclear architecture, contradictory
requirements, mandatory order, generated conflicts, unclear secrets and
weakened guards forbid parallelization. Codex remains final integration owner.

## Git Worktree Execution Rule

Use isolated worktrees and `<workflow-branch>-slice-<number>-<stream>` branches.
Workers verify branch and locks, do not merge and stay within allowed scope.

## Role and Ownership Map

Requirement: Senior Requirement Engineer. Architecture/ADR escalation: Senior
System Architect. Python composition: Senior Python Automation Developer.
Tests/evidence: Senior Tester. Docs: Senior Documentation Engineer. Order/locks:
Senior Execution Orchestrator.

## Issue Completion Discipline

- Requirement matrix path: `.tiny-swarm/evidence/solid-di-container/requirement_matrix.md`.
- Required evidence path: `.tiny-swarm/evidence/solid-di-container/`.
- Required evidence files: `requirement_matrix.md`, `implementation_summary.md`, `changed_files.md`, `test_results.md`, `remaining_risks.md`, `acceptance_checklist.md`, plus Three-Amigos and before/after dependency map under `.tiny-swarm-world/evidence/solid-di-container/`.
- Requirement Lead review: S186-01.
- System Architect Reviewer review: S186-02, including any no-op decision.
- Test / Evidence Reviewer review: S186-03.
- Issue Completion Auditor review: final chain audit.
- DONE blocking rule: open, unverified or guessed requirements force
  `INCOMPLETE`, `BLOCKED` or `FAILED`; a no-op is valid only with complete
  evidence and independent review.

## Quality-Gate Expectations, Documentation, Stop Conditions and Handoff

Use the full local quality gate and focused composition/architecture tests from
`QUALITY.md`. Arc42 must distinguish verified explicit wiring, residual work
and no-op evidence. Stop on hidden resolution, lifetime ambiguity, broad
composition rewrite, missing evidence, failed gates or unobservable external
results. Done requires the repository-wide audit, explicit wiring/no-op proof,
architecture guard, evidence and auditor PASS.

## Arc42 Check Status

Current Arc42 composition-root and LXC architecture guidance was reviewed. The
workflow explicitly allows a verified no-op outcome and does not claim #186 is
implemented before its audit.
