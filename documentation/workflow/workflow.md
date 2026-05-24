# Workflow: Autonomous Runnable Setup

## Executive Summary

This workflow creates the governed execution plan for making Tiny Swarm World
self-installing into a runnable local system from a Linux or WSL shell.

The target is one canonical, consent-gated setup path that can prepare the
platform, configure the core Docker Swarm services, verify the result, and
leave operator-readable evidence. The workflow is intentionally safety-first:
workflow creation does not run live infrastructure commands, and execution
must not mutate Multipass, Docker Swarm, netplan, socat, Portainer, Nexus,
Jenkins, RabbitMQ, SonarQube, Swagger/NGINX, images, registries, or stacks
unless the active execution slice explicitly owns that behavior and the user
has provided live-infrastructure consent.

Subagent review found that the repository already has the right protected
shape, but not the end-to-end installer:

- The supported Python CLI exists and is thin.
- Static preflight exists and can check host, dependency, port, secret,
  resource, ignore-policy, and forbidden-secret-fingerprint requirements.
- Platform `init` and `reconcile` are live-consent gated, but currently block
  before apply until command-backed verification contracts exist.
- Artifact and Deployment workflow names exist, but return blocked contract
  results until Nexus, registry, Portainer, stack, and observed-state contracts
  are implemented.
- Former direct setup scripts under `infra/prepare` and host-side
  orchestration scripts under `infra/compose` are retired. Legacy scripts under
  `infra/swarm` must not become the canonical setup path by simple promotion.
- No React/browser frontend is in scope. Setup feedback belongs to the
  console/status UI and CLI output.

The workflow is a FULL_PATH workflow because it can touch requirements,
architecture decisions, Python automation, infrastructure adapters, YAML
configuration, service contracts, tests, documentation, and quality gates.

## Target Picture

### Verified Baseline At Workflow Creation

- Active workflow version:

```text
autonomous-runnable-setup-v1.0.0
```

- Active workflow branch:

```bash
codex/workflow-autonomous-setup-20260524
```

- Root `AGENTS.md` defines Tiny Swarm World as a Linux/WSL-only Python
  automation project with hexagonal architecture and Docker Swarm as the
  current runtime model.
- Root `QUALITY.md` defines the preferred full gate:

```bash
python3 tools/quality_gate.py quality
```

- `documentation/epics/system-unification.md` says the implementation matches
  the intended system only partially, with documented blockers.
- `documentation/arc42/09_architecture_decisions.adoc` keeps ADR files under
  `documentation/architecture/adr-*.adoc`; `documentation/adr/**` is not the
  current convention.
- `src/tiny_swarm_world/__main__.py` provides `--list-workflows`,
  `--preflight`, live-consent checks, destructive confirmation checks, and
  Platform/Artifacts/Deployment workflow dispatch.
- `src/tiny_swarm_world/infrastructure/composition.py` is the concrete wiring
  root for Platform, Artifact, and Deployment service bundles.
- `documentation/system/live-operation-surfaces.adoc` classifies direct live
  scripts and assets. Default verification remains static or mocked.
- No `package.json`, TSX/JSX, browser router, or React build surface is part
  of the current project.

### Target Outcome

The completed workflow must produce:

- an installer-specific requirement baseline for "runnable setup";
- an explicit decision on autonomous setup safety, live consent, credentials,
  host prerequisites, and optional live smoke validation;
- preflight and setup manifest contracts for prerequisites, resources, ports,
  secrets, ignored local paths, and selected service profile;
- command-backed verification contracts for platform steps that can safely
  unblock `platform init` and `platform reconcile`;
- observed inventory and verification evidence that remain under ignored
  `.tiny-swarm-world/` paths and never persist raw command payloads or secrets;
- guarded Portainer deployment contracts;
- guarded Nexus/artifact registry contracts;
- default service stack deployment and verification contracts for Portainer,
  Nexus, Jenkins, RabbitMQ, SonarQube, and Swagger/NGINX;
- one canonical autonomous setup CLI workflow that orchestrates platform,
  artifacts, deployment, and final verification after live consent;
- console/status output that distinguishes refused, blocked, failed-to-apply,
  failed-to-verify, resource-gated, and completed phases;
- README, installation, deployment, system, arc42, workflow, and live-operation
  documentation synchronized with actual behavior;
- exact targeted and full quality-gate evidence.

## Requirement Clarification Record

Original request:

```text
workflow create with subagents:
Erstelle ein setup damit sich das system selbstaendig lauffaehig installieren laesst
```

Interpreted intent:

- Create a new active workflow with delegated subagent review.
- Plan a setup path that can make Tiny Swarm World install itself into a
  runnable local state.
- Keep the setup path Linux/WSL-only, Docker Swarm first, Python automation
  first, and governed by the existing safety model.
- Use the workflow for later `workflow execute with subagents` implementation.

Change type:

- Workflow creation and autonomous setup planning.

Affected process strand:

- FULL_PATH setup enablement: requirements, architecture, preflight,
  command-backed verification, inventory/evidence, platform workflows,
  artifact workflows, deployment workflows, console status, docs, and quality
  gates.

Affected architecture area:

- Platform, Artifacts, Deployment, Shared, CLI workflow contracts, preflight,
  verify-after-apply, inventory/evidence persistence, Portainer/Nexus client
  boundaries, compose assets, console/status UI, legacy live-operation
  surfaces, arc42, and workflow governance.

Explicit requirements:

- Use subagents.
- Create a workflow.
- Create a setup path so the system can install itself into a runnable state.

Implicit requirements:

- Preserve Linux/WSL-only operation and POSIX command examples.
- Preserve hexagonal architecture and application-to-port dependencies.
- Keep concrete adapter construction in
  `src/tiny_swarm_world/infrastructure/composition.py`.
- Keep `src/tiny_swarm_world/__main__.py` thin.
- Do not run live infrastructure commands during workflow creation.
- Use `QUALITY.md` as the quality-command authority.
- Treat console/status UI as terminal UI, not React/browser frontend.
- Do not reintroduce Java, Maven, or Spring Boot setup architecture.
- Keep secrets out of runtime evidence; this local non-production system may
  retain reviewed static compatibility passwords where they are intentionally
  part of the setup baseline.

Accepted assumptions:

- "Autonomous" means one orchestrated setup command after explicit
  live-infrastructure consent, not silent unattended host mutation.
- Host prerequisites such as Multipass, Docker CLI, socat, curl, and jq are
  verified and documented first. Installing host packages automatically
  requires a dedicated ADR or explicit slice decision.
- The default runnable target is the full local system: Platform plus
  Portainer, Nexus, Jenkins, RabbitMQ, SonarQube, and Swagger/NGINX. Resource
  constraints may produce a documented resource-gated result, not a false pass.
- Credentials are supplied through environment variables or ignored local
  files. No new default passwords, tokens, host IPs, or user-specific absolute
  paths may be committed.
- Live integration validation is not part of the default quality gate. It may
  be planned as an optional final smoke run only after explicit user approval
  on a disposable local environment.
- The installer-specific baseline extends the existing system-unification EPIC
  instead of replacing it.

Non-goals:

- No live infrastructure execution during workflow creation.
- No Kubernetes-first pivot.
- No browser React frontend work.
- No Spring Boot or Java-driven setup architecture.
- No microservice extraction.
- No promotion of direct legacy scripts as the canonical installer without
  ports, adapters, tests, consent controls, and documentation.
- No weakening of `.importlinter`, architecture tests, or `QUALITY.md`.
- No committing generated caches, local runtime evidence, credentials, logs,
  virtual environments, or IDE state.

Risks:

- Installer scope, consent, credentials, and "runnable" acceptance criteria
  need an explicit first execution slice before implementation.
- Current platform mutating workflows block before apply until verification
  contracts are implemented.
- Artifact and Deployment workflows are explicit but currently blocked.
- Command catalog entries are shell-oriented and mostly manual verification.
- `MultipassDockerSwarmInit` touches Swarm token flow and needs redaction and
  evidence hardening before live autonomous setup.
- Direct scripts can mutate VMs, networking, Docker, stacks, credentials, and
  volumes outside CLI consent.
- Full stack setup can exceed host resources and must report resource-gated
  status honestly.

Open questions converted into slice decisions:

- Whether host prerequisites may be installed automatically.
- Whether non-interactive live consent is ever acceptable.
- Whether a partial target profile is supported for resource-constrained hosts.
- Which secret source format becomes canonical for unattended setup.
- Which optional live smoke environment is acceptable.

Blocking questions:

- None for workflow creation. The questions above are blocking for later
  implementation slices until resolved by Slice 01 or Slice 02.

Confidence level:

```text
82 percent
```

Decision:

```text
PROCEED_WITH_ACCEPTED_ASSUMPTIONS
```

Rationale:

- The user requested workflow creation, not immediate live setup execution.
- Ambiguities can be converted into explicit early workflow slices and stop
  conditions without guessing product behavior.
- The repository already contains enough guarded CLI, preflight, architecture,
  and quality structure to author a safe execution plan.

## Execution Profile

```text
executionProfile=FULL_PATH
reason=The workflow can affect architecture decisions, Python automation,
runtime workflow wiring, live-operation safety, service contracts, docs, and
quality gates.
requiredFullReviews=senior_requirement_engineer, senior_system_architect,
senior_python_automation_developer, senior_react_frontend as React/browser
scope guard, senior_tester, senior_workflow_architect
requiredConditionalReviews=senior_devops, senior_documentation_engineer,
senior_security_sandbox_engineer, console-status-ui-developer,
resilience-engineering, adr-steward, git_commit_reviewer
requiredQualityChecks=git diff --check, targeted unit/static gates by slice,
and python3 tools/quality_gate.py quality before final release when practical
stopConditions=unverified branch, stale workflow context, live command without
explicit approval, missing setup requirement baseline, unclear ADR convention,
manual-only verification for an autonomous live step, secret leakage,
architecture boundary violation, or quality-gate weakening
```

## Scope

### Allowed Write Scope

The workflow may change:

```text
documentation/workflow/**
documentation/epics/**
documentation/architecture/**
documentation/arc42/**
documentation/deployment/**
documentation/system/**
documentation/user_guide/**
README.md
src/tiny_swarm_world/__main__.py
src/tiny_swarm_world/domain/**
src/tiny_swarm_world/application/**
src/tiny_swarm_world/infrastructure/composition.py
src/tiny_swarm_world/infrastructure/adapters/command_runner/**
src/tiny_swarm_world/infrastructure/adapters/clients/**
src/tiny_swarm_world/infrastructure/adapters/repositories/**
src/tiny_swarm_world/infrastructure/adapters/preflight/**
src/tiny_swarm_world/infrastructure/adapters/ui/**
infra/config/**
infra/compose/**
tests/**
.importlinter only with Senior Tester and Senior System Architect approval
QUALITY.md only if the quality authority is explicitly wrong
AGENTS.md only if root governance must be corrected
```

### Forbidden Write Scope

The workflow must not change:

```text
external static-analysis CI configuration
generated caches
local virtual environments
logs
IDE state
.tiny-swarm-world/**
.env
.env.local
```

Direct modification of live scripts under `infra/swarm` is allowed only when a
slice explicitly owns migration, quarantine, or compatibility updates and
verification remains static or mocked unless the user separately approves live
execution. Former executable setup surfaces under `infra/prepare` and
host-side orchestration scripts under `infra/compose` must not be restored.

## Architecture Constraints

- Preserve the hexagonal architecture.
- Domain modules must not import application, infrastructure, filesystem,
  YAML, HTTP, Docker, logging, command runner, UI adapter, or dependency
  injection concerns.
- Application services may orchestrate ports and domain objects but must not
  embed low-level shell, filesystem, HTTP, curses, Docker, or Portainer/Nexus
  details directly.
- Infrastructure adapters implement ports and contain technology-specific
  behavior.
- `src/tiny_swarm_world/infrastructure/composition.py` remains the concrete
  composition root.
- `src/tiny_swarm_world/__main__.py` remains thin.
- Platform, Artifacts, Deployment, Shared, and Console/status UI remain
  in-process responsibility boundaries, not extracted microservices.
- Direct live scripts are reference material or legacy surfaces, not the
  canonical installer contract.
- Console/status UI is terminal-only.
- Java/Maven project structure is retired unless a later explicit task changes
  scope.
- Kubernetes awareness must not displace Docker Swarm as the current target.

## Python Automation Assessment

Python automation is the primary implementation surface. The setup workflow
must address these incomplete areas in small, testable slices:

- runnable-state acceptance criteria are not installer-specific yet;
- platform mutating workflows expose step IDs and block reasons, but lack
  command-backed verification;
- observed inventory and verification evidence exist as concepts, but service
  readiness and stack health collection are not wired end to end;
- artifact workflows are blocked until image build/push, Nexus repository, and
  registry verification contracts exist;
- deployment workflows are blocked until Portainer stack apply and service
  observed-state verification ports exist;
- direct scripts contain useful operational knowledge but bypass CLI consent
  and must be migrated through ports/adapters before becoming canonical;
- setup orchestration needs explicit async phase sequencing, failure
  classification, retries, timeouts, recovery guidance, and redacted evidence.

## Frontend And Console UI Assessment

No React or browser frontend exists. The mandatory Senior React Frontend role
is a read-only scope guard and reports N/A for browser React.

Any user-facing setup progress belongs to the CLI and console/status UI:

- status labels must not rely on color alone;
- aggregate and per-service statuses must remain distinct;
- refused, blocked, resource-gated, failed-to-apply, failed-to-verify, and
  completed states must not collapse into a generic success message;
- setup output must show actionable recovery guidance without printing
  secrets, raw command payloads, tokens, or credentials.

## Test Strategy

- Use regression-first implementation.
- Start each slice with the nearest focused unit/static tests.
- Keep live infrastructure effects mocked or statically inspected by default.
- Use fake command workflows, command runners, host preflight probes,
  Portainer/Nexus/container-runtime clients, inventory repositories, evidence
  repositories, and synthetic YAML/compose fixtures.
- Patch process calls, sleeps, input, and environment variables in tests.
- Assert forbidden live calls with mocks that raise `AssertionError`.
- Do not add mutation-testing commands because repository tooling does not
  configure them.
- Do not claim `python3 tools/quality_gate.py quality` passed unless it was
  executed successfully in a suitable Linux/WSL environment.

## Resilience And Safety Requirements

- No live infrastructure commands during workflow creation.
- Mutating setup execution must require live consent before service
  construction.
- Destructive reset/destroy behavior remains outside autonomous setup unless a
  later ADR explicitly defines retention and teardown semantics.
- Every autonomous live step must have an apply contract and a verification
  contract before it can run.
- Missing verification, manual-only verification, missing observed-state
  evidence, or unsafe evidence persistence must return `blocked`.
- Failed apply stops later phases.
- Failed verification stops later phases and records redacted evidence.
- Resource-gated hosts produce resource-gated results, not false success.
- Secrets are provided through environment variables or ignored local files.
- Verification evidence stores summaries and checksums, not raw command
  strings, stdout, stderr, environment payloads, passwords, tokens, or Swarm
  join tokens.

## Ordered Slices

### Slice 01: Installer Requirement Baseline

Purpose:

- Define the installer-specific EPIC extension, runnable-state acceptance
  criteria, service profile, credentials model, resource-gated outcomes, and
  live validation boundaries before implementation.

```yaml
slice_id: "01"
profile: "FULL_PATH"
owner: "senior_requirement_engineer"
secondary_reviewers:
  - "senior_workflow_architect"
  - "senior_system_architect"
  - "senior_tester"
affected_files:
  - "documentation/epics/autonomous-runnable-setup.md"
  - "documentation/epics/system-unification.md"
  - "documentation/workflow/reports/01-installer-requirement-baseline.md"
affected_modules: []
affected_contracts:
  - "autonomous-setup-requirement"
  - "runnable-state-acceptance"
dependencies: []
parallel_group: "A"
file_locks:
  - "documentation/epics/**"
  - "documentation/workflow/reports/01-installer-requirement-baseline.md"
contract_locks:
  - "autonomous-setup-requirement"
  - "runnable-state-acceptance"
architecture_locks:
  - "Platform-Artifacts-Deployment-Shared"
quality_gates:
  targeted:
    - "git diff --check"
  required: []
documentation:
  arc42: "checked; update only if the requirement changes architecture status"
  adr: "checked; no new ADR expected unless live consent or host package installation changes"
stop_conditions:
  - "runnable state cannot be made testable"
  - "credential source would require committed secrets"
  - "autonomous setup is redefined as silent host mutation"
  - "minimum target becomes unclear"
```

Done criteria:

- Installer-specific EPIC or EPIC extension exists.
- Full and resource-gated runnable-state criteria are explicit.
- Credential, consent, and live smoke assumptions are testable.

### Slice 02: Setup Safety ADR And arc42 Alignment

Purpose:

- Decide whether autonomous setup needs a standalone ADR and align arc42 with
  the accepted setup contract before runtime wiring changes.

```yaml
slice_id: "02"
profile: "FULL_PATH"
owner: "senior_system_architect"
secondary_reviewers:
  - "adr-steward"
  - "senior_documentation_engineer"
  - "senior_security_sandbox_engineer"
affected_files:
  - "documentation/architecture/**"
  - "documentation/arc42/05_building_blocks.adoc"
  - "documentation/arc42/06_runtime_view.adoc"
  - "documentation/arc42/07_deployment_view.adoc"
  - "documentation/arc42/09_architecture_decisions.adoc"
  - "documentation/arc42/10_quality_requirements.adoc"
  - "documentation/arc42/11_risks_and_debt.adoc"
  - "documentation/workflow/reports/02-setup-safety-architecture.md"
affected_modules: []
affected_contracts:
  - "autonomous-setup-safety"
  - "adr-location-convention"
dependencies:
  - "01"
parallel_group: "B"
file_locks:
  - "documentation/architecture/**"
  - "documentation/arc42/**"
  - "documentation/workflow/reports/02-setup-safety-architecture.md"
contract_locks:
  - "autonomous-setup-safety"
  - "adr-location-convention"
architecture_locks:
  - "hexagonal-architecture"
  - "Platform-Artifacts-Deployment-Shared"
quality_gates:
  targeted:
    - "git diff --check"
    - "python3 tools/quality_gate.py arch-tests"
  required: []
documentation:
  arc42: "update when setup contract, runtime flow, deployment view, or risk status changes"
  adr: "new ADR required if consent, host package installation, evidence semantics, or script promotion changes"
stop_conditions:
  - "ADR convention cannot be followed"
  - "arc42 would document planned behavior as implemented"
  - "setup ownership crosses boundaries without a decision"
```

Done criteria:

- ADR need is explicitly accepted or rejected.
- arc42 distinguishes planned setup behavior from implemented setup behavior.

### Slice 03: Setup Preflight And Manifest Contract

Purpose:

- Extend preflight and setup manifest behavior for a full runnable setup while
  keeping checks non-mutating until live consent is provided.

```yaml
slice_id: "03"
profile: "FULL_PATH"
owner: "senior_python_automation_developer"
secondary_reviewers:
  - "setup-bootstrap-expert"
  - "linux-host-preparation"
  - "senior_tester"
affected_files:
  - "src/tiny_swarm_world/domain/preflight/**"
  - "src/tiny_swarm_world/application/ports/preflight/**"
  - "src/tiny_swarm_world/application/services/platform/preflight_service.py"
  - "src/tiny_swarm_world/infrastructure/adapters/preflight/**"
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "tests/domain/preflight/**"
  - "tests/application/services/platform/test_preflight_service.py"
  - "tests/infrastructure/adapters/preflight/**"
  - "tests/test_package_entrypoint.py"
  - "documentation/workflow/reports/03-setup-preflight-manifest.md"
affected_modules:
  - "tiny_swarm_world.domain.preflight"
  - "tiny_swarm_world.application.services.platform"
  - "tiny_swarm_world.infrastructure.adapters.preflight"
affected_contracts:
  - "setup-preflight-contract"
  - "setup-manifest-contract"
dependencies:
  - "02"
parallel_group: "C"
file_locks:
  - "src/tiny_swarm_world/domain/preflight/**"
  - "src/tiny_swarm_world/application/ports/preflight/**"
  - "src/tiny_swarm_world/application/services/platform/preflight_service.py"
  - "src/tiny_swarm_world/infrastructure/adapters/preflight/**"
  - "tests/domain/preflight/**"
  - "tests/application/services/platform/test_preflight_service.py"
  - "tests/infrastructure/adapters/preflight/**"
contract_locks:
  - "setup-preflight-contract"
  - "setup-manifest-contract"
architecture_locks:
  - "hexagonal-architecture"
  - "Shared"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.domain.preflight.test_preflight_result"
    - "PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_preflight_service"
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.preflight.test_host_preflight_probe"
    - "PYTHONPATH=src python3 -m unittest tests.test_package_entrypoint"
  required:
    - "python3 tools/quality_gate.py test"
documentation:
  arc42: "update quality requirements and runtime view if preflight semantics change"
  adr: "new ADR only if setup can install host prerequisites automatically"
stop_conditions:
  - "preflight would mutate host state"
  - "resource-gated outcome would be treated as pass"
  - "secret values would be stored or printed"
```

Done criteria:

- Setup preflight knows the selected profile and reports actionable failures.
- Setup manifest data is structured and secret-safe.

### Slice 04: Inventory And Evidence Foundation

Purpose:

- Provide safe observed inventory and verification evidence contracts for
  setup phases, services, ports, and stack readiness.

```yaml
slice_id: "04"
profile: "FULL_PATH"
owner: "senior_python_automation_developer"
secondary_reviewers:
  - "senior_system_architect"
  - "senior_security_sandbox_engineer"
  - "senior_tester"
affected_files:
  - "src/tiny_swarm_world/domain/inventory/**"
  - "src/tiny_swarm_world/application/ports/repositories/**"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/**"
  - "infra/config/inventory/**"
  - "tests/domain/inventory/**"
  - "tests/infrastructure/adapters/repositories/**"
  - "tests/architecture/test_local_state_storage.py"
  - "documentation/workflow/reports/04-inventory-evidence-foundation.md"
affected_modules:
  - "tiny_swarm_world.domain.inventory"
  - "tiny_swarm_world.application.ports.repositories"
  - "tiny_swarm_world.infrastructure.adapters.repositories"
affected_contracts:
  - "observed-inventory-contract"
  - "verification-evidence-contract"
  - "evidence-redaction-contract"
dependencies:
  - "03"
parallel_group: "D"
file_locks:
  - "src/tiny_swarm_world/domain/inventory/**"
  - "src/tiny_swarm_world/application/ports/repositories/**"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/**"
  - "infra/config/inventory/**"
  - "tests/domain/inventory/**"
  - "tests/infrastructure/adapters/repositories/**"
contract_locks:
  - "observed-inventory-contract"
  - "verification-evidence-contract"
  - "evidence-redaction-contract"
architecture_locks:
  - "Shared"
  - "hexagonal-architecture"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.domain.inventory.test_inventory_model"
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_inventory_repositories"
    - "PYTHONPATH=src python3 -m unittest tests.architecture.test_local_state_storage"
    - "python3 tools/quality_gate.py arch-tests"
  required:
    - "python3 tools/quality_gate.py test"
documentation:
  arc42: "update runtime view, deployment view, concepts, and risks if evidence storage changes"
  adr: "new ADR only if evidence semantics change materially"
stop_conditions:
  - "raw command strings, stdout, stderr, environment payloads, tokens, or passwords would be persisted"
  - "observed inventory would be committed under infra/config"
  - "domain imports infrastructure"
```

Done criteria:

- Evidence paths remain ignored local state.
- Evidence redaction is test-backed.
- Observed readiness can be represented without live calls in tests.

### Slice 05: Command-Backed Platform Verification

Purpose:

- Add command-backed or probe-backed verification contracts for platform setup
  steps so platform workflows can safely move beyond pre-apply blocks.

```yaml
slice_id: "05"
profile: "FULL_PATH"
owner: "senior_python_automation_developer"
secondary_reviewers:
  - "senior_system_architect"
  - "senior_devops"
  - "senior_tester"
  - "resilience-engineering"
affected_files:
  - "src/tiny_swarm_world/domain/command/**"
  - "src/tiny_swarm_world/application/ports/commands/**"
  - "src/tiny_swarm_world/application/services/platform/**"
  - "src/tiny_swarm_world/application/services/multipass/**"
  - "src/tiny_swarm_world/application/services/network/**"
  - "src/tiny_swarm_world/application/services/vm/**"
  - "src/tiny_swarm_world/infrastructure/adapters/command_runner/**"
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "infra/config/**/command_*.yaml"
  - "tests/domain/command/**"
  - "tests/application/services/platform/**"
  - "tests/application/services/multipass/**"
  - "tests/application/services/network/**"
  - "tests/infrastructure/adapters/command_runner/**"
  - "tests/infrastructure/test_composition.py"
  - "documentation/workflow/reports/05-platform-verification-contracts.md"
affected_modules:
  - "tiny_swarm_world.domain.command"
  - "tiny_swarm_world.application.services.platform"
  - "tiny_swarm_world.application.services.multipass"
  - "tiny_swarm_world.application.services.network"
  - "tiny_swarm_world.infrastructure.adapters.command_runner"
affected_contracts:
  - "command-verification-contract"
  - "platform-setup-contract"
  - "verify-after-apply"
dependencies:
  - "04"
parallel_group: "E"
file_locks:
  - "src/tiny_swarm_world/domain/command/**"
  - "src/tiny_swarm_world/application/ports/commands/**"
  - "src/tiny_swarm_world/application/services/platform/**"
  - "src/tiny_swarm_world/application/services/multipass/**"
  - "src/tiny_swarm_world/application/services/network/**"
  - "src/tiny_swarm_world/application/services/vm/**"
  - "src/tiny_swarm_world/infrastructure/adapters/command_runner/**"
  - "infra/config/**/command_*.yaml"
  - "tests/domain/command/**"
  - "tests/application/services/platform/**"
  - "tests/infrastructure/adapters/command_runner/**"
contract_locks:
  - "command-verification-contract"
  - "platform-setup-contract"
  - "verify-after-apply"
architecture_locks:
  - "Platform"
  - "hexagonal-architecture"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.domain.command.test_command_spec"
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.command_runner.test_command_workflow_configuration"
    - "PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_platform_workflows"
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition"
    - "python3 tools/quality_gate.py arch-lint"
    - "python3 tools/quality_gate.py arch-tests"
  required:
    - "python3 tools/quality_gate.py test"
documentation:
  arc42: "update runtime view and risks if platform workflows unblock live steps"
  adr: "new ADR only if verification semantics or token handling change materially"
stop_conditions:
  - "verification would remain manual-only for an autonomous live step"
  - "Swarm join tokens or command payloads would be logged or persisted"
  - "application service would import infrastructure"
  - "tests would execute live Multipass, Docker Swarm, netplan, or socat"
```

Done criteria:

- Platform setup steps can verify or block for specific tested reasons.
- Command token handling and evidence redaction are explicit.

### Slice 06: Portainer Deployment Contract

Purpose:

- Replace direct Portainer preparation as the setup path with guarded
  application ports, infrastructure adapters, and tested deployment contracts.

```yaml
slice_id: "06"
profile: "FULL_PATH"
owner: "senior_devops"
secondary_reviewers:
  - "senior_python_automation_developer"
  - "senior_system_architect"
  - "senior_security_sandbox_engineer"
  - "senior_tester"
affected_files:
  - "src/tiny_swarm_world/application/ports/clients/port_portainer_client.py"
  - "src/tiny_swarm_world/application/ports/repositories/port_compose_file_repository.py"
  - "src/tiny_swarm_world/application/services/deployment/**"
  - "src/tiny_swarm_world/infrastructure/adapters/clients/portainer_http_client.py"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py"
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "infra/config/compose/portainer/**"
  - "infra/compose/portainer/**"
  - "tests/application/services/deployment/**"
  - "tests/infrastructure/adapters/clients/**"
  - "tests/infrastructure/adapters/repositories/**"
  - "tests/architecture/test_legacy_surface_documentation.py"
  - "documentation/workflow/reports/06-portainer-deployment-contract.md"
affected_modules:
  - "tiny_swarm_world.application.services.deployment"
  - "tiny_swarm_world.application.ports.clients"
  - "tiny_swarm_world.infrastructure.adapters.clients"
affected_contracts:
  - "portainer-deployment-contract"
  - "compose-asset-contract"
dependencies:
  - "05"
parallel_group: "F"
file_locks:
  - "src/tiny_swarm_world/application/ports/clients/port_portainer_client.py"
  - "src/tiny_swarm_world/application/services/deployment/**"
  - "src/tiny_swarm_world/infrastructure/adapters/clients/portainer_http_client.py"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py"
  - "infra/config/compose/portainer/**"
  - "infra/compose/portainer/**"
  - "tests/application/services/deployment/**"
  - "tests/infrastructure/adapters/clients/**"
contract_locks:
  - "portainer-deployment-contract"
  - "compose-asset-contract"
architecture_locks:
  - "Deployment"
  - "hexagonal-architecture"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.application.services.deployment"
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml"
    - "PYTHONPATH=src python3 -m unittest tests.test_package_entrypoint"
    - "python3 tools/quality_gate.py arch-tests"
  required:
    - "python3 tools/quality_gate.py test"
documentation:
  arc42: "update deployment view and live-operation surfaces if Portainer support status changes"
  adr: "new ADR only if direct script support status is promoted or removed"
stop_conditions:
  - "Portainer admin credentials would be committed or printed"
  - "direct scripts bypass CLI consent"
  - "tests would contact Portainer or deploy a stack"
```

Done criteria:

- Portainer setup has a port-backed contract with mocked tests.
- Direct script status remains documented honestly.

### Slice 07: Nexus And Artifact Registry Contract

Purpose:

- Implement artifact setup and verification contracts for Nexus repository and
  registry behavior without collapsing it into Deployment ownership.

```yaml
slice_id: "07"
profile: "FULL_PATH"
owner: "senior_python_automation_developer"
secondary_reviewers:
  - "senior_system_architect"
  - "senior_devops"
  - "senior_security_sandbox_engineer"
  - "senior_tester"
affected_files:
  - "src/tiny_swarm_world/application/services/artifacts/**"
  - "src/tiny_swarm_world/application/services/nexus/**"
  - "src/tiny_swarm_world/application/ports/clients/port_nexus_client.py"
  - "src/tiny_swarm_world/application/ports/clients/port_container_runtime.py"
  - "src/tiny_swarm_world/infrastructure/adapters/clients/nexus_http_client.py"
  - "src/tiny_swarm_world/infrastructure/adapters/clients/docker_cli_runtime.py"
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "infra/config/compose/nexus/**"
  - "infra/compose/**"
  - "tests/application/services/artifacts/**"
  - "tests/application/services/nexus/**"
  - "tests/infrastructure/adapters/clients/**"
  - "documentation/workflow/reports/07-nexus-artifact-contract.md"
affected_modules:
  - "tiny_swarm_world.application.services.artifacts"
  - "tiny_swarm_world.application.services.nexus"
  - "tiny_swarm_world.application.ports.clients"
  - "tiny_swarm_world.infrastructure.adapters.clients"
affected_contracts:
  - "artifact-prepare-contract"
  - "artifact-verify-contract"
  - "nexus-registry-contract"
dependencies:
  - "05"
parallel_group: "F"
file_locks:
  - "src/tiny_swarm_world/application/services/artifacts/**"
  - "src/tiny_swarm_world/application/services/nexus/**"
  - "src/tiny_swarm_world/application/ports/clients/port_nexus_client.py"
  - "src/tiny_swarm_world/application/ports/clients/port_container_runtime.py"
  - "src/tiny_swarm_world/infrastructure/adapters/clients/nexus_http_client.py"
  - "src/tiny_swarm_world/infrastructure/adapters/clients/docker_cli_runtime.py"
  - "tests/application/services/artifacts/**"
  - "tests/application/services/nexus/**"
contract_locks:
  - "artifact-prepare-contract"
  - "artifact-verify-contract"
  - "nexus-registry-contract"
architecture_locks:
  - "Artifacts"
  - "hexagonal-architecture"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.application.services.artifacts"
    - "PYTHONPATH=src python3 -m unittest tests.application.services.nexus"
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition"
    - "python3 tools/quality_gate.py arch-tests"
  required:
    - "python3 tools/quality_gate.py test"
documentation:
  arc42: "update building blocks, runtime view, and risks if artifact workflows unblock"
  adr: "new ADR only if registry ownership or credential model changes"
stop_conditions:
  - "Nexus credentials or initial admin password material would be committed or logged"
  - "image build or push would run during tests"
  - "Artifacts and Deployment ownership becomes ambiguous"
```

Done criteria:

- `artifacts prepare` and `artifacts verify` are either executable with mocked
  contracts or blocked with more precise tested reasons.

### Slice 08: Service Stack Deployment And Verification

Purpose:

- Wire default stack deployment and verification contracts for the runnable
  service set through Deployment ports and observed-state checks.

```yaml
slice_id: "08"
profile: "FULL_PATH"
owner: "senior_python_automation_developer"
secondary_reviewers:
  - "senior_devops"
  - "senior_system_architect"
  - "senior_tester"
  - "resilience-engineering"
affected_files:
  - "src/tiny_swarm_world/application/services/deployment/**"
  - "src/tiny_swarm_world/domain/deployment/**"
  - "src/tiny_swarm_world/application/ports/clients/**"
  - "src/tiny_swarm_world/application/ports/repositories/port_compose_file_repository.py"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py"
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "infra/config/compose/**"
  - "infra/compose/**"
  - "tests/application/services/deployment/**"
  - "tests/domain/deployment/**"
  - "tests/infrastructure/adapters/repositories/**"
  - "documentation/workflow/reports/08-service-stack-deployment.md"
affected_modules:
  - "tiny_swarm_world.domain.deployment"
  - "tiny_swarm_world.application.services.deployment"
  - "tiny_swarm_world.infrastructure.adapters.repositories"
affected_contracts:
  - "deployment-apply-contract"
  - "deployment-verify-contract"
  - "service-readiness-contract"
dependencies:
  - "06"
  - "07"
parallel_group: "G"
file_locks:
  - "src/tiny_swarm_world/application/services/deployment/**"
  - "src/tiny_swarm_world/domain/deployment/**"
  - "src/tiny_swarm_world/application/ports/clients/**"
  - "src/tiny_swarm_world/application/ports/repositories/port_compose_file_repository.py"
  - "infra/config/compose/**"
  - "infra/compose/**"
  - "tests/application/services/deployment/**"
  - "tests/domain/deployment/**"
contract_locks:
  - "deployment-apply-contract"
  - "deployment-verify-contract"
  - "service-readiness-contract"
architecture_locks:
  - "Deployment"
  - "hexagonal-architecture"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.application.services.deployment"
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml"
    - "PYTHONPATH=src python3 -m unittest tests.test_package_entrypoint"
    - "python3 tools/quality_gate.py arch-tests"
  required:
    - "python3 tools/quality_gate.py test"
documentation:
  arc42: "update deployment view and runtime view when stack deployment status changes"
  adr: "new ADR only if default service set or ownership changes materially"
stop_conditions:
  - "service health would be claimed without observed-state evidence"
  - "Portainer, compose, image build, or stack upload would run in default tests"
  - "host-specific addresses or credentials would be committed"
```

Done criteria:

- Deployment apply/verify has service-specific contracts or precise tested
  blockers for every default service.

### Slice 09: Autonomous Setup Orchestrator And CLI Contract

Purpose:

- Add one canonical setup workflow command that orchestrates preflight,
  platform, artifacts, deployment, and final verification while preserving
  live-consent and thin-entrypoint rules.

```yaml
slice_id: "09"
profile: "FULL_PATH"
owner: "senior_workflow_architect"
secondary_reviewers:
  - "senior_python_automation_developer"
  - "senior_system_architect"
  - "senior_tester"
  - "senior_security_sandbox_engineer"
affected_files:
  - "src/tiny_swarm_world/__main__.py"
  - "src/tiny_swarm_world/application/services/setup/**"
  - "src/tiny_swarm_world/application/services/platform/**"
  - "src/tiny_swarm_world/application/services/artifacts/**"
  - "src/tiny_swarm_world/application/services/deployment/**"
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "tests/test_package_entrypoint.py"
  - "tests/application/services/setup/**"
  - "tests/infrastructure/test_composition.py"
  - "tests/architecture/test_hexagonal_imports.py"
  - "documentation/workflow/reports/09-autonomous-setup-orchestrator.md"
affected_modules:
  - "tiny_swarm_world.application.services.setup"
  - "tiny_swarm_world.infrastructure.composition"
  - "tiny_swarm_world.__main__"
affected_contracts:
  - "autonomous-setup-cli-contract"
  - "setup-orchestration-contract"
  - "live-consent-contract"
dependencies:
  - "08"
parallel_group: "H"
file_locks:
  - "src/tiny_swarm_world/__main__.py"
  - "src/tiny_swarm_world/application/services/setup/**"
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "tests/test_package_entrypoint.py"
  - "tests/application/services/setup/**"
  - "tests/infrastructure/test_composition.py"
contract_locks:
  - "autonomous-setup-cli-contract"
  - "setup-orchestration-contract"
  - "live-consent-contract"
architecture_locks:
  - "hexagonal-architecture"
  - "Platform-Artifacts-Deployment-Shared"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.test_package_entrypoint"
    - "PYTHONPATH=src python3 -m unittest tests.application.services.setup"
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition"
    - "python3 tools/quality_gate.py arch-lint"
    - "python3 tools/quality_gate.py arch-tests"
  required:
    - "python3 tools/quality_gate.py test"
documentation:
  arc42: "update runtime view and architecture decisions for the new CLI contract"
  adr: "new ADR required if setup contract changes live-consent semantics"
stop_conditions:
  - "entry point would construct low-level services directly"
  - "setup orchestration would bypass live consent"
  - "setup would run destructive reset/destroy behavior"
  - "workflow status would hide blocked or failed phases"
```

Done criteria:

- Setup command is listed by `--list-workflows`.
- Mutating setup refuses missing live consent before service construction.
- Setup orchestration is tested with mocked phase services.

### Slice 10: Console Status And Recovery UX

Purpose:

- Make setup progress and recovery output readable in the terminal without
  adding browser or React scope.

```yaml
slice_id: "10"
profile: "NORMAL_PATH"
owner: "senior_python_automation_developer"
secondary_reviewers:
  - "senior_react_frontend"
  - "console-status-ui-developer"
  - "senior_tester"
affected_files:
  - "src/tiny_swarm_world/application/ports/ui/**"
  - "src/tiny_swarm_world/infrastructure/adapters/ui/**"
  - "tests/infrastructure/adapters/ui/**"
  - "documentation/workflow/reports/10-console-status-recovery.md"
affected_modules:
  - "tiny_swarm_world.application.ports.ui"
  - "tiny_swarm_world.infrastructure.adapters.ui"
affected_contracts:
  - "console-status-contract"
  - "setup-recovery-output"
dependencies:
  - "09"
parallel_group: "I"
file_locks:
  - "src/tiny_swarm_world/application/ports/ui/**"
  - "src/tiny_swarm_world/infrastructure/adapters/ui/**"
  - "tests/infrastructure/adapters/ui/**"
contract_locks:
  - "console-status-contract"
  - "setup-recovery-output"
architecture_locks:
  - "Console-status-UI"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.ui.test_linux_ui"
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.ui.test_command_runner_ui_failure_semantics"
    - "PYTHONPATH=src python3 -m unittest tests.application.services.commands.test_command_executer"
  required:
    - "python3 tools/quality_gate.py test"
documentation:
  arc42: "update only if console runtime semantics change"
  adr: "not expected"
stop_conditions:
  - "work introduces package.json, React, browser routes, TSX, JSX, or browser state"
  - "color becomes the only status signal"
  - "blocked, refused, resource-gated, or failed states are rendered as success"
```

Done criteria:

- Terminal status output preserves distinct setup states and recovery actions.
- No browser frontend scope is introduced.

### Slice 11: Documentation Sync, Quality Gate, And Optional Live Smoke Handoff

Purpose:

- Synchronize user-facing documentation, record final quality evidence, and
  define the optional live smoke run as a separate, explicit operator action.

```yaml
slice_id: "11"
profile: "FULL_PATH"
owner: "senior_documentation_engineer"
secondary_reviewers:
  - "senior_workflow_architect"
  - "senior_requirement_engineer"
  - "senior_system_architect"
  - "senior_tester"
  - "senior_devops"
  - "git_commit_reviewer"
affected_files:
  - "README.md"
  - "documentation/workflow/**"
  - "documentation/epics/**"
  - "documentation/architecture/**"
  - "documentation/arc42/**"
  - "documentation/deployment/**"
  - "documentation/system/**"
  - "documentation/user_guide/**"
affected_modules: []
affected_contracts:
  - "documentation-sync"
  - "quality-evidence"
  - "optional-live-smoke-contract"
dependencies:
  - "10"
parallel_group: "J"
file_locks:
  - "README.md"
  - "documentation/**"
contract_locks:
  - "documentation-sync"
  - "quality-evidence"
  - "optional-live-smoke-contract"
architecture_locks:
  - "Platform-Artifacts-Deployment-Shared"
quality_gates:
  targeted:
    - "git diff --check"
    - "python3 tools/quality_gate.py arch-lint"
    - "python3 tools/quality_gate.py arch-tests"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "final checked or updated status required"
  adr: "final ADR references and decision status required"
stop_conditions:
  - "docs claim live setup works before mocked and static gates pass"
  - "quality results are missing"
  - "live smoke run is treated as default quality gate"
  - "optional live smoke lacks explicit disposable-environment warning"
```

Done criteria:

- README and installation docs show the canonical setup path accurately.
- Live-operation surfaces reflect the new support status.
- Exact quality commands and results are recorded.
- Optional live smoke instructions are explicit, separated, and consent-gated.

## Slice Dependency Graph

```text
01 -> 02 -> 03 -> 04 -> 05 -> 06 -> 08 -> 09 -> 10 -> 11
                         \-----> 07 ----/
```

## Parallelization Opportunities

- Slices 06 and 07 may run in parallel after Slice 05 if S3D confirms disjoint
  file, contract, and architecture locks.
- Slice 10 must wait for the setup orchestrator contract in Slice 09.
- Documentation synchronization in Slice 11 waits for all implementation
  slices.
- Default execution should still use one write-capable implementation worker
  at a time unless S3D proves write scopes are disjoint.

## Role And Subagent Ownership Map

- Senior Workflow Architect: workflow integrity, dependency graph, S3/S3D
  handoff, setup orchestrator contract.
- Senior Requirement Engineer: runnable-state baseline, EPIC extension,
  acceptance criteria, unresolved requirement decisions.
- Senior System Architect: hexagonal boundaries, ADR need, arc42 alignment,
  responsibility ownership.
- Senior Python Automation Developer: preflight, inventory/evidence, platform,
  artifact, deployment, setup orchestrator, and console implementation.
- Senior React Frontend: read-only scope guard confirming browser/React remains
  out of scope; console UI routes to console/status skills.
- Senior Tester: regression-first tests, mocks, quality gates, failure
  classification, verification evidence.
- Senior DevOps: Portainer/deployment contracts, Docker Swarm safety, live
  surface migration, optional live smoke design.
- Senior Documentation Engineer: README, installation guide, deployment docs,
  system docs, arc42 synchronization, workflow reports.
- Senior Security/Sandbox Engineer: secrets, local evidence, direct script
  risks, command redaction, unsafe defaults.
- Git reviewers/operators: commit and push readiness only after required gates
  pass.

## Quality Gate Expectations

Use `QUALITY.md` as authority.

Minimum workflow-creation check:

```bash
git diff --check
```

Preferred full gate before final implementation release:

```bash
python3 tools/quality_gate.py quality
```

Targeted gates are listed per slice. Default gates must not run live
infrastructure commands. If `python3` or required tooling is unavailable in the
current environment, record the exact failure and do not claim the gate passed.

## Documentation Synchronization Points

- `documentation/epics/autonomous-runnable-setup.md`
- `documentation/epics/system-unification.md`
- `documentation/workflow/workflow.md`
- `documentation/workflow/context-pack.md`
- `documentation/workflow/context-pack.json`
- `documentation/workflow/execution-report.md`
- `documentation/architecture/**`
- `documentation/arc42/**`
- `documentation/deployment/**`
- `documentation/system/**`
- `documentation/user_guide/**`
- `README.md`

## Commit And Push Plan

The user requested workflow creation but did not explicitly request commit or
push.

Workflow creation may be committed and pushed later when:

1. The active branch is `codex/workflow-autonomous-setup-20260524`.
2. `documentation/workflow/workflow.md` and context-pack files exist.
3. `git diff --check` passes.
4. Any skipped full quality gate is documented and justified.

Workflow execution checkpoint pushes must follow the workflow-executor rule:
one slice-scoped commit and push per completed slice after required quality
gates pass.

## Stop Conditions

Stop and report when:

- active branch is not `codex/workflow-autonomous-setup-20260524`;
- working tree contains unrelated or unclear changes;
- workflow or context-pack branch names are stale;
- installer requirement baseline cannot make runnable state testable;
- live infrastructure execution would be required without explicit user
  approval and live consent;
- host package installation or non-interactive consent would be introduced
  without ADR approval;
- application code would import infrastructure adapters;
- direct scripts would become canonical setup without ports, tests, and
  consent controls;
- raw command output, Swarm tokens, passwords, or credentials would be
  persisted or printed;
- service health would be claimed without observed-state evidence;
- quality commands are missing and no documented limitation exists;
- a slice would weaken `.importlinter`, architecture tests, or `QUALITY.md`;
- Java/Maven, React/browser, Spring Boot, Kubernetes-first, or unrelated analytics
  concerns start driving the Python automation architecture.

## Definition Of Done

This workflow is complete when:

- installer-specific requirements and runnable-state acceptance criteria exist;
- setup safety decisions are recorded in ADR/arc42 when needed;
- setup preflight and manifest contracts are test-backed;
- observed inventory and verification evidence are redacted and stored only in
  ignored local state;
- platform setup steps are verified or blocked with exact tested reasons;
- Portainer, Nexus/artifacts, and default service stack deployment contracts
  are explicit and test-backed;
- one canonical autonomous setup CLI workflow exists and preserves live
  consent;
- console/status output shows accurate setup phase status and recovery
  guidance;
- README, installation, deployment, system, arc42, workflow, and report docs
  match actual behavior;
- `python3 tools/quality_gate.py quality` passes or inability to run it is
  recorded as a blocker;
- optional live smoke validation is separated from default quality gates and
  requires explicit operator approval.

## Handoff To Workflow Execute

Workflow execution is released with this entrypoint:

```text
workflow execute with subagents
```

Before executing, the executor must verify:

```bash
git status --short --branch
git branch --show-current
git show-ref --verify --quiet refs/heads/codex/workflow-autonomous-setup-20260524
```

Execution may start only when the active branch is
`codex/workflow-autonomous-setup-20260524`, the local branch ref exists, and
the working tree contains no unrelated or unclear changes.

## arc42 Check Status

arc42 was checked during workflow creation. No arc42 update is required for
workflow creation itself because this turn only regenerates workflow artifacts.
Execution slices must update arc42 when they change implemented status,
runtime behavior, setup safety decisions, deployment wiring, quality
requirements, or risk classification.
