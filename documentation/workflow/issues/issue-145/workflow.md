# Workflow: Issue #145 — Dependency-Aware Parallel Setup Phases

Workflow ID: `issue-145-20260809`

Workflow version: `issue-145-v1.0.0`

Status: `READY_FOR_WORKFLOW`

Authoring branch: `feature/workflow-issue-chain-163-156-197-152-144-146-147-148-145-151-153-20260809`

Source: [GitHub Issue #145](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/145)

## Executive Summary

Replace the fully serial setup phase list with conservative, dependency-aware,
bounded async phase groups while keeping safety-critical shared mutations
serial and preserving deterministic progress, evidence and failure reporting.

## Target Picture

`InstallationPlan` expresses explicit dependencies; the setup orchestrator
derives bounded parallel groups. Independent branches can overlap, blocked
dependents are reported clearly, completed branches retain evidence, and all
results are reassembled deterministically. No ad hoc threading or hard-coded
phase special cases are introduced.

## Clarification, Baseline and Scope

Upstream dependency: `I148-S07`. Verified baseline: the domain plan already
contains phases/dependencies while `SetupWorkflow` executes a serial sequence
and `composition.py` assembles the default services. Requirements are in the
[matrix](requirement-matrix.md). The exact safe groups are selected by S145-S01
and S145-S04. Confidence 92%, `READY_FOR_WORKFLOW`.

Python impact is `FULL_PATH`; Console/status UI is conditional because progress
ordering changes; browser React is forbidden. Live setup remains opt-in and is
not part of default verification.

## Ordered Slices

### Slice 01 — Freeze phase dependency graph

Purpose: inventory all phase dependencies, shared resources, live guards,
result/evidence contracts and safe single-computer/multi-node boundaries.

```yaml
slice_id: I145-S01
profile: FULL_PATH
owner: Senior Requirement Engineer
secondary_reviewers: [Senior System Architect, Senior Python Automation Developer, Senior Tester]
affected_files: [src/tiny_swarm_world/domain/preflight/installation_plan.py, src/tiny_swarm_world/application/services/setup/workflow.py, src/tiny_swarm_world/infrastructure/composition.py, tests/domain/preflight/test_preflight_result.py, tests/application/services/setup/test_setup_workflow.py]
affected_modules: [InstallationPlan, SetupWorkflow, composition setup assembly]
affected_contracts: ["phase dependency graph", "shared mutation inventory", "#152 phase evidence"]
dependencies: [I148-S07]
parallel_group: SERIAL-BASELINE
file_locks: [.tiny-swarm/evidence/issue-145/**]
contract_locks: [I145-phase-graph]
architecture_locks: [safety-critical-serial-boundary]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: review runtime/deployment/quality sections
  adr: review existing setup/safety decisions
stop_conditions: [cycle, missing dependency, shared mutation unknown, upstream audit missing]
```

Done criteria: graph is acyclic, phases are classified and candidate groups
are explicit without claiming implementation.

### Slice 02 — Model bounded phase groups

Purpose: extend or reuse the plan model to represent explicit independent
groups, maximum concurrency and serial barriers.

```yaml
slice_id: I145-S02
profile: FULL_PATH
owner: Senior System Architect
secondary_reviewers: [Senior Python Automation Developer, Senior Requirement Engineer, Senior Tester]
affected_files: [src/tiny_swarm_world/domain/preflight/installation_plan.py, tests/domain/preflight/test_preflight_result.py]
affected_modules: [InstallationPlan dependency/group model]
affected_contracts: [bounded groups, dependency validation, serial barriers]
dependencies: [I145-S01]
parallel_group: SERIAL-CONTRACT
file_locks: [src/tiny_swarm_world/domain/preflight/installation_plan.py, tests/domain/preflight/test_preflight_result.py]
contract_locks: [I145-plan-group-contract]
architecture_locks: [domain-no-asyncio-or-infrastructure]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.domain.preflight.test_preflight_result]
  required: []
documentation:
  arc42: update only verified plan concept
  adr: none unless a durable concurrency policy is introduced
stop_conditions: [domain imports runtime details, cyclic group model, unbounded default]
```

Done criteria: plan groups are deterministic, validated and compatible with
single-computer and future multi-node modes.

### Slice 03 — Implement bounded async phase scheduler

Purpose: execute ready groups concurrently with an explicit limit inside the
existing async setup model.

```yaml
slice_id: I145-S03
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior System Architect, Senior Tester, Resilience Engineering]
affected_files: [src/tiny_swarm_world/application/services/setup/workflow.py, tests/application/services/setup/test_setup_workflow.py]
affected_modules: [SetupWorkflow scheduler]
affected_contracts: [bounded async execution, cancellation, timeout and phase lifecycle]
dependencies: [I145-S02]
parallel_group: SERIAL-SCHEDULER
file_locks: [src/tiny_swarm_world/application/services/setup/workflow.py, tests/application/services/setup/test_setup_workflow.py]
contract_locks: [I145-async-scheduler]
architecture_locks: [asyncio-only-no-ad-hoc-threads]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.application.services.setup.test_setup_workflow]
  required: []
documentation:
  arc42: review runtime sequence if changed
  adr: none
stop_conditions: [ad hoc threading, unbounded gather, live guard bypass, phase contract broken]
```

Done criteria: scheduler runs only dependency-ready phases, respects limit and
retains existing status/error semantics.

### Slice 04 — Preserve serial safety boundaries

Purpose: ensure preflight, shared host/provider mutations, secrets and other
identified critical operations remain serialized with explicit barriers.

```yaml
slice_id: I145-S04
profile: FULL_PATH
owner: Senior System Architect
secondary_reviewers: [Senior Python Automation Developer, Senior DevOps Engineer, Senior Tester]
affected_files: [src/tiny_swarm_world/infrastructure/composition.py, src/tiny_swarm_world/application/services/setup/workflow.py, src/tiny_swarm_world/domain/preflight/installation_plan.py, tests/infrastructure/test_composition.py, tests/application/services/setup/test_setup_workflow.py]
affected_modules: [composition phase assembly, setup safety barriers]
affected_contracts: [serial shared mutation, LiveConsent, secret/bootstrap ordering]
dependencies: [I145-S03]
parallel_group: SERIAL-SAFETY
file_locks: [src/tiny_swarm_world/infrastructure/composition.py, src/tiny_swarm_world/application/services/setup/workflow.py, src/tiny_swarm_world/domain/preflight/installation_plan.py, tests/infrastructure/test_composition.py, tests/application/services/setup/test_setup_workflow.py]
contract_locks: [I145-safety-barriers]
architecture_locks: [live-consent-fail-closed, provider-boundary]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition]
  required: []
documentation:
  arc42: synchronize verified runtime/deployment consequence
  adr: stop if safety boundary changes require a new decision
stop_conditions: [shared mutation overlaps, secret ordering changes, consent bypass, unsafe live path]
```

Done criteria: safety-critical phases remain serial and the reason is encoded
in plan/scheduler tests.

### Slice 05 — Deterministic aggregation and branch failure reporting

Purpose: preserve branch context, block/skip dependents clearly, retain
completed evidence and make progress/results deterministic despite overlap.

```yaml
slice_id: I145-S05
profile: FULL_PATH
owner: Console/status UI Developer
secondary_reviewers: [Senior Python Automation Developer, Senior Tester, Senior System Architect]
affected_files: [src/tiny_swarm_world/application/services/setup/workflow.py, src/tiny_swarm_world/application/ports/progress/port_workflow_progress.py, src/tiny_swarm_world/infrastructure/adapters/ui/progress_trace_ui.py, tests/application/services/setup/test_setup_workflow.py]
affected_modules: [setup result aggregation and progress]
affected_contracts: [deterministic output, branch failure/blocked status, phase-group durations]
dependencies: [I145-S04]
parallel_group: SERIAL-REPORTING
file_locks: [src/tiny_swarm_world/application/services/setup/workflow.py, src/tiny_swarm_world/application/ports/progress/**, src/tiny_swarm_world/infrastructure/adapters/ui/progress_trace_ui.py, tests/application/services/setup/test_setup_workflow.py]
contract_locks: [I145-reporting-contract]
architecture_locks: [ui-adapter-boundary]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.application.services.setup.test_setup_workflow]
  required: []
documentation:
  arc42: runtime/evidence wording review
  adr: preserve console reporting decision
stop_conditions: [nondeterministic order, hidden blocked dependent, completed evidence lost, duration missing]
```

Done criteria: success, dependency blocking and branch failure are visible and
phase-group duration evidence is produced through #152.

### Slice 06 — Tests, performance evidence and full quality gate

Purpose: cover graph success, dependency blocking, branch failure, concurrency
limit, deterministic output and phase-group duration.

```yaml
slice_id: I145-S06
profile: FULL_PATH
owner: Senior Tester
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Senior Python Automation Developer, Console/status UI Developer]
affected_files: [tests/domain/preflight/test_preflight_result.py, tests/application/services/setup/test_setup_workflow.py, tests/infrastructure/test_composition.py, .tiny-swarm/evidence/issue-145/**]
affected_modules: [setup parallelism regression suite]
affected_contracts: [REQ-145-01 through REQ-145-08]
dependencies: [I145-S05]
parallel_group: SERIAL-QUALITY
file_locks: [tests/**, .tiny-swarm/evidence/issue-145/**]
contract_locks: [I145-quality-evidence]
architecture_locks: [mocked-no-live-setup]
quality_gates:
  targeted: [python3 tools/quality_gate.py test]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: final quality/runtime check
  adr: none
stop_conditions: [unsafe live path, group limit untested, blocked dependency hidden, quality failure unclassified]
```

Done criteria: all matrix requirements map to tests/evidence; no live install
run is claimed.

### Slice 07 — Evidence package and independent completion audit

Purpose: audit the full setup scheduler change and release #151.

```yaml
slice_id: I145-S07
profile: FULL_PATH
owner: Issue Completion Auditor
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Senior Tester, Console/status UI Developer]
affected_files: [.tiny-swarm/evidence/issue-145/**]
affected_modules: [issue completion evidence]
affected_contracts: [I145-completion-decision]
dependencies: [I145-S06]
parallel_group: SERIAL-AUDIT
file_locks: [.tiny-swarm/evidence/issue-145/**]
contract_locks: [I145-completion-decision]
architecture_locks: [auditor-independent-from-implementer]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: final reviewed status
  adr: final status
stop_conditions: [open requirement, unsafe parallel mutation, missing timing evidence, incomplete role review]
```

Done criteria: S07 is `PASS`; otherwise #151 cannot start.

## Dependency Graph

```text
I148-S07 -> I145-S01 -> I145-S02 -> I145-S03 -> I145-S04 -> I145-S05 -> I145-S06 -> I145-S07
```

## Parallel Execution

- Can this workflow run in parallel? No; scheduler, safety and reporting locks overlap.
- Conflicting workflows: setup orchestration, platform initialization,
  readiness and Console progress workflows.
- Shared files: InstallationPlan, SetupWorkflow, composition, progress and tests.
- Shared infrastructure: none by default; live setup is opt-in and serialized.
- Requires isolated worktree: yes for every slice.
- Requires serialized live validation: yes if later explicitly authorized; not run by default.
- Merge-order constraints: S07 precedes #151.

## Automatic Work Distribution Policy

Analyze backend/runtime/tests/docs/quality/architecture/security and Console
streams, use subagents or explicit fallback, and require distribution/
consolidation evidence. Never parallelize scheduler/plan/safety/reporting
files, generated outputs, unclear dependencies, shared migrations, secrets or
weakened guards. Codex integrates.

## Git Worktree Execution Rule

Every slice is isolated, branch/lock verified and non-live by default; no worker
merges directly.

## Issue Completion Discipline

- Requirement matrix path: `documentation/workflow/issues/issue-145/requirement-matrix.md`; execution copy `.tiny-swarm/evidence/issue-145/requirement_matrix.md`.
- Required evidence path: `.tiny-swarm/evidence/issue-145/`.
- Required evidence files: standard six plus graph, safety-barrier, reporting and phase-group timing evidence.
- Requirement Lead review: S01/S07.
- System Architect Reviewer review: S01/S02/S04/S07.
- Test / Evidence Reviewer review: S06/S07.
- Issue Completion Auditor review: S07.
- DONE blocking rule: any open or unverified requirement forces `INCOMPLETE`, `BLOCKED` or `FAILED`.

## Quality-Gate Expectations

Use plan/setup/composition tests, full `python3 tools/quality_gate.py quality`
and `git diff --check`; no live installation claim is implied.

## Documentation Synchronization and Arc42 Check Status

Arc42 runtime, deployment, quality, resilience and console sections were
reviewed. Update only verified scheduling consequences; no ADR is inferred.

## Stop Conditions and Uncertainty Escalation

Stop for dependency cycles, unsafe shared mutations, nondeterministic output,
unbounded concurrency, missing evidence or live consent ambiguity. Escalate to
System Architect, Resilience Engineering, Console reviewer or Senior Tester.

## Definition of Done

All eight requirements are implemented, tested and evidenced; safety barriers,
deterministic reporting and phase-group measurements are verified; S07 is `PASS`.

## Handoff to workflow execute

Promote #145 after I148-S07, execute S01–S07 serially and start #151 only after
the independent audit passes.
