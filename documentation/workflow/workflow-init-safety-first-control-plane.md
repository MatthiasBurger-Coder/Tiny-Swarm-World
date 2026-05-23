# Workflow: Init Safety First Control Plane Hardening

## Executive Summary

This workflow improves the existing Tiny Swarm World init-safety and
boundary-separation workflow by changing the execution order.

The existing workflow identifies the right target architecture, but it delays
the most critical safety fix: normal `init` still reaches the destructive
Multipass cleanup command YAML. This workflow puts the safety fix first, then
introduces workflow taxonomy, service boundaries, typed command contracts,
state and inventory separation, and verify-after-apply behavior.

No live Multipass, Docker Swarm, netplan, socat, Portainer, Nexus, Jenkins,
RabbitMQ, SonarQube, compose, or stack deployment commands may be executed
during this workflow unless a later explicitly approved live-infrastructure
workflow allows it.

## Relationship To Existing Workflow

`documentation/workflow/workflow.md` remains the broader roadmap for init
safety and boundary separation.

This workflow is the safety-first execution order that must be used before
running broader control-plane maturity work. Do not start typed YAML, service
boundary, state model, or CLI implementation work before Slice 01 and Slice 02
in this file are complete.

## Target Picture

### Verified Baseline

- Root `AGENTS.md` defines Tiny Swarm World as a Linux/WSL-only Python
  automation project with hexagonal architecture.
- `QUALITY.md` defines the default quality gate as:

```bash
python3 tools/quality_gate.py quality
```

- The default quality gate must not create VMs, mutate networking, initialize
  Docker Swarm, deploy stacks, or bootstrap services.
- Normal Multipass init currently calls
  `command_multipass_clean_repository_yaml.yaml`.
- The cleanup YAML contains destructive commands such as
  `multipass delete --all` and `multipass purge`.
- `ApplicationServices` is still an alias for `PlatformServices`.
- The CLI still exposes low-level services through `--run`.
- Nexus stack deployment is still owned by Nexus service code instead of
  Deployment-owned service code.
- Command YAML files do not yet have a strong typed safety contract.
- Desired inventory and observed runtime state are not yet separated.
- Mutating workflows do not consistently require typed verification after
  apply.

### Target Outcome

The completed workflow must produce:

- a non-destructive normal `init` path;
- separate `init`, `reconcile`, `reset`, `destroy`, and `verify` workflows;
- explicit reset and destroy confirmation contracts;
- real `PlatformServices`, `ArtifactServices`, and `DeploymentServices`
  composition boundaries;
- workflow-level CLI commands instead of service-level `--run` dispatch;
- Nexus stack deployment owned by Deployment;
- typed command YAML contracts with safety classification and allowed workflow
  checks;
- separated desired inventory, observed state, and verification evidence;
- mandatory verify-after-apply behavior for mutating workflow steps;
- documentation that reflects the implemented safety model.

## Requirement Clarification Record

Original request:

```text
Create a new safety-first workflow that keeps the existing workflow as a
roadmap but fixes the execution order so normal init becomes non-destructive
before broader control-plane refactoring starts.
```

Interpreted intent:

- Add a new repository workflow file named
  `documentation/workflow/workflow-init-safety-first-control-plane.md`.
- Preserve the existing workflow file.
- Make the destructive-init safety fix the first production-code change.
- Keep the workflow executable slice by slice with tests and quality gates.

Change type:

- Workflow documentation update.
- Future implementation planning for application services, composition,
  command YAML contracts, CLI, state modeling, verification, tests, and
  documentation.

Affected process strand:

- `workflow create`
- future `workflow execute`

Affected architecture areas:

- Platform automation: Multipass VM lifecycle, init, reconcile, reset, destroy,
  verify, and command selection.
- Artifacts automation: Nexus readiness and repository behavior.
- Deployment automation: compose and Portainer stack ownership.
- Shared automation: command catalog, typed YAML, state evidence, composition,
  CLI dispatch, and quality gates.

Explicit requirements:

- Normal init must never run destructive cleanup.
- `init` and `reconcile` must not select destructive command YAML files.
- Destructive commands must be reachable only through explicit `reset` or
  `destroy` contracts.
- The first executable slice must add safety regression tests.
- The first production-code change must remove destructive cleanup from normal
  init.
- Service boundaries and CLI changes happen after the safety fix.

Implicit requirements:

- Keep domain code independent from application and infrastructure concerns.
- Keep application services dependent on ports, not concrete infrastructure
  adapters.
- Keep concrete adapter construction in `infrastructure/composition.py`.
- Keep `__main__.py` thin.
- Preserve Linux/WSL-only documentation and command examples.
- Keep live infrastructure execution outside default quality gates.

Assumptions:

- `init` means non-destructive creation or preparation of missing managed
  resources.
- `reconcile` means non-destructive convergence of existing managed state.
- `reset` means explicit destructive reinitialization after confirmation.
- `destroy` means explicit destructive teardown after confirmation.
- `verify` means non-mutating inspection.
- Desired inventory may live under committed configuration.
- Observed runtime state and evidence must live under an ignored local path
  such as `.tiny-swarm-world/`.

Non-goals:

- No live infrastructure execution.
- No Java example application changes.
- No Windows-native runtime support expansion.
- No big-bang package move.
- No microservice conversion of Platform, Artifacts, and Deployment.
- No committed local observed state.
- No weakening of `.importlinter`, architecture tests, or quality gates.

Risks:

- The current init path can delete and purge Multipass VMs.
- Existing tests may be skipped or stale around Multipass init behavior.
- File-name-driven command execution can bypass workflow intent if not gated.
- Boundary refactoring before the safety fix leaves the highest-risk behavior
  active for too long.

Open questions:

- Exact retention semantics for `reset` and `destroy` must be documented before
  destructive workflows are wired.

Blocking questions:

- None for creating this workflow.

Confidence level:

- 94 percent.

Decision:

```text
READY_FOR_WORKFLOW
```

## Three Amigos Decision

### Requirement Engineer Decision

The first executable slice must remove destructive cleanup from the normal init
path.

The workflow must distinguish:

- `init`: non-destructive creation and preparation
- `reconcile`: non-destructive convergence
- `reset`: explicit destructive reinitialization
- `destroy`: explicit destructive teardown
- `verify`: non-mutating inspection

### System Architect Decision

Safety must be handled before broader architectural refactoring.

Implementation order:

1. lock down destructive commands
2. make normal init safe
3. introduce workflow taxonomy
4. separate composition boundaries
5. extract Nexus stack deployment
6. introduce typed command YAML
7. introduce state and inventory
8. enforce verify-after-apply

### Senior Tester Decision

Every implementation slice must begin with tests or static architecture checks.

The first regression test must prove:

- `MultipassInitVms.run()` does not call
  `command_multipass_clean_repository_yaml.yaml`
- `init` and `reconcile` cannot select destructive command YAML files
- destructive commands are reachable only through reset or destroy contracts

## Scope

In scope:

- workflow-level planning and execution order;
- regression tests for destructive command isolation;
- non-destructive init behavior;
- workflow taxonomy;
- composition service bundles;
- deployment ownership for Nexus stack deployment;
- workflow-level CLI shape;
- typed command YAML contract;
- state, inventory, and verification evidence;
- documentation and legacy quarantine.

Out of scope:

- live infrastructure changes;
- CI additions that run live infrastructure;
- Windows-native runtime examples;
- Java example application work;
- broad package moves not needed by a slice.

## Architecture Constraints

- Preserve hexagonal dependency direction.
- Domain modules must not import application or infrastructure modules.
- Application services may orchestrate ports and domain objects only.
- Infrastructure adapters own technology-specific details.
- `composition.py` remains the wiring root.
- `__main__.py` remains a thin entry point.
- Service bundles are responsibility boundaries inside one Python application,
  not independently deployable microservices.

## Python Automation Assessment

The work is Python automation work. The safety-critical surface is command
selection and orchestration, not live command execution.

Implementation slices must use mock-based tests for command runners, VM
operations, Docker operations, network calls, Portainer, Nexus, and filesystem
effects unless a later workflow explicitly approves live infrastructure.

## Frontend Assessment

No frontend module is required for this workflow. If a future UI module is
added for workflow evidence review, it must be planned separately.

## Test Strategy

- Start with regression tests that fail against unsafe init behavior.
- Add static tests that detect destructive command strings under init or
  reconcile contracts.
- Add architecture tests around service ownership where boundaries change.
- Use focused unit tests during slices and `python3 tools/quality_gate.py
  quality` for final verification when practical.
- Do not skip tests to make a slice pass.

Destructive command patterns that must not be reachable from `init` or
`reconcile`:

```text
multipass delete --all
multipass purge
docker system prune
docker volume rm
docker stack rm
```

## Resilience Requirements

- Mutating workflow steps fail closed when safety classification is missing.
- `init` and `reconcile` fail closed when a destructive command is selected.
- `reset` and `destroy` require explicit confirmation.
- Apply failure and verify failure are reported separately.
- Missing verification evidence blocks continuation after a mutating step.

## Ordered Slices

For every slice, the allowed write scope is limited to the paths listed in
that slice's `affected_files` and `file_locks` metadata. Where a slice also
lists a forbidden write scope, the forbidden scope wins.

### Slice 01 - Safety Regression Tests Before Code Change

Goal:

- Add tests that prove the current unsafe behavior and define the required safe
  behavior before production code changes.

```yaml
slice_id: "01"
profile: "FULL_PATH"
owner: "Senior Tester"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Security Sandbox Engineer"
affected_files:
  - "tests/application/services/multipass/**"
  - "tests/application/services/platform/**"
  - "tests/architecture/**"
  - "documentation/workflow/**"
affected_modules:
  - "tiny_swarm_world.application.services.multipass"
  - "tiny_swarm_world.application.services.platform"
affected_contracts:
  - "init-non-destructive-contract"
  - "destructive-command-isolation"
dependencies: []
parallel_group: "A"
file_locks:
  - "tests/application/services/multipass/**"
  - "tests/application/services/platform/**"
  - "tests/architecture/**"
contract_locks:
  - "init-non-destructive-contract"
  - "destructive-command-isolation"
architecture_locks:
  - "live-infrastructure-safety"
quality_gates:
  targeted:
    - "python3 tools/quality_gate.py test"
    - "python3 tools/quality_gate.py arch-tests"
  required:
    - "python3 tools/quality_gate.py test"
    - "python3 tools/quality_gate.py arch-tests"
documentation:
  arc42: "no arc42 change expected unless safety policy is documented early"
  adr: "check whether destructive operation policy needs ADR follow-up"
stop_conditions:
  - "a test would require live Multipass"
  - "a test must be skipped to pass"
  - "the unsafe behavior cannot be tested without changing production code first"
```

Allowed write scope:

```text
tests/application/services/multipass/**
tests/application/services/platform/**
tests/architecture/**
documentation/workflow/**
```

Forbidden write scope:

```text
src/tiny_swarm_world/application/services/multipass/**
infra/config/**
```

Required tests:

- `MultipassInitVms` must not call
  `command_multipass_clean_repository_yaml.yaml`.
- Normal init must not reference destructive command YAML files.
- Destructive YAML files must not be reachable from init or reconcile
  workflows.
- Existing skipped Multipass init tests must be replaced or explicitly
  quarantined.

Verification commands:

```bash
python3 tools/quality_gate.py test
python3 tools/quality_gate.py arch-tests
```

### Slice 02 - Remove Destructive Cleanup From Normal Init

Goal:

- Make normal init non-destructive.

```yaml
slice_id: "02"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Tester"
  - "Senior System Architect"
  - "Senior Security Sandbox Engineer"
affected_files:
  - "src/tiny_swarm_world/application/services/multipass/multipass_init_vms.py"
  - "src/tiny_swarm_world/application/services/platform/**"
  - "tests/application/services/multipass/**"
  - "tests/application/services/platform/**"
  - "documentation/workflow/**"
affected_modules:
  - "tiny_swarm_world.application.services.multipass"
  - "tiny_swarm_world.application.services.platform"
affected_contracts:
  - "init-non-destructive-contract"
dependencies:
  - "01"
parallel_group: "B"
file_locks:
  - "src/tiny_swarm_world/application/services/multipass/multipass_init_vms.py"
  - "src/tiny_swarm_world/application/services/platform/**"
contract_locks:
  - "init-non-destructive-contract"
architecture_locks:
  - "application-service-port-boundary"
  - "live-infrastructure-safety"
quality_gates:
  targeted:
    - "python3 tools/quality_gate.py test"
  required:
    - "python3 tools/quality_gate.py test"
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "record non-destructive init behavior when production change lands"
  adr: "check destructive operation policy ADR need"
stop_conditions:
  - "the fix would edit the destructive cleanup YAML instead of removing it from init"
  - "normal init would still select cleanup by file name"
  - "tests require live infrastructure"
```

Required change:

`MultipassInitVms.run()` must no longer call:

```text
command_multipass_clean_repository_yaml.yaml
```

The destructive YAML may remain, but it must not be used by normal init.

Forbidden write scope:

```text
infra/config/multipass/command_multipass_clean_repository_yaml.yaml
```

Acceptance criteria:

- Normal init does not execute cleanup.
- Cleanup YAML remains unused by init.
- Tests prove cleanup is not called.
- No live infrastructure command is executed.

Verification commands:

```bash
python3 tools/quality_gate.py test
python3 tools/quality_gate.py quality
```

### Slice 03 - Introduce Workflow Taxonomy

Goal:

- Introduce explicit platform workflow classes and operation semantics.

```yaml
slice_id: "03"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "src/tiny_swarm_world/application/services/platform/**"
  - "src/tiny_swarm_world/domain/**"
  - "tests/application/services/platform/**"
  - "tests/architecture/**"
  - "documentation/workflow/**"
affected_modules:
  - "tiny_swarm_world.application.services.platform"
  - "tiny_swarm_world.domain"
affected_contracts:
  - "platform-workflow-taxonomy"
  - "reset-destroy-confirmation"
dependencies:
  - "02"
parallel_group: "C"
file_locks:
  - "src/tiny_swarm_world/application/services/platform/**"
  - "tests/application/services/platform/**"
contract_locks:
  - "platform-workflow-taxonomy"
  - "reset-destroy-confirmation"
architecture_locks:
  - "hexagonal-application-boundary"
quality_gates:
  targeted:
    - "python3 tools/quality_gate.py test"
    - "python3 tools/quality_gate.py typecheck"
  required:
    - "python3 tools/quality_gate.py test"
    - "python3 tools/quality_gate.py typecheck"
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "update runtime view when workflows are implemented"
  adr: "check whether operation taxonomy needs ADR record"
stop_conditions:
  - "reset or destroy can run without explicit confirmation"
  - "init or reconcile can select destructive commands"
```

New use cases:

```text
PlatformInitWorkflow
PlatformReconcileWorkflow
PlatformResetWorkflow
PlatformDestroyWorkflow
PlatformVerifyWorkflow
```

Semantics:

| Workflow | Mutating | Destructive | Meaning |
| --- | ---: | ---: | --- |
| init | yes | no | create missing managed resources |
| reconcile | yes | no | converge existing managed state |
| reset | yes | yes | explicitly reinitialize managed resources |
| destroy | yes | yes | explicitly tear down managed resources |
| verify | no | no | inspect current state |

Verification commands:

```bash
python3 tools/quality_gate.py test
python3 tools/quality_gate.py typecheck
python3 tools/quality_gate.py quality
```

### Slice 04 - Separate Composition Boundaries

Goal:

- Replace the platform-only composition alias with real service bundles.

```yaml
slice_id: "04"
profile: "FULL_PATH"
owner: "Senior System Architect"
secondary_reviewers:
  - "Senior Python Automation Developer"
  - "Senior Tester"
affected_files:
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "src/tiny_swarm_world/__main__.py"
  - "tests/infrastructure/**"
  - "tests/architecture/**"
  - "documentation/workflow/**"
affected_modules:
  - "tiny_swarm_world.infrastructure.composition"
  - "tiny_swarm_world.__main__"
affected_contracts:
  - "application-service-bundles"
dependencies:
  - "03"
parallel_group: "D"
file_locks:
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "src/tiny_swarm_world/__main__.py"
  - "tests/infrastructure/**"
contract_locks:
  - "application-service-bundles"
architecture_locks:
  - "composition-root"
  - "thin-entrypoint"
quality_gates:
  targeted:
    - "python3 tools/quality_gate.py arch-tests"
    - "python3 tools/quality_gate.py test"
  required:
    - "python3 tools/quality_gate.py arch-tests"
    - "python3 tools/quality_gate.py test"
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "update building blocks and runtime view for service bundles"
  adr: "align with separate platform/artifacts/deployment ADR"
stop_conditions:
  - "service construction would run external commands"
  - "__main__.py would import concrete adapters directly"
  - "ApplicationServices remains an alias for PlatformServices"
```

Required target:

```python
@dataclass(frozen=True)
class PlatformServices:
    ...

@dataclass(frozen=True)
class ArtifactServices:
    ...

@dataclass(frozen=True)
class DeploymentServices:
    ...

@dataclass(frozen=True)
class ApplicationServices:
    platform: PlatformServices
    artifacts: ArtifactServices
    deployment: DeploymentServices
```

Required builders:

```python
build_platform_services()
build_artifact_services()
build_deployment_services()
build_application_services()
```

Acceptance criteria:

- `ApplicationServices = PlatformServices` no longer exists.
- Constructors remain side-effect free.
- No live commands execute during service construction.
- `__main__.py` stays thin.

Verification commands:

```bash
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py test
python3 tools/quality_gate.py quality
```

### Slice 05 - Extract Nexus Stack Deployment

Goal:

- Move Nexus stack deployment ownership to Deployment.

```yaml
slice_id: "05"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "src/tiny_swarm_world/application/services/nexus/ensure_nexus_stack.py"
  - "src/tiny_swarm_world/application/services/deployment/**"
  - "tests/application/services/nexus/**"
  - "tests/application/services/deployment/**"
  - "tests/architecture/**"
  - "documentation/workflow/**"
  - "documentation/arc42/**"
affected_modules:
  - "tiny_swarm_world.application.services.nexus"
  - "tiny_swarm_world.application.services.deployment"
affected_contracts:
  - "deployment-stack-ownership"
  - "artifact-nexus-boundary"
dependencies:
  - "04"
parallel_group: "E"
file_locks:
  - "src/tiny_swarm_world/application/services/nexus/ensure_nexus_stack.py"
  - "src/tiny_swarm_world/application/services/deployment/**"
  - "tests/application/services/nexus/**"
  - "tests/application/services/deployment/**"
  - "documentation/arc42/**"
contract_locks:
  - "deployment-stack-ownership"
  - "artifact-nexus-boundary"
architecture_locks:
  - "application-service-ownership"
quality_gates:
  targeted:
    - "python3 tools/quality_gate.py test"
    - "python3 tools/quality_gate.py arch-tests"
  required:
    - "python3 tools/quality_gate.py test"
    - "python3 tools/quality_gate.py arch-tests"
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "update building blocks for deployment-owned stack lifecycle"
  adr: "align with separate platform/artifacts/deployment ADR"
stop_conditions:
  - "artifact services would import Portainer ports"
  - "deployment services would own Nexus repository internals"
```

Target ownership:

```text
deployment:
  - ensure stack exists
  - create/update Portainer stack
  - compose stack lifecycle

artifacts:
  - Nexus readiness
  - Nexus admin access
  - Nexus anonymous access
  - Nexus repository configuration
  - Docker/Maven registry behavior
```

Required refactoring:

Move or wrap:

```text
application/services/nexus/ensure_nexus_stack.py
```

into Deployment-owned service code such as:

```text
application/services/deployment/ensure_stack.py
application/services/deployment/ensure_nexus_stack.py
```

Verification commands:

```bash
python3 tools/quality_gate.py test
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py quality
```

### Slice 06 - Workflow-Level CLI

Goal:

- Replace low-level service CLI dispatch with workflow-level commands.

```yaml
slice_id: "06"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "src/tiny_swarm_world/__main__.py"
  - "src/tiny_swarm_world/application/services/platform/**"
  - "src/tiny_swarm_world/application/services/deployment/**"
  - "src/tiny_swarm_world/application/services/nexus/**"
  - "tests/**"
  - "documentation/workflow/**"
affected_modules:
  - "tiny_swarm_world.__main__"
  - "tiny_swarm_world.application.services.platform"
  - "tiny_swarm_world.application.services.deployment"
affected_contracts:
  - "workflow-cli-contract"
  - "reset-destroy-confirmation"
dependencies:
  - "05"
parallel_group: "F"
file_locks:
  - "src/tiny_swarm_world/__main__.py"
  - "tests/**"
contract_locks:
  - "workflow-cli-contract"
  - "reset-destroy-confirmation"
architecture_locks:
  - "thin-entrypoint"
  - "composition-root"
quality_gates:
  targeted:
    - "python3 tools/quality_gate.py test"
    - "python3 tools/quality_gate.py typecheck"
  required:
    - "python3 tools/quality_gate.py test"
    - "python3 tools/quality_gate.py typecheck"
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "update runtime view for workflow-level commands"
  adr: "check CLI command contract decision need"
stop_conditions:
  - "listing commands builds live services"
  - "reset or destroy can run without confirmation"
  - "default CLI invocation mutates resources"
```

Current CLI style:

```bash
python -m tiny_swarm_world --run multipass-init-vms
```

Target CLI style:

```bash
python -m tiny_swarm_world platform init
python -m tiny_swarm_world platform reconcile
python -m tiny_swarm_world platform verify
python -m tiny_swarm_world platform reset --confirm RESET_TINY_SWARM_PLATFORM
python -m tiny_swarm_world platform destroy --confirm DESTROY_TINY_SWARM_PLATFORM

python -m tiny_swarm_world artifacts prepare
python -m tiny_swarm_world artifacts verify

python -m tiny_swarm_world deployment apply
python -m tiny_swarm_world deployment verify
```

Required rules:

- No workflow runs by default.
- Listing commands must not build live services.
- Reset and destroy must require explicit confirmation.
- `--preflight` remains safe and non-mutating.

Verification commands:

```bash
python3 tools/quality_gate.py test
python3 tools/quality_gate.py typecheck
python3 tools/quality_gate.py quality
```

### Slice 07 - Typed Command YAML Contract

Goal:

- Introduce a typed command catalog with workflow-aware safety validation.

```yaml
slice_id: "07"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior System Architect"
  - "Senior Tester"
  - "Senior Security Sandbox Engineer"
affected_files:
  - "src/tiny_swarm_world/domain/**"
  - "src/tiny_swarm_world/application/**"
  - "src/tiny_swarm_world/infrastructure/adapters/**"
  - "infra/config/**"
  - "tests/**"
  - "documentation/workflow/**"
affected_modules:
  - "tiny_swarm_world.domain"
  - "tiny_swarm_world.application"
  - "tiny_swarm_world.infrastructure.adapters"
affected_contracts:
  - "typed-command-yaml-contract"
  - "command-safety-classification"
  - "allowed-workflows"
dependencies:
  - "06"
parallel_group: "G"
file_locks:
  - "src/tiny_swarm_world/domain/**"
  - "src/tiny_swarm_world/application/**"
  - "src/tiny_swarm_world/infrastructure/adapters/**"
  - "infra/config/**"
  - "tests/**"
contract_locks:
  - "typed-command-yaml-contract"
  - "command-safety-classification"
architecture_locks:
  - "domain-infrastructure-isolation"
  - "application-port-boundary"
quality_gates:
  targeted:
    - "python3 tools/quality_gate.py test"
    - "python3 tools/quality_gate.py typecheck"
  required:
    - "python3 tools/quality_gate.py test"
    - "python3 tools/quality_gate.py typecheck"
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "update concepts and quality requirements for typed command contract"
  adr: "check typed command catalog ADR need"
stop_conditions:
  - "destructive shell strings are accepted without destructive safety class"
  - "mutating commands are accepted without verify specification"
  - "workflow usage can bypass allowed_workflows"
```

Minimum required fields:

```yaml
id:
description:
intent:
execution_mode:
safety_class:
scope:
allowed_workflows:
parameters:
effects:
verify:
runner:
command_type:
vm_type:
command:
```

Required safety classes:

```text
safe_read
safe_mutation
destructive
credential_mutation
network_mutation
```

Validation must reject:

- missing IDs;
- duplicate IDs;
- missing safety class;
- destructive shell strings without destructive classification;
- mutating commands without verify spec;
- commands used by workflows not listed in `allowed_workflows`.

Verification commands:

```bash
python3 tools/quality_gate.py test
python3 tools/quality_gate.py typecheck
python3 tools/quality_gate.py quality
```

### Slice 08 - State And Inventory Model

Goal:

- Introduce desired inventory, observed state, and verification evidence.

```yaml
slice_id: "08"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior System Architect"
  - "Senior Tester"
  - "Senior Security Sandbox Engineer"
affected_files:
  - "src/tiny_swarm_world/domain/**"
  - "src/tiny_swarm_world/application/**"
  - "src/tiny_swarm_world/infrastructure/adapters/**"
  - "tests/**"
  - ".gitignore"
  - "documentation/workflow/**"
affected_modules:
  - "tiny_swarm_world.domain"
  - "tiny_swarm_world.application"
  - "tiny_swarm_world.infrastructure.adapters"
affected_contracts:
  - "desired-inventory"
  - "observed-inventory"
  - "verification-evidence"
dependencies:
  - "07"
parallel_group: "H"
file_locks:
  - "src/tiny_swarm_world/domain/**"
  - "src/tiny_swarm_world/application/**"
  - "src/tiny_swarm_world/infrastructure/adapters/**"
  - "tests/**"
  - ".gitignore"
contract_locks:
  - "desired-inventory"
  - "observed-inventory"
  - "verification-evidence"
architecture_locks:
  - "domain-infrastructure-isolation"
  - "local-state-not-committed"
quality_gates:
  targeted:
    - "python3 tools/quality_gate.py test"
    - "python3 tools/quality_gate.py typecheck"
    - "python3 tools/quality_gate.py arch-tests"
  required:
    - "python3 tools/quality_gate.py test"
    - "python3 tools/quality_gate.py typecheck"
    - "python3 tools/quality_gate.py arch-tests"
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "update concepts, runtime, and deployment views for inventory"
  adr: "check state and evidence storage ADR need"
stop_conditions:
  - "observed state would be committed under infra/config"
  - "domain model imports filesystem, YAML, HTTP, or command runners"
```

Domain concepts:

```text
DesiredInventory
ObservedInventory
VmDesiredState
VmObservedState
NetworkObservedState
DockerObservedState
SwarmObservedState
StackObservedState
ArtifactRegistryObservedState
VerificationResult
VerificationStatus
```

Verification status values:

```text
not_checked
verified
failed_to_apply
failed_to_verify
blocked
refused
```

Storage rules:

- Desired inventory may live under `infra/config`.
- Observed inventory must live under `.tiny-swarm-world/`.
- `.tiny-swarm-world/` must remain ignored by Git.
- Domain must not import filesystem, YAML, HTTP, or command runners.

Verification commands:

```bash
python3 tools/quality_gate.py test
python3 tools/quality_gate.py typecheck
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py quality
```

### Slice 09 - Verify After Every Apply

Goal:

- Force verification after every mutating workflow step.

```yaml
slice_id: "09"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior System Architect"
  - "Senior Tester"
  - "Senior Security Sandbox Engineer"
affected_files:
  - "src/tiny_swarm_world/application/**"
  - "src/tiny_swarm_world/domain/**"
  - "src/tiny_swarm_world/infrastructure/adapters/**"
  - "tests/**"
  - "documentation/workflow/**"
affected_modules:
  - "tiny_swarm_world.application"
  - "tiny_swarm_world.domain"
  - "tiny_swarm_world.infrastructure.adapters"
affected_contracts:
  - "verify-after-apply"
  - "verification-evidence"
dependencies:
  - "08"
parallel_group: "I"
file_locks:
  - "src/tiny_swarm_world/application/**"
  - "src/tiny_swarm_world/domain/**"
  - "src/tiny_swarm_world/infrastructure/adapters/**"
  - "tests/**"
contract_locks:
  - "verify-after-apply"
  - "verification-evidence"
architecture_locks:
  - "workflow-continuation-safety"
quality_gates:
  targeted:
    - "python3 tools/quality_gate.py test"
    - "python3 tools/quality_gate.py typecheck"
  required:
    - "python3 tools/quality_gate.py test"
    - "python3 tools/quality_gate.py typecheck"
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "update runtime and quality requirements for apply/verify sequencing"
  adr: "check verify-after-apply ADR need"
stop_conditions:
  - "a mutating workflow can continue without verification evidence"
  - "apply failure and verify failure cannot be reported separately"
```

Required rule:

```text
apply succeeded
and
verify succeeded
```

Required tests:

- Mutating workflow without verify spec fails.
- Failed apply stops workflow.
- Failed verify stops workflow.
- Workflow cannot silently continue after missing verification evidence.

Verification commands:

```bash
python3 tools/quality_gate.py test
python3 tools/quality_gate.py typecheck
python3 tools/quality_gate.py quality
```

### Slice 10 - Documentation And Legacy Quarantine

Goal:

- Synchronize documentation and quarantine unsafe legacy scripts.

```yaml
slice_id: "10"
profile: "FULL_PATH"
owner: "Senior Documentation Engineer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "README.md"
  - "documentation/arc42/**"
  - "documentation/user_guide/**"
  - "documentation/deployment/**"
  - "documentation/architecture/**"
  - "documentation/workflow/**"
affected_modules: []
affected_contracts:
  - "operator-documentation"
  - "legacy-quarantine"
dependencies:
  - "01"
  - "02"
  - "03"
  - "04"
  - "05"
  - "06"
  - "07"
  - "08"
  - "09"
parallel_group: "J"
file_locks:
  - "README.md"
  - "documentation/arc42/**"
  - "documentation/user_guide/**"
  - "documentation/deployment/**"
  - "documentation/architecture/**"
  - "documentation/workflow/**"
contract_locks:
  - "operator-documentation"
  - "legacy-quarantine"
architecture_locks:
  - "documentation-implementation-consistency"
quality_gates:
  targeted:
    - "git diff --check"
    - "python3 tools/quality_gate.py arch-tests"
  required:
    - "git diff --check"
    - "python3 tools/quality_gate.py arch-tests"
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "final synchronization across constraints, runtime, deployment, concepts, quality, and risks"
  adr: "final ADR index synchronization"
stop_conditions:
  - "documentation claims implemented behavior that is not verified"
  - "legacy destructive behavior remains undocumented or unquarantined"
```

Required documentation updates:

```text
README.md
documentation/arc42/**
documentation/user_guide/**
documentation/deployment/**
documentation/architecture/**
```

Required notes:

- Normal init is non-destructive.
- Reset and destroy are explicit.
- Live commands require consent.
- Observed state is local and ignored.
- Legacy scripts are deprecated, quarantined, or documented as unsupported.

Verification commands:

```bash
git diff --check
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py quality
```

## Slice Dependency Graph

| Slice | Name | Depends On | Parallelization |
| --- | --- | --- | --- |
| 01 | Safety Regression Tests Before Code Change | none | first slice |
| 02 | Remove Destructive Cleanup From Normal Init | 01 | blocked by safety tests |
| 03 | Introduce Workflow Taxonomy | 02 | blocked by safety fix |
| 04 | Separate Composition Boundaries | 03 | blocked by taxonomy |
| 05 | Extract Nexus Stack Deployment | 04 | blocked by service bundles |
| 06 | Workflow-Level CLI | 05 | blocked by workflows and bundles |
| 07 | Typed Command YAML Contract | 06 | blocked by workflow command model |
| 08 | State And Inventory Model | 07 | blocked by typed command evidence |
| 09 | Verify After Every Apply | 08 | blocked by evidence model |
| 10 | Documentation And Legacy Quarantine | 01, 02, 03, 04, 05, 06, 07, 08, 09 | final sync only |

Parallelization is intentionally limited. The first two slices are sequential
because safety regression tests must exist before the first production-code
change. Later slices may be split internally only when write scopes are
disjoint and the owning workflow architect confirms no contract lock conflict.

## Role Ownership Map

- Senior Requirement Engineer: taxonomy, acceptance criteria, destructive
  operation policy, reset/destroy confirmation semantics.
- Senior System Architect: service boundaries, composition root, architecture
  locks, ADR and arc42 alignment.
- Senior Python Automation Developer: application service changes, typed YAML,
  state model, CLI dispatch, verification orchestration.
- Senior Tester: regression-first tests, architecture tests, quality-gate
  routing, skipped-test quarantine.
- Senior Security Sandbox Engineer: destructive command isolation,
  confirmation contracts, local evidence storage safety.
- Senior Documentation Engineer: README, arc42, user guide, deployment docs,
  legacy quarantine notes.
- Senior Workflow Architect: slice dependency order, lock conflicts, execution
  handoff.

## Quality-Gate Expectations

The full local quality gate remains:

```bash
python3 tools/quality_gate.py quality
```

Use targeted gates inside slices as listed in each slice metadata block.

Documentation-only workflow edits must at least run:

```bash
git diff --check
```

Do not claim `quality` passed unless it was actually executed.

## Documentation Synchronization Points

- Slice 02: document that normal init is non-destructive when implemented.
- Slice 03: document operation taxonomy and reset/destroy confirmation
  semantics.
- Slice 04: update building block documentation for service bundles.
- Slice 05: update deployment ownership for Nexus stack deployment.
- Slice 06: update CLI documentation and examples.
- Slice 07: document typed command YAML fields and safety classes.
- Slice 08: document desired inventory, observed state, and local evidence
  storage.
- Slice 09: document verify-after-apply behavior and failure reporting.
- Slice 10: synchronize README, arc42, user guide, deployment docs, ADR index,
  and legacy script status.

## Stop Conditions

Stop workflow execution if:

- any slice would require live infrastructure without explicit approval;
- normal init still reaches destructive cleanup after Slice 02;
- destructive command patterns are reachable from `init` or `reconcile`;
- reset or destroy can run without explicit confirmation;
- command YAML validation accepts destructive shell strings without destructive
  classification;
- observed runtime state would be committed;
- application services import concrete infrastructure adapters;
- `__main__.py` becomes a concrete adapter construction site;
- quality gates are weakened or skipped without documented justification.

## Uncertainty Escalation Rules

Escalate to the Senior Requirement Engineer and Senior System Architect before
continuing when:

- reset and destroy retention semantics are unclear;
- a command appears both destructive and necessary for normal reconciliation;
- a workflow needs a command whose safety class or verification spec is
  missing;
- service ownership is ambiguous between Artifacts and Deployment;
- implementation evidence contradicts this workflow.

## Commit And Push Plan

No commit or push is part of this workflow update.

Before any future commit:

- inspect `git status --short`;
- include only files owned by the executed slice;
- run the required slice gates or document why a gate was skipped;
- do not stage generated caches, logs, local state, or live evidence.

## Final Definition Of Done

This workflow is complete when:

- normal init no longer calls destructive cleanup;
- `init`, `reconcile`, `reset`, `destroy`, and `verify` exist as separate
  workflows;
- reset and destroy require explicit confirmation;
- real `PlatformServices`, `ArtifactServices`, and `DeploymentServices` exist;
- CLI exposes workflow-level commands;
- Nexus stack deployment is deployment-owned;
- command YAML files are typed and safety-classified;
- desired inventory and observed state are separated;
- every mutating workflow step requires verification;
- documentation reflects implemented behavior;
- `python3 tools/quality_gate.py quality` passes;
- no live infrastructure command is part of the default quality gate.

## Handoff To Workflow Execute

Execute this workflow slice by slice.

Mandatory first steps:

1. Execute Slice 01 and add failing or protective regression tests.
2. Execute Slice 02 and remove destructive cleanup from normal init.
3. Re-run the required quality gates for Slice 02.
4. Only then continue with taxonomy, service boundaries, typed YAML, state,
   verification, and documentation slices.

Do not start with typed YAML, service boundaries, or CLI work before Slice 01
and Slice 02 are complete.

## arc42 Check Status

No arc42 content was changed by creating this workflow file.

Future implementation slices must check and update the relevant arc42 files
when behavior changes:

- `documentation/arc42/02_constraints.adoc`
- `documentation/arc42/03_solution_strategy.adoc`
- `documentation/arc42/05_building_blocks.adoc`
- `documentation/arc42/06_runtime_view.adoc`
- `documentation/arc42/07_deployment_view.adoc`
- `documentation/arc42/08_concepts.adoc`
- `documentation/arc42/09_architecture_decisions.adoc`
- `documentation/arc42/10_quality_requirements.adoc`
- `documentation/arc42/11_risks_and_debt.adoc`
- `documentation/arc42/12_glossary.adoc`
