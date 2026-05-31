# Workflow: Installation Observability And Console Status

## Metadata

```yaml
workflow_id: install-observability-console-status-v1.0.0
created: 2026-05-31
branch: feature/workflow-install-observability-20260529
status: READY_FOR_EXECUTION
request: "Durchgehend Logging und GUI response fuer die komplette Installation; pruefen ob PortUI/self.ui und class logger ueberall genutzt werden; workflow create with agents fortsetzen."
process_strand: S3D
execution_profile: NORMAL_PATH
primary_boundary: Console/status UI
secondary_boundaries:
  - Shared
  - Platform
  - Setup
live_infrastructure_default: false
```

## Executive Summary

The current implementation only partially satisfies the requested behavior.
`CommandExecuter` already uses `PortUI`, `self.ui = ui`, and a class logger, but
the canonical `setup run` and `platform` installation workflows do not flow
through that executor. `SetupWorkflow` still prints phase progress directly,
and platform steps report typed verification results without a continuous
console GUI update path.

This workflow creates a no-skip implementation plan for continuous, redacted
installation progress across setup and platform phases. The architecture-safe
target is not to inject `PortUI` into every service. Instead, add a narrow
application progress port and wire an infrastructure adapter that translates
structured progress events to `PortUI` updates and centralized logging.

## Requirement Clarification Gate

```yaml
gate: requirement_clarification
status: PROCEED_WITH_ACCEPTED_ASSUMPTIONS
confidence: 0.86
decision: "Create workflow with documented assumptions; implementation must start with a progress contract before touching runtime services."
```

Original request:

- Verify whether every installation operation uses `PortUI`, `self.ui = ui`,
  and `logging.getLogger(self.__class__.__name__)`.
- Ensure every step and failure is visible in the console GUI.
- Use central logging for every step.
- Continue `workflow create with agents` on a dedicated branch.
- Do not skip required implementation coverage.

Interpreted intent:

- The full installation path must emit continuous status events for phase
  start, step start, successful result, blocked result, failure, and final
  aggregate state.
- The console GUI must be driven from a single status channel.
- Logging must be consistent and redacted.
- The implementation must preserve hexagonal architecture.

Accepted assumptions:

- "Complete installation" means `setup run` plus its configured phases:
  preflight, platform init, platform reconcile, platform verify, artifacts,
  deployment, and final verification where present.
- "Continuous" means deterministic event emission at each workflow phase and
  verifiable installation step, not arbitrary polling.
- `PortUI` remains the terminal status implementation, but application logic
  should depend on a narrower progress-reporting port.
- Class loggers are allowed in application and infrastructure services, but
  domain code remains free of logging concerns.
- Live LXD, Incus, Docker, Swarm, compose, or service bootstrap commands are
  not run during workflow authoring or default quality gates.

Non-goals:

- Browser UI, React frontend, web dashboard, or Kubernetes-first UI behavior.
- Expanding Windows UI behavior.
- Treating logs as verification evidence.
- Persisting raw command output, commands, stdout, stderr, environment
  payloads, tokens, passwords, Swarm join tokens, host paths, or local IPs.
- Running live infrastructure without explicit approval.

Open non-blocking questions:

- Whether a later heartbeat event is needed during long-running live commands.
- Whether run-specific log correlation IDs should become mandatory in a later
  workflow.

## Verified Baseline

- Active branch verified: `feature/workflow-install-observability-20260529`.
- Existing `CommandExecuter` already imports `PortUI`, stores `self.ui = ui`,
  and uses `logging.getLogger(self.__class__.__name__)`.
- `AsyncCommandRunnerUI` and `SyncCommandRunnerUI` instantiate `CommandExecuter`
  with a concrete `PortUI`.
- `SetupWorkflow` currently prints progress via `_print_phase_progress()`.
- `PlatformInitWorkflow`, `PlatformReconcileWorkflow`, and related platform
  steps use typed `VerificationResult` contracts but do not emit `PortUI`
  updates.
- Existing tests cover command executor UI updates, Linux UI status behavior,
  setup phase printing, and platform workflow stop behavior.
- Missing tests: setup-to-terminal UI integration, multi-command update order,
  logger configuration behavior, and no-skip progress event coverage.

## Target Picture

After implementation:

- `setup run` starts a terminal progress surface after live consent is accepted.
- Every setup phase emits start and terminal status events.
- Every platform workflow step emits start, apply result, verification result,
  and terminal status events.
- Command-backed legacy execution continues to update `PortUI` through
  `CommandExecuter`.
- Modern setup/platform execution updates `PortUI` through a structured
  progress port and infrastructure adapter.
- Central logging records the same safe event lifecycle with class-based
  loggers or a configured progress logger.
- A failure must remain visible and must not be overwritten by later aggregate
  success.
- Downstream `not_run` phases are explicitly reported.
- Tests prove no workflow slice may skip required progress and logging
  behavior.

## Architecture Direction

- Application services may emit structured progress events through an
  application port.
- Infrastructure adapters translate progress events to `PortUI` and logging.
- Concrete UI adapters, curses behavior, `FactoryUI`, and `LoggerFactory`
  remain infrastructure concerns.
- Domain code must not import logging, UI, infrastructure, curses, command
  runners, or dependency wiring.
- `src/tiny_swarm_world/infrastructure/composition.py` remains the wiring root.
- `src/tiny_swarm_world/__main__.py` remains thin.

## Role Ownership

- Senior Requirement Engineer: acceptance granularity, non-goals, EPIC drift.
- Senior System Architect: hexagonal boundary and arc42 alignment.
- Senior Python Automation Developer: progress port, service integration,
  composition-safe wiring.
- Senior Tester: regression strategy and no-skip evidence.
- Senior React Frontend Developer: no implementation scope; records no browser
  frontend involvement.
- Console/status UI skills: terminal adapter behavior and aggregate state.

## Slice Plan

### Slice 01 - Requirement And Baseline Audit

```yaml
slice_id: "01"
profile: NORMAL_PATH
owner: Senior Requirement Engineer
secondary_reviewers:
  - Senior System Architect
  - Senior Tester
affected_files:
  - documentation/workflow/**
  - documentation/epics/**
  - documentation/arc42/**
affected_modules:
  - workflow governance
  - setup requirements
  - console status UI requirements
affected_contracts:
  - installation progress contract
dependencies: []
parallel_group: serial-01
file_locks:
  - workflow-observability-requirements
contract_locks:
  - installation-progress-contract
architecture_locks:
  - console-status-architecture-baseline
quality_gates:
  targeted:
    - git diff --check
  required:
    - git diff --check
documentation:
  arc42: review-required
  adr: review-not-required
stop_conditions:
  - Continuous status granularity cannot be defined without guessing.
  - Documentation would claim implemented behavior before source changes exist.
```

Done criteria:

- The requirement states exactly which setup/platform transitions must emit
  progress.
- EPIC drift is documented as "partially implemented" until runtime code is
  changed.
- No live infrastructure commands are run.

### Slice 02 - Structured Progress Port

```yaml
slice_id: "02"
profile: NORMAL_PATH
owner: Senior Python Automation Developer
secondary_reviewers:
  - Senior System Architect
  - Senior Tester
affected_files:
  - src/tiny_swarm_world/application/ports/**
  - src/tiny_swarm_world/application/services/setup/**
  - tests/application/**
affected_modules:
  - tiny_swarm_world.application.ports
  - tiny_swarm_world.application.services.setup
affected_contracts:
  - PortWorkflowProgress
  - workflow progress event
dependencies:
  - "01"
parallel_group: serial-02
file_locks:
  - application-progress-port
contract_locks:
  - structured-progress-event-contract
architecture_locks:
  - application-port-boundary
quality_gates:
  targeted:
    - PYTHONPATH=src python3 -m unittest tests.application.services.setup.test_setup_workflow
  required:
    - python3 tools/quality_gate.py lint
documentation:
  arc42: review-required
  adr: not-required
stop_conditions:
  - Application code would import infrastructure UI, FactoryUI, LoggerFactory, or curses.
  - Progress events allow raw command strings, stdout, stderr, secrets, tokens, or environment data.
```

Done criteria:

- A narrow progress port exists in `application/ports`.
- Events include workflow, phase, target, task, step, status, result, safe
  message, and optional recovery hint.
- Unsafe payload keys are rejected or cannot be represented.

### Slice 03 - Setup Workflow Progress Integration

```yaml
slice_id: "03"
profile: NORMAL_PATH
owner: Senior Python Automation Developer
secondary_reviewers:
  - Senior Tester
  - Senior System Architect
affected_files:
  - src/tiny_swarm_world/application/services/setup/**
  - tests/application/services/setup/**
affected_modules:
  - tiny_swarm_world.application.services.setup
affected_contracts:
  - setup phase progress events
dependencies:
  - "02"
parallel_group: serial-03
file_locks:
  - setup-workflow-progress
contract_locks:
  - setup-progress-contract
architecture_locks:
  - setup-application-boundary
quality_gates:
  targeted:
    - PYTHONPATH=src python3 -m unittest tests.application.services.setup.test_setup_workflow
  required:
    - python3 tools/quality_gate.py typecheck
documentation:
  arc42: not-required
  adr: not-required
stop_conditions:
  - Phase failures can be overwritten by final success.
  - Downstream not_run phases are not emitted.
```

Done criteria:

- `SetupWorkflow` emits progress for refused, blocked, phase start, phase
  completed, phase failed, stopped, downstream `not_run`, and final completed.
- Existing CLI text behavior is either preserved behind the same port or
  intentionally replaced by the progress adapter.
- Tests prove no phase is skipped in status reporting.

### Slice 04 - Platform Workflow Progress Integration

```yaml
slice_id: "04"
profile: NORMAL_PATH
owner: Senior Python Automation Developer
secondary_reviewers:
  - Senior System Architect
  - Senior Tester
affected_files:
  - src/tiny_swarm_world/application/services/platform/**
  - tests/application/services/platform/**
affected_modules:
  - tiny_swarm_world.application.services.platform
affected_contracts:
  - platform step progress events
dependencies:
  - "02"
parallel_group: serial-04
file_locks:
  - platform-workflow-progress
contract_locks:
  - platform-progress-contract
architecture_locks:
  - platform-application-boundary
quality_gates:
  targeted:
    - PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_platform_workflows
  required:
    - python3 tools/quality_gate.py typecheck
documentation:
  arc42: review-required
  adr: not-required
stop_conditions:
  - Platform workflow continues after failed apply or failed verification.
  - Verification results are emitted without redaction review.
```

Done criteria:

- Platform pre-apply guard, mutating steps, direct verification, verify steps,
  blocked states, failed apply, failed verify, and completion emit progress.
- `LxcDockerInstallStep` and `LxcSwarmBootstrapStep` expose node-result
  summaries through safe progress events.
- Tests assert event order and terminal state preservation.

### Slice 05 - PortUI And Logging Adapter Wiring

```yaml
slice_id: "05"
profile: NORMAL_PATH
owner: Senior Python Automation Developer
secondary_reviewers:
  - Console/status UI skills
  - Senior Tester
  - Senior System Architect
affected_files:
  - src/tiny_swarm_world/infrastructure/adapters/ui/**
  - src/tiny_swarm_world/infrastructure/logging/**
  - src/tiny_swarm_world/infrastructure/composition.py
  - tests/infrastructure/**
affected_modules:
  - tiny_swarm_world.infrastructure.adapters.ui
  - tiny_swarm_world.infrastructure.logging
  - tiny_swarm_world.infrastructure.composition
affected_contracts:
  - progress-to-PortUI adapter
  - progress-to-logging adapter
dependencies:
  - "02"
parallel_group: serial-05
file_locks:
  - infrastructure-progress-adapters
contract_locks:
  - terminal-progress-adapter-contract
architecture_locks:
  - infrastructure-adapter-boundary
quality_gates:
  targeted:
    - PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.ui.test_linux_ui tests.infrastructure.test_composition
  required:
    - python3 tools/quality_gate.py lint
documentation:
  arc42: review-required
  adr: not-required
stop_conditions:
  - UI thread lifecycle is controlled by application services.
  - LoggerFactory is imported into application services.
```

Done criteria:

- Infrastructure provides a composite progress sink that updates `PortUI` and
  writes centralized logs.
- Composition wires the progress sink into setup/platform services.
- Non-interactive/test mode remains deterministic.

### Slice 06 - Command Executor No-Skip Hardening

```yaml
slice_id: "06"
profile: NORMAL_PATH
owner: Senior Tester
secondary_reviewers:
  - Senior Python Automation Developer
affected_files:
  - src/tiny_swarm_world/application/services/commands/command_executer/**
  - tests/application/services/commands/**
affected_modules:
  - tiny_swarm_world.application.services.commands
affected_contracts:
  - command execution status updates
dependencies:
  - "02"
parallel_group: serial-06
file_locks:
  - command-executor-status-tests
contract_locks:
  - command-executor-progress-contract
architecture_locks:
  - command-application-boundary
quality_gates:
  targeted:
    - PYTHONPATH=src python3 -m unittest tests.application.services.commands.test_command_executer
  required:
    - python3 tools/quality_gate.py test
documentation:
  arc42: not-required
  adr: not-required
stop_conditions:
  - Multi-command execution misses start, success, failure, or final status updates.
  - Failure status can be overwritten by closing success.
```

Done criteria:

- Tests cover multi-command event order.
- Tests cover logger calls for start, before runner, success, failure, status
  update, and final completion.
- Redaction assertions remain in place.

### Slice 07 - CLI Console Lifecycle

```yaml
slice_id: "07"
profile: NORMAL_PATH
owner: Senior Python Automation Developer
secondary_reviewers:
  - Console/status UI skills
  - Senior Tester
affected_files:
  - src/tiny_swarm_world/__main__.py
  - src/tiny_swarm_world/infrastructure/composition.py
  - tests/**
affected_modules:
  - tiny_swarm_world.__main__
  - tiny_swarm_world.infrastructure.composition
affected_contracts:
  - setup run terminal lifecycle
dependencies:
  - "03"
  - "04"
  - "05"
parallel_group: serial-07
file_locks:
  - cli-console-lifecycle
contract_locks:
  - setup-run-console-lifecycle
architecture_locks:
  - thin-entrypoint-boundary
quality_gates:
  targeted:
    - PYTHONPATH=src python3 -m unittest tests.test_package_entrypoint tests.infrastructure.test_composition
  required:
    - python3 tools/quality_gate.py test
documentation:
  arc42: review-required
  adr: not-required
stop_conditions:
  - Entry point constructs concrete UI adapters directly instead of using composition.
  - Console UI starts before required live consent is accepted.
```

Done criteria:

- `setup run` starts and stops terminal status rendering through composition.
- Refused live consent does not start a live installation UI loop.
- Final aggregate status is success only when no failure, blocked, or refused
  state occurred.

### Slice 08 - Documentation And Quality Gate

```yaml
slice_id: "08"
profile: NORMAL_PATH
owner: Senior Tester
secondary_reviewers:
  - Senior Documentation Engineer
  - Senior Requirement Engineer
  - Senior System Architect
affected_files:
  - documentation/**
  - tests/**
affected_modules:
  - documentation
  - tests
affected_contracts:
  - no-skip verification evidence
dependencies:
  - "07"
parallel_group: serial-08
file_locks:
  - observability-documentation-quality
contract_locks:
  - observability-acceptance-contract
architecture_locks:
  - arc42-observability-alignment
quality_gates:
  targeted:
    - git diff --check
    - PYTHONPATH=src python3 -m unittest tests.application.services.commands.test_command_executer tests.application.services.setup.test_setup_workflow tests.application.services.platform.test_platform_workflows tests.infrastructure.adapters.ui.test_linux_ui tests.infrastructure.adapters.ui.test_command_runner_ui_failure_semantics tests.infrastructure.test_composition tests.test_package_entrypoint
  required:
    - python3 tools/quality_gate.py quality
documentation:
  arc42: required
  adr: review-required
stop_conditions:
  - Any required progress test is skipped.
  - Full quality gate fails or is not reported.
  - Documentation presents mocked behavior as live-verified installation success.
```

Done criteria:

- arc42 documents the structured progress and logging path.
- Tests prove setup/platform/command paths report progress without skips.
- Full quality gate result is recorded.

## Dependency Graph

```text
01 -> 02 -> 03 -> 07 -> 08
          -> 04 -> 07
          -> 05 -> 07
          -> 06 -> 08
```

## Verification Strategy

Targeted command set:

```bash
PYTHONPATH=src python3 -m unittest tests.application.services.commands.test_command_executer
PYTHONPATH=src python3 -m unittest tests.application.services.setup.test_setup_workflow
PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_platform_workflows
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.ui.test_linux_ui
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.ui.test_command_runner_ui_failure_semantics
PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition tests.test_package_entrypoint
python3 tools/quality_gate.py quality
```

Default verification must not run live LXD, Incus, LXC, Docker, Docker Swarm,
compose, Portainer, Nexus, Jenkins, RabbitMQ, SonarQube, or service bootstrap
commands.

## Definition Of Done

- Every setup phase has a progress event for start and terminal state.
- Every platform step has a progress event for start and terminal state.
- Command executor status updates remain covered and redacted.
- Console GUI receives status through `PortUI` via infrastructure adapter.
- Central logs receive the same safe lifecycle information.
- No required workflow test is skipped.
- No unsafe payload is logged, displayed, or persisted.
- Architecture checks keep domain independent and infrastructure isolated.
- `python3 tools/quality_gate.py quality` passes or the exact blocker is
  documented.

## Handoff To Workflow Execute

`workflow execute` may start with Slice 01. Before any implementation write,
verify the active branch is still
`feature/workflow-install-observability-20260529`, verify the context pack is
fresh, and apply the slice metadata locks above.
