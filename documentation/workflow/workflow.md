# Workflow: LXC Docker Swarm Bootstrap

## Metadata

```yaml
workflow_id: lxc-docker-swarm-bootstrap-v1.0.0
created: 2026-05-29
branch: feature/workflow-lxc-docker-install-20260529
status: READY_FOR_EXECUTION
request: "Überarbeite die stelle damit auf den LXC Container docker installiert wird. Nimm als grundlage die multipass vorgehenweise und passe diese für die LXC an"
process_strand: S3D
execution_profile: NORMAL_PATH
primary_boundary: Platform
secondary_boundaries:
  - Shared
  - Console/status UI
provider_target: lxc_native
legacy_reference: multipass_legacy
live_infrastructure_default: false
```

## Executive Summary

Create the implementation path that installs Docker Engine inside the managed
LXC containers created by the default `lxc_native` provider and then
initializes the Docker Swarm manager and workers inside those containers.

The implementation must use the existing Multipass Docker install and Swarm
initialization flow as the behavioral baseline:

- install Docker package prerequisites;
- configure the official Docker apt repository;
- install Docker Engine, CLI, containerd, Buildx, and Compose plugin;
- verify Docker availability on each node;
- initialize the Swarm manager;
- retrieve the worker join token without persisting it;
- join worker nodes;
- verify the Swarm node state.

The LXC version must adapt the execution surface from `multipass exec` to the
managed LXD/Incus backend already selected by `lxc_native`. It must preserve
the hexagonal architecture: application services orchestrate ports and domain
objects, while concrete `lxc` or `incus` command execution remains in
infrastructure adapters and configuration.

This workflow does not deploy Portainer, Nexus, Jenkins, RabbitMQ, SonarQube,
Swagger/NGINX, service-access, or Vaultwarden. It unblocks the Platform phase
that currently stops after LXC node creation.

## Requirement Clarification Gate

```yaml
gate: requirement_clarification
status: PROCEED_WITH_ACCEPTED_ASSUMPTIONS
confidence: 0.88
decision: "Create workflow for implementation; do not run live infrastructure during workflow authoring."
```

Accepted interpretation:

- "die stelle" means the current LXC-native setup gap after platform node
  creation, where provider-native Docker installation and Docker Swarm
  initialization are still blocked.
- "auf den LXC Container docker installiert" means Docker Engine must be
  installed inside each managed LXC node, not on the WSL/Linux host and not in
  Multipass VMs.
- "Nimm als grundlage die multipass vorgehenweise" means the Multipass install
  and Swarm services/configuration are the functional template, but the new
  code must be LXD/Incus-native and provider-safe.

Accepted assumptions:

- The default LXC node image remains Ubuntu-based and compatible with the
  official Docker Engine apt repository.
- The existing Docker-in-container profile baseline remains the starting
  point: `security.nesting=true`,
  `security.syscalls.intercept.mknod=true`, and
  `security.syscalls.intercept.setxattr=true`.
- LXD and Incus must both be supported through the selected managed backend.
- Docker install and Swarm operations are live infrastructure mutations and
  remain behind existing `--live` plus interactive consent.
- Swarm join tokens, raw command output, local IP addresses, and host-specific
  details must not be persisted as trusted evidence.

Open non-blocking questions:

- Whether the Docker package version should remain "latest stable" from the
  official apt repository or become a pinned operator option.
- Whether a later reduced service profile should allow a single-node Swarm for
  low-resource hosts.

## External Planning Sources

These sources inform the workflow only. Repository code and ADRs remain
authoritative for implementation.

- Docker's official Ubuntu install documentation uses the apt repository path
  and installs `docker-ce`, `docker-ce-cli`, `containerd.io`,
  `docker-buildx-plugin`, and `docker-compose-plugin`.
- LXD documentation states that Docker-in-LXD requires
  `security.nesting=true`, and OverlayFS-oriented Docker use should also set
  syscall interception for `mknod` and `setxattr`.
- Incus documentation mirrors the same Docker-in-container nesting direction
  and keeps privileged-container choices security-sensitive.

## Governing Inputs

- `AGENTS.md`
- `QUALITY.md`
- `documentation/epics/system-unification.md`
- `documentation/epics/autonomous-runnable-setup.md`
- `documentation/architecture/adr-lxc-native-node-provider.adoc`
- `documentation/architecture/adr-autonomous-setup-safety.adoc`
- `documentation/arc42/06_runtime_view.adoc`
- `documentation/arc42/07_deployment_view.adoc`
- `documentation/arc42/09_architecture_decisions.adoc`
- `src/tiny_swarm_world/application/services/multipass/multipass_docker_install.py`
- `src/tiny_swarm_world/application/services/multipass/multipass_docker_swarm_init.py`
- `infra/config/docker/command_multipass_docker_install_yaml.yaml`
- `infra/config/docker/command_multipass_docker_prepare_repository_yaml.yaml`
- `infra/config/docker/command_multipass_docker_verify_yaml.yaml`
- `src/tiny_swarm_world/infrastructure/adapters/clients/lxc_node_provider.py`
- `infra/config/node-providers/provider_config.yaml`

## Architecture Direction

The implementation must preserve these ownership rules:

- Platform owns LXD/Incus provider readiness, LXC node lifecycle, Docker
  install, Docker Swarm initialization, node IP lookup, and platform
  verification.
- Artifacts and Deployment stay out of this workflow except for blocked-state
  compatibility after Platform succeeds.
- Domain code may receive provider-neutral value objects and result types, but
  must not import command runners, YAML adapters, Docker clients, LXD/Incus
  clients, logging, or composition.
- Application services may orchestrate Docker install and Swarm steps through
  ports and typed results, but must not embed low-level shell, filesystem, or
  backend command details.
- Infrastructure adapters own `lxc exec` and `incus exec` behavior, command
  timeout handling, backend-specific error classification, and output
  redaction.
- `src/tiny_swarm_world/infrastructure/composition.py` remains the only normal
  runtime wiring root.
- `src/tiny_swarm_world/__main__.py` remains thin.

## Target Behavior

After this workflow is implemented and verified:

- `setup run --live` with accepted interactive consent can continue from
  LXC-native platform node creation into Docker installation on
  `swarm-manager`, `swarm-worker-1`, and `swarm-worker-2`.
- Direct `platform init --live` uses the same LXC-native Docker install and
  Swarm bootstrap contracts as setup-driven platform init.
- The Docker install step is idempotent: already-installed Docker is verified
  and does not force a reinstall unless verification fails.
- The install step uses the selected backend command prefix:
  `lxc exec <node> -- ...` for LXD or `incus exec <node> -- ...` for Incus.
- The Swarm manager is initialized only when the manager is not already part
  of a Swarm.
- Worker nodes join only when not already active in the target Swarm.
- Re-runs report verified or reconciled state without requiring destructive
  reset.
- Verification returns typed, summary-only evidence for Docker version,
  daemon active state, manager state, worker membership count, and failed
  nodes.
- Raw command strings, stdout, stderr, Swarm join tokens, and local node IPs
  are redacted or omitted from persisted evidence.

## Out Of Scope

- Installing LXD, Incus, Docker, or other packages on the host.
- Repairing host daemon, group, bridge, firewall, VPN, or snap state.
- Changing the live-consent model.
- Making privileged containers the silent default.
- Deploying Portainer or application service stacks.
- Building or publishing images.
- Removing Multipass legacy support.
- Browser or React frontend work.
- Java, Maven, or Spring Boot structure.
- Kubernetes-first behavior.

## Roles

Mandatory workflow roles:

- Senior System Architect: validates Platform ownership, ADR/arc42 alignment,
  and Docker-in-container risk boundaries.
- Senior Requirement Engineer: keeps the German request, EPIC extension, and
  acceptance criteria aligned.
- Senior Documentation Engineer: updates workflow, ADR/arc42 references, and
  operator documentation without claiming unverified live success.
- Senior Tester: defines mocked regression gates, live-smoke boundaries, and
  typed evidence expectations.
- Senior DevOps Engineer: adapts Multipass Docker/Swarm behavior to
  LXD/Incus-managed containers and reviews idempotency.
- Senior Python Automation Developer: implements services, ports, adapters,
  and composition wiring.
- Senior React Frontend Developer: no implementation work; records that this
  workflow has no browser or React frontend scope.

Specialist skills:

- `workflow-executor`
- `workflow-slice-execution`
- `python-automation`
- `python-test-automation`
- `devops-docker`
- `linux-host-preparation`
- `docker-engine-installation`
- `docker-swarm-initialization`
- `swarm-node-management`
- `idempotent-platform-automation`
- `platform-verification`
- `secrets-and-config-management`
- `observability-and-diagnostics`
- `arc42-architecture-governance`
- `adr-steward`

## Slice Plan

### Slice 01 - Baseline Multipass Behavior And LXC Contract

```yaml
slice: 01
name: baseline-multipass-lxc-contract
status: READY
owner: Senior Requirement Engineer
allowed_files:
  - documentation/workflow/**
  - documentation/architecture/**
  - documentation/arc42/**
  - documentation/epics/**
locks:
  - workflow-contract
quality_gates:
  - git diff --check
live_infrastructure: prohibited
```

Tasks:

- Map the existing Multipass Docker install and Swarm initialization sequence
  into LXC-native requirements.
- Define LXD and Incus command adaptation rules without implementing shell
  details in application code.
- Record idempotency expectations for install, manager init, token retrieval,
  worker join, and verification.
- Identify ADR updates if implementation needs any security contract beyond
  the current Docker-in-container profile.

Done:

- A report states which Multipass behaviors are copied, adapted, or rejected.
- No documentation claims live Docker-in-LXC success before evidence exists.

### Slice 02 - Domain And Application Contracts

```yaml
slice: 02
name: lxc-docker-domain-application-contracts
status: READY
owner: Senior Python Automation Developer
allowed_files:
  - src/tiny_swarm_world/domain/**
  - src/tiny_swarm_world/application/ports/**
  - src/tiny_swarm_world/application/services/platform/**
  - tests/domain/**
  - tests/application/**
locks:
  - platform-domain-contracts
quality_gates:
  - PYTHONPATH=src python -m unittest discover tests/domain tests/application
  - python3 tools/quality_gate.py lint
live_infrastructure: prohibited
```

Tasks:

- Add provider-neutral value objects/results for container Docker readiness,
  Docker install outcome, Swarm manager state, worker join state, and
  verification evidence summaries if existing types are insufficient.
- Add or extend application ports for container command execution and
  container network identity lookup.
- Keep application services independent from LXD/Incus concrete adapters.
- Add tests for already-installed Docker, missing Docker, failed install,
  already-active manager, fresh manager init, already-joined worker, and failed
  worker join.

Done:

- Domain imports remain infrastructure-free.
- Application services can be tested entirely with fakes.

### Slice 03 - LXD/Incus Docker Install Adapter

```yaml
slice: 03
name: lxc-docker-install-adapter
status: READY
owner: Senior DevOps Engineer
allowed_files:
  - src/tiny_swarm_world/infrastructure/adapters/**
  - src/tiny_swarm_world/infrastructure/composition.py
  - infra/config/docker/**
  - tests/infrastructure/**
locks:
  - lxc-provider-adapters
  - docker-command-config
quality_gates:
  - PYTHONPATH=src python -m unittest discover tests/infrastructure
  - python3 tools/quality_gate.py lint
live_infrastructure: prohibited
```

Tasks:

- Implement the concrete LXD/Incus exec adapter for Docker install commands.
- Prefer structured command templates or existing YAML command helpers over
  ad hoc string construction.
- Keep the official Docker apt repository install path aligned with current
  Docker documentation and the existing Multipass baseline.
- Ensure command evidence is summarized and redacted before leaving the
  infrastructure boundary.
- Add deterministic tests that assert backend command prefix, node targeting,
  timeout behavior, and redaction.

Done:

- Tests prove `lxc` and `incus` command variants are selected through backend
  configuration, not hard-coded application branching.
- No raw command output is persisted as verification evidence.

### Slice 04 - LXC Docker Install Application Workflow

```yaml
slice: 04
name: lxc-docker-install-workflow
status: READY
owner: Senior Python Automation Developer
allowed_files:
  - src/tiny_swarm_world/application/services/platform/**
  - src/tiny_swarm_world/infrastructure/composition.py
  - tests/application/**
  - tests/infrastructure/**
locks:
  - platform-init-workflow
quality_gates:
  - PYTHONPATH=src python -m unittest discover tests/application tests/infrastructure
  - python3 tools/quality_gate.py typecheck
live_infrastructure: prohibited
```

Tasks:

- Wire Docker install after LXC node creation and before Swarm
  initialization.
- Preserve apply-then-verify semantics: do not continue when install evidence
  is missing, failed, or non-verified.
- Support re-run behavior for already-installed Docker.
- Report blocked, failed-to-apply, and failed-to-verify states using existing
  setup/platform vocabulary.

Done:

- `platform init` and `setup run` can reach a mocked verified Docker install
  phase for all configured LXC nodes.
- Failure on any required node stops later Swarm work.

### Slice 05 - LXC Docker Swarm Init And Join

```yaml
slice: 05
name: lxc-docker-swarm-init-join
status: READY
owner: Senior DevOps Engineer
allowed_files:
  - src/tiny_swarm_world/application/services/platform/**
  - src/tiny_swarm_world/infrastructure/adapters/**
  - src/tiny_swarm_world/infrastructure/composition.py
  - infra/config/docker/**
  - tests/application/**
  - tests/infrastructure/**
locks:
  - swarm-bootstrap
  - lxc-provider-adapters
quality_gates:
  - PYTHONPATH=src python -m unittest discover tests/application tests/infrastructure
  - python3 tools/quality_gate.py typecheck
live_infrastructure: prohibited
```

Tasks:

- Initialize the manager inside `swarm-manager` when it is not already part of
  the target Swarm.
- Read the manager advertise address through provider/container network
  identity lookup and keep the concrete IP out of committed files and trusted
  evidence.
- Retrieve worker join token only in-memory.
- Join `swarm-worker-1` and `swarm-worker-2` idempotently.
- Verify final Swarm state by manager and worker membership.

Done:

- Tests prove tokens are not stored in evidence, logs, reports, or thrown
  exceptions.
- Re-runs handle already-initialized manager and already-joined workers.

### Slice 06 - Setup And Platform Integration

```yaml
slice: 06
name: setup-platform-integration
status: READY
owner: Senior System Architect
allowed_files:
  - src/tiny_swarm_world/application/services/setup/**
  - src/tiny_swarm_world/application/services/platform/**
  - src/tiny_swarm_world/infrastructure/composition.py
  - src/tiny_swarm_world/__main__.py
  - tests/application/**
  - tests/infrastructure/**
locks:
  - setup-run-phases
  - composition-root
quality_gates:
  - PYTHONPATH=src python -m unittest discover tests/application tests/infrastructure
  - python3 tools/quality_gate.py test
live_infrastructure: prohibited
```

Tasks:

- Replace the default LXC `platform reconcile` blocker with the new
  provider-native Docker install and Swarm bootstrap path where appropriate.
- Ensure direct `platform init --live` and setup-driven platform init use the
  same implementation path.
- Keep Artifacts and Deployment blocked until their own provider-native
  contracts are implemented.
- Keep CLI changes thin and composition-owned.

Done:

- A mocked full Platform phase reaches verified LXC nodes, Docker installed,
  and Swarm initialized.
- The setup phase summary distinguishes Platform success from later
  Artifacts/Deployment blockers.

### Slice 07 - Operator Documentation And Architecture Sync

```yaml
slice: 07
name: docs-architecture-sync
status: READY
owner: Senior Documentation Engineer
allowed_files:
  - README.md
  - documentation/**
  - OPERATIONAL_READINESS_CHECKLIST.md
locks:
  - documentation
quality_gates:
  - git diff --check
live_infrastructure: prohibited
```

Tasks:

- Update setup documentation to state that default LXC-native Platform now
  installs Docker and initializes Swarm only after implementation evidence
  exists.
- Update EPIC, arc42 runtime/deployment, and ADR index language so planned,
  implemented, blocked, and live-verified states remain distinct.
- Add recovery notes for common LXD/Incus Docker-in-container failures without
  documenting host mutation as automatic behavior.

Done:

- Documentation is aligned with source and tests.
- No service stack deployment success is claimed by Platform-only evidence.

### Slice 08 - Quality And Optional Live Smoke Evidence

```yaml
slice: 08
name: quality-live-smoke-boundary
status: READY
owner: Senior Tester
allowed_files:
  - tests/**
  - tools/**
  - documentation/workflow/**
  - documentation/system/**
locks:
  - quality-gates
  - live-smoke-boundary
quality_gates:
  - python3 tools/quality_gate.py quality
live_infrastructure: optional_after_explicit_user_approval
```

Tasks:

- Run the full repository quality gate.
- Define the optional live-smoke command sequence and evidence capture
  checklist, but do not run it without explicit user approval.
- If live smoke is approved, validate on the current target separately from
  static tests and store only redacted local evidence under
  `.tiny-swarm-world/evidence/live-installation/<run-id>/`.
- Classify live smoke as native Linux LXD, native Linux Incus, WSL2 LXD, or
  WSL2 Incus. Do not generalize one target to another.

Done:

- Mocked/static quality gate passes.
- Optional live-smoke result, if executed, is clearly separated from
  repository quality evidence.

## Acceptance Criteria

- LXC-native Docker install is implemented without using Multipass commands
  on the default path.
- Multipass remains available only behind explicit `multipass_legacy`.
- Docker install and Swarm bootstrap run inside the managed LXC containers,
  not on the host.
- The implementation supports both LXD and Incus backend selection.
- The implementation is idempotent for already-created nodes, already
  installed Docker, already-initialized manager, and already-joined workers.
- Platform workflow continuation remains apply-then-verify.
- Artifacts and Deployment remain separate boundaries and are not presented as
  complete by this Platform workflow.
- Default tests do not run live LXD, Incus, LXC, Docker, Swarm, compose,
  Portainer, Nexus, Jenkins, RabbitMQ, SonarQube, or service bootstrap
  commands.
- Raw command payloads, tokens, secrets, environment payloads, local IPs, and
  host-specific paths are not persisted in committed files or trusted
  evidence.
- Documentation states only what is implemented and verified.

## Stop Conditions

Stop and report before continuing when:

- implementation would require running live LXD, Incus, LXC, Docker, Swarm, or
  stack commands without explicit user approval;
- Docker-in-container requires privileged containers or broad host mounts
  beyond the accepted profile baseline;
- host package installation, daemon repair, group repair, bridge repair, or
  firewall mutation becomes necessary;
- LXD and Incus behavior cannot share a provider-neutral application contract;
- application or domain code would need to import infrastructure adapters;
- Swarm join tokens or raw command output would be persisted;
- documentation would claim live success from mocked tests or static review;
- the implementation would touch Artifacts or Deployment live behavior beyond
  maintaining their blocked contracts.

## Verification Strategy

Default verification:

- targeted unit tests for domain/application contracts;
- infrastructure adapter tests with fake command runners;
- composition tests with fake providers;
- architecture/lint/typecheck through repository quality gates;
- docs whitespace checks.

Optional live verification:

- run only after explicit user approval;
- use the existing `--live` and interactive confirmation contract;
- collect redacted local evidence only;
- report target-specific results for WSL2 LXD/Incus or native Linux
  LXD/Incus.
