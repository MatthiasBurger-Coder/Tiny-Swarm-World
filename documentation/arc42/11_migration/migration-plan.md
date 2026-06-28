# Migration Plan

Status: archival planning baseline. Multipass path references are superseded by
`documentation/arc42/09_decisions/adr-retire-multipass-legacy-provider.adoc` and must
not be used as current routing or implementation targets.

This plan separates Platform, Artifacts, Deployment, and Shared responsibilities
without a big-bang refactoring. Each slice should keep the working tree small
and should avoid live infrastructure commands.

## Global Rules

- Do not run live `multipass`, Docker Swarm, netplan, socat, Portainer, Nexus,
  Jenkins, Apache Pulsar, SonarQube, or compose deployment commands during migration
  work unless explicitly requested.
- Preserve the current hexagonal rules:
  - domain does not import application
  - domain does not import infrastructure
  - application does not import infrastructure
  - infrastructure implements ports
  - `composition.py` remains the wiring root
  - `__main__.py` remains thin
- Keep behavior changes explicit. Most slices below should be no-behavior-change
  moves, aliases, tests, or documentation updates.
- Use WSL/Linux commands from the repository root.

## Slice 1: Documentation and Boundary Decision

Goal:

- Record current responsibility ownership, conflicts, ADR, migration plan, and
  agent split.

Affected files/directories:

- `documentation/arc42/05_analysis`
- `documentation/arc42/11_migration`
- `documentation/process/agent-plans`
- `documentation/process/agent-tasks`

Files explicitly forbidden:

- `src`
- `infra`
- `tests`
- `.importlinter`
- `tools/quality_gate.py`

Expected behavior change:

- None.

Expected no-behavior-change areas:

- All production code, scripts, configs, and tests.

Tests to add/update:

- None.

Quality gate command:

- `python3 tools/quality_gate.py arch-lint`
- `python3 tools/quality_gate.py arch-tests`

Rollback strategy:

- Remove the newly added analysis, migration, agent-plan, and agent-task files
  from their current documentation folders.

Acceptance criteria:

- Required architecture files exist.
- Responsibility classification is explicit.
- Agent tasks are copy-paste-ready.
- Architecture checks pass or blockers are documented.

## Slice 2: Architecture Test Expansion

Goal:

- Add tests that detect responsibility-boundary regressions without moving
  production files.

Affected files/directories:

- `tests/architecture`
- `.importlinter` only if needed and justified
- `documentation/arc42/05_analysis` if findings need updates

Files explicitly forbidden:

- former `src/tiny_swarm_world/application/services/multipass` (superseded)
- `src/tiny_swarm_world/application/services/network`
- `src/tiny_swarm_world/application/services/vm`
- `src/tiny_swarm_world/application/services/nexus`
- `infra`

Expected behavior change:

- None.

Expected no-behavior-change areas:

- Runtime provisioning and deployment behavior.

Tests to add/update:

- Static import or AST tests that mark the current boundaries.
- Tests should allow current known transitional conflicts only if documented.

Quality gate command:

- `python3 tools/quality_gate.py arch-lint`
- `python3 tools/quality_gate.py arch-tests`
- `python3 tools/quality_gate.py test` if only static/unit tests are touched.

Rollback strategy:

- Revert the new architecture tests and any documentation update in the same
  slice.

Acceptance criteria:

- Existing hexagonal checks still pass.
- New checks document current known exceptions rather than breaking all work.
- No live infrastructure command is executed.

## Slice 3: Platform Boundary Preparation

Goal:

- Prepare a platform namespace and classify VM, network, Docker install, and
  Swarm behavior without changing runtime semantics.

Affected files/directories:

- former `src/tiny_swarm_world/domain/multipass` (superseded)
- `src/tiny_swarm_world/domain/network`
- former `src/tiny_swarm_world/application/services/multipass` (superseded)
- `src/tiny_swarm_world/application/services/network`
- `src/tiny_swarm_world/application/services/vm`
- platform-related ports and adapters
- platform-related tests
- platform sections in `documentation/arc42/05_analysis`

Files explicitly forbidden:

- `infra/config/compose`
- Nexus repository bootstrap logic
- Portainer stack upload logic

Expected behavior change:

- None unless an existing platform bug is fixed and documented.

Expected no-behavior-change areas:

- Stack deployment and artifact publishing.

Tests to add/update:

- Unit tests for platform use cases with mocked command workflow.
- Static tests that platform application services do not depend on concrete
  infrastructure adapters.

Quality gate command:

- `python3 tools/quality_gate.py quality`

Rollback strategy:

- Revert platform namespace changes and compatibility imports together.

Acceptance criteria:

- Platform services are easier to identify.
- Import-linter still passes.
- No deployment or artifact behavior changes are introduced.

## Slice 4: Deployment Boundary Preparation

Goal:

- Make compose, Portainer, and stack lifecycle ownership explicit.

Affected files/directories:

- `src/tiny_swarm_world/domain/deployment`
- `src/tiny_swarm_world/application/ports/clients/port_portainer_client.py`
- `src/tiny_swarm_world/application/ports/repositories/port_compose_file_repository.py`
- `src/tiny_swarm_world/infrastructure/adapters/clients/portainer_http_client.py`
- `src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py`
- `infra/config/compose`
- `infra/config/compose`
- deployment-related tests and docs

Files explicitly forbidden:

- Multipass VM lifecycle services
- Docker daemon installation services
- Swarm init/join services
- Nexus repository internals except endpoint configuration as dependency

Expected behavior change:

- None by default. Destructive reset behavior should only be isolated behind an
  explicit operation in a later approved slice.

Expected no-behavior-change areas:

- Platform provisioning and artifact registry configuration.

Tests to add/update:

- Unit tests for compose repository and Portainer client behavior.
- Static tests that deployment does not own Multipass/netplan behavior.

Quality gate command:

- `python3 tools/quality_gate.py quality`

Rollback strategy:

- Revert deployment namespace or script organization changes in one commit.

Acceptance criteria:

- Stack deployment behavior is no longer hidden under Nexus or platform naming.
- Live deployment commands remain opt-in and documented.

## Slice 5: Artifact Boundary Preparation

Goal:

- Separate Docker image build/push and Nexus repository configuration from
  stack deployment and platform provisioning.

Affected files/directories:

- `src/tiny_swarm_world/domain/nexus`
- `src/tiny_swarm_world/application/services/nexus`
- `src/tiny_swarm_world/application/ports/clients/port_nexus_client.py`
- `src/tiny_swarm_world/infrastructure/adapters/clients/nexus_http_client.py`
- artifact-related tests and docs

Files explicitly forbidden:

- Multipass VM lifecycle
- netplan
- Swarm init/join
- Portainer stack deployment except as a dependency port or precondition

Expected behavior change:

- None unless a Nexus bootstrap bug is fixed and documented.

Expected no-behavior-change areas:

- Platform provisioning and service stack rollout.

Tests to add/update:

- Unit tests for Nexus repository/user configuration.
- Tests that artifact services do not directly deploy stacks after the split.

Quality gate command:

- `python3 tools/quality_gate.py quality`

Rollback strategy:

- Revert artifact namespace changes and keep existing Nexus service paths.

Acceptance criteria:

- Artifact responsibilities are explicit.
- `EnsureNexusStack` migration is planned or completed as a deployment
  responsibility.
- No image push command runs during tests.

## Slice 6: Composition and CLI Boundary Split

Goal:

- Make the entry point and composition root expose separate workflows without
  embedding broad business logic in `__main__.py`.

Affected files/directories:

- `src/tiny_swarm_world/__main__.py`
- `src/tiny_swarm_world/infrastructure/composition.py`
- CLI-facing documentation
- workflow orchestration tests

Files explicitly forbidden:

- Live infrastructure scripts
- Broad service logic moves not already prepared by earlier slices

Expected behavior change:

- Only documented CLI command naming changes if explicitly approved.

Expected no-behavior-change areas:

- Underlying platform, artifact, and deployment use cases.

Tests to add/update:

- Tests for builder functions and thin entry point behavior.
- No tests that execute live infra.

Quality gate command:

- `python3 tools/quality_gate.py quality`

Rollback strategy:

- Revert composition and entry point changes.

Acceptance criteria:

- `__main__.py` remains thin.
- `composition.py` remains the only concrete wiring root.
- Boundary-specific builders are clear and tested.

## Slice 7: Infra Directory Reorganization

Goal:

- Gradually move infra assets from technology-based folders to responsibility
  folders with compatibility shims and documentation.

Affected files/directories:

- `infra/config`
- `infra/config/compose`
- `infra/utils.sh`
- documentation and tests that reference these paths

Files explicitly forbidden:

- Python production source unless path references must be updated in a small,
  reviewed slice.

Expected behavior change:

- None if compatibility shims are used.

Expected no-behavior-change areas:

- Actual VM, network, Docker, Swarm, Portainer, Nexus, and stack commands.

Tests to add/update:

- Static tests for expected paths.
- Unit tests for repositories that resolve compose or command YAML paths.

Quality gate command:

- `python3 tools/quality_gate.py quality`

Rollback strategy:

- Revert moved files and compatibility shims together.

Acceptance criteria:

- New path names express Platform, Artifacts, Deployment, and Shared.
- Existing documented commands still work or have explicit replacement commands.
- Live scripts still path-resolve from `${BASH_SOURCE[0]}`.

## Slice 8: Legacy Quarantine and Cleanup

Goal:

- Mark, quarantine, or remove transitional files only after ownership and
  replacement behavior are proven.

Affected files/directories:

- duplicate Portainer setup scripts
- duplicate or stale issue import files if explicitly approved

Files explicitly forbidden:

- Active platform, artifact, or deployment implementation files unless the
  cleanup depends on a reviewed replacement.

Expected behavior change:

- None for supported workflows. Unsupported legacy entry points may become
  explicitly deprecated.

Expected no-behavior-change areas:

- Canonical Python entry point and documented live scripts.

Tests to add/update:

- Documentation link checks or static tests for supported entry points.
- Tests proving no supported import references removed files.

Quality gate command:

- `python3 tools/quality_gate.py quality`

Rollback strategy:

- Restore quarantined files and deprecation notes.

Acceptance criteria:

- Supported workflows are documented.
- Broken or duplicate legacy scripts no longer look like first-class entry
  points.
- No live command is executed as part of cleanup validation.
