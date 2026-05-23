# Workflow: Init Safety and Boundary Separation

## Execution Precedence

Before executing this broader roadmap, execute
`documentation/workflow/workflow-init-safety-first-control-plane.md`.

That safety-first workflow preserves this file as the broader target roadmap,
but moves the critical fix ahead of the rest: normal init must stop reaching
destructive Multipass cleanup before typed YAML, service-boundary, state model,
or CLI work starts.

## Executive Summary

This workflow defines the governed implementation path for making Tiny Swarm
World safer and more explicit at the workflow level.

The target change removes destructive VM cleanup from normal initialization,
introduces separate `reconcile`, `reset`, and `destroy` workflows, separates
Platform, Artifacts, and Deployment responsibilities, moves the CLI from
low-level service execution to workflow execution, extracts Nexus stack
deployment into Deployment ownership, strengthens command YAML typing,
introduces a state/inventory model, and requires verification after every
mutating apply step.

Workflow creation does not execute live infrastructure. All Multipass, Docker
Swarm, netplan, socat, compose, Portainer, Nexus, Jenkins, RabbitMQ, SonarQube,
and Swagger/NGINX operations remain forbidden unless a later workflow execution
receives explicit live infrastructure approval.

## Target Picture

### Verified Baseline At Workflow Creation

This baseline is historical. The safety-first execution branch has since
implemented the critical init safety, workflow taxonomy, service-boundary,
typed command, inventory, CLI, and verify-after-apply slices.

- Root `AGENTS.md` defines Tiny Swarm World as a Linux/WSL-only Python
  automation project with hexagonal architecture.
- `QUALITY.md` defines the default quality gate as:

```bash
python3 tools/quality_gate.py quality
```

- The default quality gate must not create VMs, mutate networking, initialize
  Docker Swarm, deploy stacks, or bootstrap services.
- `src/tiny_swarm_world/application/services/multipass/multipass_init_vms.py`
  currently runs `command_multipass_clean_repository_yaml.yaml` before normal
  initialization.
- `infra/config/multipass/command_multipass_clean_repository_yaml.yaml`
  currently contains `multipass delete --all` and `multipass purge`.
- `src/tiny_swarm_world/infrastructure/composition.py` currently exposes
  `PlatformServices` and aliases `ApplicationServices = PlatformServices`.
- `src/tiny_swarm_world/__main__.py` currently exposes low-level service names
  through `--run`, not workflow-level commands.
- Nexus stack deployment behavior currently lives under
  `application/services/nexus/ensure_nexus_stack.py` while the Deployment
  namespace re-exports it as a compatibility facade.
- Command YAML loading validates only indirectly by constructing
  `CommandEntity` from loose dictionary keys.
- No durable state/inventory model currently separates desired inventory from
  observed runtime state.
- `infra/config/network/netplant/command_netplant_setup_yaml.yaml` ends with
  `netplan apply` and does not require a typed verification gate afterwards.
- `documentation/architecture/adr-separate-platform-artifacts-deployment.adoc`
  already proposes Platform, Artifacts, Deployment, and Shared responsibility
  boundaries.

### Target Outcome

The completed workflow must produce:

- a non-destructive normal `init` path;
- separate `reconcile`, `reset`, `destroy`, and `verify` workflows;
- explicit destructive-operation policy and tests proving that `init` and
  `reconcile` cannot execute delete/purge behavior;
- real `PlatformServices`, `ArtifactServices`, and `DeploymentServices`
  builders and dataclasses in the composition root;
- a workflow-level CLI that remains thin and delegates to composed workflows;
- Nexus stack deployment owned by Deployment, while Nexus repository and
  artifact behavior stays in Artifacts;
- typed command YAML contracts with command identity, intent, safety class,
  parameters, effects, allowed workflows, and verification specs;
- a state/inventory model that separates desired configuration from observed
  runtime facts;
- mandatory verify-after-apply behavior for platform and deployment changes;
- architecture tests and documentation that protect the new boundaries.

## Requirement Clarification Record

Original request:

```text
Workflow create with subagents:
1. Destruktive VM-Cleanup-Schritte aus dem normalen Init entfernen
2. reconcile/reset/destroy als getrennte Workflows einfuehren
3. PlatformServices, ArtifactServices und DeploymentServices wirklich trennen
4. CLI auf Workflow-Ebene umbauen
5. Nexus Stack Deployment aus Artifacts/Nexus herausloesen
6. Command-YAMLs staerker typisieren
7. State-/Inventory-Modell einfuehren
8. Verify-Schritte nach jedem Apply erzwingen
```

Interpreted intent:

- Create a repository workflow, using subagent review, for an architecture and
  automation refactoring that makes normal initialization safe, separates
  explicit workflow intent, and enforces state verification.
- Treat Platform, Artifacts, and Deployment as responsibility boundaries inside
  the existing Python automation architecture. This workflow does not claim
  they are independently deployable microservices.
- Preserve root `AGENTS.md`, `QUALITY.md`, hexagonal imports, live
  infrastructure safety, and the Linux/WSL-only operating model.

Change type:

- Workflow creation and future implementation planning.
- Future production-code changes to application services, domain models,
  ports, infrastructure adapters, command YAMLs, CLI and tests.
- Future documentation synchronization for arc42, README and user/operator
  documentation.

Affected process strand:

- `workflow create`.

Affected architecture areas:

- Platform automation: VM lifecycle, network, Docker install, Swarm init/join,
  runtime probes and inventory facts.
- Artifact automation: Nexus repository/user/readiness behavior, Docker/Maven
  publishing contracts, image build/push contracts.
- Deployment automation: compose stacks, Portainer stack create/update/upload,
  Nexus stack deployment and service lifecycle.
- Shared automation: command catalog, YAML handling, command result evidence,
  composition root, CLI dispatch and quality gates.

Explicit requirements:

- Remove destructive VM cleanup from normal init.
- Introduce `reconcile`, `reset`, and `destroy` as separate workflows.
- Truly separate PlatformServices, ArtifactServices and DeploymentServices.
- Rebuild CLI around workflow-level commands.
- Extract Nexus stack deployment from Artifacts/Nexus ownership.
- Strongly type command YAMLs.
- Introduce a state/inventory model.
- Force verification steps after every apply.

Implicit requirements:

- Keep `__main__.py` thin.
- Keep concrete adapter construction in `infrastructure/composition.py`.
- Do not weaken `.importlinter`, architecture tests or quality gates.
- Do not run live infrastructure during normal development or workflow
  creation.
- Keep tests mock-based and deterministic unless a later live workflow
  explicitly allows integration execution.
- Update arc42 and user/operator documentation when behavior changes.

Assumptions accepted for workflow creation:

- `init` means create or prepare missing managed resources without deletion.
- `reconcile` means converge existing managed state non-destructively.
- `reset` means explicit reinitialization of managed runtime resources and may
  run destructive commands only after a dedicated reset confirmation contract.
- `destroy` means explicit teardown of managed runtime resources and may run
  destructive commands only after a dedicated destroy confirmation contract.
- `verify` means inspect and report current state without mutating resources.
- Desired inventory is product configuration and may live under committed
  `infra/config` files.
- Observed runtime inventory and command evidence must live under an ignored
  local state/evidence root such as `.tiny-swarm-world/`.
- Exact reset/destroy retention rules are implementation acceptance criteria in
  Slice 01 and must be documented before destructive code is changed.

Non-goals:

- No live infrastructure execution during workflow creation.
- No Java example application changes.
- No Windows-native runtime expansion.
- No big-bang source tree move.
- No default CI job that runs live Multipass or Docker Swarm.
- No conversion of Platform, Artifacts and Deployment into microservices.
- No committed secrets, host-specific absolute paths or local state snapshots.

Risks:

- Current normal init can delete and purge all Multipass VMs.
- After the safety-first workflow execution, Multipass init safety regression
  tests are active. The known skipped test is a legacy network-service test at
  `tests/application/services/network/test_network_service.py`.
- Command workflow execution is filename-driven and currently coupled to UI
  runner adapters.
- Nexus bootstrap combines stack deployment, readiness, admin access and
  anonymous access.
- The responsibility ADR is accepted as a direction and partially implemented;
  package moves and deployment/artifact workflow wiring remain pending.
- arc42 runtime, deployment, decision, quality and risk pages are currently
  sparse and need synchronization when behavior changes.
- A dirty worktree was detected during workflow creation with source/preflight
  changes outside the workflow artifact edits. Workflow execution must resolve
  overlap before editing those files.

Open questions:

- Which exact CLI flag names and typed phrases should be used for reset and
  destroy confirmation?
- Which reset mode preserves Docker images, volumes, stack data and evidence?
- Which observed state files are retained after destroy?

Blocking questions:

- None for workflow creation. The open questions are execution gates for
  Slice 01 and stop implementation until answered in that slice.

Confidence level:

- 91 percent for workflow creation.
- Less than 90 percent for live execution or implementation without completing
  Slice 01.

Decision:

```text
READY_FOR_WORKFLOW
```

EPIC traceability:

- No `documentation/epics` files are present.
- Answer to "Does the implementation still match the EPIC?": cannot verify
  against a dedicated EPIC because no EPIC source exists.
- Temporary requirement baseline for this workflow: the user request, root
  `AGENTS.md`, root `QUALITY.md`, the existing architecture documentation,
  current arc42 files, subagent reviews, and
  `documentation/architecture/adr-separate-platform-artifacts-deployment.adoc`.

## Three Amigos Review

### Senior Requirement Engineer

- The requirement is actionable when the workflow defines operation taxonomy,
  destructive-operation policy, acceptance criteria and stop conditions.
- Missing EPIC traceability is recorded as a gap, not a workflow-creation
  blocker.
- Reset/destroy retention policy must be settled before implementation runs
  destructive code.

### Senior System Architect

- Platform, Artifacts and Deployment are responsibility boundaries in the
  Python automation, not independent runtime services.
- `composition.py` remains the wiring root.
- `__main__.py` remains a thin CLI entrypoint.
- Nexus stack deployment belongs to Deployment. Nexus repository and artifact
  behavior belongs to Artifacts.
- Typed command YAML and state/inventory contracts must precede workflow
  execution changes.

### Senior Python Automation Developer

- Command YAML should become a typed command catalog with command identity,
  intent, execution mode, safety class, effects and verification.
- A state/inventory model should separate desired configuration from observed
  facts for VMs, network, Docker, Swarm, stacks, services and artifacts.
- Normal init must not reference the current clean command YAML.
- Apply workflows must not return success until their verify step passes.

### Senior React Frontend Developer

- No React or browser frontend module is present.
- This workflow has no frontend build or UI implementation impact.
- User experience impact is CLI/operator UX: discoverable workflows, explicit
  destructive intent, clear refusal messages and actionable verification
  failures.
- Future dashboards or evidence viewers require a separate frontend workflow.

### Senior Tester

- Default tests must remain static or mock-based.
- Required gates must come from `QUALITY.md`.
- Tests must prove destructive cleanup is unreachable from `init` and
  `reconcile`.
- Tests must prove malformed command YAML fails closed.
- Tests must prove apply/verify result states are distinct.

### Dependency And Deadlock Validator

- Typed command YAML and state/inventory are foundational contracts and should
  precede workflow-level mutation changes.
- Service wiring separation and Nexus extraction can proceed after the
  architecture baseline stabilizes.
- CLI work depends on the workflow taxonomy and service builders.
- Verify-after-apply depends on typed command specs, inventory state and
  workflow dispatch.
- Documentation and legacy cleanup are last to avoid publishing unsupported
  behavior.

## Workflow Contracts

### Operation Taxonomy

| Workflow | Mutation | Destructive commands allowed | Purpose | Required result |
| --- | --- | --- | --- | --- |
| `init` | yes | no | create missing managed resources and fail on ambiguous conflicts | applied then verified |
| `reconcile` | yes | no | converge existing managed resources without deletion | reconciled then verified |
| `reset` | yes | yes, gated | explicitly reinitialize selected managed resources | reset then verified |
| `destroy` | yes | yes, gated | explicitly tear down selected managed resources | destroyed then verified absent |
| `verify` | no | no | inspect desired versus observed state | observed state report |

### Destructive Operation Policy

- Commands containing VM deletion, purge, stack deletion, volume removal,
  Docker prune, netplan deletion, socat teardown or credential reset must be
  classified as destructive in the typed command catalog.
- Destructive commands must declare `allowed_workflows` and may only be
  selected by `reset` or `destroy`.
- `init` and `reconcile` must fail at validation time if their command plan
  contains destructive commands.
- `reset` and `destroy` require explicit CLI intent and a confirmation contract
  defined in Slice 01 before implementation.
- Cleanup of generated evidence or local observed-state files is not implied by
  destroy unless a separate cleanup option is explicitly defined and tested.

### Command YAML Contract

Future command YAML entries must become typed command specs with at least:

- `id`
- `description`
- `intent`
- `execution_mode`
- `safety_class`
- `scope`
- `allowed_workflows`
- `parameters`
- `effects`
- `verify`
- `runner`
- `command_type`
- `vm_type`
- `command`

Validation must reject:

- missing required fields;
- duplicate indexes or IDs;
- unknown runner, command type, VM type, intent or safety class;
- destructive shell strings without destructive classification;
- command specs without a required verification declaration when they mutate
  state;
- workflow plans whose command safety class is not allowed for that workflow.

### State And Inventory Contract

- Desired inventory describes intended managed resources and belongs to product
  configuration, currently rooted under `infra/config`.
- Observed inventory describes discovered runtime facts and must be kept in an
  ignored local state root, not committed product config.
- Inventory must distinguish desired VMs, observed VM facts, network facts,
  Docker daemon facts, Swarm membership, stack deployment facts, service
  endpoint facts and artifact registry facts.
- Verification produces typed status: `not_checked`, `verified`,
  `failed_to_apply`, `failed_to_verify`, `blocked`, or `refused`.
- Domain models must not import YAML, filesystem, command runners, HTTP clients
  or infrastructure adapters.

### Verify-After-Apply Contract

- Every mutating workflow step must declare a verify step.
- A workflow may proceed to the next mutating step only after the previous
  verify step passes.
- Verification failure is not the same as apply failure and must be reported
  separately.
- Automatic retry or repair after failed verification is allowed only when the
  owning workflow explicitly defines the bounded retry behavior.
- No workflow may silently continue after missing verification evidence.

## Ordered Slices

### Slice 01 - Requirement And Safety Contract

Purpose:

- Define the operation taxonomy, destructive-operation policy, reset/destroy
  confirmation contract, inventory ownership assumptions and acceptance
  criteria before production code changes.

```yaml
slice_id: "01"
profile: "FULL_PATH"
owner: "Senior Requirement Engineer"
secondary_reviewers:
  - "Senior System Architect"
  - "Senior Tester"
  - "Senior Security Sandbox Engineer"
affected_files:
  - "documentation/workflow/**"
  - "documentation/architecture/**"
affected_modules: []
affected_contracts:
  - "operation-taxonomy"
  - "destructive-operation-policy"
  - "reset-destroy-confirmation"
dependencies: []
parallel_group: "A"
file_locks:
  - "documentation/workflow/**"
  - "documentation/architecture/**"
contract_locks:
  - "operation-taxonomy"
  - "destructive-operation-policy"
architecture_locks:
  - "live-infrastructure-safety"
quality_gates:
  targeted:
    - "git diff --check"
  required:
    - "git diff --check"
documentation:
  arc42: "check constraints, runtime, quality and risks"
  adr: "check destructive operation ADR need"
stop_conditions:
  - "reset or destroy confirmation semantics are unclear"
  - "init or reconcile semantics would still allow implicit deletion"
```

Allowed write scope:

- Workflow and architecture documentation only.

Done criteria:

- `init`, `reconcile`, `reset`, `destroy`, and `verify` are defined.
- Destructive operation policy is explicit.
- EPIC trace gap is recorded.
- Implementation slices have testable acceptance criteria.

Verification commands:

```bash
git diff --check
python3 -m json.tool documentation/workflow/context-pack.json
```

### Slice 02 - ADR And arc42 Baseline

Purpose:

- Keep the accepted Platform/Artifacts/Deployment responsibility ADR aligned
  with arc42 baseline sections before further boundary-moving slices.

```yaml
slice_id: "02"
profile: "FULL_PATH"
owner: "Senior System Architect"
secondary_reviewers:
  - "Senior Documentation Engineer"
  - "Senior Requirement Engineer"
affected_files:
  - "documentation/architecture/adr-separate-platform-artifacts-deployment.adoc"
  - "documentation/arc42/**"
  - "documentation/architecture/**"
affected_modules: []
affected_contracts:
  - "platform-artifacts-deployment-boundaries"
dependencies:
  - "01"
parallel_group: "B"
file_locks:
  - "documentation/architecture/**"
  - "documentation/arc42/**"
contract_locks:
  - "responsibility-boundaries"
architecture_locks:
  - "hexagonal-architecture"
  - "composition-root-wiring"
quality_gates:
  targeted:
    - "git diff --check"
    - "python3 tools/quality_gate.py arch-tests"
  required:
    - "git diff --check"
documentation:
  arc42: "update building blocks, runtime, deployment, decisions, quality, risks"
  adr: "accept or supersede responsibility ADR"
stop_conditions:
  - "Platform/Artifacts/Deployment are described as microservices without runtime evidence"
  - "ADR status remains ambiguous before source boundary moves"
```

Allowed write scope:

- Architecture documentation, ADRs and arc42 files.

Done criteria:

- Responsibility boundary decision is accepted or superseded.
- arc42 documents current and target responsibilities without claiming
  implementation that does not exist.

Verification commands:

```bash
git diff --check
python3 tools/quality_gate.py arch-tests
```

### Slice 03 - Typed Command YAML Contract

Purpose:

- Introduce typed command catalog models and validation so workflow plans can
  reject unsafe or malformed command specs before execution.

```yaml
slice_id: "03"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Tester"
  - "Senior System Architect"
affected_files:
  - "src/tiny_swarm_world/domain/command/**"
  - "src/tiny_swarm_world/application/ports/commands/**"
  - "src/tiny_swarm_world/application/services/commands/**"
  - "src/tiny_swarm_world/infrastructure/adapters/command_runner/**"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/**"
  - "infra/config/**/command_*.yaml"
  - "tests/domain/command/**"
  - "tests/infrastructure/adapters/command_runner/**"
affected_modules:
  - "tiny_swarm_world.domain.command"
  - "tiny_swarm_world.application.ports.commands"
  - "tiny_swarm_world.infrastructure.adapters.command_runner"
  - "tiny_swarm_world.infrastructure.adapters.repositories"
affected_contracts:
  - "typed-command-yaml-schema"
  - "command-safety-classification"
  - "command-verification-spec"
dependencies:
  - "01"
  - "02"
parallel_group: "C"
file_locks:
  - "src/tiny_swarm_world/domain/command/**"
  - "src/tiny_swarm_world/application/ports/commands/**"
  - "src/tiny_swarm_world/application/services/commands/**"
  - "src/tiny_swarm_world/infrastructure/adapters/command_runner/**"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/**"
  - "infra/config/**/command_*.yaml"
  - "tests/domain/command/**"
  - "tests/infrastructure/adapters/command_runner/**"
contract_locks:
  - "typed-command-yaml-schema"
  - "destructive-command-classification"
architecture_locks:
  - "domain-no-infrastructure-imports"
  - "application-no-infrastructure-imports"
quality_gates:
  targeted:
    - "python3 tools/quality_gate.py test"
    - "python3 tools/quality_gate.py typecheck"
    - "python3 tools/quality_gate.py arch-tests"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "update concepts and quality if schema becomes product contract"
  adr: "add ADR if typed command YAML is a lasting architecture decision"
stop_conditions:
  - "destructive command strings cannot be classified deterministically"
  - "YAML validation would require ad hoc string parsing instead of structured loading"
  - "application services would need concrete infrastructure imports"
```

Allowed write scope:

- Command domain, command ports/services, command YAML repository/runner
  adapters, command YAML files and matching tests.

Done criteria:

- YAML validation fails closed.
- Destructive commands declare safety class and allowed workflows.
- Existing command YAML files are either typed or explicitly bridged by a
  compatibility adapter with tests.
- Command workflow no longer relies on raw filename strings as the only
  application contract.

Verification commands:

```bash
python3 tools/quality_gate.py test
python3 tools/quality_gate.py typecheck
python3 tools/quality_gate.py quality
```

### Slice 04 - State And Inventory Model

Purpose:

- Add the domain and port contracts for desired inventory, observed state and
  verification evidence without live runtime mutation.

```yaml
slice_id: "04"
profile: "FULL_PATH"
owner: "Senior System Architect"
secondary_reviewers:
  - "Senior Python Automation Developer"
  - "Senior Tester"
affected_files:
  - "src/tiny_swarm_world/domain/**"
  - "src/tiny_swarm_world/application/ports/**"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/**"
  - "infra/config/vm/**"
  - "tests/domain/**"
  - "tests/infrastructure/adapters/repositories/**"
affected_modules:
  - "tiny_swarm_world.domain"
  - "tiny_swarm_world.application.ports"
  - "tiny_swarm_world.infrastructure.adapters.repositories"
affected_contracts:
  - "desired-inventory"
  - "observed-state"
  - "verification-result"
dependencies:
  - "01"
  - "02"
parallel_group: "C"
file_locks:
  - "src/tiny_swarm_world/domain/**"
  - "src/tiny_swarm_world/application/ports/**"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/**"
  - "infra/config/vm/**"
  - "tests/domain/**"
  - "tests/infrastructure/adapters/repositories/**"
contract_locks:
  - "state-inventory-model"
architecture_locks:
  - "domain-isolation"
  - "observed-state-not-committed"
quality_gates:
  targeted:
    - "python3 tools/quality_gate.py test"
    - "python3 tools/quality_gate.py typecheck"
    - "python3 tools/quality_gate.py arch-tests"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "update concepts and runtime view"
  adr: "add ADR if state persistence authority is established"
stop_conditions:
  - "observed host state would be committed to product config"
  - "domain model would import YAML, filesystem, command runner or HTTP details"
  - "inventory persistence authority remains undefined"
```

Allowed write scope:

- State/inventory domain objects, ports, repository adapters, tests and
  documentation needed to define ownership.

Done criteria:

- Desired inventory and observed state are separate concepts.
- Verification status is typed.
- Observed state storage is ignored or otherwise prevented from being committed.
- Tests cover missing, stale and conflicting observed state.

Verification commands:

```bash
python3 tools/quality_gate.py test
python3 tools/quality_gate.py typecheck
python3 tools/quality_gate.py quality
```

### Slice 05 - Workflow Taxonomy And Non-Destructive Init

Purpose:

- Replace destructive normal init behavior with explicit platform workflows for
  init, reconcile, reset, destroy and verify.

```yaml
slice_id: "05"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Tester"
  - "Senior Security Sandbox Engineer"
  - "Senior System Architect"
affected_files:
  - "src/tiny_swarm_world/application/services/platform/**"
  - "src/tiny_swarm_world/application/services/multipass/**"
  - "src/tiny_swarm_world/application/services/network/**"
  - "src/tiny_swarm_world/application/services/vm/**"
  - "src/tiny_swarm_world/application/ports/commands/**"
  - "infra/config/multipass/**"
  - "infra/config/docker/**"
  - "infra/config/network/**"
  - "tests/application/services/platform/**"
  - "tests/application/services/multipass/**"
affected_modules:
  - "tiny_swarm_world.application.services.platform"
  - "tiny_swarm_world.application.services.multipass"
  - "tiny_swarm_world.application.services.network"
  - "tiny_swarm_world.application.services.vm"
affected_contracts:
  - "platform-init"
  - "platform-reconcile"
  - "platform-reset"
  - "platform-destroy"
  - "platform-verify"
dependencies:
  - "03"
  - "04"
parallel_group: "D"
file_locks:
  - "src/tiny_swarm_world/application/services/platform/**"
  - "src/tiny_swarm_world/application/services/multipass/**"
  - "src/tiny_swarm_world/application/services/network/**"
  - "src/tiny_swarm_world/application/services/vm/**"
  - "infra/config/multipass/**"
  - "infra/config/docker/**"
  - "infra/config/network/**"
  - "tests/application/services/platform/**"
  - "tests/application/services/multipass/**"
contract_locks:
  - "platform-workflow-taxonomy"
  - "destructive-operation-policy"
architecture_locks:
  - "platform-responsibility-boundary"
  - "external-command-safety"
quality_gates:
  targeted:
    - "python3 tools/quality_gate.py test"
    - "python3 tools/quality_gate.py typecheck"
    - "python3 tools/quality_gate.py arch-tests"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "update runtime view when workflows are implemented"
  adr: "destructive operation semantics ADR if not already added"
stop_conditions:
  - "init still calls command_multipass_clean_repository_yaml.yaml"
  - "init or reconcile can select multipass delete or purge"
  - "reset or destroy can run without explicit confirmation contract"
```

Allowed write scope:

- Platform application workflows, compatibility wrappers, platform command
  YAML references and tests.

Done criteria:

- Normal init does not run clean/delete/purge.
- `reconcile`, `reset`, `destroy` and `verify` are distinct use cases.
- Reset/destroy are gated.
- Tests prove destructive commands are unreachable from init/reconcile.

Verification commands:

```bash
python3 tools/quality_gate.py test
python3 tools/quality_gate.py quality
```

### Slice 06 - Service Wiring Separation

Purpose:

- Introduce real `PlatformServices`, `ArtifactServices`, and
  `DeploymentServices` composition boundaries and remove the platform-only
  application alias.

```yaml
slice_id: "06"
profile: "FULL_PATH"
owner: "Senior System Architect"
secondary_reviewers:
  - "Senior Python Automation Developer"
  - "Senior Tester"
affected_files:
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "src/tiny_swarm_world/application/services/platform/**"
  - "src/tiny_swarm_world/application/services/artifacts/**"
  - "src/tiny_swarm_world/application/services/deployment/**"
  - "tests/infrastructure/test_composition.py"
  - "tests/application/services/platform/**"
  - "tests/application/services/artifacts/**"
  - "tests/application/services/deployment/**"
  - "tests/architecture/**"
affected_modules:
  - "tiny_swarm_world.infrastructure.composition"
  - "tiny_swarm_world.application.services.platform"
  - "tiny_swarm_world.application.services.artifacts"
  - "tiny_swarm_world.application.services.deployment"
affected_contracts:
  - "composition-service-builders"
dependencies:
  - "02"
  - "04"
parallel_group: "D"
file_locks:
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "src/tiny_swarm_world/application/services/platform/**"
  - "src/tiny_swarm_world/application/services/artifacts/**"
  - "src/tiny_swarm_world/application/services/deployment/**"
  - "tests/infrastructure/test_composition.py"
  - "tests/application/services/**"
  - "tests/architecture/**"
contract_locks:
  - "composition-service-builders"
architecture_locks:
  - "composition-root-wiring"
  - "thin-entrypoint"
  - "responsibility-boundaries"
quality_gates:
  targeted:
    - "python3 tools/quality_gate.py arch-tests"
    - "python3 tools/quality_gate.py test"
    - "python3 tools/quality_gate.py typecheck"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "update building blocks"
  adr: "not required unless responsibility ADR changes"
stop_conditions:
  - "application services import concrete infrastructure adapters"
  - "ApplicationServices remains a platform-only alias"
  - "service builders create external side effects during construction"
```

Allowed write scope:

- Composition root, service namespace exports and related tests.

Done criteria:

- Separate builders and dataclasses exist for Platform, Artifacts and
  Deployment.
- Constructors remain side-effect free.
- `__main__.py` still does not import concrete adapters.
- Architecture tests protect the split.

Verification commands:

```bash
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py test
python3 tools/quality_gate.py quality
```

### Slice 07 - Nexus Stack Deployment Extraction

Purpose:

- Move Nexus stack deployment behavior to Deployment ownership while keeping
  Nexus repository and artifact bootstrap behavior in Artifacts.

```yaml
slice_id: "07"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "src/tiny_swarm_world/application/services/deployment/**"
  - "src/tiny_swarm_world/application/services/artifacts/**"
  - "src/tiny_swarm_world/application/services/nexus/**"
  - "src/tiny_swarm_world/application/ports/clients/port_portainer_client.py"
  - "src/tiny_swarm_world/application/ports/repositories/port_compose_file_repository.py"
  - "tests/application/services/deployment/**"
  - "tests/application/services/artifacts/**"
  - "tests/application/services/nexus/**"
  - "tests/architecture/**"
  - "documentation/arc42/**"
affected_modules:
  - "tiny_swarm_world.application.services.deployment"
  - "tiny_swarm_world.application.services.artifacts"
  - "tiny_swarm_world.application.services.nexus"
affected_contracts:
  - "deployment-stack-lifecycle"
  - "nexus-artifact-bootstrap"
dependencies:
  - "06"
parallel_group: "E"
file_locks:
  - "src/tiny_swarm_world/application/services/deployment/**"
  - "src/tiny_swarm_world/application/services/artifacts/**"
  - "src/tiny_swarm_world/application/services/nexus/**"
  - "src/tiny_swarm_world/application/ports/clients/port_portainer_client.py"
  - "src/tiny_swarm_world/application/ports/repositories/port_compose_file_repository.py"
  - "tests/application/services/deployment/**"
  - "tests/application/services/artifacts/**"
  - "tests/application/services/nexus/**"
  - "tests/architecture/**"
  - "documentation/arc42/**"
contract_locks:
  - "nexus-stack-deployment-boundary"
architecture_locks:
  - "deployment-responsibility-boundary"
  - "artifact-responsibility-boundary"
quality_gates:
  targeted:
    - "python3 tools/quality_gate.py test"
    - "python3 tools/quality_gate.py arch-tests"
    - "python3 tools/quality_gate.py typecheck"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "update deployment view and building blocks"
  adr: "not required unless responsibility decision changes"
stop_conditions:
  - "Nexus artifact services still import Portainer or compose repository ports after extraction"
  - "deployment service reaches into Nexus repository internals"
  - "live Portainer or Nexus calls are needed for tests"
```

Allowed write scope:

- Deployment/artifact/Nexus application services, relevant ports and tests.
- arc42 documentation for stack lifecycle ownership.

Done criteria:

- Stack deployment is generalized or moved under Deployment.
- Artifact services depend on deployment readiness by explicit input, not by
  deploying stacks themselves.
- Tests prove artifact services do not export or import stack deployment.

Verification commands:

```bash
python3 tools/quality_gate.py test
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py quality
```

### Slice 08 - Workflow-Level CLI

Purpose:

- Replace the public low-level service CLI with workflow-level commands while
  keeping the entrypoint thin and all wiring in composition.

```yaml
slice_id: "08"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Tester"
  - "Senior UX Designer"
  - "Senior System Architect"
affected_files:
  - "src/tiny_swarm_world/__main__.py"
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "src/tiny_swarm_world/application/services/**"
  - "tests/test_package_entrypoint.py"
  - "tests/infrastructure/test_composition.py"
  - "README.md"
  - "documentation/user_guide/**"
  - "documentation/arc42/**"
affected_modules:
  - "tiny_swarm_world.__main__"
  - "tiny_swarm_world.infrastructure.composition"
  - "tiny_swarm_world.application.services"
affected_contracts:
  - "workflow-level-cli"
dependencies:
  - "05"
  - "06"
  - "07"
parallel_group: "F"
file_locks:
  - "src/tiny_swarm_world/__main__.py"
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "src/tiny_swarm_world/application/services/**"
  - "tests/test_package_entrypoint.py"
  - "tests/infrastructure/test_composition.py"
  - "README.md"
  - "documentation/user_guide/**"
  - "documentation/arc42/**"
contract_locks:
  - "workflow-level-cli"
architecture_locks:
  - "thin-entrypoint"
  - "composition-root-wiring"
quality_gates:
  targeted:
    - "python3 tools/quality_gate.py test"
    - "python3 tools/quality_gate.py typecheck"
    - "python3 tools/quality_gate.py arch-tests"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "update building blocks and runtime view"
  adr: "not required unless public CLI compatibility decision is architectural"
stop_conditions:
  - "__main__.py embeds low-level orchestration logic"
  - "workflow CLI wiring requires concrete adapter construction outside infrastructure/composition.py"
  - "composition changes create live infrastructure side effects during construction"
  - "list/help paths construct live services"
  - "destroy or reset can run without explicit confirmation"
  - "arc42 building-block and runtime-view updates would describe unimplemented behavior as implemented"
```

Allowed write scope:

- CLI, composition, workflow dispatch services, CLI tests and CLI docs.

Done criteria:

- CLI exposes workflow-level commands such as platform init/reconcile/reset/
  destroy/verify and deployment/artifact workflows.
- Listing workflows does not build services.
- No command runs by default.
- Destructive workflow commands require explicit confirmation.

Verification commands:

```bash
python3 tools/quality_gate.py test
python3 tools/quality_gate.py quality
```

### Slice 09 - Verify After Every Apply

Purpose:

- Enforce verification after every mutating apply step across platform and
  deployment workflows.

```yaml
slice_id: "09"
profile: "FULL_PATH"
owner: "Senior Tester"
secondary_reviewers:
  - "Senior Python Automation Developer"
  - "Senior System Architect"
affected_files:
  - "src/tiny_swarm_world/application/services/platform/**"
  - "src/tiny_swarm_world/application/services/deployment/**"
  - "src/tiny_swarm_world/application/ports/commands/**"
  - "src/tiny_swarm_world/domain/**"
  - "infra/config/**/command_*.yaml"
  - "tests/application/services/platform/**"
  - "tests/application/services/deployment/**"
  - "tests/domain/**"
  - "tests/infrastructure/adapters/command_runner/**"
affected_modules:
  - "tiny_swarm_world.application.services.platform"
  - "tiny_swarm_world.application.services.deployment"
  - "tiny_swarm_world.application.ports.commands"
  - "tiny_swarm_world.domain"
affected_contracts:
  - "verify-after-apply"
  - "verification-evidence"
dependencies:
  - "03"
  - "04"
  - "05"
  - "07"
  - "08"
parallel_group: "G"
file_locks:
  - "src/tiny_swarm_world/application/services/platform/**"
  - "src/tiny_swarm_world/application/services/deployment/**"
  - "src/tiny_swarm_world/application/ports/commands/**"
  - "src/tiny_swarm_world/domain/**"
  - "infra/config/**/command_*.yaml"
  - "tests/application/services/platform/**"
  - "tests/application/services/deployment/**"
  - "tests/domain/**"
  - "tests/infrastructure/adapters/command_runner/**"
contract_locks:
  - "verify-after-apply"
  - "command-verification-spec"
architecture_locks:
  - "failure-propagation"
  - "evidence-integrity"
quality_gates:
  targeted:
    - "python3 tools/quality_gate.py test"
    - "python3 tools/quality_gate.py typecheck"
    - "python3 tools/quality_gate.py arch-tests"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "update runtime and quality requirements"
  adr: "add ADR if verification semantics become architecture decision"
stop_conditions:
  - "mutating command has no verification spec"
  - "workflow continues after failed verification"
  - "verification failure is collapsed into generic command failure"
  - "verification requires live infrastructure during default quality gate"
```

Allowed write scope:

- Platform/deployment workflow code, verification domain models, command YAML
  verification specs and tests.

Done criteria:

- Every apply step has an immediate verification step.
- Verification failures stop workflow execution.
- Apply failure and verify failure are reported distinctly.
- Tests prove no mutating workflow can succeed without verification evidence.

Verification commands:

```bash
python3 tools/quality_gate.py test
python3 tools/quality_gate.py typecheck
python3 tools/quality_gate.py quality
```

### Slice 10 - Documentation, Quality Sync, And Legacy Quarantine

Purpose:

- Synchronize documentation, quality evidence and legacy cleanup notes after
  implementation slices have proven supported replacement workflows.

```yaml
slice_id: "10"
profile: "FULL_PATH"
owner: "Senior Documentation Engineer"
secondary_reviewers:
  - "Senior Tester"
  - "Senior System Architect"
  - "Senior Python Automation Developer"
affected_files:
  - "README.md"
  - "documentation/**"
  - "tests/architecture/**"
  - "infra/swarm/**"
  - "infra/prepare/**"
affected_modules: []
affected_contracts:
  - "operator-runbook"
  - "legacy-quarantine-policy"
dependencies:
  - "02"
  - "03"
  - "04"
  - "05"
  - "06"
  - "07"
  - "08"
  - "09"
parallel_group: "H"
file_locks:
  - "README.md"
  - "documentation/**"
  - "tests/architecture/**"
  - "infra/swarm/**"
  - "infra/prepare/**"
contract_locks:
  - "operator-runbook"
  - "legacy-quarantine-policy"
architecture_locks:
  - "documentation-authority"
  - "live-infrastructure-safety"
quality_gates:
  targeted:
    - "git diff --check"
    - "python3 tools/quality_gate.py arch-tests"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "final synchronization across building blocks, runtime, deployment, concepts, quality and risks"
  adr: "check all new architecture decisions are listed"
stop_conditions:
  - "documentation claims live validation without evidence"
  - "legacy scripts are removed before supported replacements are verified"
  - "runbook contains host-specific secrets or absolute paths"
```

Allowed write scope:

- Documentation, architecture tests and explicitly approved legacy quarantine
  files only.

Current execution note:

- The safety-first Slice 10 in
  `documentation/workflow/workflow-init-safety-first-control-plane.md` is a
  documentation-only checkpoint. The broader roadmap scope above lists
  architecture tests and legacy script areas for future cleanup, but this
  safety-first execution must not edit `tests/**`, `infra/swarm/**`, or
  `infra/prepare/**` without explicit approval outside the doc-only slice.

Done criteria:

- README and user docs describe workflow-level commands.
- arc42 and ADR index match implemented behavior.
- Legacy/destructive scripts are marked, quarantined or removed only after
  replacement workflows and references are proven.
- Final quality gate result is recorded.

Verification commands:

```bash
git diff --check
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py quality
```

## Slice Dependency Graph

```text
01
  -> 02
      -> 03
      -> 04
          -> 05
          -> 06
              -> 07
                  -> 08
                      -> 09
                          -> 10
```

Parallelization:

- Slice 03 and Slice 04 may run in parallel after Slice 02 if write scopes stay
  disjoint.
- Slice 05 and Slice 06 may overlap only after their shared contracts are
  stable and file ownership is split explicitly.
- Slice 10 can draft documentation structure early, but final content depends
  on implemented command names, verification states and quality evidence.

## Role Ownership Map

- Senior Workflow Architect: dependency graph, slice metadata and execution
  readiness.
- Senior Requirement Engineer: operation taxonomy, destructive policy,
  acceptance criteria and EPIC traceability.
- Senior System Architect: responsibility boundaries, ADRs, arc42 and
  composition constraints.
- Senior Python Automation Developer: command YAML typing, state/inventory
  implementation, workflow use cases, service builders and CLI dispatch.
- Senior Tester: regression tests, architecture tests, verify-after-apply and
  quality gate evidence.
- Senior Security Sandbox Engineer: destructive operation gates, live
  infrastructure refusal and secret/state safety.
- Senior Documentation Engineer: README, arc42, user guide and legacy
  quarantine documentation.
- Senior React Frontend Developer: no implementation role for this workflow;
  reviews only CLI/operator UX impact.

## Subagent Review Summary

Subagent reviews completed during workflow creation:

- Senior Requirement Engineer: requirement classification, acceptance criteria,
  non-goals, EPIC trace gap and recommended slices.
- Senior System Architect: architecture constraints, boundary risks, ADR/arc42
  needs, affected files and stop conditions.
- Senior Python Automation Developer: command/YAML, inventory, workflow and
  service split implementation sequence.
- Senior React Frontend Developer: confirmed no frontend module and scoped UX
  impact to CLI/operator behavior.
- Senior Tester: safe targeted gates, regression tests per slice, acceptance
  checks and stop conditions.

No subagent was authorized to run live infrastructure commands.

## Quality-Gate Expectations

Required final gate for implementation slices:

```bash
python3 tools/quality_gate.py quality
```

Targeted gates during development:

```bash
python3 tools/quality_gate.py lint
python3 tools/quality_gate.py arch-lint
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py typecheck
python3 tools/quality_gate.py test
```

Documentation-only gate:

```bash
git diff --check
```

Workflow creation checks:

```bash
git diff --check
python3 -m json.tool documentation/workflow/context-pack.json
```

## Documentation Synchronization Points

- After Slice 01: workflow safety and destructive operation semantics are
  stable enough for implementation.
- After Slice 02: ADR/arc42 baseline authorizes boundary-moving slices.
- After Slice 03: command YAML documentation explains typed command specs.
- After Slice 04: state/inventory documentation explains desired versus
  observed state.
- After Slice 05: operator docs no longer describe destructive init as normal.
- After Slice 08: README and user guide describe workflow-level CLI commands.
- After Slice 09: runtime and quality docs describe verify-after-apply
  evidence and failure semantics.
- After Slice 10: legacy script status and final quality evidence are recorded.

## Stop Conditions

Stop workflow execution when:

- active branch is not `architecture/workflow-init-service-boundaries-20260523`;
- unrelated worktree changes overlap the active slice write scope;
- `init` still implies `multipass delete --all` or `multipass purge`;
- `reconcile` can run destructive cleanup;
- `reset` or `destroy` can run without explicit confirmation;
- typed command YAML, inventory ownership or destructive operation policy is
  unclear in the active slice;
- Platform/Artifacts/Deployment are described as microservices without runtime
  independence evidence;
- application services import concrete infrastructure adapters;
- Nexus stack deployment remains artifact-owned after extraction begins;
- a mutating workflow step lacks a verification spec;
- a workflow continues after failed verification;
- a required quality gate fails;
- a test is skipped or weakened to make a gate pass;
- live infrastructure would be needed for a default quality gate;
- user secrets, host-specific paths or local observed state would be committed.

## Commit And Push Plan

- Do not commit or push unless explicitly requested.
- Commit workflow-creation documentation separately from implementation slices.
- Each implementation slice should be committed only after its required gates
  pass or documented blockers are accepted.
- Do not include generated evidence, local state, logs, virtual environments,
  caches or secrets.
- Use the repository git commit preparation workflow before committing or
  pushing.

## Definition Of Done

This workflow is done when:

- normal init is non-destructive;
- `reconcile`, `reset`, `destroy` and `verify` are separate workflows;
- PlatformServices, ArtifactServices and DeploymentServices are real
  composition boundaries;
- CLI exposes workflows rather than only low-level service names;
- Nexus stack deployment is Deployment-owned;
- command YAMLs are typed and safety-classified;
- desired inventory, observed state and verification evidence are modeled;
- every mutating apply step is followed by verification;
- docs and architecture tests reflect implemented behavior;
- `python3 tools/quality_gate.py quality` passes for implementation slices;
- no live infrastructure action is part of the default quality gate.

## Handoff To Workflow Execute

Workflow execution must begin with Slice 01. It must not jump directly to
source changes or live validation.

Before any implementation slice edits source files, the executor must inspect
the current worktree and resolve ownership of any existing changes that overlap
the slice file locks. The workflow authoring step observed source/preflight
changes outside `documentation/workflow/**`; these must be treated as user or
parallel work unless the user explicitly says otherwise.

## arc42 Check Status

Checked files:

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
- `documentation/architecture/adr-separate-platform-artifacts-deployment.adoc`

Current status:

- No arc42 content was changed during workflow creation.
- Slice 02 must update arc42 and ADR status before implementation slices move
  responsibility boundaries.
