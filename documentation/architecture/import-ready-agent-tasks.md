# Import-Ready Agent Tasks

Status: archival planning baseline. Multipass path references are superseded by
`documentation/architecture/adr-retire-multipass-legacy-provider.adoc` and must
not be imported as current implementation tasks.

This file follows the repository's existing Markdown issue-import style and
does not depend on removed GitHub import staging artifacts.

## [Architecture][A-001] Document responsibility boundaries and open questions

- Labels: architecture, documentation, agent-task
- Severity: Medium
- Area: Architecture Boundary Analysis
- Finding ID: A-001

### Summary
Analyze and maintain the documented split between Platform, Artifacts,
Deployment, and Shared responsibilities.

### Evidence
- `documentation/architecture/responsibility-separation-analysis.md`
- `documentation/architecture/adr-separate-platform-artifacts-deployment.adoc`

### Recommended remediation
Keep responsibility classification and mixed-boundary findings current while
avoiding production-code changes.

### Acceptance criteria
- Current files are classified by responsibility.
- Mixed-boundary findings include owner, risk, and follow-up agent.
- `python3 tools/quality_gate.py arch-lint` and
  `python3 tools/quality_gate.py arch-tests` pass or blockers are recorded.

### Dependencies
- None

## [Platform][A-002] Prepare platform provisioning boundary

- Labels: architecture, platform, agent-task
- Severity: High
- Area: Platform Provisioning
- Finding ID: A-002

### Summary
Prepare the historical platform boundary. Multipass-specific evidence paths are
superseded; current implementation must use LXC-native provider ownership,
retained legacy command-template classification, network, guarded legacy
netplan handling, socat, Docker daemon installation, and Swarm init/join
behavior.

### Evidence
- former `src/tiny_swarm_world/application/services/multipass` (superseded)
- `src/tiny_swarm_world/application/services/network`
- `src/tiny_swarm_world/application/services/vm`
- former `infra/config/multipass` (superseded)
- `infra/config/docker`
- `infra/config/network`

### Recommended remediation
Create small no-behavior-change slices that make platform ownership explicit and
keep application services dependent on ports.

### Acceptance criteria
- Platform services and configs are clearly owned.
- No deployment or artifact behavior changes.
- No live infrastructure command is executed.
- Safe quality gates pass or blockers are documented.

### Dependencies
- A-001

## [Artifacts][A-003] Separate artifact registry and publishing responsibilities

- Labels: architecture, artifacts, nexus, agent-task
- Severity: High
- Area: Artifact Registry / Build Publishing
- Finding ID: A-003

### Summary
Separate Dockerfile generation, image build/tag/push, Nexus registry setup, and
Maven repository setup from platform provisioning and stack deployment.

### Evidence
- `src/tiny_swarm_world/application/services/nexus`
- `src/tiny_swarm_world/domain/nexus`
- `src/tiny_swarm_world/application/ports/clients/port_nexus_client.py`
- `src/tiny_swarm_world/infrastructure/adapters/clients/nexus_http_client.py`
- `infra/config/compose/**/Dockerfile`
- Python artifact workflow contracts

### Recommended remediation
Move artifact responsibilities behind artifact use cases and ports. Treat Nexus
stack deployment as a deployment precondition, not as repository configuration.

### Acceptance criteria
- Artifact and Nexus repository behavior is explicit.
- No Docker build/login/push is executed during tests.
- Safe quality gates pass or blockers are documented.

### Dependencies
- A-001

## [Deployment][A-004] Separate stack deployment responsibilities

- Labels: architecture, deployment, portainer, compose, agent-task
- Severity: High
- Area: Stack / Service Deployment
- Finding ID: A-004

### Summary
Separate compose stack definitions, Portainer stack upload, and service
deployment lifecycle from platform provisioning and artifact publishing.

### Evidence
- `src/tiny_swarm_world/domain/deployment`
- `src/tiny_swarm_world/application/ports/clients/port_portainer_client.py`
- `src/tiny_swarm_world/application/ports/repositories/port_compose_file_repository.py`
- `src/tiny_swarm_world/infrastructure/adapters/clients/portainer_http_client.py`
- `src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py`
- `infra/config/compose`
- image build contexts under `infra/config/compose`
- `infra/config/compose`
- Python deployment workflow contracts

### Recommended remediation
Make stack deployment ownership explicit and isolate destructive reset behavior
behind documented opt-in operations.

### Acceptance criteria
- Deployment files and APIs are clearly owned.
- No Multipass, netplan, or Swarm behavior is introduced into deployment.
- No live stack deployment is executed during tests.

### Dependencies
- A-001

## [Composition][A-005] Split composition and CLI workflow by responsibility

- Labels: architecture, cli, composition, agent-task
- Severity: Medium
- Area: Composition / CLI Workflow
- Finding ID: A-005

### Summary
Make `__main__.py` and `composition.py` reflect separated platform, artifact,
and deployment workflows while preserving a thin entry point.

### Evidence
- `src/tiny_swarm_world/__main__.py`
- `src/tiny_swarm_world/infrastructure/composition.py`

### Recommended remediation
Add or prepare boundary-specific builder functions and keep concrete adapter
wiring in the composition root.

### Acceptance criteria
- `__main__.py` remains thin.
- `composition.py` remains the wiring root.
- Hexagonal import rules still pass.

### Dependencies
- A-002
- A-003
- A-004

## [Quality][A-006] Protect responsibility split with architecture tests

- Labels: architecture, tests, quality-gate, agent-task
- Severity: High
- Area: Test and Quality Gate
- Finding ID: A-006

### Summary
Extend architecture tests and import rules to protect the responsibility split
without executing live infrastructure.

### Evidence
- `.importlinter`
- `tools/quality_gate.py`
- `tests/architecture/test_hexagonal_imports.py`

### Recommended remediation
Add conservative responsibility-boundary tests and document any missing tooling
or blockers exactly.

### Acceptance criteria
- Architecture tests protect the split.
- Quality gate remains safe.
- No live infra command is executed.

### Dependencies
- A-001

## [Docs][A-007] Align README, arc42, and user guides with target boundaries

- Labels: architecture, documentation, arc42, agent-task
- Severity: Medium
- Area: Documentation / arc42
- Finding ID: A-007

### Summary
Align project documentation with Platform, Artifacts, Deployment, and Shared
responsibility boundaries.

### Evidence
- `README.md`
- `documentation/arc42`
- `documentation/system`
- `documentation/deployment`
- `documentation/user_guide`
- `documentation/architecture`

### Recommended remediation
Update docs to describe workflows by responsibility and mark live operations
clearly.

### Acceptance criteria
- Docs use the target boundary names consistently.
- Java/Maven project structure is not reintroduced.
- No production code, tests, scripts, or infra configs are modified.

### Dependencies
- A-001
