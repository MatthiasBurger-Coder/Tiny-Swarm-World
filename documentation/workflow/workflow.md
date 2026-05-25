# Workflow: Stable Live Setup

## Executive Summary

This workflow creates the governed implementation plan for making the canonical
Tiny Swarm World live setup path stable from a Linux or WSL shell, including
the same shell context used by an IntelliJ terminal or run configuration.

The reported failure is not a Python dependency or Ruff installation problem.
The project quality gate passed. The live setup failed because preflight proved
only that the `multipass` executable exists, while the later `platform init`
phase needed a working Multipass daemon/socket and failed at
`platform:init:multipass-vms`.

Target command:

```bash
PYTHONPATH=src python3 -m tiny_swarm_world setup run --live
```

Target behavior:

- from a Linux/WSL IntelliJ terminal, the command either installs the selected
  stable local Multipass Docker Swarm environment or fails before mutation with
  actionable host-prerequisite diagnostics;
- Multipass socket, driver and access failures are reported during live
  readiness/preflight, not as a late `failed_to_apply` during VM creation;
- direct `platform init --live` receives the same host-readiness guard;
- default verification remains static or mocked and does not run Multipass,
  Docker Swarm, compose, netplan, `socat`, Portainer, Nexus, Jenkins,
  RabbitMQ, SonarQube, Swagger/NGINX, Vaultwarden, image build, image push or
  stack deployment commands.

No live infrastructure command may run during workflow creation. Future
workflow execution must keep live smoke validation separate from the default
quality gate.

## Target Picture

### Verified Baseline At Workflow Creation

- Active workflow version:

```text
stable-live-setup-v1.0.0
```

- Active workflow branch:

```bash
feature/workflow-stable-live-setup-20260525
```

- Root `AGENTS.md` defines Tiny Swarm World as Linux/WSL-only, Python
  automation, hexagonal architecture and Docker Swarm-first.
- Root `QUALITY.md` defines the full local quality gate:

```bash
python3 tools/quality_gate.py quality
```

- The reported local gate completed successfully:
  `lint`, `arch-lint`, `arch-tests`, `typecheck`, and `test` passed.
- The quality output still included noisy intentional test failure log lines
  and one unawaited coroutine warning; these are test hygiene issues, not the
  live setup root cause.
- Manual host evidence before live setup:

```text
multipass info -> cannot connect to the multipass socket
multipass get local.driver -> cannot connect to the multipass socket
```

- `setup run --live` passed setup preflight, then stopped during
  `platform init` with:

```text
platform:init:multipass-vms -> failed_to_apply
Apply failed for platform:init:multipass-vms: CommandExecutionFailed
```

- Local `.tiny-swarm-world` evidence was inspected after the first workflow
  draft. The directory is ignored by Git and remains local evidence only.
- The runner logs confirm two separate classes of failure:
  - `boom` entries are intentional test/mock noise from command-runner tests,
    not live infrastructure failures;
  - current live setup failures are `CommandExecutionError` events for
    `swarm-manager`, `swarm-worker-1` and `swarm-worker-2` with return code
    `2`, while stdout and stderr are redacted.
- `AsyncPortCommandRunner.log` shows the failing commands start in parallel
  and fail before useful stderr is persisted; the exact Multipass stderr is
  therefore still unavailable from the committed-safe evidence.
- `live-runs/setup-20260525-014558.log` shows an earlier full setup run that
  reached `completed`, including deployment verification and platform
  verification. The system is therefore not inherently impossible to install;
  the current failure is state/readiness/diagnostic handling that must become
  deterministic.
- Older local live-run logs show additional historical failure classes in
  later phases: Portainer admin verification, Nexus readiness/admin access and
  Jenkins image preparation. These are downstream hardening targets after the
  Multipass readiness boundary is fixed.
- The existing `documentation/workflow/**` content described the prior
  service-access/Vaultwarden workflow and is stale for this branch.

### Target Outcome

After workflow execution, the system should provide:

- a live-readiness preflight contract that distinguishes executable presence
  from Multipass daemon/socket/driver usability;
- fail-closed checks that block both `setup run --live` and direct
  `platform init --live` before mutating commands when host runtime access is
  unavailable;
- Multipass init command templates that do not treat "cannot connect to
  Multipass" as "VM does not exist";
- safe failure classification for known host-runtime failures without
  exposing raw stdout, stderr, commands, tokens, passwords, local IPs or
  user-specific paths;
- endpoint and WSL/localhost strategy captured through ports/configuration
  rather than adapter shortcuts;
- credential and setup profile behavior aligned with the autonomous runnable
  setup EPIC;
- static/mocked tests that reproduce the reported failure shape;
- synchronized user guide, troubleshooting, arc42 and workflow documentation;
- optional live smoke instructions that require explicit user approval and
  redacted evidence.

## Requirement Clarification Record

Original request, normalized:

```text
Analyze the problem from the shown terminal session. Then create a workflow
with subagents. Goal: when this command is run from IntelliJ,
PYTHONPATH=src python3 -m tiny_swarm_world setup run --live, a stable
environment should be installed and the shown errors should disappear.
```

Interpreted intent:

- Create a new active workflow on a dedicated branch.
- Use delegated subagent review.
- Plan changes that make live setup reliable and diagnosable from the
  supported Linux/WSL execution context.
- Treat IntelliJ as an IDE shell/runner surface that must use the same
  Linux/WSL interpreter, working directory and environment as the terminal.

Change type:

- FULL_PATH workflow creation for setup preflight, platform readiness,
  command catalog behavior, diagnostics, endpoint strategy, credentials,
  deployment readiness, tests and documentation.

Affected process strand:

- Autonomous runnable setup and live platform/deployment readiness.

Affected architecture area:

- Domain preflight configuration and status concepts.
- Application preflight service, setup orchestration and platform workflow
  guards.
- Infrastructure host probe and command runner/adapters.
- YAML command catalogs under `infra/config`.
- Composition root wiring.
- Console/status UI text only if recovery messages change.
- Documentation, arc42, EPIC and workflow context pack.

Explicit requirements:

- Analyze the reported terminal failure.
- Create a workflow with subagents.
- Make `PYTHONPATH=src python3 -m tiny_swarm_world setup run --live` stable
  for IntelliJ/Linux/WSL execution.
- Remove the observed late Multipass/socket failure mode.

Implicit requirements:

- Preserve Linux/WSL-only behavior and POSIX examples.
- Preserve live-consent controls.
- Do not run live infrastructure commands during workflow creation or default
  verification.
- Preserve hexagonal architecture.
- Keep infrastructure-specific Multipass, Docker, shell and YAML details in
  infrastructure adapters or configuration.
- Keep `src/tiny_swarm_world/infrastructure/composition.py` as the concrete
  wiring root.
- Keep the default quality gate static/mocked.
- Keep diagnostics redacted and actionable.
- Do not introduce Java, Maven, Spring Boot, browser React, Kubernetes-first
  behavior or external static-analysis CI.

Accepted assumptions:

- The manual Multipass socket failures were observed from the same Linux/WSL
  user context intended for IntelliJ execution.
- Socket/daemon/driver failures are host prerequisite failures and should
  block live setup before VM mutation.
- The workflow should plan detection and guided remediation, not automatic
  host repair.
- QEMU remains the expected Linux/WSL Multipass driver unless a later ADR
  changes the runtime model.
- Static preflight without live consent may remain static; accepted live
  preflight may use safe read-only runtime probes.
- Slice 06 establishes operator-supplied password values as the guided setup
  credential source of truth; the remaining committed default is the
  Vaultwarden external Swarm secret name, not a token value.

Non-goals:

- No live Multipass, Docker, Swarm, compose, netplan, `socat`, Portainer,
  Nexus, Jenkins, RabbitMQ, SonarQube, Swagger/NGINX, Vaultwarden, image build,
  image push or service bootstrap during workflow creation.
- No automatic installation of host packages.
- No automatic `sudo`, group membership, socket ownership, driver mutation or
  service restart without a later explicit approval and ADR where required.
- No Windows-native support expansion.
- No non-interactive live consent model unless a later ADR accepts it.
- No claim of live service health without observed evidence.

Risks:

- Preflight can continue to pass while live platform state is unusable if the
  Multipass readiness gap remains.
- Direct `platform init --live` currently bypasses setup preflight and needs
  its own readiness guard.
- The current Multipass init shell command conflates VM absence with
  Multipass socket failure.
- Over-redaction can hide useful failure classification; under-redaction can
  leak commands, paths, tokens or host details.
- IntelliJ run configurations without stdin can fail live consent even when
  the shell environment is otherwise correct.
- WSL localhost forwarding and hardcoded `http://localhost:9000` Portainer
  access can diverge from the actual Swarm node route.
- Desired inventory, service-access profile and documentation can drift unless
  synchronized before claiming a full stable setup.

Open questions delegated to slices:

- Whether endpoint resolution should prefer localhost, node IP, or a
  profile-specific operator override for each service.
- Whether legacy local compatibility defaults outside the guided setup path
  should become explicit development profile values or be replaced by ignored
  local secret sources.
- Whether optional guided host remediation should remain documentation-only or
  become a future approved live workflow.

Blocking questions:

- None for workflow creation. Any decision that would mutate host services,
  change consent semantics, change static secret policy, change endpoint
  routing or claim live health becomes a slice stop condition until governed.

Confidence level:

```text
88 percent
```

Decision:

```text
PROCEED_WITH_ACCEPTED_ASSUMPTIONS
```

## Problem Analysis

The failure chain is:

1. `ruff`, `mypy`, `import-linter` and project dependencies are installed in
   `.venv`, and the quality gate passes.
2. `multipass info` and `multipass get local.driver` both fail with:

```text
cannot connect to the multipass socket
```

3. `setup run --live` executes preflight.
4. Preflight checks `multipass` as a dependency using executable lookup. That
   proves only that the binary is available on `PATH`.
5. Preflight reports all checks passed, including existing service ports.
6. `platform init` starts `MultipassInitVms`.
7. `MultipassInitVms` executes
   `infra/config/multipass/command_multipass_init_repository_yaml.yaml`.
8. The first command runs `multipass info {vm_instance}` and treats every
   non-zero result as "VM missing", then attempts `multipass launch`.
9. Because the real problem is socket/daemon access, `multipass launch` also
   fails.
10. `AsyncPortCommandRunner` raises `CommandExecutionError`.
11. `CommandExecuter` wraps it as `CommandExecutionFailed`.
12. `PlatformInitWorkflow` records `failed_to_apply`.
13. `SetupWorkflow` stops later phases as `not_run`.

This is a host-readiness and orchestration-boundary problem, not a Ruff or
Python package problem.

Refinement from local logs:

- The exact latest failing shell command output is not visible because the
  command runner records a redacted diagnostic payload.
- The strongest supported conclusion is that the current failure occurs in the
  Multipass VM initialization path before later deployment phases can run.
- The logs do not prove "VM already exists" as the root cause. Existing or
  broken VMs remain a plausible operator-side condition, but the product issue
  is broader: setup must distinguish Multipass unreachable, daemon/socket
  access problems, driver problems, VM absence and existing bad VM state before
  mutation.
- The earlier successful live run is important regression evidence. Future
  implementation must preserve the ability to complete a full setup while
  making later reruns stable and diagnosable.

## Execution Profile

```text
executionProfile=FULL_PATH
reason=The workflow affects live setup behavior, host preflight, platform
guards, command catalog semantics, diagnostics, endpoint strategy, credentials,
tests, documentation, arc42 and optional live smoke evidence.
requiredFullReviews=Senior Requirement Engineer, Senior System Architect,
Senior Python Automation Developer, Senior React Frontend Developer,
Senior Tester
conditionalReviews=Senior DevOps Engineer, Senior Documentation Engineer,
Console/status UI skills, Security Sandbox Engineer, Platform Verification
requiredQualityChecks=git diff --check for workflow creation; targeted tests
per implementation slice; python3 tools/quality_gate.py quality before final
implementation release when practical
stopConditions=live commands required without explicit approval, architecture
boundary violation, raw evidence leakage, host mutation hidden in defaults,
consent model change without ADR, or live health claimed without evidence
```

## Subagent Review Summary

Senior Requirement Engineer:

- Confirmed EPIC drift: autonomous setup requires preflight to identify host
  prerequisite blockers before mutation, but the reported setup run reached
  `platform init`.
- Recommended fail-fast preflight and documented non-goals for automatic host
  repair.

Senior System Architect:

- Confirmed stale workflow context and required regeneration.
- Identified boundary risks around endpoint strategy, WSL forwarding,
  credential source of truth, desired inventory drift and live evidence.
- Reinforced hexagonal boundaries and composition-root ownership.

Senior Python Automation Developer:

- Located the core code path: preflight executable lookup, platform init
  Multipass command catalog, command runner exception wrapping and workflow
  `failed_to_apply`.
- Recommended live consent-gated Multipass readiness, direct platform guard,
  command-template correction and safe error classification.

Senior React Frontend Developer:

- Confirmed browser/React work is out of scope.
- Identified console/status UI as the only UI-relevant area if recovery text
  or terminal status states change.

Senior Tester:

- Recommended regression-first mocked tests for preflight boundary, setup
  phase stopping, direct platform guard, redacted diagnostics and command
  catalog behavior.
- Confirmed default quality gates must not run live infrastructure.

## Architecture Constraints

- Domain code may define preflight capabilities, categories, status values and
  safe result objects. It must not import subprocess, Multipass, Docker,
  Portainer, YAML parsers, file managers, logging setup or dependency
  injection containers.
- Application services may orchestrate ports and domain objects. They must not
  embed low-level shell, filesystem, HTTP, Docker, curses or Multipass details.
- Infrastructure adapters own executable lookup, safe read-only host probes,
  subprocess invocation, YAML parsing, filesystem access and external clients.
- Command catalog YAML may contain shell commands only within existing
  governed command catalog boundaries.
- `src/tiny_swarm_world/infrastructure/composition.py` remains the concrete
  wiring root.
- `src/tiny_swarm_world/__main__.py` remains thin: parse CLI, compose
  dependencies, invoke services, print summaries.
- IntelliJ support means documented Linux/WSL interpreter and terminal
  expectations, not Windows-native behavior.

## Python Automation Assessment

Likely implementation areas:

- `src/tiny_swarm_world/domain/preflight/preflight_configuration.py`
- `src/tiny_swarm_world/domain/preflight/preflight_check.py`
- `src/tiny_swarm_world/application/ports/preflight/port_host_preflight_probe.py`
- `src/tiny_swarm_world/application/services/platform/preflight_service.py`
- `src/tiny_swarm_world/application/services/setup/workflow.py`
- `src/tiny_swarm_world/application/services/platform/workflows.py`
- `src/tiny_swarm_world/application/services/multipass/multipass_init_vms.py`
- `src/tiny_swarm_world/infrastructure/adapters/preflight/host_preflight_probe.py`
- `src/tiny_swarm_world/infrastructure/adapters/command_runner/async_command_runner.py`
- `src/tiny_swarm_world/application/services/commands/command_executer/command_executer.py`
- `src/tiny_swarm_world/infrastructure/composition.py`
- `infra/config/multipass/command_multipass_init_repository_yaml.yaml`
- `infra/config/multipass/command_multipass_instance_status_yaml.yaml`

Expected design direction:

- Add a structured host runtime readiness result rather than returning raw
  stdout/stderr.
- Gate live readiness probes by accepted live consent or a mutating workflow
  guard.
- Keep static `--preflight` non-mutating and safe.
- Make direct `platform init --live` and setup-driven platform init share the
  same readiness decision.
- Classify Multipass socket, driver, permission and daemon access failures
  with safe identifiers and remediation text.

## Frontend Assessment

No browser frontend or React work is in scope.

Out of scope:

- `package.json`;
- JavaScript or TypeScript package manager lockfiles;
- React, Vite, TSX, JSX, browser routing or frontend state management;
- browser smoke claims without explicit live evidence.

Console/status UI work is conditional only if implementation changes terminal
status labels, summaries, recovery actions or failure classification text.

## Resilience Requirements

- Fail before mutation when host runtime prerequisites are unavailable.
- Distinguish `refused`, `blocked`, `resource_gated`, `failed_to_apply` and
  `failed_to_verify`.
- Do not retry host socket failures blindly.
- Do not turn daemon/socket failures into VM creation attempts.
- Preserve redaction while exposing safe failure classes.
- Keep optional live smoke evidence local, ignored and redacted.

## Ordered Slices

### Slice 01 - Governance Reset And Baseline

Purpose:

- Replace stale service-access workflow context with this stable-live-setup
  workflow.
- Record the problem analysis, accepted assumptions, scope, stop conditions
  and subagent findings.

```yaml
slice_id: "01"
profile: FULL_PATH
owner: Senior Workflow Architect
secondary_reviewers:
  - Senior Requirement Engineer
  - Senior System Architect
  - Senior Tester
affected_files:
  - documentation/workflow/workflow.md
  - documentation/workflow/context-pack.md
  - documentation/workflow/context-pack.json
  - documentation/workflow/execution-report.md
  - documentation/workflow/reports/01-subagent-review-summary.md
  - documentation/workflow/reports/02-problem-analysis.md
  - documentation/workflow/reports/03-local-log-evidence.md
affected_modules: []
affected_contracts:
  - workflow-context-pack
  - autonomous-setup-requirement-baseline
dependencies: []
parallel_group: A
file_locks:
  - documentation/workflow/**
contract_locks:
  - workflow-context-pack
architecture_locks:
  - planned-vs-implemented-documentation
quality_gates:
  targeted:
    - git diff --check
  required:
    - git diff --check
documentation:
  arc42: documentation/arc42/07_deployment_view.adoc; documentation/arc42/10_quality_requirements.adoc; documentation/arc42/11_risks_and_debt.adoc
  adr: documentation/architecture/adr-autonomous-setup-safety.adoc
stop_conditions:
  - Existing workflow context cannot be safely regenerated.
  - Workflow creation would need live infrastructure commands.
```

Allowed write scope:

- `documentation/workflow/**` only.

Done criteria:

- Workflow files describe stable live setup, not service-access/Vaultwarden
  implementation.
- Context pack records branch, roles, affected areas and governing hashes.
- `git diff --check` passes.

### Slice 02 - Regression Baseline And Test Output Hygiene

Purpose:

- Capture current failure behavior in mocked tests before changing runtime
  behavior.
- Classify quality-gate noise from intentional test failures and the unawaited
  coroutine warning.
- Preserve the local-log distinction between test/mock `boom`, redacted
  Multipass return-code failures and downstream service-readiness failures.

```yaml
slice_id: "02"
profile: FULL_PATH
owner: Senior Tester
secondary_reviewers:
  - Senior Python Automation Developer
  - Senior System Architect
affected_files:
  - tests/application/services/platform/test_preflight_service.py
  - tests/infrastructure/adapters/preflight/test_host_preflight_probe.py
  - tests/application/services/setup/test_setup_workflow.py
  - tests/application/services/platform/test_platform_workflows.py
  - tests/test_package_entrypoint.py
  - tests/application/services/commands/test_command_executer.py
  - tests/infrastructure/adapters/ui/test_command_runner_ui_failure_semantics.py
  - tests/infrastructure/adapters/command_runner/test_async_command_runner.py
affected_modules:
  - tests.application.services.platform
  - tests.infrastructure.adapters.preflight
  - tests.application.services.setup
  - tests.infrastructure.adapters.command_runner
affected_contracts:
  - setup-preflight-failure-boundary
  - test-output-hygiene
dependencies:
  - "01"
parallel_group: B
file_locks:
  - tests/application/services/platform/**
  - tests/infrastructure/adapters/preflight/**
  - tests/application/services/setup/**
  - tests/application/services/commands/**
  - tests/infrastructure/adapters/ui/**
  - tests/infrastructure/adapters/command_runner/**
  - tests/test_package_entrypoint.py
contract_locks:
  - setup-preflight-failure-boundary
  - redacted-diagnostics
architecture_locks:
  - default-gates-no-live-infra
quality_gates:
  targeted:
    - PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_preflight_service
    - PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.preflight.test_host_preflight_probe
    - PYTHONPATH=src python3 -m unittest tests.application.services.setup.test_setup_workflow
    - PYTHONPATH=src python3 -m unittest tests.test_package_entrypoint
  required:
    - python3 tools/quality_gate.py test
documentation:
  arc42: documentation/arc42/10_quality_requirements.adoc
  adr: ""
stop_conditions:
  - Tests would call real Multipass, Docker, Swarm, compose, netplan, socat or service bootstrap commands.
  - Tests require raw stdout, stderr, command strings, secrets or host-specific paths.
```

Allowed write scope:

- Tests and test fixtures for the affected setup/preflight/command runner
  behavior.

Done criteria:

- A mocked test proves that executable presence alone is insufficient for
  live setup.
- A mocked test proves live readiness failure stops before platform mutation.
- Intentional failure logs and coroutine warnings are either removed or
  explicitly classified without hiding real failures.

### Slice 03 - Live Multipass Readiness Preflight

Purpose:

- Add safe, consent-gated host runtime readiness checks for Multipass daemon,
  socket accessibility and expected driver state.
- Keep static `--preflight` static unless live consent is accepted.

```yaml
slice_id: "03"
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers:
  - Senior System Architect
  - Senior Tester
affected_files:
  - src/tiny_swarm_world/domain/preflight/preflight_configuration.py
  - src/tiny_swarm_world/domain/preflight/preflight_check.py
  - src/tiny_swarm_world/domain/preflight/__init__.py
  - src/tiny_swarm_world/application/ports/preflight/port_host_preflight_probe.py
  - src/tiny_swarm_world/application/services/platform/preflight_service.py
  - src/tiny_swarm_world/infrastructure/adapters/preflight/host_preflight_probe.py
  - tests/application/services/platform/test_preflight_service.py
  - tests/infrastructure/adapters/preflight/test_host_preflight_probe.py
affected_modules:
  - tiny_swarm_world.domain.preflight
  - tiny_swarm_world.application.ports.preflight
  - tiny_swarm_world.application.services.platform
  - tiny_swarm_world.infrastructure.adapters.preflight
affected_contracts:
  - live-host-runtime-readiness
  - multipass-driver-readiness
dependencies:
  - "02"
parallel_group: C
file_locks:
  - src/tiny_swarm_world/domain/preflight/**
  - src/tiny_swarm_world/application/ports/preflight/**
  - src/tiny_swarm_world/application/services/platform/preflight_service.py
  - src/tiny_swarm_world/infrastructure/adapters/preflight/**
  - tests/application/services/platform/test_preflight_service.py
  - tests/infrastructure/adapters/preflight/test_host_preflight_probe.py
contract_locks:
  - live-host-runtime-readiness
  - preflight-result-redaction
architecture_locks:
  - hexagonal-domain-independence
  - infrastructure-owns-subprocess
quality_gates:
  targeted:
    - PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_preflight_service
    - PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.preflight.test_host_preflight_probe
    - python3 tools/quality_gate.py arch-tests
  required:
    - python3 tools/quality_gate.py test
documentation:
  arc42: documentation/arc42/10_quality_requirements.adoc
  adr: documentation/architecture/adr-autonomous-setup-safety.adoc
stop_conditions:
  - Static preflight starts mutating host state.
  - Domain imports subprocess or infrastructure adapters.
  - Diagnostics expose raw command output, local paths, usernames or socket details beyond safe classifications.
```

Allowed write scope:

- Preflight domain/application/adapter code and focused tests.

Done criteria:

- Live preflight reports a failed check such as
  `RUNTIME-MULTIPASS-SOCKET` or equivalent when the socket is unavailable.
- Remediation points the operator to Multipass daemon/socket/driver repair
  without executing repair.
- Static preflight remains safe and non-mutating.

### Slice 04 - Platform Init Guard And Command Catalog Semantics

Purpose:

- Ensure direct `platform init --live` and setup-driven `platform init` share
  the same host-readiness guard.
- Update Multipass command templates so socket/daemon failure does not fall
  through to VM creation.

```yaml
slice_id: "04"
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers:
  - Senior DevOps Engineer
  - Senior Tester
affected_files:
  - src/tiny_swarm_world/__main__.py
  - src/tiny_swarm_world/application/services/multipass/multipass_init_vms.py
  - src/tiny_swarm_world/application/services/platform/workflows.py
  - src/tiny_swarm_world/application/services/setup/workflow.py
  - src/tiny_swarm_world/infrastructure/composition.py
  - infra/config/multipass/command_multipass_init_repository_yaml.yaml
  - infra/config/multipass/command_multipass_instance_status_yaml.yaml
  - tests/test_package_entrypoint.py
  - tests/application/services/platform/test_platform_workflows.py
  - tests/application/services/setup/test_setup_workflow.py
  - tests/infrastructure/adapters/command_runner/test_command_workflow_configuration.py
affected_modules:
  - tiny_swarm_world.application.services.multipass
  - tiny_swarm_world.application.services.platform
  - tiny_swarm_world.application.services.setup
  - tiny_swarm_world.infrastructure.composition
  - infra.config.multipass
affected_contracts:
  - platform-init-readiness-guard
  - multipass-init-command-catalog
dependencies:
  - "03"
parallel_group: D
file_locks:
  - src/tiny_swarm_world/__main__.py
  - src/tiny_swarm_world/application/services/multipass/**
  - src/tiny_swarm_world/application/services/platform/**
  - src/tiny_swarm_world/application/services/setup/**
  - src/tiny_swarm_world/infrastructure/composition.py
  - infra/config/multipass/**
  - tests/test_package_entrypoint.py
  - tests/application/services/platform/**
  - tests/application/services/setup/**
  - tests/infrastructure/adapters/command_runner/**
contract_locks:
  - platform-init-readiness-guard
  - command-catalog-safety
architecture_locks:
  - entrypoint-thinness
  - application-port-dependency
  - composition-root
quality_gates:
  targeted:
    - PYTHONPATH=src python3 -m unittest tests.test_package_entrypoint
    - PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_platform_workflows
    - PYTHONPATH=src python3 -m unittest tests.application.services.setup.test_setup_workflow
    - PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.command_runner.test_command_workflow_configuration
    - python3 tools/quality_gate.py arch-tests
  required:
    - python3 tools/quality_gate.py test
documentation:
  arc42: documentation/arc42/07_deployment_view.adoc; documentation/arc42/10_quality_requirements.adoc
  adr: documentation/architecture/adr-autonomous-setup-safety.adoc
stop_conditions:
  - Direct platform init can still run Multipass mutation after a failed readiness check.
  - VM absence cannot be distinguished from Multipass unreachable in tests.
  - Entry point starts constructing low-level infrastructure directly.
```

Allowed write scope:

- CLI dispatch, platform/setup orchestration, Multipass command catalog and
  directly related tests.

Done criteria:

- `setup run --live` and `platform init --live` both stop before mutation when
  Multipass readiness fails.
- Multipass command template handles daemon/socket failures separately from
  missing VM state.
- Workflow result remains redacted and actionable.

### Slice 05 - Endpoint, WSL Forwarding And IntelliJ Execution Contract

Purpose:

- Model operator endpoint selection and WSL localhost forwarding as explicit
  configuration/port behavior.
- Document IntelliJ execution as Linux/WSL shell use, not Windows-native
  support.

```yaml
slice_id: "05"
profile: FULL_PATH
owner: Senior System Architect
secondary_reviewers:
  - Senior DevOps Engineer
  - Senior Python Automation Developer
  - Senior Tester
affected_files:
  - src/tiny_swarm_world/domain/deployment/service_stack_contract.py
  - src/tiny_swarm_world/application/services/deployment/service_stack_plan.py
  - src/tiny_swarm_world/infrastructure/composition.py
  - documentation/user_guide/installation.adoc
  - documentation/user_guide/troubleshooting.adoc
  - documentation/arc42/07_deployment_view.adoc
  - tests/domain/deployment/test_service_stack_contract.py
  - tests/application/services/deployment/test_service_stack_plan.py
  - tests/infrastructure/test_composition.py
affected_modules:
  - tiny_swarm_world.domain.deployment
  - tiny_swarm_world.application.services.deployment
  - tiny_swarm_world.infrastructure.composition
affected_contracts:
  - endpoint-resolution
  - wsl-localhost-forwarding
  - intellij-linux-wsl-execution
dependencies:
  - "04"
parallel_group: E
file_locks:
  - src/tiny_swarm_world/domain/deployment/**
  - src/tiny_swarm_world/application/services/deployment/**
  - src/tiny_swarm_world/infrastructure/composition.py
  - documentation/user_guide/**
  - documentation/arc42/07_deployment_view.adoc
  - tests/domain/deployment/**
  - tests/application/services/deployment/**
  - tests/infrastructure/test_composition.py
contract_locks:
  - endpoint-resolution
  - operator-execution-context
architecture_locks:
  - deployment-boundary
  - no-windows-native-expansion
quality_gates:
  targeted:
    - PYTHONPATH=src python3 -m unittest tests.domain.deployment.test_service_stack_contract
    - PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_service_stack_plan
    - PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition
    - git diff --check
  required:
    - python3 tools/quality_gate.py test
documentation:
  arc42: documentation/arc42/07_deployment_view.adoc
  adr: documentation/architecture/adr-autonomous-setup-safety.adoc
stop_conditions:
  - Endpoint behavior depends on hardcoded host-specific IPs or user paths.
  - IntelliJ instructions add Windows-native support or PowerShell examples.
  - Service health is claimed from endpoint configuration alone.
```

Allowed write scope:

- Endpoint/configuration contracts, deployment planning tests and Linux/WSL
  documentation.

Done criteria:

- IntelliJ command expectations are documented as WSL/Linux terminal
  prerequisites.
- Portainer/service endpoint defaults are explicit and test-backed.
- Localhost forwarding gaps are diagnosed separately from service readiness.

### Slice 06 - Credential, Profile And Inventory Consistency

Purpose:

- Align setup manifest, desired inventory, service-access default profile and
  credential source behavior before claiming a stable full setup.

```yaml
slice_id: "06"
profile: FULL_PATH
owner: Senior System Architect
secondary_reviewers:
  - Senior Python Automation Developer
  - Senior Security Sandbox Engineer
  - Senior Tester
affected_files:
  - src/tiny_swarm_world/application/services/platform/preflight_service.py
  - src/tiny_swarm_world/domain/preflight/preflight_configuration.py
  - src/tiny_swarm_world/domain/preflight/setup_manifest.py
  - src/tiny_swarm_world/domain/deployment/service_stack_contract.py
  - src/tiny_swarm_world/infrastructure/composition.py
  - infra/config/inventory/**
  - infra/config/compose/service-access/docker-compose.yml
  - documentation/epics/autonomous-runnable-setup.md
  - documentation/epics/service-access-dashboard-vaultwarden.md
  - documentation/arc42/11_risks_and_debt.adoc
  - documentation/deployment/system.adoc
  - documentation/workflow/execution-report.md
  - tests/application/services/platform/test_preflight_service.py
  - tests/domain/preflight/test_preflight_result.py
  - tests/domain/deployment/test_service_stack_contract.py
  - tests/architecture/test_local_state_storage.py
  - tests/infrastructure/adapters/repositories/test_inventory_repositories.py
  - tests/infrastructure/test_composition.py
affected_modules:
  - tiny_swarm_world.application.services.platform
  - tiny_swarm_world.domain.preflight
  - tiny_swarm_world.domain.deployment
  - tiny_swarm_world.infrastructure.composition
  - infra.config
affected_contracts:
  - setup-profile-contract
  - desired-inventory-contract
  - credential-source-contract
dependencies:
  - "05"
parallel_group: F
file_locks:
  - src/tiny_swarm_world/application/services/platform/preflight_service.py
  - src/tiny_swarm_world/domain/preflight/**
  - src/tiny_swarm_world/domain/deployment/**
  - src/tiny_swarm_world/infrastructure/composition.py
  - infra/config/inventory/**
  - infra/config/compose/service-access/**
  - documentation/epics/**
  - documentation/arc42/11_risks_and_debt.adoc
  - documentation/deployment/system.adoc
  - documentation/workflow/execution-report.md
  - tests/application/services/platform/test_preflight_service.py
  - tests/domain/preflight/**
  - tests/domain/deployment/**
  - tests/architecture/**
  - tests/infrastructure/adapters/repositories/test_inventory_repositories.py
  - tests/infrastructure/test_composition.py
contract_locks:
  - setup-profile-contract
  - credential-source-contract
  - desired-inventory-contract
architecture_locks:
  - credential-evidence-redaction
  - planned-vs-implemented-documentation
quality_gates:
  targeted:
    - PYTHONPATH=src python3 -m unittest tests.domain.preflight.test_preflight_result
    - PYTHONPATH=src python3 -m unittest tests.domain.deployment.test_service_stack_contract
    - PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_preflight_service
    - PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_inventory_repositories
    - PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition
    - PYTHONPATH=src python3 -m unittest tests.architecture.test_local_state_storage
    - git diff --check
  required:
    - python3 tools/quality_gate.py test
documentation:
  arc42: documentation/arc42/11_risks_and_debt.adoc
  adr: documentation/architecture/adr-autonomous-setup-safety.adoc
stop_conditions:
  - Secrets, tokens, passwords, credential-bearing URLs or host IPs would be committed.
  - Static defaults are treated as production-like secrets.
  - Desired inventory and default setup profile cannot be reconciled without a governance decision.
```

Allowed write scope:

- Profile, inventory, credential contracts, docs and focused tests.

Done criteria:

- Full setup profile, service-access inclusion and desired inventory are
  aligned or explicitly documented as staged.
- Secret source behavior is clear and redacted.
- Missing secrets block before deployment when required by the selected
  profile.

### Slice 07 - Artifact, Registry And Deployment Readiness

Purpose:

- Harden the later setup phases so a host that passes platform readiness can
  continue through artifact preparation, registry verification, bootstrap,
  stack deployment and service readiness with observed-state checks.

```yaml
slice_id: "07"
profile: FULL_PATH
owner: Senior DevOps Engineer
secondary_reviewers:
  - Senior Python Automation Developer
  - Senior Tester
  - Senior System Architect
affected_files:
  - src/tiny_swarm_world/application/ports/clients/port_portainer_client.py
  - src/tiny_swarm_world/application/ports/clients/port_swarm_stack_runtime.py
  - src/tiny_swarm_world/application/services/artifacts/**
  - src/tiny_swarm_world/application/services/deployment/**
  - src/tiny_swarm_world/infrastructure/adapters/clients/**
  - src/tiny_swarm_world/infrastructure/composition.py
  - tests/application/services/artifacts/**
  - tests/application/services/deployment/**
  - tests/infrastructure/adapters/clients/**
  - tests/infrastructure/test_composition.py
affected_modules:
  - tiny_swarm_world.application.ports.clients
  - tiny_swarm_world.application.services.artifacts
  - tiny_swarm_world.application.services.deployment
  - tiny_swarm_world.infrastructure.adapters.clients
affected_contracts:
  - nexus-registry-readiness
  - portainer-bootstrap-readiness
  - swarm-stack-readiness
  - service-health-readiness
dependencies:
  - "06"
parallel_group: G
file_locks:
  - src/tiny_swarm_world/application/ports/clients/port_portainer_client.py
  - src/tiny_swarm_world/application/ports/clients/port_swarm_stack_runtime.py
  - src/tiny_swarm_world/application/services/artifacts/**
  - src/tiny_swarm_world/application/services/deployment/**
  - src/tiny_swarm_world/infrastructure/adapters/clients/**
  - src/tiny_swarm_world/infrastructure/composition.py
  - tests/application/services/artifacts/**
  - tests/application/services/deployment/**
  - tests/infrastructure/adapters/clients/**
  - tests/infrastructure/test_composition.py
contract_locks:
  - artifact-readiness
  - deployment-readiness
  - observed-state-verification
architecture_locks:
  - application-port-dependency
  - infrastructure-client-boundary
quality_gates:
  targeted:
    - PYTHONPATH=src python3 -m unittest tests.application.services.artifacts
    - PYTHONPATH=src python3 -m unittest tests.application.services.deployment
    - PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients
    - PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition
    - python3 tools/quality_gate.py arch-tests
  required:
    - python3 tools/quality_gate.py test
documentation:
  arc42: documentation/arc42/07_deployment_view.adoc; documentation/arc42/10_quality_requirements.adoc; documentation/arc42/11_risks_and_debt.adoc
  adr: documentation/architecture/adr-autonomous-setup-safety.adoc
stop_conditions:
  - Readiness is inferred without observed state.
  - Tests contact real Portainer, Nexus, Docker, Multipass or Swarm.
  - Application code embeds low-level HTTP, shell, Docker or filesystem details.
```

Allowed write scope:

- Artifact/deployment application services, infrastructure clients, wiring and
  focused tests.

Done criteria:

- Later setup phases report `blocked`, `failed_to_prepare`,
  `failed_to_verify` or `completed` with redacted evidence.
- Registry, Portainer and service readiness have mocked contract tests.
- No default gate performs live infrastructure work.

### Slice 08 - Documentation, Quality Evidence And Optional Live Smoke Handoff

Purpose:

- Synchronize docs with implemented behavior.
- Record exact verification evidence.
- Define optional live smoke steps without running them by default.

```yaml
slice_id: "08"
profile: FULL_PATH
owner: Senior Documentation Engineer
secondary_reviewers:
  - Senior Tester
  - Senior Workflow Architect
  - Senior System Architect
affected_files:
  - README.md
  - documentation/user_guide/installation.adoc
  - documentation/user_guide/usage.adoc
  - documentation/user_guide/troubleshooting.adoc
  - documentation/system/live-operation-surfaces.adoc
  - documentation/system/multipass-setup.adoc
  - documentation/arc42/06_runtime_view.adoc
  - documentation/arc42/07_deployment_view.adoc
  - documentation/arc42/10_quality_requirements.adoc
  - documentation/arc42/11_risks_and_debt.adoc
  - documentation/workflow/**
affected_modules: []
affected_contracts:
  - documentation-sync
  - quality-evidence
  - optional-live-smoke-handoff
dependencies:
  - "02"
  - "03"
  - "04"
  - "05"
  - "06"
  - "07"
parallel_group: H
file_locks:
  - README.md
  - documentation/user_guide/**
  - documentation/system/**
  - documentation/arc42/**
  - documentation/workflow/**
contract_locks:
  - documentation-sync
  - quality-evidence
architecture_locks:
  - planned-vs-implemented-documentation
quality_gates:
  targeted:
    - git diff --check
    - python3 tools/quality_gate.py arch-tests
    - python3 tools/quality_gate.py test
  required:
    - python3 tools/quality_gate.py quality
documentation:
  arc42: documentation/arc42/06_runtime_view.adoc; documentation/arc42/07_deployment_view.adoc; documentation/arc42/10_quality_requirements.adoc; documentation/arc42/11_risks_and_debt.adoc
  adr: documentation/architecture/adr-autonomous-setup-safety.adoc
stop_conditions:
  - Documentation claims live setup success before evidence exists.
  - Full quality gate fails or is skipped without recorded justification.
  - Optional live smoke is mixed into default quality gates.
```

Allowed write scope:

- User guide, system docs, arc42, workflow evidence and final handoff.

Done criteria:

- Docs explain IntelliJ/Linux/WSL execution, Multipass readiness blockers and
  safe remediation.
- Quality evidence records exact commands and outcomes.
- Optional live smoke is separate, explicit and redacted.

## Slice Dependency Graph

```text
01 -> 02 -> 03 -> 04 -> 05 -> 06 -> 07 -> 08
02 -------------------------------> 08
03 -------------------------------> 08
04 -------------------------------> 08
05 -------------------------------> 08
06 -------------------------------> 08
07 -------------------------------> 08
```

The graph is mostly sequential because readiness, command semantics, endpoint
strategy, credential/profile consistency and later deployment readiness depend
on each other. Read-only reviews may run in parallel; write-capable work must
respect slice locks.

## Parallelization Opportunities

- Slice 02 test baselining may run with read-only documentation review after
  Slice 01.
- Slice 05 endpoint documentation exploration may run read-only while Slice 03
  implementation is drafted, but writes wait for Slice 04 readiness semantics.
- Slice 06 profile/inventory review may start read-only once Slice 05 begins.
- Slice 08 documentation drafts may be prepared read-only throughout, then
  updated with actual evidence only after implementation slices complete.

## Role And Subagent Ownership Map

| Role | Ownership |
|---|---|
| Senior Workflow Architect | Workflow structure, dependency graph, metadata, locks, handoff |
| Senior Requirement Engineer | Requirement baseline, EPIC drift, acceptance criteria |
| Senior System Architect | Hexagonal boundaries, endpoint strategy, profile/inventory governance |
| Senior Python Automation Developer | Preflight, setup/platform orchestration, command catalog semantics |
| Senior React Frontend Developer | N/A React scope guard, console/status UI routing awareness |
| Senior Tester | Regression tests, redaction checks, quality-gate evidence |
| Senior DevOps Engineer | Multipass/Docker/Swarm readiness, artifact/deployment runtime contracts |
| Senior Documentation Engineer | User guide, troubleshooting, arc42, workflow sync |
| Senior Security Sandbox Engineer | Secret handling, evidence redaction, host mutation boundaries |
| Console/status UI skills | Conditional terminal status/recovery text only |

## Quality-Gate Expectations

Workflow creation:

```bash
git diff --check
```

Targeted implementation checks:

```bash
PYTHONPATH=src python3 -m unittest tests.test_package_entrypoint
PYTHONPATH=src python3 -m unittest tests.application.services.setup.test_setup_workflow
PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_preflight_service
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.preflight.test_host_preflight_probe
PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_platform_workflows
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.command_runner.test_command_workflow_configuration
PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py test
python3 tools/quality_gate.py quality
```

No quality gate may create VMs, change networking, initialize Docker Swarm,
deploy stacks, contact Portainer/Nexus live, run Vaultwarden/NGINX containers,
or bootstrap service credentials.

## Documentation Synchronization Points

- Slice 01: workflow and context pack.
- Slice 03: preflight quality requirements and host runtime prerequisites.
- Slice 04: platform init behavior and Multipass troubleshooting.
- Slice 05: IntelliJ/Linux/WSL execution contract and endpoint strategy.
- Slice 06: EPIC, inventory, profile and credential-source consistency.
- Slice 07: artifact/deployment readiness docs.
- Slice 08: README, user guide, arc42, workflow evidence and optional live
  smoke handoff.

## Stop Conditions

Stop and report when:

- live infrastructure execution is required without explicit approval;
- the workflow would auto-repair host packages, socket permissions, drivers or
  service state without an ADR and live approval;
- domain code would import infrastructure concerns;
- application services would embed low-level shell, Docker, HTTP or filesystem
  details directly;
- commands, stdout, stderr, tokens, passwords, local IPs, usernames or
  user-specific paths would be persisted as evidence;
- direct `platform init --live` could still bypass readiness checks;
- endpoint strategy requires guessing localhost versus node-IP behavior;
- documentation would claim live setup success before evidence exists;
- quality commands cannot be verified from `QUALITY.md`;
- React/browser frontend or Windows-native behavior is introduced.

## Commit And Push Plan

No commit or push is requested by this workflow creation request.

When the user later asks for commit or push preparation:

- inspect `git status --short --branch`;
- review changed files and line-ending noise;
- run required gates for the changed scope;
- stage only workflow-related files;
- use commit messaging governed by the git commit preparation skills.

## Definition Of Done

- `documentation/workflow/workflow.md` exists and includes complete slice
  metadata.
- `documentation/workflow/context-pack.md` and
  `documentation/workflow/context-pack.json` exist and match this branch.
- Subagent review findings are reflected in the workflow.
- The problem analysis explains why quality passed while live setup failed.
- Local `.tiny-swarm-world` evidence is summarized without committing raw logs,
  host IPs, secrets or user-specific details.
- arc42 impact is checked and represented in slice documentation
  requirements.
- Workflow creation verification passes `git diff --check`.
- No live infrastructure command was run.
- No implementation code, stack deployment or service bootstrap was performed
  during workflow creation.

## Handoff To Workflow Execute

Use:

```text
workflow execute with subagents
```

Before execution:

- verify the active branch is
  `feature/workflow-stable-live-setup-20260525`;
- verify context pack hashes are current;
- verify slice metadata and locks;
- run S3/S3D preflight;
- begin at Slice 02 for implementation, because Slice 01 is this workflow
  creation;
- keep writes inside each slice's allowed scope;
- stop on any live-infrastructure, secret, endpoint, consent, ADR or
  architecture blocker.

Final publication is checkpoint-only for workflow execution unless the user
explicitly requests commit or push. No `push auto`, pull request, merge,
branch cleanup, force-push or push to `main` is part of this workflow.

## arc42 Check Status

Checked during workflow creation:

- `documentation/arc42/06_runtime_view.adoc`
- `documentation/arc42/07_deployment_view.adoc`
- `documentation/arc42/10_quality_requirements.adoc`
- `documentation/arc42/11_risks_and_debt.adoc`

arc42 files are not changed during workflow creation. They are synchronized in
the implementation slices when behavior changes are made.
