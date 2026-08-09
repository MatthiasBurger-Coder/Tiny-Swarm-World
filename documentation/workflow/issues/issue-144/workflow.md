# Workflow: Issue #144 — Non-Blocking Async Readiness Polling

Workflow ID: `issue-144-20260809`

Workflow version: `issue-144-v1.0.0`

Status: `READY_FOR_WORKFLOW`

Authoring branch: `feature/workflow-issue-chain-163-156-197-152-144-146-147-148-145-151-153-20260809`

Source: [GitHub Issue #144](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/144)

## Executive Summary

Remove blocking `time.sleep()` calls from install-path readiness orchestration
while preserving retry semantics, progress publication and safe boundaries for
blocking transports. The shared performance contract from #152 is mandatory.

## Target Picture

Nexus, SonarQube and Infisical readiness paths yield to the event loop between
attempts, retain explicit timeout/interval/attempt semantics and expose
progress during waits. Any unavoidable synchronous transport is isolated behind
a clearly named async boundary such as `asyncio.to_thread()`.

## Clarification, Baseline and Scope

Upstream dependency: `I152-S06`. Requirements: [matrix](requirement-matrix.md).
Verified targets include `wait_for_nexus_ready.py`,
`ensure_sonarqube_admin_access.py` and `infisical_bootstrap_http_client.py`;
the broader inventory must confirm all setup/deployment install-path loops.
Non-goals are nested event loops, busy waiting, ad hoc background threads,
live services and unrelated UI rewrites. Confidence 92%,
`READY_FOR_WORKFLOW`.

Python impact is `FULL_PATH`; frontend is `NOT_APPLICABLE`; console review is
conditional only for progress-event changes. Resilience requires equivalent
retry/failure semantics and redacted evidence.

## Ordered Slices

### Slice 01 — Inventory blocking loops and acceptance matrix

Purpose: scan all install-path callers, distinguish allowed adapter sleeps from
blocking orchestration and freeze timeout/retry/progress contracts.

```yaml
slice_id: I144-S01
profile: FULL_PATH
owner: Senior Requirement Engineer
secondary_reviewers: [Senior System Architect, Senior Python Automation Developer, Senior Tester]
affected_files: [src/tiny_swarm_world/application/services/nexus/wait_for_nexus_ready.py, src/tiny_swarm_world/application/services/nexus/ensure_nexus_admin_access.py, src/tiny_swarm_world/application/services/deployment/ensure_sonarqube_admin_access.py, src/tiny_swarm_world/infrastructure/adapters/clients/infisical_bootstrap_http_client.py, tests/**]
affected_modules: [install-path readiness inventory]
affected_contracts: ["blocking-loop inventory", "retry semantics", "#152 evidence segments"]
dependencies: [I152-S06]
parallel_group: SERIAL-BASELINE
file_locks: [.tiny-swarm/evidence/issue-144/**]
contract_locks: [I144-loop-inventory]
architecture_locks: [no-unrelated-sleep-removal]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: review runtime/resilience sections
  adr: review existing async/safety decisions
stop_conditions: ["unknown install-path caller", "retry semantics not observable", "#152 unavailable"]
```

Done criteria: every relevant loop is classified as change, adapter boundary
or non-scope and mapped to a later slice.

### Slice 02 — Define async readiness boundary and progress contract

Purpose: select the smallest async orchestration contract for retries,
timeouts, transport fallback and progress callbacks.

```yaml
slice_id: I144-S02
profile: FULL_PATH
owner: Senior System Architect
secondary_reviewers: [Senior Python Automation Developer, Senior Tester, Senior Requirement Engineer]
affected_files: [src/tiny_swarm_world/application/ports/progress/port_workflow_progress.py, src/tiny_swarm_world/application/services/**, tests/application/services/setup/test_setup_workflow.py]
affected_modules: [async readiness orchestration, workflow progress]
affected_contracts: [yielding wait, retry policy, progress between attempts]
dependencies: [I144-S01]
parallel_group: SERIAL-CONTRACT
file_locks: [src/tiny_swarm_world/application/ports/progress/**, src/tiny_swarm_world/application/services/**]
contract_locks: [I144-async-readiness-contract]
architecture_locks: [ports-before-adapters, no-nested-loop]
quality_gates:
  targeted: [python3 tools/quality_gate.py arch-tests]
  required: []
documentation:
  arc42: document verified resilience boundary if changed
  adr: stop if durable retry decision requires ADR
stop_conditions: [threading workaround, unclear cancellation/timeout, progress API cannot be tested]
```

Done criteria: downstream implementations have an explicit async contract and
no hidden sleep/cancellation semantics.

### Slice 03 — Convert Nexus readiness orchestration

Purpose: replace blocking readiness wait in `WaitForNexusReady` with native
async waiting or an explicit wrapper while preserving exceptions and attempts.

```yaml
slice_id: I144-S03
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior System Architect, Senior Tester]
affected_files: [src/tiny_swarm_world/application/services/nexus/wait_for_nexus_ready.py, src/tiny_swarm_world/application/services/nexus/bootstrap_nexus.py, tests/application/services/nexus/test_bootstrap_nexus.py, tests/application/services/artifacts/test_artifact_service_exports.py]
affected_modules: [Nexus bootstrap/readiness]
affected_contracts: [Nexus retry equivalence, async wait, redacted failure]
dependencies: [I144-S02]
parallel_group: P144-SERVICE-CONVERSIONS
file_locks: [src/tiny_swarm_world/application/services/nexus/**, tests/application/services/nexus/**, tests/application/services/artifacts/test_artifact_service_exports.py]
contract_locks: [I144-async-readiness-contract, I144-nexus-api]
architecture_locks: [application-async-orchestration]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.application.services.nexus.test_bootstrap_nexus]
  required: []
documentation:
  arc42: no change unless runtime sequence changes materially
  adr: none
stop_conditions: [sync callers broken without boundary, retry semantics altered, time.sleep remains in install path]
```

Done criteria: Nexus tests cover readiness, failure, retries and event-loop
yield behavior with no live service.

### Slice 04 — Convert SonarQube readiness/admin orchestration

Purpose: make availability/authentication retry waits non-blocking while
keeping credential redaction and status semantics intact.

```yaml
slice_id: I144-S04
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior System Architect, Senior Tester]
affected_files: [src/tiny_swarm_world/application/services/deployment/ensure_sonarqube_admin_access.py, tests/application/services/deployment/test_ensure_sonarqube_admin_access.py]
affected_modules: [SonarQube admin readiness]
affected_contracts: [async retry, credential-safe evidence, access state]
dependencies: [I144-S02]
parallel_group: P144-SERVICE-CONVERSIONS
file_locks: [src/tiny_swarm_world/application/services/deployment/ensure_sonarqube_admin_access.py, tests/application/services/deployment/test_ensure_sonarqube_admin_access.py]
contract_locks: [I144-async-readiness-contract, I144-sonarqube-api]
architecture_locks: [no-credential-leak]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_ensure_sonarqube_admin_access]
  required: []
documentation:
  arc42: review resilience/credential wording
  adr: none
stop_conditions: [password appears in task/evidence, synchronous caller ambiguity, changed access outcome]
```

Done criteria: availability and authentication waits yield, statuses remain
compatible and tests cover retry/failure behavior.

### Slice 05 — Isolate Infisical blocking transport fallback

Purpose: move readiness polling out of blocking install-path orchestration or
wrap the transport safely without changing bootstrap result semantics.

```yaml
slice_id: I144-S05
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior System Architect, Senior Tester, Resilience Engineering]
affected_files: [src/tiny_swarm_world/infrastructure/adapters/clients/infisical_bootstrap_http_client.py, src/tiny_swarm_world/application/services/deployment/ensure_infisical_bootstrap.py, tests/infrastructure/adapters/clients/test_infisical_bootstrap_http_client.py, tests/application/services/deployment/test_ensure_infisical_bootstrap.py]
affected_modules: [Infisical bootstrap readiness]
affected_contracts: [transport boundary, recovery attempt, bootstrap state]
dependencies: [I144-S02]
parallel_group: P144-SERVICE-CONVERSIONS
file_locks: [src/tiny_swarm_world/infrastructure/adapters/clients/infisical_bootstrap_http_client.py, src/tiny_swarm_world/application/services/deployment/ensure_infisical_bootstrap.py, tests/infrastructure/adapters/clients/test_infisical_bootstrap_http_client.py, tests/application/services/deployment/test_ensure_infisical_bootstrap.py]
contract_locks: [I144-async-readiness-contract, I144-infisical-api]
architecture_locks: [adapter-owns-transport, no-live-test]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_infisical_bootstrap_http_client]
  required: []
documentation:
  arc42: review runtime/resilience path
  adr: none
stop_conditions: [unbounded thread fallback, bootstrap state changes, real HTTP call in tests]
```

Done criteria: a named async boundary exists if transport remains sync; tests
cover retry/recovery/HTTP error behavior with mocks.

### Slice 06 — Publish progress during waits

Purpose: ensure at least one progress/event callback can run between two retry
waits and preserve deterministic status/evidence output.

```yaml
slice_id: I144-S06
profile: FULL_PATH
owner: Console/status UI Developer
secondary_reviewers: [Senior Python Automation Developer, Senior Tester, Senior System Architect]
affected_files: [src/tiny_swarm_world/application/ports/progress/port_workflow_progress.py, src/tiny_swarm_world/application/services/setup/workflow.py, src/tiny_swarm_world/infrastructure/adapters/ui/progress_trace_ui.py, tests/application/services/setup/test_setup_workflow.py]
affected_modules: [workflow progress and readiness events]
affected_contracts: [between-attempt event publication, readable status]
dependencies: [I144-S03, I144-S04, I144-S05]
parallel_group: SERIAL-PROGRESS
file_locks: [src/tiny_swarm_world/application/ports/progress/**, src/tiny_swarm_world/application/services/setup/workflow.py, src/tiny_swarm_world/infrastructure/adapters/ui/progress_trace_ui.py, tests/application/services/setup/test_setup_workflow.py]
contract_locks: [I144-progress-during-wait]
architecture_locks: [ui-adapter-only]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.application.services.setup.test_setup_workflow]
  required: []
documentation:
  arc42: review runtime/progress wording
  adr: preserve console reporting decision
stop_conditions: [event callback runs only after completion, UI hides blocked/failed state, cross-layer import]
```

Done criteria: deterministic async tests demonstrate callback interleaving and
the console/status contract remains clear.

### Slice 07 — Regression, performance evidence and quality gate

Purpose: run all targeted readiness tests, static sleep inventory and full gate;
record old/new or non-blocking timing evidence using #152.

```yaml
slice_id: I144-S07
profile: FULL_PATH
owner: Senior Tester
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Senior Python Automation Developer]
affected_files: [tests/application/services/nexus/test_bootstrap_nexus.py, tests/application/services/deployment/test_ensure_sonarqube_admin_access.py, tests/infrastructure/adapters/clients/test_infisical_bootstrap_http_client.py, tests/application/services/setup/test_setup_workflow.py, .tiny-swarm/evidence/issue-144/**]
affected_modules: [async readiness regression suite]
affected_contracts: [REQ-144-02 through REQ-144-08]
dependencies: [I144-S06]
parallel_group: SERIAL-QUALITY
file_locks: [tests/**, .tiny-swarm/evidence/issue-144/**]
contract_locks: [I144-quality-evidence]
architecture_locks: [mocked-services]
quality_gates:
  targeted: [python3 tools/quality_gate.py test, git diff --check]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: quality/resilience check
  adr: none
stop_conditions: [time.sleep remains in targeted install path, callback test missing, quality failure unclassified]
```

Done criteria: every loop is verified, evidence records measurement limits and
local/live states remain distinct.

### Slice 08 — Evidence package and independent completion audit

Purpose: audit all nine matrix requirements and release #146.

```yaml
slice_id: I144-S08
profile: FULL_PATH
owner: Issue Completion Auditor
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Senior Tester, Console/status UI Developer]
affected_files: [.tiny-swarm/evidence/issue-144/**]
affected_modules: [issue completion evidence]
affected_contracts: [I144-completion-decision]
dependencies: [I144-S07]
parallel_group: SERIAL-AUDIT
file_locks: [.tiny-swarm/evidence/issue-144/**]
contract_locks: [I144-completion-decision]
architecture_locks: [auditor-independent-from-implementer]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: final reviewed status
  adr: final status
stop_conditions: [open retry requirement, missing targeted evidence, hidden live claim, downstream scope leakage]
```

Done criteria: S08 is `PASS`; otherwise the chain stops before #146.

## Dependency Graph

```text
I152-S06 -> I144-S01 -> I144-S02 -> { I144-S03, I144-S04, I144-S05 }
{ I144-S03, I144-S04, I144-S05 } -> I144-S06 -> I144-S07 -> I144-S08
```

## Parallel Execution

- Can this workflow run in parallel? Partially: S03/S04/S05 may run in
  isolated worktrees after S02; S06 onward is serial.
- Conflicting workflows: any readiness/retry, progress or resilience workflow
  touching the same services/ports.
- Shared files: async contract, progress port, setup workflow and #152 schema.
- Shared infrastructure: mocked HTTP/client ports only; no live services.
- Requires isolated worktree: yes; mandatory for S03–S05.
- Requires serialized live validation: live validation is not applicable by default.
- Merge-order constraints: service conversions converge at S06; S08 precedes #146.

## Automatic Work Distribution Policy

Analyze backend, runtime, tests, docs, quality, architecture, security and
conditional Console streams for every slice; use subagents or documented
fallback, and require distribution/consolidation evidence. Never parallelize
shared async contracts, ambiguous cancellation, generated files, secrets,
contradictory requirements or weakened retries/guards. Codex integrates.

## Git Worktree Execution Rule

Every slice uses an isolated worktree; workers verify branch/locks, do not run
live services and do not merge directly.

## Issue Completion Discipline

- Requirement matrix path: `documentation/workflow/issues/issue-144/requirement-matrix.md`; execution copy `.tiny-swarm/evidence/issue-144/requirement_matrix.md`.
- Required evidence path: `.tiny-swarm/evidence/issue-144/` using #152 performance schema.
- Required evidence files: standard six plus loop inventory, callback interleaving and performance records.
- Requirement Lead review: S01/S08.
- System Architect Reviewer review: S02/S05/S08.
- Test / Evidence Reviewer review: S07/S08.
- Issue Completion Auditor review: S08.
- DONE blocking rule: any open or unverified requirement forces `INCOMPLETE`, `BLOCKED` or `FAILED`.

## Quality-Gate Expectations

Use focused Nexus/SonarQube/Infisical/setup tests, `python3 tools/quality_gate.py
quality` and `git diff --check`. Local gate is not live installation evidence.

## Documentation Synchronization and Arc42 Check Status

Arc42 runtime, resilience, quality and console reporting sections were
reviewed. Update only verified retry/progress behavior; no ADR is inferred.

## Stop Conditions and Uncertainty Escalation

Stop for retry semantic drift, event-loop blockage, transport boundary
ambiguity, credential leakage, missing #152 contract or unavailable quality
evidence. Escalate to System Architect/Tester/Console reviewer as appropriate.

## Definition of Done

All matrix rows have implementation and verification evidence, targeted and
full quality gates are classified, no live services ran, and S08 is `PASS`.

## Handoff to workflow execute

Promote #144 after I152-S06; execute S01/S02, the isolated S03–S05 streams,
then S06–S08 serially. Start #146 only after S08 `PASS`.
