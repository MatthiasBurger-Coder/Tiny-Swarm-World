# EPIC: System Unification

## Status

```text
ACTIVE_BASELINE
```

## Requirement Source

This EPIC is created by workflow Slice 01 from these repository-visible
sources:

- user request: create a workflow with subagents to check system completeness
  and unify the system;
- accepted responsibility direction in
  `documentation/architecture/adr-separate-platform-artifacts-deployment.adoc`;
- current arc42 architecture documentation;
- active workflow `documentation/workflow/workflow.md`.

No prior `documentation/epics/` source existed at baseline creation time.

## EPIC Extensions

The autonomous runnable setup baseline extends this EPIC:

- `documentation/epics/autonomous-runnable-setup.md`

The extension defines what "runnable setup" must mean before implementation
slices wire live Platform, Artifacts, and Deployment behavior. It does not
replace this system-unification EPIC and does not claim that autonomous setup
is already implemented.

## Intent

Tiny Swarm World remains one Linux/WSL-only Python automation system for a
Docker Swarm-first local infrastructure environment. The system is unified by
in-process responsibility boundaries, not by extracting new services:

- Platform;
- Artifacts;
- Deployment;
- Shared;
- Console/status UI.

The EPIC completes and verifies those boundaries while preserving the existing
hexagonal architecture.

## Mandatory EPIC Question

Does the implementation still match the intended EPIC?

```text
PARTIALLY, WITH DOCUMENTED BLOCKERS
```

Implemented or substantially present:

- Python package split into `domain`, `application`, and `infrastructure`.
- Platform workflow entry points and composition root.
- Command safety metadata, workflow allow-list checks, and destructive command
  safeguards.
- Desired/observed inventory and verification evidence concepts.
- Host-neutral desired inventory baseline under `infra/config/inventory`.
- Verify-after-apply workflow foundation.
- Console/status UI adapters.
- Explicit blocked workflow contracts for Artifact and Deployment commands.
- Canonical `setup run` workflow-level orchestration with live-consent refusal
  before setup service construction.
- Setup terminal status and recovery output that preserves refused, blocked,
  resource-gated, failed-to-apply, failed-to-verify, failed, and completed
  states.
- Static live-operation surface catalog for guarded, transitional, deprecated,
  legacy, and supported asset surfaces.
- Documentation that identifies the Platform, Artifacts, Deployment, and
  Shared direction.

Planned or incomplete:

- Artifacts and Deployment are composition boundaries with workflow contracts,
  but live Nexus, registry, Portainer, and observed-state behavior remains
  blocked.
- Mutating Platform workflow steps do not yet expose concrete verification
  contracts.
- Command catalog entries mostly declare manual verification rather than
  command-backed verification.
- Legacy direct scripts remain live-operation surfaces outside the CLI consent
  guard and are classified for static review.
- The autonomous runnable setup requirement baseline exists as an EPIC
  extension, and the fail-closed setup orchestrator exists, but full live
  runnable setup remains incomplete until command-backed platform
  verification, artifact publication, registry checks, first-time stack
  bootstrap, and service readiness evidence are wired.

## Scope

In scope:

- EPIC traceability and completeness criteria.
- ADR and arc42 alignment.
- Responsibility-boundary tests.
- Command catalog, inventory, and evidence unification.
- Platform verify-after-apply contracts.
- Artifact and Deployment workflow contracts.
- Console/status UI consistency.
- Static classification of legacy live-operation scripts.
- README, architecture, deployment, system, user-guide, workflow, and report
  synchronization.

Out of scope:

- Live Multipass, Docker Swarm, compose, netplan, socat, Portainer, Nexus,
  Jenkins, RabbitMQ, SonarQube, or Swagger/NGINX execution.
- Kubernetes-first architecture.
- Browser React frontend work.
- Spring Boot or Java-driven architecture.
- Microservice extraction.
- Big-bang file moves.
- Weakening `.importlinter`, architecture tests, or `QUALITY.md`.

## Acceptance Criteria

- The EPIC and workflow baseline classify repository areas as implemented,
  planned, blocked, transitional, legacy, or out of scope.
- Platform, Artifacts, Deployment, Shared, and Console/status UI boundaries are
  backed by tests or explicitly documented blockers.
- Artifact/deployment workflow wiring is not documented as implemented until it
  is executable and test-backed.
- Verify-after-apply is preserved as fail-closed behavior.
- Command verification and evidence redaction prevent raw command payloads,
  secrets, and credential material from becoming trusted evidence.
- Desired inventory uses committed, host-neutral configuration.
- Legacy live-operation scripts are classified by static inspection only.
- All verification uses repository quality gates and mocked or static checks by
  default.
- Autonomous setup requirements preserve the Platform, Artifacts, Deployment,
  Shared, and Console/status UI ownership model. Documentation may describe
  the implemented fail-closed `setup run` orchestrator, but must not present
  full live runnable setup as implemented until later verification evidence
  proves it.

## Non-Functional Requirements

- Linux/WSL-only operation remains the baseline.
- Documentation examples use POSIX paths and shell commands.
- Tests do not execute live infrastructure commands.
- `src/tiny_swarm_world/infrastructure/composition.py` remains the concrete
  wiring root.
- `src/tiny_swarm_world/__main__.py` remains thin.
- Local runtime artifacts stay under ignored local-state paths.

## Stop Conditions

Stop execution when:

- implementation would require live infrastructure commands;
- responsibility ownership would require guessing;
- application code would import infrastructure adapters;
- raw command output, secrets, or credential material would be persisted as
  trusted verification evidence;
- documentation would present planned behavior as implemented;
- a change would weaken architecture or quality gates.
