# Workflow: Issue #146 — Bounded Concurrent Per-Node Docker Preparation

Workflow ID: `issue-146-20260809`

Workflow version: `issue-146-v1.0.0`

Status: `READY_FOR_WORKFLOW`

Authoring branch: `feature/workflow-issue-chain-163-156-197-152-144-146-147-148-145-151-153-20260809`

Source: [GitHub Issue #146](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/146)

## Executive Summary

Run independent per-node Docker inspect/install/verify operations concurrently
with bounded concurrency, deterministic aggregation and explicit failure
isolation. Swarm-level and shared-host operations remain outside the issue.

## Target Picture

`LxcDockerInstallService` owns a per-node lifecycle coroutine and a bounded
scheduler. Results are reassembled by configured node order/name, preserve
manager/worker role evidence and report node, role, operation phase and the
original redacted error for failures.

## Clarification, Baseline and Scope

Upstream dependency: `I144-S08`. The current service loops node-by-node and
existing tests use deterministic runtime doubles. Requirements are in the
[matrix](requirement-matrix.md). Exact concurrency limit and failure model are
chosen by S146-S01/S146-S03. No live LXC/Docker command is authorized.
Confidence 93%, `READY_FOR_WORKFLOW`.

## Ordered Slices

### Slice 01 — Verify independence and concurrency contract

Purpose: prove node-local operations are independent, identify shared host
state, select a bounded limit and map evidence fields.

```yaml
slice_id: I146-S01
profile: FULL_PATH
owner: Senior System Architect
secondary_reviewers: [Senior Requirement Engineer, Senior Python Automation Developer, Senior Tester]
affected_files: [src/tiny_swarm_world/application/services/platform/incus/lxc_docker_install.py, src/tiny_swarm_world/application/ports/node_provider/port_container_docker_runtime.py, tests/application/services/platform/test_lxc_docker_install.py]
affected_modules: [LXC Docker runtime preparation]
affected_contracts: [node independence, bounded concurrency, role/error evidence]
dependencies: [I144-S08]
parallel_group: SERIAL-BASELINE
file_locks: [.tiny-swarm/evidence/issue-146/**]
contract_locks: [I146-node-lifecycle-contract]
architecture_locks: [node-local-only]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: review deployment/runtime concurrency constraints
  adr: stop if a durable scalability decision needs ADR
stop_conditions: [shared mutable host state, unbounded target set, role semantics absent]
```

Done criteria: an approved node lifecycle and explicit maximum concurrency are
recorded without broadening into platform-wide parallelism.

### Slice 02 — Extract per-node lifecycle coroutine

Purpose: implement inspect → install if needed → verify for one node with
isolated result/error context.

```yaml
slice_id: I146-S02
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior System Architect, Senior Tester]
affected_files: [src/tiny_swarm_world/application/services/platform/incus/lxc_docker_install.py, tests/application/services/platform/test_lxc_docker_install.py]
affected_modules: [per-node Docker lifecycle]
affected_contracts: [I146-node-lifecycle-contract]
dependencies: [I146-S01]
parallel_group: SERIAL-IMPLEMENTATION
file_locks: [src/tiny_swarm_world/application/services/platform/incus/lxc_docker_install.py, tests/application/services/platform/test_lxc_docker_install.py]
contract_locks: [I146-node-lifecycle]
architecture_locks: [application-service-depends-on-port]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_lxc_docker_install]
  required: []
documentation:
  arc42: no change unless responsibility changes
  adr: none
stop_conditions: [node lifecycle calls shared host operation, error loses node context, old serial behavior hidden]
```

Done criteria: one-node behavior remains equivalent and independently testable.

### Slice 03 — Add bounded concurrent scheduler

Purpose: execute per-node coroutines with an explicit semaphore/limit and
preserve cancellation/failure isolation.

```yaml
slice_id: I146-S03
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior System Architect, Senior Tester, Resilience Engineering]
affected_files: [src/tiny_swarm_world/application/services/platform/incus/lxc_docker_install.py, tests/application/services/platform/test_lxc_docker_install.py]
affected_modules: [bounded node scheduler]
affected_contracts: [maximum concurrency, cancellation and failure isolation]
dependencies: [I146-S02]
parallel_group: SERIAL-CONCURRENCY
file_locks: [src/tiny_swarm_world/application/services/platform/incus/lxc_docker_install.py, tests/application/services/platform/test_lxc_docker_install.py]
contract_locks: [I146-bounded-scheduler]
architecture_locks: [asyncio-only-no-live-parallelism]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_lxc_docker_install]
  required: []
documentation:
  arc42: record verified bounded-concurrency consequence
  adr: none unless durable global limit is decided
stop_conditions: [unbounded gather, shared host mutation overlap, cancellation leaks]
```

Done criteria: limit is configurable/testable and concurrent execution is
observable with deterministic doubles.

### Slice 04 — Deterministic aggregation and failure evidence

Purpose: reassemble out-of-order completions by configured order and include
node name, role, operation phase and original error classification.

```yaml
slice_id: I146-S04
profile: FULL_PATH
owner: Senior Tester
secondary_reviewers: [Senior Python Automation Developer, Senior System Architect]
affected_files: [src/tiny_swarm_world/application/services/platform/incus/lxc_docker_install.py, src/tiny_swarm_world/application/services/platform/docker_swarm_lxc_contract.py, tests/application/services/platform/test_lxc_docker_install.py]
affected_modules: [result aggregation and evidence]
affected_contracts: [stable result ordering, mixed success/failure, role evidence]
dependencies: [I146-S03]
parallel_group: SERIAL-AGGREGATION
file_locks: [src/tiny_swarm_world/application/services/platform/incus/lxc_docker_install.py, src/tiny_swarm_world/application/services/platform/docker_swarm_lxc_contract.py, tests/application/services/platform/test_lxc_docker_install.py]
contract_locks: [I146-result-evidence]
architecture_locks: [redacted-error-preservation]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_lxc_docker_install]
  required: []
documentation:
  arc42: quality/evidence review
  adr: none
stop_conditions: [nondeterministic output, missing failure context, raw secret/command evidence]
```

Done criteria: mixed outcomes and out-of-order completion tests pass and
aggregated workflow contracts remain compatible.

### Slice 05 — Performance evidence and regression gate

Purpose: measure bounded concurrency with deterministic timing doubles where
practical and run targeted/full local quality checks.

```yaml
slice_id: I146-S05
profile: FULL_PATH
owner: Senior Tester
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Senior Python Automation Developer]
affected_files: [tests/application/services/platform/test_lxc_docker_install.py, .tiny-swarm/evidence/issue-146/**]
affected_modules: [concurrency tests and performance evidence]
affected_contracts: ["#152 node segment", "local-only measurement"]
dependencies: [I146-S04]
parallel_group: SERIAL-QUALITY
file_locks: [tests/application/services/platform/test_lxc_docker_install.py, .tiny-swarm/evidence/issue-146/**]
contract_locks: [I146-quality-evidence]
architecture_locks: [mocked-runtime]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_lxc_docker_install]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: final concurrency/quality check
  adr: none
stop_conditions: [timing presented as universal, live node operation required, gate failure unclassified]
```

Done criteria: concurrency limit and mixed outcomes are evidenced; local gate
state is exact; no live nodes are touched.

### Slice 06 — Evidence package and independent completion audit

Purpose: audit the eight requirements and release #147.

```yaml
slice_id: I146-S06
profile: FULL_PATH
owner: Issue Completion Auditor
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Senior Tester]
affected_files: [.tiny-swarm/evidence/issue-146/**]
affected_modules: [issue completion evidence]
affected_contracts: [I146-completion-decision]
dependencies: [I146-S05]
parallel_group: SERIAL-AUDIT
file_locks: [.tiny-swarm/evidence/issue-146/**]
contract_locks: [I146-completion-decision]
architecture_locks: [auditor-independent-from-implementer]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: final reviewed status
  adr: final status
stop_conditions: [open requirement, unbounded concurrency, missing evidence, live claim]
```

Done criteria: S06 is `PASS`; otherwise #147 cannot start.

## Dependency Graph

```text
I144-S08 -> I146-S01 -> I146-S02 -> I146-S03 -> I146-S04 -> I146-S05 -> I146-S06
```

## Parallel Execution

- Can this workflow run in parallel? No; the scheduler and evidence contracts
  are sequential.
- Conflicting workflows: node-provider runtime, Docker installation or broad
  setup parallelization workflows.
- Shared files: LXC Docker service, runtime port, aggregation tests and #152 evidence.
- Shared infrastructure: mocked runtime only; no live nodes.
- Requires isolated worktree: yes for every slice.
- Requires serialized live validation: live validation is prohibited by default.
- Merge-order constraints: S06 precedes #147.

## Automatic Work Distribution Policy

Analyze backend/runtime/tests/quality/architecture/security streams; frontend is
not applicable. Use real subagents or documented fallback and require
distribution/consolidation evidence. Never parallelize shared scheduler or
aggregation files, unclear state ownership, generated evidence, or weakened
failure isolation. Codex consolidates.

## Git Worktree Execution Rule

Every slice is isolated and branch/lock verified; workers never merge directly
or execute Docker/LXC commands.

## Issue Completion Discipline

- Requirement matrix path: `documentation/workflow/issues/issue-146/requirement-matrix.md`; execution copy `.tiny-swarm/evidence/issue-146/requirement_matrix.md`.
- Required evidence path: `.tiny-swarm/evidence/issue-146/`.
- Required evidence files: standard six plus independence, concurrency-limit, mixed-outcome and timing evidence.
- Requirement Lead review: S01/S06.
- System Architect Reviewer review: S01/S03/S06.
- Test / Evidence Reviewer review: S04/S05/S06.
- Issue Completion Auditor review: S06.
- DONE blocking rule: open or unverified requirements force `INCOMPLETE`, `BLOCKED` or `FAILED`.

## Quality-Gate Expectations

Use the focused LXC Docker unit tests, full `python3 tools/quality_gate.py
quality` and `git diff --check`; classify all live states as not run.

## Documentation Synchronization and Arc42 Check Status

Arc42 deployment, quality and risk sections were reviewed. Update only
verified bounded-concurrency consequences; no global architecture decision is
assumed.

## Stop Conditions and Uncertainty Escalation

Stop for shared host state, unbounded concurrency, nondeterministic evidence,
role/error loss, live command requirements or quality ambiguity. Escalate to
System Architect, Resilience Engineering or Senior Tester.

## Definition of Done

All eight requirements are implemented/tested/evidenced, the concurrency limit
is bounded, output deterministic, no live command ran and S06 is `PASS`.

## Handoff to workflow execute

Promote #146 after I144-S08, run S01–S06 serially and start #147 only after
the independent audit passes.
