# Agent Split Plan

Status: archival planning baseline. Multipass path references are superseded by
`documentation/architecture/adr-retire-multipass-legacy-provider.adoc` and must
not be used as current routing or implementation targets.

This plan breaks the follow-up work into specialized Codex agents. Each task is
copy-paste-ready and should be run only after the architecture decision is
accepted.

## General Rules for All Agents

- Work in WSL/Linux from the repository root.
- Read `AGENTS.md`, `src/tiny_swarm_world/AGENTS.md`, `infra/AGENTS.md`,
  `.importlinter`, `README.md`, and `tools/quality_gate.py` before changing
  files.
- Inspect `git status --short` before edits.
- Do not overwrite unrelated user changes.
- Do not run live infrastructure commands:
  - `multipass`
  - Docker Swarm operations
  - live docker compose deployment
  - netplan changes
  - socat forwarding
  - Nexus bootstrap against a real service
  - Portainer bootstrap against a real service
  - Jenkins/RabbitMQ/SonarQube live setup
- Preserve hexagonal imports.
- Run only safe unit, static, architecture, and quality-gate checks.

## Agent 1: Architecture Boundary Analyst

Role:

- Principal software architect and documentation analyst.

Scope:

- Analyze and document current responsibility boundaries.

Allowed files:

- `documentation/architecture`
- `documentation/arc42` only for cross references after approval

Forbidden files:

- production source files under `src`
- shell scripts under `infra`
- infra config
- tests

Required reading:

- `AGENTS.md`
- `src/tiny_swarm_world/AGENTS.md`
- `infra/AGENTS.md`
- `.importlinter`
- `README.md`
- `tools/quality_gate.py`
- `documentation/architecture/responsibility-separation-analysis.md`
- `documentation/architecture/adr-separate-platform-artifacts-deployment.adoc`

Exact task steps:

1. Inspect `git status --short`.
2. Re-read current architecture docs.
3. Verify that Platform, Artifacts, Deployment, and Shared responsibility
   definitions still match the code.
4. Add or update documentation findings only.
5. Do not modify production code, scripts, or tests.
6. Run safe architecture checks.

Output artifacts:

- Updated responsibility classification.
- Updated mixed-boundary findings.
- Open questions and risk notes.

Tests and quality gates:

- `python3 tools/quality_gate.py arch-lint`
- `python3 tools/quality_gate.py arch-tests`

Stop-and-report conditions:

- Any required source-code change appears necessary.
- Current docs contradict `AGENTS.md`.
- A responsibility cannot be classified with high confidence.

Acceptance criteria:

- Documentation is specific to real files.
- No production behavior changes.
- Quality gate result is recorded.

## Agent 2: Platform Provisioning Refactoring Agent

Role:

- Docker Swarm, Multipass, WSL/Linux networking, and platform provisioning
  specialist.

Scope:

- historical Multipass VM lifecycle (superseded).
- VM discovery.
- netplan.
- socat.
- Docker daemon installation.
- Docker Swarm init/join.

Allowed files after architecture approval:

- former `src/tiny_swarm_world/domain/multipass` (superseded)
- `src/tiny_swarm_world/domain/network`
- former `src/tiny_swarm_world/application/services/multipass` (superseded)
- `src/tiny_swarm_world/application/services/network`
- `src/tiny_swarm_world/application/services/vm`
- platform-related ports
- platform-related infrastructure adapters
- former `infra/config/multipass` (superseded)
- `infra/config/docker` for daemon install and Swarm commands only
- `infra/config/network`
- `infra/config/vm`
- related tests and docs

Forbidden files:

- `infra/compose`
- service stack deployment logic
- Portainer stack upload logic
- Nexus repository bootstrap except as a documented platform dependency
- artifact build/push scripts

Required reading:

- all general required files
- `documentation/architecture/responsibility-separation-analysis.md`
- `documentation/architecture/adr-separate-platform-artifacts-deployment.adoc`
- platform-related tests under `tests/application/services/multipass`,
  `tests/application/services/network`, and `tests/domain/network`

Exact task steps:

1. Inspect `git status --short`.
2. Map current platform files to the target boundary.
3. Propose a small no-behavior-change slice before moving files.
4. If approved, make only targeted platform changes.
5. Keep application services dependent on ports, not infrastructure adapters.
6. Add or update platform unit tests with mocked command workflow.
7. Do not execute live platform commands.

Output artifacts:

- Platform boundary change summary.
- Updated tests or docs.
- List of files intentionally left untouched.

Tests and quality gates:

- `python3 tools/quality_gate.py arch-lint`
- `python3 tools/quality_gate.py arch-tests`
- `python3 tools/quality_gate.py test`
- `python3 tools/quality_gate.py quality` when production code changes

Stop-and-report conditions:

- A change would run or require live Multipass, Docker Swarm, netplan, or socat.
- A required refactor touches deployment or artifact ownership.
- Import-linter would be violated.

Acceptance criteria:

- Platform ownership is clearer.
- No service deployment or artifact publishing behavior changes.
- Safe tests pass or blockers are documented.

## Agent 3: Artifact Registry / Build Publishing Agent

Role:

- Artifact publishing, Docker image build, Nexus registry, and Maven repository
  specialist.

Scope:

- Dockerfile generation.
- Image build/tag/push concepts.
- Nexus Docker registry.
- Nexus Maven repository.
- Artifact publishing workflows.

Allowed files after architecture approval:

- `src/tiny_swarm_world/domain/nexus`
- `src/tiny_swarm_world/application/services/nexus`
- `src/tiny_swarm_world/application/ports/clients/port_nexus_client.py`
- artifact-related ports
- `src/tiny_swarm_world/infrastructure/adapters/clients/nexus_http_client.py`
- artifact-related adapters
- artifact-related docs and tests

Forbidden files:

- Multipass VM lifecycle.
- netplan.
- socat.
- Docker Swarm init/join.
- Portainer stack deployment except as a consumer dependency.
- Stack upload scripts except for documenting required artifact inputs.

Required reading:

- all general required files
- `documentation/architecture/responsibility-separation-analysis.md`
- `documentation/architecture/adr-separate-platform-artifacts-deployment.adoc`
- `tests/application/services/nexus/test_bootstrap_nexus.py`

Exact task steps:

1. Inspect `git status --short`.
2. Separate Nexus repository configuration from Nexus stack deployment in the
   design.
3. Identify whether `EnsureNexusStack` should move to deployment or remain as a
   compatibility facade.
4. Make only the approved artifact slice.
5. Ensure no Docker build, login, push, or Nexus live bootstrap is executed.
6. Add unit tests using mocks for Nexus and container runtime ports.

Output artifacts:

- Artifact boundary change summary.
- Nexus responsibility notes.
- Updated artifact tests or docs.

Tests and quality gates:

- `python3 tools/quality_gate.py arch-lint`
- `python3 tools/quality_gate.py arch-tests`
- `python3 tools/quality_gate.py test`
- `python3 tools/quality_gate.py quality` when production code changes

Stop-and-report conditions:

- Work requires a real Nexus, Docker registry, or image push.
- Work requires changing platform provisioning.
- Work requires changing Portainer stack deployment beyond approved dependency
  boundaries.

Acceptance criteria:

- Artifact publishing and Nexus repository behavior are separated from stack
  deployment.
- Tests use ports/mocks.
- No live registry action is run.

## Agent 4: Stack Deployment Agent

Role:

- Portainer, compose, and service stack deployment specialist.

Scope:

- Compose files.
- Stack definitions.
- Portainer stack upload.
- Service deployment lifecycle.
- Jenkins, RabbitMQ, SonarQube, Swagger/NGINX, Nexus, and Portainer stack
  metadata.

Allowed files after architecture approval:

- `src/tiny_swarm_world/domain/deployment`
- `src/tiny_swarm_world/application/ports/clients/port_portainer_client.py`
- `src/tiny_swarm_world/application/ports/repositories/port_compose_file_repository.py`
- deployment-related application services
- `src/tiny_swarm_world/infrastructure/adapters/clients/portainer_http_client.py`
- `src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py`
- `infra/compose`
- `infra/config/compose`
- deployment-related tests and docs

Forbidden files:

- Historical Multipass VM creation is superseded by the retired-provider ADR.
- Docker daemon installation.
- Swarm initialization.
- netplan and socat.
- Nexus repository internals except endpoint/configuration dependency data.
- artifact image build/push implementation.

Required reading:

- all general required files
- `documentation/architecture/responsibility-separation-analysis.md`
- `documentation/architecture/adr-separate-platform-artifacts-deployment.adoc`
- `tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py`

Exact task steps:

1. Inspect `git status --short`.
2. Identify stack deployment behavior currently hidden in Nexus or scripts.
3. Prepare a small no-behavior-change deployment boundary slice.
4. If approved, migrate stack ownership or add compatibility facades.
5. Keep destructive reset behavior explicit and documented.
6. Add static or unit tests for compose and Portainer behavior.

Output artifacts:

- Deployment boundary change summary.
- Updated tests or docs.
- Explicit note on any live command that was not run.

Tests and quality gates:

- `python3 tools/quality_gate.py arch-lint`
- `python3 tools/quality_gate.py arch-tests`
- `python3 tools/quality_gate.py test`
- `python3 tools/quality_gate.py quality` when production code changes

Stop-and-report conditions:

- Work would deploy stacks against live Portainer or Docker Swarm.
- Work requires platform provisioning changes.
- Work requires artifact publishing changes beyond declared dependency inputs.

Acceptance criteria:

- Deployment ownership is clearer.
- No live stack deploy is executed.
- Tests verify behavior through mocks or static checks.

## Agent 5: Composition / CLI Workflow Agent

Role:

- Application composition, CLI workflow, and use-case orchestration specialist.

Scope:

- `src/tiny_swarm_world/__main__.py`
- `src/tiny_swarm_world/infrastructure/composition.py`
- workflow orchestration boundaries
- CLI/service workflow naming

Allowed files after architecture approval:

- `src/tiny_swarm_world/__main__.py`
- `src/tiny_swarm_world/infrastructure/composition.py`
- workflow orchestration objects
- CLI-facing documentation
- tests for composition and entry point behavior

Forbidden files:

- live infrastructure scripts
- broad business logic moves not already prepared by other agents
- direct command YAML changes unless only references are updated after approved
  path moves

Required reading:

- all general required files
- `documentation/architecture/adr-separate-platform-artifacts-deployment.adoc`
- current `src/tiny_swarm_world/infrastructure/composition.py`
- current `src/tiny_swarm_world/__main__.py`

Exact task steps:

1. Inspect `git status --short`.
2. Confirm which platform, artifact, and deployment use cases exist.
3. Propose boundary-specific builder functions or workflow names.
4. Keep `__main__.py` thin.
5. Keep concrete adapter construction in `composition.py`.
6. Add tests that do not execute live infrastructure.

Output artifacts:

- Composition and CLI workflow summary.
- Updated entry point or composition tests.
- Documentation of supported workflows.

Tests and quality gates:

- `python3 tools/quality_gate.py arch-lint`
- `python3 tools/quality_gate.py arch-tests`
- `python3 tools/quality_gate.py test`
- `python3 tools/quality_gate.py quality` when production code changes

Stop-and-report conditions:

- A workflow change would alter public user behavior without approval.
- A change would require live infrastructure execution.
- Composition would need application-to-infrastructure imports.

Acceptance criteria:

- Entry point remains thin.
- Composition root reflects separated use cases.
- Hexagonal import rules still pass.

## Agent 6: Test and Quality Gate Agent

Role:

- Architecture test, import-linter, and quality-gate specialist.

Scope:

- Unit tests.
- Architecture tests.
- Import-linter contracts.
- Quality gate documentation.
- Mocks for external command execution.

Allowed files:

- `tests`
- `.importlinter`
- `tools/quality_gate.py` only if needed and justified
- quality gate documentation
- `documentation/architecture`

Forbidden files:

- live Multipass, Docker, Portainer, Nexus, netplan, or socat commands
- production behavior changes only to satisfy tests
- production source unless a test exposes a real bug and the fix is approved

Required reading:

- all general required files
- `tests/architecture/test_hexagonal_imports.py`
- `documentation/architecture/adr-separate-platform-artifacts-deployment.adoc`
- `documentation/user_guide/troubleshooting.adoc`

Exact task steps:

1. Inspect `git status --short`.
2. Review the current quality gate commands.
3. Add or adjust architecture tests for responsibility boundaries.
4. Keep tests static or mock-based.
5. Do not install global tooling without permission.
6. Record exact missing dependency errors when tools are unavailable.

Output artifacts:

- Updated architecture tests.
- Updated quality gate docs if needed.
- Exact command output summary.

Tests and quality gates:

- `python3 tools/quality_gate.py arch-lint`
- `python3 tools/quality_gate.py arch-tests`
- `python3 tools/quality_gate.py quality` if safe and no live commands are
  triggered

Stop-and-report conditions:

- A quality command would execute live infrastructure.
- A missing dependency requires global installation.
- Existing source behavior must be changed to make tests pass.

Acceptance criteria:

- Quality gate remains safe for local development.
- Architecture tests protect the split without false precision.
- Missing tool blockers are clearly documented.

## Agent 7: Documentation / arc42 Agent

Role:

- Architecture documentation, arc42, deployment guide, and user guide specialist.

Scope:

- Architecture docs.
- Runtime view.
- Deployment view.
- Concepts.
- Risks/debt.
- Glossary.

Allowed files:

- `README.md`
- `documentation/arc42`
- `documentation/system`
- `documentation/deployment`
- `documentation/user_guide`
- `documentation/architecture`
- new architecture decision records

Forbidden files:

- production code
- tests
- shell scripts
- infrastructure configs

Required reading:

- all general required files
- `documentation/architecture/responsibility-separation-analysis.md`
- `documentation/architecture/adr-separate-platform-artifacts-deployment.adoc`
- current arc42 files
- current user guide files

Exact task steps:

1. Inspect `git status --short`.
2. Align docs with Platform, Artifacts, Deployment, and Shared naming.
3. Mark live infrastructure commands clearly.
4. Do not reintroduce Java/Maven project structure unless product scope
   explicitly changes.
5. Do not change scripts or production code.
6. Run safe architecture checks.

Output artifacts:

- Updated README/arc42/user guide sections.
- Updated risk/debt and glossary entries.
- Documentation-only change summary.

Tests and quality gates:

- `python3 tools/quality_gate.py arch-lint`
- `python3 tools/quality_gate.py arch-tests`

Stop-and-report conditions:

- Documentation would require production behavior changes.
- Existing docs conflict with source and the correct behavior is unclear.
- A live command would be needed to verify a statement.

Acceptance criteria:

- Docs describe the target boundaries consistently.
- Live operations are marked as live.
- No production files are modified.
