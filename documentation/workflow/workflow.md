# Workflow: Installation Phases And Port Registry

Version: `installation-phases-port-registry-v1.0.0`
Created: `2026-06-20`
Branch: `feature/workflow-installation-phases-port-registry-20260620`
Status: `READY_FOR_WORKFLOW`

## Executive Summary

Create an executable workflow for making Tiny Swarm World installation order and port allocation deterministic. The workflow covers a central port registry, installation phase registry, dependency graph, health/validation plan, and the Python automation needed to consume those declarations through existing hexagonal boundaries.

The current repository already accepts Traefik-backed centralized ingress on ports `80` and `443` for the service-access setup profile. This workflow must not silently replace that ADR-backed ingress baseline with high-numbered gateway ports. High-numbered service ports may be introduced as direct, diagnostic, or compatibility mappings only after the architecture slice records the intended port model.

## Requirement Clarification Gate

Original Request:

- Create a workflow for fixed installation order and a clean port concept for Tiny Swarm World services.
- Model install phases from preflight through LXC/LXD/Incus, Docker Swarm, secrets, registry, CI/CD, quality, messaging, observability, service access, Swagger/API docs, and greenpath validation.
- Introduce central files such as `ports.yaml`, `installation-plan.yaml`, `services.yaml`, `dependencies.yaml`, `health-checks.yaml`, and `validation-plan.yaml`.

Interpreted Intent:

- Build a workflow that later implements declarative setup planning and port governance without bypassing the current Python automation, live-consent, Docker Swarm, LXC-native, and hexagonal architecture constraints.

Change Type:

- Product behavior workflow for Python automation, configuration, deployment contracts, tests, and documentation.

Affected Process Strand:

- `workflow create`
- later `workflow execute` over setup, platform, artifacts, deployment, preflight, and documentation strands.

Affected Architecture Area:

- Domain: installation plan, port registry, dependency graph, health/validation concepts.
- Application: setup orchestration, preflight checks, deployment plan construction, validation sequencing.
- Infrastructure: YAML repositories for new registries and compose/stack configuration integration.
- Configuration: `infra/config/**` desired-state files.
- Documentation: arc42 deployment/concepts/quality and operator setup guidance.

Explicit Requirements:

- Define fixed installation phases.
- Define fixed service dependencies.
- Define central port ranges and service port assignments.
- Keep ports centrally declared instead of hard-coded across compose files, Python code, and templates.
- Add port preflight checks.
- Add phase-level health and validation checks.
- Keep service-access/control UI as a late-installed but first-used operator entry point.

Implicit Requirements:

- Preserve Linux/WSL-only operation.
- Preserve LXC-native through LXD or Incus as the supported node-provider direction.
- Preserve Docker Swarm-first deployment.
- Preserve current live-infrastructure consent and fail-closed behavior.
- Use structured YAML parsing and repository adapters.
- Do not claim live service health without observed-state or smoke evidence.
- Do not introduce React, Java, Maven, Spring Boot, Kubernetes-first behavior, or direct live scripts as canonical behavior.

Assumptions:

- The central registry belongs under `infra/config` unless the architecture slice finds a stronger existing desired-state location.
- Traefik `80/443` remains the public centralized ingress baseline unless an ADR change is explicitly authored.
- High-numbered ports are useful for direct/diagnostic host mappings, local compatibility endpoints, and preflight conflict detection.
- Observability services such as Prometheus, Grafana, Loki, and Alertmanager can be modeled as optional until repository compose contracts exist.
- RabbitMQ is a requested target service, but the current repository baseline contains Apache Pulsar rather than RabbitMQ. RabbitMQ must be added only through a service-stack slice with tests and docs, or documented as deferred if not selected.

Non-Goals:

- No live LXD, Incus, LXC, Docker Swarm, compose, Portainer, Nexus, Jenkins, SonarQube, Infisical, Pulsar, RabbitMQ, Prometheus, Grafana, or Swagger mutation during default verification.
- No replacement of accepted Traefik ingress without ADR coverage.
- No browser React frontend project.
- No Java/Maven/Spring Boot structure.
- No Kubernetes-first migration.
- No committed secrets, host IPs, Swarm tokens, local absolute paths, or credential-bearing URLs.

Risks:

- The proposed high-numbered gateway ports can conflict with the accepted Traefik `80/443` ingress direction if treated as public ingress replacement.
- Existing compose files still publish several direct ports such as `8080`, `8081`, `9000`, `9001`, `5000`, `5001`, `6650`, `7750`, `8087`, `9527`, and `8084`.
- Service registry work can touch shared deployment contracts and must be sliced carefully.
- RabbitMQ and observability services are not currently present as compose stacks in the verified baseline.

Open Questions:

- Should RabbitMQ replace, complement, or remain separate from the existing Pulsar baseline? This is non-blocking if RabbitMQ is modeled as deferred or optional until a later explicit service-selection decision.
- Should high-numbered ports become direct host ports while Traefik remains the main user ingress, or should they become a later ADR-backed ingress replacement? The workflow assumes direct/diagnostic use until ADR says otherwise.

Blocking Questions:

- None for workflow authoring.

Confidence Level:

- `92%`

Decision:

- `READY_FOR_WORKFLOW`

## Five-Role Three Amigos Review

Senior Requirement Engineer:

- Requirements are concrete enough for workflow authoring. The workflow must record Pulsar vs RabbitMQ and Traefik vs high-port gateway assumptions instead of hiding them.

Senior System Architect:

- The workflow fits the autonomous setup and service-access EPICs when it keeps setup orchestration in Python, uses ports/adapters for YAML loading, and preserves accepted Traefik ingress unless an ADR changes it.

Senior Python Automation Developer:

- Implementation should introduce typed domain models and repository ports before wiring setup/preflight/deployment behavior. Compose and manifest integration must use structured YAML APIs.

Senior React Frontend Developer:

- No React frontend impact is approved. Service-access remains an infrastructure dashboard/static asset and console/status UI remains terminal-only unless a later workflow verifies a browser frontend module.

Senior Tester:

- Default gates must use static and mocked tests. Targeted tests should cover YAML schema validation, duplicate port detection, phase dependency ordering, preflight conflict reporting, health-check planning, and fail-closed validation semantics.

Dependency / Deadlock Validator:

- The slice order is acyclic: architecture decision first, registry schema second, domain/application consumers third, deployment/compose migration after consumers, validation last.

Does the implementation still match the EPIC?

- Yes, if execution preserves the autonomous runnable setup EPIC and service-access EPIC boundaries and does not claim live runnable success before evidence exists.

## Execution Profile

`executionProfile=FULL_PATH`

Reason:

- The workflow affects setup/deployment behavior, configuration contracts, port allocation, service ordering, quality gates, architecture documentation, and possible future service-stack expansion.

Required Full Reviews:

- Senior Requirement Engineer
- Senior System Architect
- Senior Python Automation Developer
- Senior React Frontend Developer impact check
- Senior Tester
- Senior Documentation Engineer
- Senior DevOps Engineer where deployment and runtime configuration are touched
- Security review where secrets, credential references, or service exposure are touched

Quality Commands:

- Targeted during execution: relevant `PYTHONPATH=src python3 -m unittest ...` commands per slice.
- Required before commit/push of implementation slices: `python3 tools/quality_gate.py quality`.
- Documentation-only targeted gate: `git diff --check`.

## Target Picture

Tiny Swarm World has one declarative setup model that can answer:

- which phase runs in which order;
- which services belong to each phase;
- which services depend on previous phases or service readiness;
- which external host ports are reserved, diagnostic, or ingress-owned;
- which internal container ports remain unchanged;
- which preflight checks block mutation;
- which health checks verify each phase;
- which validation checks prove the greenpath without claiming live success by default.

## Verified Baseline

Repository evidence checked during workflow creation:

- Root branch was `main`, then workflow branch `feature/workflow-installation-phases-port-registry-20260620` was created and verified.
- Root `AGENTS.md` defines Linux/WSL-only, Python automation, Docker Swarm-first, LXC-native direction.
- `QUALITY.md` defines `python3 tools/quality_gate.py quality` and targeted gates.
- `documentation/epics/autonomous-runnable-setup.md` requires preflight, resource, port, secret, platform, artifact, deployment, and readiness checks before full runnable success.
- `documentation/epics/service-access-dashboard-vaultwarden.md` requires service-access/Vaultwarden safety and forbids React scope.
- `documentation/arc42/07_deployment_view.adoc` documents Traefik `80/443` as the current service-access public ingress baseline.
- `documentation/arc42/08_concepts.adoc` documents desired inventory, observed state, evidence, ingress, and workflow distribution concepts.
- `src/tiny_swarm_world/domain/preflight/setup_manifest.py` currently owns setup port and secret requirements.
- `src/tiny_swarm_world/domain/deployment/service_stack_contract.py` currently owns service stack endpoint defaults.
- `infra/config/compose/**/docker-compose.yml` currently contains direct published ports for several stacks.

## Target Outcome

After `workflow execute`, the repository should contain:

- a central port registry with tested ranges, uniqueness, service mapping, internal/external semantics, and ingress/direct exposure classification;
- a central installation phase registry with dependency ordering and required/optional service membership;
- application services that consume the registries through ports and domain models;
- setup/preflight behavior that checks required host ports before mutation;
- deployment/service-stack planning that is aligned with the registry;
- health and validation planning that fails closed when evidence is unavailable;
- synchronized arc42 and operator documentation.

## Scope

In scope:

- `infra/config` desired-state files for ports, phases, dependencies, health checks, and validation plans.
- Python domain models for port registry and installation plan concepts.
- Application ports/services for registry loading, phase ordering, preflight planning, and validation planning.
- Infrastructure YAML repositories and composition wiring.
- Existing compose stack contract alignment for Portainer, Nexus, Jenkins, SonarQube, Apache Pulsar, Swagger/NGINX, Infisical, service-access, and Traefik.
- Tests for schema validation, ordering, duplicate detection, preflight integration, deployment planning, and evidence semantics.
- Documentation and arc42 synchronization.

Out of scope:

- Live infrastructure execution.
- Claims that services are live-installed, reachable, or healthy.
- Browser React frontend implementation.
- Replacing Pulsar with RabbitMQ without explicit service selection and compose contract.
- Replacing Traefik `80/443` public ingress without ADR coverage.

## Architecture Constraints

- Preserve hexagonal boundaries.
- Domain code must not import YAML, filesystem, command runners, HTTP clients, logging, Docker clients, or infrastructure adapters.
- Application services may orchestrate domain objects and ports but must not parse files or run shell commands directly.
- Infrastructure adapters implement YAML and filesystem details.
- Composition remains in `src/tiny_swarm_world/infrastructure/composition.py` and related composition modules.
- Config files under `infra/config` are product behavior and must be validated through structured YAML APIs.
- Default tests and quality gates must not run live infrastructure commands.

## Python Automation Assessment

Expected Python surfaces:

- New or extended domain models for port ranges, service ports, installation phases, dependency edges, health checks, and validation steps.
- New application ports for loading those desired-state declarations.
- Infrastructure YAML repositories using `ruamel.yaml` in the established style.
- Setup/preflight/deployment services that consume typed data, not raw YAML dictionaries.
- Composition wiring that keeps concrete repositories out of application service constructors.

## Frontend Assessment

- No browser React frontend is in scope.
- The existing service-access static dashboard may need route/port display updates only if the registry becomes the source for its catalog.
- Console/status UI impact is limited to setup progress and validation status wording if execution slices change operator output.

## Test Strategy

Regression-first tests should cover:

- central port registry loads valid YAML and rejects duplicate external ports;
- invalid port range, invalid service id, host-specific values, and credential-bearing URL rejection;
- installation phases sort deterministically and reject cycles;
- setup manifest required ports are derived from or checked against the central registry;
- service stack endpoint contracts align with registry entries and do not claim readiness;
- compose published ports are either registry-backed, ingress-owned, or explicitly diagnostic/deferred;
- health and validation plans fail closed when an observed-state source is missing;
- default quality gates remain mocked/static and do not execute live infrastructure.

## Resilience Requirements

- Port conflict preflight must block before mutation.
- Dependency cycles must block workflow planning.
- Missing health-check evidence must produce `blocked` or `failed_to_verify`, never success.
- Resource-gated profiles must remain distinct from full runnable success.
- Secrets must be represented by source names or external secret names, not values.
- Evidence must stay redacted and under ignored `.tiny-swarm-world/**` paths.

## Ordered Slices

### Slice 01 - Architecture And Port Model Decision

Purpose:

- Record the exact port model before implementation: Traefik `80/443` remains the current public ingress baseline; high-numbered ports are direct/diagnostic/compatibility allocations unless an ADR explicitly changes ingress.

Prerequisites:

- Workflow branch active.

```yaml
slice_id: "01"
profile: "FULL_PATH"
owner: "Senior System Architect"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior Documentation Engineer"
affected_files:
  - "documentation/arc42/07_deployment_view.adoc"
  - "documentation/arc42/08_concepts.adoc"
  - "documentation/arc42/09_architecture_decisions.adoc"
  - "documentation/architecture/adr-traefik-https-ingress-existing-ca.adoc"
affected_modules: []
affected_contracts:
  - "Traefik ingress baseline"
  - "service-access setup profile"
dependencies: []
parallel_group: "architecture"
file_locks:
  - "documentation/arc42/**"
  - "documentation/architecture/adr-traefik-https-ingress-existing-ca.adoc"
contract_locks:
  - "public ingress port model"
architecture_locks:
  - "Docker Swarm-first deployment"
  - "LXC-native provider direction"
quality_gates:
  targeted:
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "Check and update deployment/concepts/ADR index if the port model changes."
  adr: "Required only if replacing Traefik 80/443 public ingress with high-numbered public gateway ports."
stop_conditions:
  - "Stop if high-numbered ports would contradict accepted Traefik ingress without an ADR."
```

Done Criteria:

- The workflow execution records whether the port registry governs direct ports, public ingress, or both.
- arc42 remains aligned with the selected model.
- ADR need is explicitly resolved.

Verification Commands:

- `git diff --check`

### Slice 02 - Central Port Registry Contract

Purpose:

- Add a central desired-state port registry under `infra/config` with range definitions, service mappings, external/internal semantics, exposure class, and ownership metadata.

Prerequisites:

- Slice 01 completed.

```yaml
slice_id: "02"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "infra/config/ports.yaml"
  - "src/tiny_swarm_world/domain/preflight/setup_manifest.py"
  - "src/tiny_swarm_world/domain/network/port_forwarding_plan.py"
  - "tests/domain/preflight/test_preflight_result.py"
  - "tests/domain/network/test_port_forwarding_plan.py"
affected_modules:
  - "tiny_swarm_world.domain.preflight"
  - "tiny_swarm_world.domain.network"
affected_contracts:
  - "Port registry schema"
dependencies:
  - "01"
parallel_group: "backend"
file_locks:
  - "infra/config/ports.yaml"
  - "src/tiny_swarm_world/domain/**"
  - "tests/domain/**"
contract_locks:
  - "port registry schema"
architecture_locks:
  - "domain parser-independent model"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.domain.network.test_port_forwarding_plan tests.domain.preflight.test_preflight_result"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "Concepts may need a port registry summary."
  adr: "Not expected unless ingress baseline changes."
stop_conditions:
  - "Stop if the registry would contain host-specific IP addresses, secrets, or credential-bearing URLs."
  - "Stop if domain code would parse YAML directly."
```

Done Criteria:

- Port ranges and service port entries are centrally declared.
- Duplicate external ports are rejected by tests.
- Internal container ports can remain service defaults while external mappings are governed.

Verification Commands:

- `PYTHONPATH=src python3 -m unittest tests.domain.network.test_port_forwarding_plan tests.domain.preflight.test_preflight_result`

### Slice 03 - Port Registry Repository And Preflight Integration

Purpose:

- Load the port registry through an application repository port and infrastructure YAML adapter, then integrate required host-port checks into setup preflight planning.

Prerequisites:

- Slice 02 completed.

```yaml
slice_id: "03"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Tester"
  - "Senior DevOps Engineer"
affected_files:
  - "src/tiny_swarm_world/application/ports/repositories/port_port_registry_repository.py"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/port_registry_yaml_repository.py"
  - "src/tiny_swarm_world/application/services/platform/preflight_service.py"
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "tests/infrastructure/adapters/repositories/test_port_registry_yaml_repository.py"
  - "tests/application/services/platform/test_preflight_service.py"
affected_modules:
  - "tiny_swarm_world.application.ports.repositories"
  - "tiny_swarm_world.infrastructure.adapters.repositories"
  - "tiny_swarm_world.application.services.platform"
affected_contracts:
  - "setup preflight port availability"
dependencies:
  - "02"
parallel_group: "backend"
file_locks:
  - "src/tiny_swarm_world/application/ports/repositories/**"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/**"
  - "src/tiny_swarm_world/application/services/platform/preflight_service.py"
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "tests/infrastructure/adapters/repositories/**"
  - "tests/application/services/platform/test_preflight_service.py"
contract_locks:
  - "port registry repository contract"
  - "preflight blocker semantics"
architecture_locks:
  - "application depends on ports, infrastructure implements adapters"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_port_registry_yaml_repository tests.application.services.platform.test_preflight_service"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "Update concepts/building blocks if a new repository port is introduced."
  adr: "Not expected."
stop_conditions:
  - "Stop if preflight executes live networking commands in default tests."
  - "Stop if infrastructure repository details leak into domain or application models."
```

Done Criteria:

- Registry YAML loads via infrastructure adapter.
- Application preflight can report port conflicts as blockers.
- Tests use fakes/mocks and no live socket mutation.

Verification Commands:

- `PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_port_registry_yaml_repository tests.application.services.platform.test_preflight_service`

### Slice 04 - Installation Phase Registry And Dependency Graph

Purpose:

- Add a central phase plan for setup order and validate acyclic dependencies for preflight, platform, cluster, network/routing, secrets, artifacts, CI/CD, quality, messaging, observability, control, docs, and validation phases.

Prerequisites:

- Slice 01 completed.

```yaml
slice_id: "04"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior Tester"
affected_files:
  - "infra/config/installation-plan.yaml"
  - "src/tiny_swarm_world/domain/preflight/setup_manifest.py"
  - "src/tiny_swarm_world/application/services/setup/workflow.py"
  - "tests/application/services/setup/test_setup_workflow.py"
  - "tests/domain/preflight/test_preflight_result.py"
affected_modules:
  - "tiny_swarm_world.domain.preflight"
  - "tiny_swarm_world.application.services.setup"
affected_contracts:
  - "installation phase registry"
  - "setup phase sequencing"
dependencies:
  - "01"
parallel_group: "backend"
file_locks:
  - "infra/config/installation-plan.yaml"
  - "src/tiny_swarm_world/domain/preflight/**"
  - "src/tiny_swarm_world/application/services/setup/**"
  - "tests/application/services/setup/**"
contract_locks:
  - "setup workflow phase order"
architecture_locks:
  - "fail-closed setup orchestration"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.application.services.setup.test_setup_workflow tests.domain.preflight.test_preflight_result"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "Runtime/deployment view should summarize ordered setup phases."
  adr: "Not expected."
stop_conditions:
  - "Stop if dependency cycles exist."
  - "Stop if a missing phase verification path can still report success."
```

Done Criteria:

- Installation phases are declared centrally.
- Phase dependencies sort deterministically.
- Cycle and missing-required-service cases fail closed.

Verification Commands:

- `PYTHONPATH=src python3 -m unittest tests.application.services.setup.test_setup_workflow tests.domain.preflight.test_preflight_result`

### Slice 05 - Service Registry And Stack Alignment

Purpose:

- Align service stack contracts, desired inventory, compose stack metadata, and registry service names so each selected service has a phase, dependency, port classification, and readiness target.

Prerequisites:

- Slices 02 and 04 completed.

```yaml
slice_id: "05"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior DevOps Engineer"
  - "Senior Tester"
affected_files:
  - "infra/config/services.yml"
  - "infra/config/inventory/desired_inventory.yaml"
  - "infra/config/compose/**/docker-compose.yml"
  - "src/tiny_swarm_world/domain/deployment/service_stack_contract.py"
  - "src/tiny_swarm_world/application/services/deployment/service_stack_plan.py"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py"
  - "tests/domain/deployment/test_service_stack_contract.py"
  - "tests/application/services/deployment/test_service_stack_plan.py"
  - "tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py"
affected_modules:
  - "tiny_swarm_world.domain.deployment"
  - "tiny_swarm_world.application.services.deployment"
  - "tiny_swarm_world.infrastructure.adapters.repositories"
affected_contracts:
  - "service stack contract"
  - "compose published port extraction"
  - "desired inventory selected stacks"
dependencies:
  - "02"
  - "04"
parallel_group: "runtime"
file_locks:
  - "infra/config/services.yml"
  - "infra/config/inventory/desired_inventory.yaml"
  - "infra/config/compose/**"
  - "src/tiny_swarm_world/domain/deployment/**"
  - "src/tiny_swarm_world/application/services/deployment/**"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py"
contract_locks:
  - "service stack registry"
  - "compose stack port mapping"
architecture_locks:
  - "Deployment responsibility boundary"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.domain.deployment.test_service_stack_contract tests.application.services.deployment.test_service_stack_plan tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "Update deployment view when direct published ports change or are reclassified."
  adr: "Required if service exposure model changes beyond documented Traefik/direct-port compatibility."
stop_conditions:
  - "Stop if Portainer becomes a bootstrap dependency for Portainer."
  - "Stop if service readiness is claimed from static config alone."
  - "Stop if RabbitMQ is added without service-stack contract, compose, tests, and docs."
```

Done Criteria:

- Selected services map to registry entries and phases.
- Compose published ports are either registry-backed, ingress-owned, or explicitly deferred.
- Current Pulsar baseline and any RabbitMQ decision are explicit.

Verification Commands:

- `PYTHONPATH=src python3 -m unittest tests.domain.deployment.test_service_stack_contract tests.application.services.deployment.test_service_stack_plan tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml`

### Slice 06 - Health Check And Validation Plan Registry

Purpose:

- Add health-check and validation-plan declarations that distinguish static readiness plans from observed runtime evidence.

Prerequisites:

- Slices 04 and 05 completed.

```yaml
slice_id: "06"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Tester"
  - "Senior DevOps Engineer"
affected_files:
  - "infra/config/health-checks.yaml"
  - "infra/config/validation-plan.yaml"
  - "src/tiny_swarm_world/application/services/deployment/verify_swarm_service_readiness.py"
  - "src/tiny_swarm_world/application/services/deployment/workflows.py"
  - "tests/application/services/deployment/test_verify_swarm_service_readiness.py"
  - "tests/application/services/deployment/test_deployment_workflows.py"
affected_modules:
  - "tiny_swarm_world.application.services.deployment"
affected_contracts:
  - "health check registry"
  - "greenpath validation plan"
dependencies:
  - "04"
  - "05"
parallel_group: "quality"
file_locks:
  - "infra/config/health-checks.yaml"
  - "infra/config/validation-plan.yaml"
  - "src/tiny_swarm_world/application/services/deployment/**"
  - "tests/application/services/deployment/**"
contract_locks:
  - "service readiness evidence semantics"
architecture_locks:
  - "observed-state evidence remains local and redacted"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_verify_swarm_service_readiness tests.application.services.deployment.test_deployment_workflows"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "Update quality requirements with validation-plan fail-closed behavior."
  adr: "Not expected."
stop_conditions:
  - "Stop if HTTP checks are documented as live default quality gates."
  - "Stop if missing observed evidence reports healthy."
```

Done Criteria:

- Health checks and greenpath validation steps are centrally declared.
- Runtime evidence remains separate from desired checks.
- Tests prove missing evidence fails closed.

Verification Commands:

- `PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_verify_swarm_service_readiness tests.application.services.deployment.test_deployment_workflows`

### Slice 07 - Operator Documentation And Arc42 Synchronization

Purpose:

- Update operator docs, arc42, and EPIC references to explain the installation phase model, port registry, current Traefik ingress baseline, and validation semantics.

Prerequisites:

- Slices 02 through 06 completed or explicitly skipped with evidence.

```yaml
slice_id: "07"
profile: "FULL_PATH"
owner: "Senior Documentation Engineer"
secondary_reviewers:
  - "Senior System Architect"
  - "Senior Requirement Engineer"
  - "Senior Tester"
affected_files:
  - "README.md"
  - "documentation/deployment/system.adoc"
  - "documentation/system/lxc-native-setup.adoc"
  - "documentation/configuration/config-contract-inventory.md"
  - "documentation/arc42/05_building_blocks.adoc"
  - "documentation/arc42/06_runtime_view.adoc"
  - "documentation/arc42/07_deployment_view.adoc"
  - "documentation/arc42/08_concepts.adoc"
  - "documentation/arc42/10_quality_requirements.adoc"
  - "documentation/epics/autonomous-runnable-setup.md"
affected_modules: []
affected_contracts:
  - "operator setup documentation"
dependencies:
  - "02"
  - "03"
  - "04"
  - "05"
  - "06"
parallel_group: "documentation"
file_locks:
  - "README.md"
  - "documentation/**"
contract_locks:
  - "documented setup behavior"
architecture_locks:
  - "arc42 deployment and concept consistency"
quality_gates:
  targeted:
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "Must be synchronized."
  adr: "Only if execution changed accepted architecture decisions."
stop_conditions:
  - "Stop if docs would claim live installation or health without evidence."
  - "Stop if docs use Windows-specific setup commands or paths."
```

Done Criteria:

- Documentation describes implemented behavior only.
- Planned services remain clearly marked as planned, optional, or deferred.
- arc42 is consistent with registry and setup behavior.

Verification Commands:

- `git diff --check`

### Slice 08 - Full Quality Gate And Execution Handoff

Purpose:

- Run final verification, classify any failures through repository quality rules, and prepare the workflow evidence for commit/push readiness if requested.

Prerequisites:

- Slices 01 through 07 completed or explicitly stopped with evidence.

```yaml
slice_id: "08"
profile: "FULL_PATH"
owner: "Senior Tester"
secondary_reviewers:
  - "Quality Gate Orchestrator"
  - "Senior Workflow Architect"
affected_files:
  - ".codex/evidence/**"
  - "documentation/workflow/context-pack.md"
  - "documentation/workflow/context-pack.json"
affected_modules: []
affected_contracts:
  - "quality gate evidence"
dependencies:
  - "07"
parallel_group: "quality"
file_locks:
  - ".codex/evidence/**"
  - "documentation/workflow/**"
contract_locks:
  - "workflow execute evidence"
architecture_locks: []
quality_gates:
  targeted:
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "Confirm synchronized."
  adr: "Confirm no missing ADR remains."
stop_conditions:
  - "Stop on failed or unverifiable required quality gate."
  - "Stop if generated local artifacts, caches, logs, or secrets appear in git status."
```

Done Criteria:

- Required gates are run or explicitly justified if skipped.
- Evidence records targeted and full gate outcomes.
- No generated local state is staged.

Verification Commands:

- `python3 tools/quality_gate.py quality`

## Slice Dependency Graph

```text
01
|\
| +-- 04
|     \
02 ----+-- 05 -- 06 -- 07 -- 08
  \
   +-- 03
```

Execution order:

1. Slice 01
2. Slice 02 and Slice 04 may run after Slice 01 if isolated worktrees are used and file locks are disjoint.
3. Slice 03 may run after Slice 02.
4. Slice 05 waits for Slices 02 and 04.
5. Slice 06 waits for Slices 04 and 05.
6. Slice 07 waits for implementation slices.
7. Slice 08 runs last.

## Parallel Execution

- Can this workflow run in parallel? `limited`
- Conflicting workflows: any workflow that touches `infra/config/**`, setup/deployment services, compose stack contracts, `documentation/arc42/**`, or service-access/Traefik ingress.
- Shared files: `src/tiny_swarm_world/infrastructure/composition.py`, `src/tiny_swarm_world/domain/preflight/setup_manifest.py`, `src/tiny_swarm_world/domain/deployment/service_stack_contract.py`, `infra/config/compose/**`, `documentation/arc42/**`.
- Shared infrastructure: LXC/LXD/Incus, Docker Swarm, compose stacks, Portainer, Nexus, Jenkins, SonarQube, Infisical, Pulsar, service-access, Traefik.
- Requires isolated worktree: `yes`
- Requires serialized live validation: `yes`
- Merge-order constraints: architecture and registry contracts before consumers; documentation after behavior; final quality last.

Parallelization Opportunities:

- Slice 02 and Slice 04 may be split after Slice 01 if Three Amigos confirms disjoint files.
- Slice 03 can run in parallel with Slice 04 after Slice 02 only if setup manifest files are not shared.
- Documentation drafting for Slice 07 may begin read-only earlier, but writes wait until implementation behavior is known.

## Automatic Work Distribution Policy

During `workflow execute`, Codex must analyze every slice for safe specialist stream decomposition before implementation.

Stream map:

- backend: Senior Python Automation Developer for domain, application, ports, repositories, and composition.
- frontend: console/status UI skills for terminal/status output; browser React impact check is N/A unless a verified frontend module exists.
- tests: Senior Tester and quality-gate skills.
- runtime: Senior DevOps Engineer for compose, Docker Swarm, LXC exposure, and service-stack runtime contracts.
- documentation: Senior Documentation Engineer.
- quality: Quality Gate Orchestrator and Senior Tester.
- architecture: Senior System Architect and arc42 governance.
- security: security and secrets/configuration review where port exposure, credentials, or evidence are touched.

`workflow execute` must use real Codex subagents where supported. If callable subagents are unavailable, the executor must perform explicit role-based fallback review in the main thread and record that fallback in `.codex/evidence/slice-<number>-distribution.md`.

Before implementation for each slice:

- write `.codex/evidence/slice-<number>-distribution.md`;
- record whether the slice can be split into backend, frontend, tests, runtime, documentation, quality, architecture, or security streams;
- record file locks, contract locks, and stop conditions.

After implementation for each implemented slice:

- write `.codex/evidence/slice-<number>-consolidation.md`;
- record accepted stream changes, rejected changes, tests run, and remaining risk.

Non-parallelization rules:

- Do not parallelize overlapping files.
- Do not parallelize unclear architecture boundaries.
- Do not parallelize contradictory requirements.
- Do not parallelize mandatory ordering.
- Do not parallelize shared migrations or strict schema/config sequencing.
- Do not parallelize generated-file conflicts.
- Do not parallelize when Three Amigos marks the slice not safely parallelizable.
- Do not parallelize unclear secrets handling.
- Do not parallelize weakened safety guards.

Codex remains final integration owner for consolidation, tests, evidence, PR readiness, and merge readiness.

## Git Worktree Execution Rule

Every executable stream must use an isolated worktree and stream branch when parallelized.

Stream branch format:

```text
feature/workflow-installation-phases-port-registry-20260620-slice-<number>-<stream>
```

Rules:

- Verify the stream branch belongs to this workflow before writing.
- Do not implement on `main`, `master`, `develop`, or shared branches.
- Stream workers must not merge directly into the main workflow branch.
- Codex consolidates stream results into `feature/workflow-installation-phases-port-registry-20260620` after evidence and tests pass.
- Live validation is serialized unless isolated disposable infrastructure is explicitly approved.

## Role Ownership Map

- Senior Workflow Architect: workflow dependency ordering and execution handoff.
- Senior Requirement Engineer: requirement drift, EPIC fit, open assumptions.
- Senior System Architect: architecture boundaries, Traefik/port model, ADR need.
- Senior Python Automation Developer: domain, application, repositories, composition, tests.
- Senior React Frontend Developer: mandatory impact check; no React scope approved.
- Senior Tester: regression design and quality gate evidence.
- Senior DevOps Engineer: compose, Swarm, LXC exposure, service-stack runtime contracts.
- Senior Documentation Engineer: README, arc42, deployment/system docs.
- Security reviewer: secrets, credential references, port exposure, evidence redaction.

## Quality Gate Expectations

Use commands from `QUALITY.md` only.

Targeted gates:

- `git diff --check` for documentation-only slices.
- `PYTHONPATH=src python3 -m unittest <nearest test modules>` for implementation slices.

Required final gate:

```bash
python3 tools/quality_gate.py quality
```

The default quality gate must not execute live infrastructure commands.

## Documentation Synchronization Points

- Slice 01: arc42 and ADR check for port model.
- Slice 05: deployment view if compose published ports or service stack endpoint behavior changes.
- Slice 06: quality requirements if validation evidence semantics change.
- Slice 07: README, deployment docs, system docs, configuration docs, EPIC notes, and arc42 synchronization.

## Stop Conditions

Stop workflow execution if:

- active branch is not the workflow branch or its approved stream branch;
- a slice would touch files outside its allowed scope;
- Traefik ingress would be replaced without ADR coverage;
- live infrastructure commands would be required without explicit approval;
- domain/application/infrastructure dependency direction would be violated;
- service health would be claimed without observed-state or smoke evidence;
- secrets, tokens, local IP addresses, local absolute paths, or raw command output would be committed or persisted as evidence;
- RabbitMQ is added without explicit service-stack contract, compose, tests, and docs;
- quality commands cannot be verified from `QUALITY.md`;
- unrelated local changes appear and ownership is unclear.

## Uncertainty Escalation Rules

- Port model conflict: escalate to Senior System Architect and ADR steward.
- Pulsar vs RabbitMQ service-selection conflict: escalate to Senior Requirement Engineer and Senior System Architect.
- Secret-handling uncertainty: escalate to security and secrets/configuration review.
- Quality gate uncertainty: escalate to Senior Tester and Quality Gate Orchestrator.
- Branch or file-lock conflict: escalate to Senior Workflow Architect and conflict-resolution skill.

## Commit And Push Plan

- Do not commit or push during workflow creation unless explicitly requested.
- During `workflow execute`, each slice commit must represent exactly one slice.
- `push auto` is not implied by this workflow. If later requested, it must run the full guarded lifecycle described in root `AGENTS.md`.

## Definition Of Done

- `documentation/workflow/workflow.md` exists and validates against workflow-authoring structure.
- `documentation/workflow/context-pack.md` and `documentation/workflow/context-pack.json` exist.
- Branch evidence is recorded.
- Slices include YAML metadata, dependencies, file locks, quality gates, documentation impact, and stop conditions.
- arc42 check status is recorded.
- `workflow execute` can start from this workflow without guessing scope.

## Handoff To Workflow Execute

`workflow execute` may proceed after verifying:

- active branch is `feature/workflow-installation-phases-port-registry-20260620`;
- `documentation/workflow/context-pack.json` hashes still match governing files;
- no unrelated or unclear local changes exist;
- slice metadata is intact;
- S3/S3D preflight confirms dependency order and file locks;
- live infrastructure commands remain out of default gates unless explicitly approved.

## arc42 Check Status

Checked during workflow creation:

- `documentation/arc42/05_building_blocks.adoc`
- `documentation/arc42/07_deployment_view.adoc`
- `documentation/arc42/08_concepts.adoc`
- `documentation/arc42/09_architecture_decisions.adoc`
- `documentation/arc42/10_quality_requirements.adoc`

Result:

- arc42 already documents the current Traefik `80/443` ingress baseline, desired/observed state separation, evidence redaction, and service-access profile boundaries.
- No arc42 file was changed during workflow creation.
- Slice 01 and Slice 07 are responsible for arc42 updates during execution if implementation changes behavior or documented contracts.
