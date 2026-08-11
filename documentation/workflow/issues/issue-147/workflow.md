# Workflow: Issue #147 — Remove Duplicate Stack Verification and Lookups

Workflow ID: `issue-147-20260809`

Workflow version: `issue-147-v1.0.0`

Status: `READY_FOR_WORKFLOW`

Authoring branch: `feature/workflow-issue-chain-163-156-197-152-144-146-147-148-145-151-153-20260809`

Source: [GitHub Issue #147](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/147)

## Executive Summary

Make stack-apply verification single-pass per workflow step and reduce
repeated step-local Portainer/LXC/API lookups without introducing a long-lived
cache or changing deployment semantics.

## Target Picture

An apply step returns enough observed state for its normal post-apply path;
failure recovery distinguishes “apply failed but stack exists”, “does not
exist” and “lookup failed” without paying for a redundant full verification.
Lookup snapshots are step-scoped, explicitly invalidated and never suppress a
required refresh.

## Clarification, Baseline and Scope

Upstream dependency: `I146-S06`. Requirements: [matrix](requirement-matrix.md).
Verified targets include `ensure_service_stack.py`, Portainer HTTP adapter and
LXC Swarm runtime lookup methods. No live Portainer/LXC calls are permitted;
tests use mocks/fakes and #152 call-count evidence. Confidence 92%,
`READY_FOR_WORKFLOW`.

## Shared #152 performance evidence handoff

Use `documentation/process/performance-evidence-contract.md` and write
consumer evidence below `.tiny-swarm/evidence/issue-147/`. The stable segment
ID is `stack-apply-registration`; record API/registration lookup counters and
comparable baseline/new values without persisting raw responses or identities.
Mocked call counts are local contract evidence and do not claim live Portainer
or LXC performance.

## Ordered Slices

### Slice 01 — Freeze call graph and observed-state contract

Purpose: map success/failure lookup calls, verification retries, invalidation
events and required evidence before editing.

```yaml
slice_id: I147-S01
profile: FULL_PATH
owner: Senior Requirement Engineer
secondary_reviewers: [Senior System Architect, Senior Python Automation Developer, Senior Tester]
affected_files: [src/tiny_swarm_world/application/services/deployment/ensure_service_stack.py, src/tiny_swarm_world/infrastructure/adapters/clients/portainer_http_client.py, src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py, tests/application/services/deployment/test_ensure_service_stack.py]
affected_modules: [stack apply/verify and remote lookup path]
affected_contracts: [step-local observed state, failure classification, lookup inventory]
dependencies: [I146-S06]
parallel_group: SERIAL-BASELINE
file_locks: [.tiny-swarm/evidence/issue-147/**]
contract_locks: [I147-call-graph]
architecture_locks: [no-cross-invocation-cache]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: review runtime/deployment evidence
  adr: review existing deployment decisions
stop_conditions: [call graph incomplete, external state semantics unclear, upstream audit missing]
```

Done criteria: success/failure paths and required refresh points are explicit.

### Slice 02 — Remove redundant failure-path verification

Purpose: change `EnsureServiceStack` so apply-error recovery does not execute a
full verification pass that normal post-apply verification will repeat.

```yaml
slice_id: I147-S02
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior System Architect, Senior Tester]
affected_files: [src/tiny_swarm_world/application/services/deployment/ensure_service_stack.py, tests/application/services/deployment/test_ensure_service_stack.py]
affected_modules: [EnsureServiceStack]
affected_contracts: [single-pass failure recovery, unchanged result semantics]
dependencies: [I147-S01]
parallel_group: SERIAL-IMPLEMENTATION
file_locks: [src/tiny_swarm_world/application/services/deployment/ensure_service_stack.py, tests/application/services/deployment/test_ensure_service_stack.py]
contract_locks: [I147-failure-recovery]
architecture_locks: [application-service-contract]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_ensure_service_stack]
  required: []
documentation:
  arc42: no change unless verified runtime sequence changes
  adr: none
stop_conditions: [apply failure loses classification, normal verification skipped, duplicate verification remains]
```

Done criteria: the error path distinguishes existence/absence/lookup failure
and does not duplicate the full retry loop.

### Slice 03 — Introduce step-scoped observed-state snapshot

Purpose: reuse safe stack-registration data inside one apply step and define
explicit invalidation/refresh rules.

```yaml
slice_id: I147-S03
profile: FULL_PATH
owner: Senior System Architect
secondary_reviewers: [Senior Python Automation Developer, Senior Tester, Resilience Engineering]
affected_files: [src/tiny_swarm_world/application/services/deployment/ensure_service_stack.py, src/tiny_swarm_world/application/services/deployment/service_stack_plan.py, src/tiny_swarm_world/application/ports/clients/port_deployment_gateway.py, tests/application/services/deployment/test_ensure_service_stack.py]
affected_modules: [step-local stack state]
affected_contracts: [snapshot reuse, explicit invalidation, required refresh]
dependencies: [I147-S02]
parallel_group: SERIAL-STATE
file_locks: [src/tiny_swarm_world/application/services/deployment/ensure_service_stack.py, src/tiny_swarm_world/application/services/deployment/service_stack_plan.py, src/tiny_swarm_world/application/ports/clients/port_deployment_gateway.py, tests/application/services/deployment/test_ensure_service_stack.py]
contract_locks: [I147-step-snapshot]
architecture_locks: [no-persistent-external-state]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_ensure_service_stack]
  required: []
documentation:
  arc42: record verified state-lifetime semantics
  adr: none
stop_conditions: [snapshot crosses workflow invocation, stale data suppresses retry, mutable global cache]
```

Done criteria: state lifetime and invalidation are explicit in code/tests.

### Slice 04 — Reduce adapter/API lookup duplication

Purpose: reuse safe observed data across Portainer/LXC adapter layers without
changing port contracts or hiding a required remote refresh.

```yaml
slice_id: I147-S04
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior System Architect, Senior Tester]
affected_files: [src/tiny_swarm_world/infrastructure/adapters/clients/portainer_http_client.py, src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py, src/tiny_swarm_world/infrastructure/adapters/clients/lxc/services/lxc_portainer_http_client.py, tests/infrastructure/adapters/clients/test_portainer_http_client.py, tests/infrastructure/adapters/clients/test_lxc_swarm_runtime.py]
affected_modules: [Portainer/LXC stack lookup adapters]
affected_contracts: [lookup reuse, refresh/invalidation, API call-count reduction]
dependencies: [I147-S03]
parallel_group: SERIAL-ADAPTER
file_locks: [src/tiny_swarm_world/infrastructure/adapters/clients/portainer_http_client.py, src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py, src/tiny_swarm_world/infrastructure/adapters/clients/lxc/services/lxc_portainer_http_client.py, tests/infrastructure/adapters/clients/**]
contract_locks: [I147-adapter-lookup-contract]
architecture_locks: [adapter-owns-remote-transport]
quality_gates:
  targeted: [python3 tools/quality_gate.py test]
  required: []
documentation:
  arc42: no change unless adapter responsibility changes
  adr: none
stop_conditions: [remote state assumed durable, refresh suppressed, transport semantics altered]
```

Done criteria: safe step-local lookup reuse is measurable and required refresh
paths remain observable.

### Slice 05 — Call-count, stale-state and regression evidence

Purpose: assert expected lookup counts on success/failure, stale snapshot
refresh, unchanged workflow semantics and #152 measurement limits.

```yaml
slice_id: I147-S05
profile: FULL_PATH
owner: Senior Tester
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Senior Python Automation Developer]
affected_files: [tests/application/services/deployment/test_ensure_service_stack.py, tests/infrastructure/adapters/clients/test_portainer_http_client.py, tests/infrastructure/adapters/clients/test_lxc_swarm_runtime.py, .tiny-swarm/evidence/issue-147/**]
affected_modules: [stack verification regression tests]
affected_contracts: [REQ-147-01 through REQ-147-07]
dependencies: [I147-S04]
parallel_group: SERIAL-QUALITY
file_locks: [tests/**, .tiny-swarm/evidence/issue-147/**]
contract_locks: [I147-quality-evidence]
architecture_locks: [mocked-remote-state]
quality_gates:
  targeted: [python3 tools/quality_gate.py test]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: quality/evidence check
  adr: none
stop_conditions: [call counts not deterministic, stale data hides retry, live API required, gate unclassified]
```

Done criteria: all success/failure and stale-state cases pass and evidence is
recorded as local/mocked rather than live.

### Slice 06 — Evidence package and independent completion audit

Purpose: audit the call-count reduction, safety and unchanged semantics before
starting #148.

```yaml
slice_id: I147-S06
profile: FULL_PATH
owner: Issue Completion Auditor
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Senior Tester]
affected_files: [.tiny-swarm/evidence/issue-147/**]
affected_modules: [issue completion evidence]
affected_contracts: [I147-completion-decision]
dependencies: [I147-S05]
parallel_group: SERIAL-AUDIT
file_locks: [.tiny-swarm/evidence/issue-147/**]
contract_locks: [I147-completion-decision]
architecture_locks: [auditor-independent-from-implementer]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: final reviewed status
  adr: final status
stop_conditions: [open requirement, persistent cache, missing call-count evidence, changed semantics]
```

Done criteria: S06 is `PASS`; only then #148 may start.

## Dependency Graph

```text
I146-S06 -> I147-S01 -> I147-S02 -> I147-S03 -> I147-S04 -> I147-S05 -> I147-S06
```

## Parallel Execution

- Can this workflow run in parallel? No; observed-state and adapter contracts
  require ordering.
- Conflicting workflows: deployment stack, Portainer, LXC runtime or caching
  changes touching the same files.
- Shared files: EnsureServiceStack, deployment gateway, adapter tests and #152 evidence.
- Shared infrastructure: mocked remote/API doubles only.
- Requires isolated worktree: yes for every slice.
- Requires serialized live validation: live validation is prohibited by default.
- Merge-order constraints: S06 precedes #148.

## Automatic Work Distribution Policy

Analyze backend/runtime/tests/quality/architecture/security streams; frontend is
not applicable. Use subagents or documented fallback and distribution/
consolidation evidence. Do not parallelize state contracts, shared adapters,
generated files, ambiguous invalidation, secrets or safety guards. Codex
consolidates.

## Git Worktree Execution Rule

Every slice is isolated, lock-verified and non-live; no worker merges directly.

## Issue Completion Discipline

- Requirement matrix path: `documentation/workflow/issues/issue-147/requirement-matrix.md`; execution copy `.tiny-swarm/evidence/issue-147/requirement_matrix.md`.
- Required evidence path: `.tiny-swarm/evidence/issue-147/`.
- Required evidence files: standard six plus call graph, invalidation and call-count evidence.
- Requirement Lead review: S01/S06.
- System Architect Reviewer review: S01/S03/S04/S06.
- Test / Evidence Reviewer review: S05/S06.
- Issue Completion Auditor review: S06.
- DONE blocking rule: any open or unverified requirement forces `INCOMPLETE`, `BLOCKED` or `FAILED`.

## Quality-Gate Expectations

Use deployment/adapter tests, full `python3 tools/quality_gate.py quality` and
`git diff --check`; no live remote claim.

## Documentation Synchronization and Arc42 Check Status

Arc42 runtime/deployment/quality sections and existing deployment decisions
were reviewed. Document only verified step-local state semantics.

## Stop Conditions and Uncertainty Escalation

Stop for stale-state risk, unknown API ownership, call-count ambiguity,
semantic regression or missing evidence. Escalate architecture/resilience to
the System Architect and tests to the Senior Tester.

## Definition of Done

All seven requirements, call-count evidence, stale-refresh tests, local gates
and issue evidence are complete; S06 is `PASS`.

## Handoff to workflow execute

Promote #147 after I146-S06 and execute all six slices serially before #148.
