# Workflow: Installation Observability And Console Status

## Metadata

```yaml
workflow_id: install-observability-console-status-v1.0.0
created: 2026-05-31
branch: feature/workflow-install-observability-20260529
status: COMPLETED
request: "Durchgehend Logging und GUI response fuer die komplette Installation; logging als Cross-Cutting-Modul mit lueckenloser Methoden-Nachverfolgung inklusive Exceptions; pruefen ob PortUI/self.ui und class logger ueberall genutzt werden; workflow create/execute with agents fortsetzen."
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

At workflow authoring time, the implementation only partially satisfied the
requested behavior.
`CommandExecuter` already uses `PortUI`, `self.ui = ui`, and a class logger, but
the canonical `setup run` and `platform` installation workflows do not flow
through that executor. `SetupWorkflow` still prints phase progress directly,
and platform steps report typed verification results without a continuous
console GUI update path.

This workflow records a no-skip implementation plan for continuous, redacted
installation observability. Slices 06-10 implement the method trace contract,
runtime integration, infrastructure adapters, and setup console lifecycle for
the current declared installation runtime scope. The clarified requirement is
not limited to setup
phase and platform step progress: the installation runtime path must also have
gapless method-flow tracing for covered methods, including exception paths.

The architecture-safe target is not to inject `PortUI`, `FactoryUI`,
`LoggerFactory`, or concrete loggers into every service. Logging is accepted as
a Shared cross-cutting observability module by ADR
`documentation/architecture/adr-cross-cutting-method-trace-logging.adoc`.
High-level workflow progress remains a separate application progress contract;
method-flow trace events must be correlated with it and projected to
centralized logging and safe terminal UI output through infrastructure
adapters.

## Requirement Clarification Gate

```yaml
gate: requirement_clarification
status: REVISED_BY_USER_CLARIFICATION
confidence: 0.95
decision: "Continue workflow with ADR-governed cross-cutting method trace logging; existing progress slices remain partial high-level status coverage."
```

Original request:

- Verify whether every installation operation uses `PortUI`, `self.ui = ui`,
  and `logging.getLogger(self.__class__.__name__)`.
- Ensure every step and failure is visible in the console GUI.
- Use central logging for every step.
- Insert logging and UI-visible trace output for every covered method in the
  installation runtime path, including exception paths, so program flow can be
  reconstructed without gaps.
- Treat logging as a cross-cutting module that requires ADR coverage.
- Continue `workflow create with agents` on a dedicated branch.
- Do not skip required implementation coverage.

Interpreted intent:

- The full installation path must emit continuous status events for phase
  start, step start, successful result, blocked result, failure, and final
  aggregate state.
- The full installation runtime path must emit method-level trace events for
  `entered`, `returned`, and `raised` outcomes.
- The console GUI must be driven from a single status channel.
- Logging must be consistent and redacted.
- The implementation must preserve hexagonal architecture.

Accepted assumptions:

- "Complete installation" means `setup run` plus its configured phases:
  preflight, platform init, platform reconcile, platform verify, artifacts,
  deployment, and final verification where present.
- "Continuous" means deterministic event emission at each workflow phase,
  verifiable installation step, and covered installation runtime method, not
  arbitrary polling.
- "Every method" means every method in the documented installation execution
  path unless a method has an explicit tested exemption. Expanding this to all
  pure domain value-object methods requires a later scope decision.
- `PortUI` remains the terminal status implementation, but application logic
  should depend on narrower progress or trace ports.
- Concrete class loggers, logger factories, curses behavior, and terminal UI
  adapters remain infrastructure concerns; domain code remains free of logging
  concerns.
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
- Whether terminal UI should expose detailed method tracing by default or only
  in a diagnostic mode after the cross-cutting trace module exists.

## Verified Baseline At Authoring

- Active branch verified: `feature/workflow-install-observability-20260529`.
- Existing `CommandExecuter` already imports `PortUI`, stores `self.ui = ui`,
  and uses `logging.getLogger(self.__class__.__name__)`.
- `AsyncCommandRunnerUI` and `SyncCommandRunnerUI` instantiate `CommandExecuter`
  with a concrete `PortUI`.
- `SetupWorkflow` currently prints progress via `_print_phase_progress()`.
- `PlatformInitWorkflow`, `PlatformReconcileWorkflow`, and related platform
  steps use typed `VerificationResult` contracts but do not emit `PortUI`
  updates.
- Slices 02-04 added a high-level `PortWorkflowProgress` contract plus setup
  and platform progress events. This remains partial status coverage, not
  complete method-flow trace coverage.
- Existing tests cover command executor UI updates, Linux UI status behavior,
  setup phase printing, and platform workflow stop behavior.
- Missing tests: setup-to-terminal UI integration, multi-command update order,
  logger configuration behavior, no-skip progress event coverage, no-skip
  method trace coverage, exception trace coverage, and trace redaction.

## Target Picture

After implementation, delivered through the completed slices and verified in
`documentation/workflow/execution-report.md`:

- `setup run` starts a terminal progress surface after live consent is accepted.
- Every setup phase emits start and terminal status events.
- Every platform workflow step emits start, apply result, verification result,
  and terminal status events.
- Every covered installation runtime method emits trace events for entry,
  normal return, and exception exit, or has an explicit tested exemption.
- Command-backed legacy execution continues to update `PortUI` through
  `CommandExecuter`.
- Modern setup/platform execution updates `PortUI` through a structured
  progress port and infrastructure adapter.
- Central logging records both safe high-level progress and safe method-flow
  trace events with correlation data.
- A failure must remain visible and must not be overwritten by later aggregate
  success.
- Downstream `not_run` phases are explicitly reported.
- Tests prove no workflow slice may skip required progress, method trace, or
  logging behavior.

## Architecture Direction

- Application services may emit structured progress events through an
  application port.
- Application services may participate in method tracing through an
  application trace port or composition-applied wrapper, not through concrete
  infrastructure logging imports.
- Infrastructure adapters translate progress and method trace events to
  `PortUI` and logging.
- Concrete UI adapters, curses behavior, `FactoryUI`, and `LoggerFactory`
  remain infrastructure concerns.
- Domain code must not import logging, UI, infrastructure, curses, command
  runners, or dependency wiring.
- `src/tiny_swarm_world/infrastructure/composition.py` remains the wiring root.
- `src/tiny_swarm_world/__main__.py` remains thin.
- ADR `documentation/architecture/adr-cross-cutting-method-trace-logging.adoc`
  governs the cross-cutting trace module and its redaction boundaries.

## Role Ownership

- Senior Requirement Engineer: acceptance granularity, non-goals, EPIC drift.
- Senior System Architect: hexagonal boundary and arc42 alignment.
- Senior Python Automation Developer: progress port, service integration,
  method trace port, wrapper behavior, and composition-safe wiring.
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
  - installation method trace contract
dependencies: []
parallel_group: serial-01
file_locks:
  - workflow-observability-requirements
contract_locks:
  - installation-progress-contract
  - installation-method-trace-contract
architecture_locks:
  - console-status-architecture-baseline
quality_gates:
  targeted:
    - git diff --check
  required:
    - git diff --check
documentation:
  arc42: review-required
  adr: superseded-by-cross-cutting-trace-adr
stop_conditions:
  - Continuous status granularity cannot be defined without guessing.
  - Documentation would claim implemented behavior before source changes exist.
```

Done criteria:

- The requirement states exactly which setup/platform transitions must emit
  progress.
- The clarified method trace requirement is recorded as ADR-governed scope
  before further adapter wiring.
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
  adr: not-required-for-high-level-progress-only
stop_conditions:
  - Application code would import infrastructure UI, FactoryUI, LoggerFactory, or curses.
  - Progress events allow raw command strings, stdout, stderr, secrets, tokens, or environment data.
```

Done criteria:

- A narrow progress port exists in `application/ports`.
- Events include workflow, phase, target, task, step, status, result, safe
  message, and optional recovery hint.
- Unsafe payload keys are rejected or cannot be represented.
- This slice remains high-level progress coverage only and does not claim
  method trace completion.

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
  adr: not-required-for-high-level-progress-only
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
- This slice remains high-level progress coverage only and does not claim
  method trace completion.

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
  adr: not-required-for-high-level-progress-only
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
- This slice remains high-level progress coverage only and does not claim
  method trace completion.

### Slice 05 - Cross-Cutting Method Trace ADR And Scope

```yaml
slice_id: "05"
profile: NORMAL_PATH
owner: Senior System Architect
secondary_reviewers:
  - Senior Requirement Engineer
  - Senior Tester
  - Senior Python Automation Developer
affected_files:
  - documentation/architecture/**
  - documentation/arc42/**
  - documentation/workflow/**
affected_modules:
  - architecture documentation
  - workflow governance
affected_contracts:
  - cross-cutting-method-trace-logging-adr
  - installation-method-trace-scope
dependencies:
  - "04"
parallel_group: serial-05
file_locks:
  - observability-adr-and-workflow-scope
contract_locks:
  - installation-method-trace-contract
architecture_locks:
  - shared-cross-cutting-observability-boundary
quality_gates:
  targeted:
    - git diff --check
  required:
    - git diff --check
documentation:
  arc42: required
  adr: required
stop_conditions:
  - Method-level trace logging is introduced without ADR coverage.
  - Workflow still claims phase or step progress is sufficient for lueckenlose tracing.
  - Documentation would claim method trace implementation before source changes exist.
```

Done criteria:

- ADR accepts logging as a Shared cross-cutting observability module.
- arc42 distinguishes high-level workflow progress from method-level trace
  logging.
- Workflow acceptance criteria require `entered`, `returned`, and `raised`
  coverage for every covered installation runtime method or an explicit tested
  exemption.
- Previous setup/platform progress slices are documented as partial status
  coverage, not complete observability.

### Slice 06 - Method Trace Port And Wrapper Contract

```yaml
slice_id: "06"
profile: NORMAL_PATH
owner: Senior Python Automation Developer
secondary_reviewers:
  - Senior System Architect
  - Senior Tester
affected_files:
  - src/tiny_swarm_world/application/ports/**
  - src/tiny_swarm_world/application/services/shared/**
  - tests/application/ports/**
  - tests/application/services/shared/**
affected_modules:
  - tiny_swarm_world.application.ports
  - tiny_swarm_world.application.services.shared
affected_contracts:
  - PortMethodTrace
  - MethodTraceEvent
  - method trace wrapper
dependencies:
  - "05"
parallel_group: serial-06
file_locks:
  - application-method-trace-contract
contract_locks:
  - method-trace-event-contract
architecture_locks:
  - application-port-boundary
quality_gates:
  targeted:
    - PYTHONPATH=src python3 -m unittest tests.application.ports.test_method_trace
    - PYTHONPATH=src python3 -m unittest tests.application.services.shared.test_method_trace_wrapper
  required:
    - python3 tools/quality_gate.py typecheck
documentation:
  arc42: not-required
  adr: implemented-by-slice-05
stop_conditions:
  - Trace events allow raw arguments, return payloads, command strings, stdout, stderr, tokens, paths, IPs, raw exception messages, or stack traces.
  - The trace wrapper swallows or changes original exception behavior.
  - Application code imports infrastructure logging, LoggerFactory, PortUI, FactoryUI, or curses.
```

Done criteria:

- A method trace port and safe event contract exist in application-owned code.
- Sync and async wrappers emit `entered` plus `returned` for normal execution.
- Sync and async wrappers emit `entered` plus `raised` for exceptions while
  preserving original exception propagation.
- Trace events contain only safe structural metadata and sanitized exception
  classification.

### Slice 07 - Installation Method Trace Coverage Guard

```yaml
slice_id: "07"
profile: NORMAL_PATH
owner: Senior Tester
secondary_reviewers:
  - Senior Python Automation Developer
  - Senior System Architect
affected_files:
  - tests/architecture/**
  - documentation/workflow/**
affected_modules:
  - architecture tests
  - workflow governance
affected_contracts:
  - installation method trace coverage manifest
  - trace exemption contract
dependencies:
  - "06"
parallel_group: serial-07
file_locks:
  - installation-method-trace-coverage
contract_locks:
  - method-trace-exemption-contract
architecture_locks:
  - architecture-test-boundary
quality_gates:
  targeted:
    - PYTHONPATH=src python3 -m unittest tests.architecture.test_installation_method_trace_coverage
  required:
    - python3 tools/quality_gate.py arch-tests
documentation:
  arc42: not-required
  adr: implemented-by-slice-05
stop_conditions:
  - A covered runtime method can be added without trace coverage or an explicit tested exemption.
  - Trace sink internals, logger factories, or terminal render loops recurse into self-tracing.
```

Done criteria:

- An explicit installation trace coverage manifest exists for setup, platform,
  command execution, composition-created installation objects, and trace/UI
  adapter boundaries.
- Static or reflective tests fail when an in-scope method lacks trace coverage
  or an explicit exemption.
- Exemptions are documented and limited to protocols, abstract declarations,
  trace sinks, logger factories, terminal render loops, and methods outside
  the installation runtime path.

### Slice 08 - Setup Platform And Command Method Trace Integration

```yaml
slice_id: "08"
profile: NORMAL_PATH
owner: Senior Python Automation Developer
secondary_reviewers:
  - Senior Tester
  - Senior System Architect
affected_files:
  - src/tiny_swarm_world/application/services/setup/**
  - src/tiny_swarm_world/application/services/platform/**
  - src/tiny_swarm_world/application/services/commands/command_executer/**
  - tests/application/services/setup/**
  - tests/application/services/platform/**
  - tests/application/services/commands/**
  - tests/architecture/**
affected_modules:
  - tiny_swarm_world.application.services.setup
  - tiny_swarm_world.application.services.platform
  - tiny_swarm_world.application.services.commands
affected_contracts:
  - setup method trace lifecycle
  - platform method trace lifecycle
  - command method trace lifecycle
dependencies:
  - "06"
  - "07"
parallel_group: serial-08
file_locks:
  - application-runtime-method-tracing
contract_locks:
  - installation-method-trace-contract
architecture_locks:
  - application-boundary
quality_gates:
  targeted:
    - PYTHONPATH=src python3 -m unittest tests.application.services.setup.test_setup_workflow
    - PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_platform_workflows
    - PYTHONPATH=src python3 -m unittest tests.application.services.commands.test_command_executer
    - PYTHONPATH=src python3 -m unittest tests.architecture.test_installation_method_trace_coverage
  required:
    - python3 tools/quality_gate.py typecheck
documentation:
  arc42: not-required
  adr: implemented-by-slice-05
stop_conditions:
  - Any covered setup, platform, or command method lacks entered, returned, or raised coverage.
  - Exception traces can be overwritten by later aggregate success.
  - Concrete infrastructure UI or logging imports are added to application services.
```

Done criteria:

- Setup, platform, and command execution runtime methods emit trace lifecycle
  events through the application trace contract.
- Refused, blocked, failed apply, failed verify, missing evidence, and raised
  exception paths emit `raised` or safe failure trace events before propagation
  or workflow result conversion.
- Existing high-level progress assertions remain intact.
- Architecture trace coverage tests pass with only explicit exemptions.

### Slice 09 - PortUI Logging And Trace Adapter Wiring

```yaml
slice_id: "09"
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
  - trace-to-PortUI adapter
  - trace-to-logging adapter
dependencies:
  - "06"
  - "08"
parallel_group: serial-09
file_locks:
  - infrastructure-progress-and-trace-adapters
contract_locks:
  - terminal-progress-adapter-contract
  - terminal-trace-adapter-contract
architecture_locks:
  - infrastructure-adapter-boundary
quality_gates:
  targeted:
    - PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.ui.test_linux_ui tests.infrastructure.test_composition
  required:
    - python3 tools/quality_gate.py lint
documentation:
  arc42: review-required
  adr: implemented-by-slice-05
stop_conditions:
  - UI thread lifecycle is controlled by application services.
  - LoggerFactory is imported into application services.
  - Trace logging records raw exception text, traceback, raw arguments, return payloads, commands, stdout, stderr, env, tokens, paths, or local IPs.
```

Done criteria:

- Infrastructure provides a composite progress and trace sink that updates
  `PortUI` and writes centralized logs.
- Logging adapter tests prove one safe log record per trace event and no
  `exc_info`, traceback, raw exception text, command output, or sensitive
  payload.
- Terminal adapter tests prove raised trace events remain visible and cannot be
  overwritten by later success-like events.
- Composition wires progress and trace sinks into setup/platform/command
  installation services.
- Non-interactive/test mode remains deterministic.

### Slice 10 - CLI Console Lifecycle

```yaml
slice_id: "10"
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
  - setup run trace correlation lifecycle
dependencies:
  - "08"
  - "09"
parallel_group: serial-10
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
  adr: implemented-by-slice-05
stop_conditions:
  - Entry point constructs concrete UI adapters directly instead of using composition.
  - Console UI starts before required live consent is accepted.
```

Done criteria:

- `setup run` starts and stops terminal status rendering through composition.
- Refused live consent does not start a live installation UI loop.
- Final aggregate status is success only when no failure, blocked, refused, or
  raised trace state occurred.
- Trace correlation is initialized at the composition or entry boundary without
  making `__main__.py` own concrete trace/logging internals.

### Slice 11 - Documentation And Quality Gate

```yaml
slice_id: "11"
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
  - no-skip method trace evidence
dependencies:
  - "10"
parallel_group: serial-11
file_locks:
  - observability-documentation-quality
contract_locks:
  - observability-acceptance-contract
architecture_locks:
  - arc42-observability-alignment
quality_gates:
  targeted:
    - git diff --check
    - PYTHONPATH=src python3 -m unittest tests.application.ports.test_method_trace tests.application.services.shared.test_method_trace_wrapper tests.architecture.test_installation_method_trace_coverage tests.application.services.commands.test_command_executer tests.application.services.setup.test_setup_workflow tests.application.services.platform.test_platform_workflows tests.infrastructure.adapters.ui.test_linux_ui tests.infrastructure.adapters.ui.test_command_runner_ui_failure_semantics tests.infrastructure.test_composition tests.test_package_entrypoint
  required:
    - python3 tools/quality_gate.py quality
documentation:
  arc42: required
  adr: review-required
stop_conditions:
  - Any required progress test is skipped.
  - Any required method trace coverage test is skipped.
  - Full quality gate fails or is not reported.
  - Documentation presents mocked behavior as live-verified installation success.
```

Done criteria:

- arc42 documents the structured progress path and cross-cutting method trace
  logging path.
- arc42 documents method trace logging as a Shared observability module
  governed by ADR.
- Tests prove setup/platform/command paths report progress and method traces
  without skips.
- Full quality gate result is recorded.

## Dependency Graph

```text
01 -> 02 -> 03
          -> 04 -> 05 -> 06 -> 07 -> 08 -> 09 -> 10 -> 11
```

## Verification Strategy

Targeted command set:

```bash
PYTHONPATH=src python3 -m unittest tests.application.ports.test_method_trace
PYTHONPATH=src python3 -m unittest tests.application.services.shared.test_method_trace_wrapper
PYTHONPATH=src python3 -m unittest tests.architecture.test_installation_method_trace_coverage
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
- Every covered installation runtime method has trace coverage for entered,
  returned, and raised events or an explicit tested exemption.
- Command executor status updates remain covered and redacted.
- Console GUI receives status and safe trace projection through `PortUI` via
  infrastructure adapter.
- Central logs receive the same safe progress and method trace lifecycle
  information.
- No required workflow test is skipped.
- No unsafe payload is logged, displayed, or persisted.
- Architecture checks keep domain independent and infrastructure isolated.
- `python3 tools/quality_gate.py quality` passes or the exact blocker is
  documented.

## Handoff To Workflow Execute

`workflow execute` may continue with Slice 05. Before any implementation write,
verify the active branch is still
`feature/workflow-install-observability-20260529`, verify the context pack is
fresh, and apply the slice metadata locks above.
