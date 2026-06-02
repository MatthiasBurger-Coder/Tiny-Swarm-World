# Responsibility Separation Analysis

Status: analysis and planning only; pre-removal Multipass path references are
archival and superseded by
`documentation/architecture/adr-retire-multipass-legacy-provider.adoc`.

This document records the current responsibility boundaries in Tiny Swarm World
and identifies the files that should be owned by future bounded areas. No live
infrastructure commands were run for this analysis.

## Safety Inspection

Repository state before documentation changes:

- `git status --short --branch` reported `## main...origin/main`.
- No tracked staged or unstaged changes were present before this analysis.
- Generated caches, local virtual environments, debugger artifacts, and logs
  appear as ignored files through `git status --ignored --short`; they are not
  part of the tracked source set.

Required files inspected first:

- `AGENTS.md`
- `src/tiny_swarm_world/AGENTS.md`
- `infra/AGENTS.md`
- `.importlinter`
- `README.md`
- `tools/quality_gate.py`

Additional relevant areas inspected:

- `src/tiny_swarm_world/domain`
- `src/tiny_swarm_world/application`
- `src/tiny_swarm_world/infrastructure`
- `infra/config`
- `infra/compose`
- `infra/prepare` (retired navigation notes only)
- `infra/swarm`
- `tests`
- existing import-ready issue files

## Current State Summary

The repository already follows a basic hexagonal package split:

- `domain` holds value objects and domain concepts.
- `application` holds use cases and ports.
- `infrastructure` holds concrete adapters and wiring.
- `.importlinter` prevents domain-to-application, domain-to-infrastructure,
  and application-to-infrastructure imports.

The main structural issue is not the hexagonal layering itself. The issue is
that several different business responsibilities are grouped by technology or
runtime tool instead of by responsibility:

- VM, network, Docker installation, and Swarm provisioning.
- Docker image build/push, Nexus repository setup, and artifact publishing.
- Compose stacks, Portainer stack upload, and service deployment.
- Shared command/YAML/file/path/logging infrastructure.

The target `infra/platform`, `infra/artifacts`, `infra/deployment`, and
`infra/shared` directories now exist as documentation markers only. Existing
infra assets have not been moved yet, so existing documented commands and
script-relative paths remain unchanged.

## A. Platform Provisioning

Platform Provisioning owns everything needed to create and prepare the local
cluster substrate.

### Source Code

- former `src/tiny_swarm_world/domain/multipass` (superseded)
- `src/tiny_swarm_world/domain/network`
- former `src/tiny_swarm_world/application/services/multipass` (superseded)
- `src/tiny_swarm_world/application/services/network`
- `src/tiny_swarm_world/application/services/platform`
  compatibility namespace for the incremental platform boundary migration
- `src/tiny_swarm_world/application/services/vm`
- `src/tiny_swarm_world/application/ports/repositories/port_vm_repository.py`
- `src/tiny_swarm_world/application/ports/repositories/port_yaml_repository.py`
  when used for netplan repository behavior
- `src/tiny_swarm_world/infrastructure/adapters/repositories/vm_repository_yaml.py`
- `src/tiny_swarm_world/infrastructure/adapters/repositories/netplan_repository.py`

### Infrastructure Assets

- `infra/config/cloud-init-manager.yaml`
- former `infra/config/multipass` (superseded)
- `infra/config/docker/command_multipass_docker_install_yaml.yaml`
- `infra/config/docker/command_multipass_docker_prepare_repository_yaml.yaml`
- `infra/config/docker/command_multipass_docker_swarm_join_worker.yaml`
- `infra/config/docker/command_multipass_docker_swarm_manager_init.yaml`
- `infra/config/docker/command_multipass_docker_swarm_manager_ip.yaml`
- `infra/config/docker/command_multipass_docker_swarm_manager_join_token.yaml`
- `infra/config/network`
- `infra/config/vm`
- `infra/swarm`
- `infra/platform/README.md` as target boundary marker
- `infra/swarm/README.md` documents the current legacy helper status

### Tests and Documentation

- `tests/application/services/multipass`
- `tests/application/services/network`
- `tests/domain/network`
- `documentation/system/multipass-setup.adoc`
- `documentation/system/network.adoc`

## B. Artifact Build / Registry / Publishing

Artifact Build / Registry / Publishing owns image and artifact publication,
Nexus repository behavior, and future Maven or Docker registry workflows.

### Source Code

- `src/tiny_swarm_world/domain/nexus`
- `src/tiny_swarm_world/application/services/artifacts`
  compatibility namespace for the incremental artifact boundary migration
- `src/tiny_swarm_world/application/ports/clients/port_nexus_client.py`
- `src/tiny_swarm_world/infrastructure/adapters/clients/nexus_http_client.py`
- `src/tiny_swarm_world/application/services/nexus/enable_nexus_anonymous_access.py`
- `src/tiny_swarm_world/application/services/nexus/ensure_nexus_admin_access.py`
- `src/tiny_swarm_world/application/services/nexus/wait_for_nexus_ready.py`
- `src/tiny_swarm_world/application/services/nexus/nexus_bootstrap_configuration.py`

### Infrastructure Assets

- `infra/compose/**/Dockerfile`
- `infra/artifacts/README.md` as target boundary marker
- service configuration files that are used as image build contexts

### Tests and Documentation

- Nexus-specific parts of `tests/application/services/nexus`
- Nexus setup sections in `documentation/deployment/system.adoc`
- Nexus setup sections in `documentation/user_guide/usage.adoc`

## C. Stack / Service Deployment

Stack / Service Deployment owns service stack definitions, compose repositories,
Portainer stack APIs, and service lifecycle through Portainer or Docker Swarm.

### Source Code

- `src/tiny_swarm_world/domain/deployment`
- `src/tiny_swarm_world/application/services/deployment`
  compatibility namespace for the incremental deployment boundary migration
- `src/tiny_swarm_world/application/ports/clients/port_portainer_client.py`
- `src/tiny_swarm_world/application/ports/repositories/port_compose_file_repository.py`
- `src/tiny_swarm_world/infrastructure/adapters/clients/portainer_http_client.py`
- `src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py`
- `src/tiny_swarm_world/application/services/nexus/ensure_nexus_stack.py`
  currently belongs here by behavior, despite living under `services/nexus`.

### Infrastructure Assets

- `infra/config/compose`
- stack directories under `infra/compose`, including:
  - `infra/config/compose/jenkins`
  - `infra/config/compose/swagger`
- `infra/prepare/portainer/README.md` documents the retired direct preparation
  surface
- Portainer stack compose files under `infra/config/compose/portainer`
- service stack compose files under `infra/config/compose/nexus`,
  `infra/config/compose/rabbitmq`, and `infra/config/compose/sonarqube`
- `infra/deployment/README.md` as target boundary marker

### Tests and Documentation

- `tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py`
- Portainer/stack related tests that may be added later
- deployment sections in `documentation/deployment/system.adoc`
- service deployment sections in `documentation/user_guide/usage.adoc`

## D. Shared Kernel / Cross-Cutting Infrastructure

Shared infrastructure is reusable plumbing. It should not own platform,
artifact, or deployment decisions.

### Source Code

- `src/tiny_swarm_world/domain/command`
- `src/tiny_swarm_world/application/services/commands`
- `src/tiny_swarm_world/application/ports/commands`
- `src/tiny_swarm_world/application/ports/file_management`
- `src/tiny_swarm_world/application/ports/ui`
- `src/tiny_swarm_world/application/ports/repositories/port_command_repository.py`
- `src/tiny_swarm_world/infrastructure/adapters/command_runner`
- `src/tiny_swarm_world/infrastructure/adapters/file_management`
- `src/tiny_swarm_world/infrastructure/adapters/yaml`
- `src/tiny_swarm_world/infrastructure/adapters/ui`
- `src/tiny_swarm_world/infrastructure/adapters/repositories/command_multipass_init_repository_yaml.py`
- `src/tiny_swarm_world/infrastructure/dependency_injection`
- `src/tiny_swarm_world/infrastructure/logging`
- `src/tiny_swarm_world/infrastructure/project_paths.py`
- `src/tiny_swarm_world/infrastructure/os_types.py`
- `src/tiny_swarm_world/infrastructure/composition.py`
  now exposes `build_platform_services()` and keeps
  `build_application_services()` as a compatibility wrapper

### Repository and Quality Tooling

- `tools/quality_gate.py`
- `infra/shared/README.md` as target boundary marker
- `.importlinter`
- `.gitattributes`
- `.gitignore`
- `requirements.txt`
- `setup.py`
- `environment.yml`

## E. Legacy / Example / Transitional Areas

These areas need explicit classification before any cleanup:

- The former Java/Maven example application has been removed. Do not
  reintroduce Java, Maven, or Spring Boot as project build surfaces unless a
  later task explicitly changes scope.
- `infra/swarm/prepere.py` imports modules that are not present in the tracked
  `infra/swarm/multipass` directory. It looks transitional or broken.
- `infra/swarm/multipass/multipass_setup.py` and
  `infra/swarm/multipass/multipass_socat_setup.py` duplicate parts of the
  Python application services and command YAML workflow.
- `infra/swarm/network/network_manager.py` mixes WSL, Windows `netsh`,
  Multipass discovery, and iptables behavior.
- Former direct preparation helpers under `infra/prepare` have been retired.
- Spelling issues such as `netplant`, `prepere.py`, `portain_setup.py`, and
  `excecuteable_commands.py` are structural cleanup candidates, but renames
  should be separate behavior-preserving slices.
- Ignored generated/runtime files include `__pycache__`, `.venv`, `bin`, `lib`,
  `.ruff_cache`, `.mypy_cache`, `.import_linter_cache`, `logs`, `infra/logs`,
  and debugger artifacts. They should remain ignored and not become part of the
  architecture split.

## Responsibility Conflict Findings

| ID | File or Area | Current Responsibility | Conflicting Responsibility | Boundary Problem | Proposed Target Owner | Risk | Follow-up Agent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C-001 | `src/tiny_swarm_world/application/services/nexus/ensure_nexus_stack.py` | Nexus bootstrap | Portainer stack deployment | A Nexus service directly owns stack creation/update through Portainer. | Deployment | Medium | Stack Deployment Agent |
| C-002 | `src/tiny_swarm_world/application/services/nexus/bootstrap_nexus.py` | Nexus workflow orchestration | Deployment plus registry configuration | A single workflow combines stack deployment, readiness, credential rotation, and anonymous access. | Split between Deployment and Artifacts | Medium | Artifact Registry Agent plus Stack Deployment Agent |
| C-003 | `infra/prepare/nexus/setup.py` | Retired Nexus setup entrypoint | Composition root, Portainer client, Docker runtime, Nexus client | The former direct script wired concrete deployment and artifact adapters outside the main composition root. | Resolved by removal; behavior belongs behind setup workflow contracts | Retired | Composition / CLI Workflow Agent |
| C-004 | `infra/compose/create_dockerfiles.sh` | Retired image build and registry push helper | Stack deployment directory | The former helper mixed Dockerfile generation, build, login, push, and registry credentials in `infra/compose`. | Resolved by removal; artifacts behavior belongs to Python artifact workflow | Retired | Artifact Registry Agent |
| C-005 | `infra/compose/upload_all_stacks.sh` | Retired stack upload helper | Image build and push | The former helper sourced image publishing before stack processing. | Resolved by removal; deployment should call artifact output through workflow contracts | Retired | Stack Deployment Agent |
| C-006 | `infra/prepare/prepare.sh` | Retired top-level preparation helper | Portainer setup with optional Nexus setup | The former umbrella script could mix unrelated live setup actions. | Resolved by removal; use setup workflow | Retired | Composition / CLI Workflow Agent |
| C-007 | `infra/prepare/portainer/portain_setup.py` | Retired Portainer setup duplicate | Multipass, socat, iptables, Docker cleanup, stack deploy | The former script coupled platform networking and deployment. | Resolved by removal; split behavior across Platform and Deployment workflow contracts | Retired | Platform Provisioning Agent plus Stack Deployment Agent |
| C-008 | `infra/prepare/portainer/prepare.sh` | Retired Portainer stack deployment helper | Docker system prune and volume removal | The former helper mixed deployment bootstrap with destructive Docker cleanup. | Resolved by removal; reset behavior must stay explicit | Retired | Stack Deployment Agent |
| C-009 | `infra/config/docker` | Docker install and Swarm commands | Artifact Docker image build meaning | Directory name `docker` can mean platform daemon setup or artifact image workflows. | Platform for current files; future artifact config elsewhere | Low | Platform Provisioning Agent |
| C-010 | `src/tiny_swarm_world/infrastructure/composition.py` | Wiring root | Boundary service bundles | Composition now exposes platform, artifact, and deployment builders and keeps the existing application builder as a compatibility wrapper; live artifact and deployment behavior remains blocked behind explicit workflow contracts. | Shared composition root with boundary-specific builders | Medium | Composition / CLI Workflow Agent |
| C-011 | `src/tiny_swarm_world/__main__.py` | Thin entry point | Runtime inspection plus commented provisioning workflow | It is thin, but the active command and commented workflow obscure supported user workflows. | CLI workflow | Low | Composition / CLI Workflow Agent |
| C-012 | `infra/swarm` | Legacy platform helpers | Duplicate or broken live provisioning scripts | Scripts overlap with Python services and one imports missing modules. | Legacy quarantine, then Platform if still needed | Medium | Platform Provisioning Agent |
| C-013 | `tests` | Layer-based grouping | Missing responsibility boundary checks | Tests protect hexagonal imports but not platform/artifact/deployment ownership. | Test and Quality Gate | Low | Test and Quality Gate Agent |

## High Confidence Target Owners

- Platform Provisioning: Multipass, VM, WSL/Linux networking, netplan, socat,
  Docker daemon install, Swarm init/join, VM/cluster state discovery.
- Artifacts: Dockerfile generation, image build/tag/push, Nexus repository
  setup, Maven/Docker registry configuration, future publishing workflows.
- Deployment: compose stack definitions, compose repository, Portainer stack
  create/update/upload, service lifecycle for Portainer, Nexus, Jenkins,
  RabbitMQ, SonarQube, Swagger/NGINX.
- Shared: command execution abstractions, YAML/file/path/logging utilities,
  composition root, quality gate, import rules, test infrastructure.

## Open Questions

- Should Portainer itself be treated as a platform service dependency or as the
  first deployment stack? Current files support both interpretations. The
  recommended target is: Portainer compose deployment belongs to Deployment;
  Portainer availability as a prerequisite is exposed as a Deployment port.
- Should Nexus stack deployment be owned by Deployment while Nexus repository
  configuration is owned by Artifacts? The recommended answer is yes.
- Should `infra/swarm` be removed or kept as legacy documentation? It should be
  quarantined first, then removed only after feature parity is proven.
- Should generated Dockerfiles remain tracked? Current repository tracks some
  Dockerfiles and templates. Future artifact work should decide whether
  generated Dockerfiles are source artifacts or build outputs on a per-service
  basis.
