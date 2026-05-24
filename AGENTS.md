# AGENTS.md

## Project Identity

Tiny Swarm World is a Linux/WSL-only local infrastructure automation project.
It provisions and operates a production-like Docker Swarm environment on
Multipass virtual machines and ships ready-to-use service stacks such as
Portainer, Nexus, Jenkins, RabbitMQ, SonarQube, and Swagger/NGINX.

The project is a Python automation codebase using a hexagonal architecture.
Do not reintroduce Java, Maven, or Spring Boot project structure unless a later
explicit task changes the product scope.

## Operating Assumptions

- Treat the runtime as WSL or Linux only.
- Use POSIX paths and shell commands in examples, scripts, tests, and docs.
- Do not add new Windows-specific behavior, PowerShell commands, or backslash
  path examples unless explicitly requested for legacy documentation cleanup.
- Existing Windows-oriented files are legacy compatibility surface. Do not
  expand them unless a task explicitly asks for that.
- Do not introduce external static-analysis CI configuration unless explicitly
  requested.

## Repository Map

- `src/tiny_swarm_world/domain`: core business concepts and rules.
- `src/tiny_swarm_world/application`: use cases, orchestration services, and ports.
- `src/tiny_swarm_world/application/ports`: interfaces for commands, repositories, file
  management, UI, and external clients.
- `src/tiny_swarm_world/infrastructure`: concrete adapters, dependency wiring, logging,
  YAML handling, command runners, UI adapters, and file management.
- `infra/config`: YAML command, VM, network, and compose stack configuration data.
- `infra/compose`: image build contexts and related Dockerfiles for stack services.
- `infra/prepare`: retired notes for former direct local-service preparation
  helpers; it must not contain executable setup entry points.
- `infra/swarm`: swarm setup and helper scripts.
- `tests`: unit tests organized by architecture layer.
- `documentation`: arc42, deployment, system, and user guide documentation.

## Architecture Rules

- Preserve the existing hexagonal architecture.
- Keep domain code independent from application and infrastructure concerns.
- Domain modules must not import command runners, file managers, HTTP clients,
  Docker clients, UI adapters, YAML parsers, logging setup, or dependency
  injection containers.
- Application services may orchestrate ports and domain objects, but should not
  embed low-level shell, filesystem, HTTP, curses, or Docker details directly.
- Application services must depend on ports, not concrete infrastructure
  adapters.
- Infrastructure adapters implement ports and contain technology-specific
  details.
- Keep standard runtime wiring in
  `src/tiny_swarm_world/infrastructure/composition.py`; do not move concrete
  adapter construction into application services.
- Entry-point code such as `src/tiny_swarm_world/__main__.py` should stay thin:
  compose dependencies, invoke application services, and report progress.
- Prefer small services with explicit dependencies over global lookups. Where
  the current container is used, keep registrations clear and local.

## Python Conventions

- Run Python code from the repository root with `PYTHONPATH=src` when needed.
- Use package imports in the existing style, for example
  `from tiny_swarm_world.application.services...` and
  `from tiny_swarm_world.infrastructure.adapters...`.
- Keep source comments, docstrings, and annotations in English.
- Keep code compatible with Python 3.12 unless a task explicitly changes the
  supported version.
- Use `asyncio` consistently for asynchronous command orchestration.
- Do not hide external command execution in constructors or import-time side
  effects.
- Prefer typed value objects and small domain classes for command, VM, network,
  deployment, and Nexus concepts.

## Configuration And YAML

- Treat files under `infra/config` as part of the product behavior, not as
  throwaway examples.
- Use structured YAML APIs or existing YAML adapter helpers instead of ad hoc
  string manipulation.
- Keep command templates readable and deterministic.
- Avoid embedding host-specific absolute paths, user names, IP addresses, or
  secrets in committed configuration.
- Preserve service stack boundaries under `infra/config/compose` and
  `infra/compose`.

## External System Safety

Many project commands can create VMs, change networking, install Docker, or
deploy stacks. Do not run these unless the user explicitly asks for live
infrastructure changes:

- `multipass`
- `docker swarm`
- compose deployments
- netplan changes
- `socat` port forwarding
- Nexus, Jenkins, Portainer, RabbitMQ, or SonarQube bootstrap scripts

For normal development, prefer unit tests with mocks and targeted static
inspection.

## Testing

- Preferred quality gate from the repository root:
  `python3 tools/quality_gate.py quality`
- During development, run the nearest relevant sub-gate first:
  `python3 tools/quality_gate.py lint`,
  `python3 tools/quality_gate.py typecheck`, or
  `python3 tools/quality_gate.py test`
- For targeted changes, run the nearest relevant test file, for example:
  `PYTHONPATH=src python -m unittest tests.infrastructure.adapters.ui.test_linux_ui`
- The quality gate sets `PYTHONPATH=src` automatically. Manual Python test
  commands still need `PYTHONPATH=src`.
- `arch-lint` requires `.importlinter`; `arch-tests` requires
  `tests.architecture.test_hexagonal_imports`.
- Add or update tests when changing domain behavior, application orchestration,
  command construction, YAML parsing, path handling, repositories, or adapters.
- Mock command execution, network calls, VM operations, and Docker operations
  unless the task explicitly requests an integration run.
- Keep Linux/WSL behavior as the baseline in tests.

## Documentation

- Keep documentation aligned with the Linux/WSL-only operating model.
- Prefer forward-slash paths in documentation and examples.
- Update the relevant file under `documentation/` when a behavior, workflow, or
  deployment step changes.
- Keep README instructions concise and operational.

## Change Discipline

- Keep changes scoped to the requested behavior.
- Do not rewrite unrelated legacy modules as part of a narrow task.
- Do not commit generated caches such as `__pycache__`, logs, local virtual
  environments, or IDE state.
- Preserve user changes already present in the working tree.
- Before removing a legacy adapter or config file, verify no tests, scripts, or
  docs still reference it.

## Skill And Agent Governance

Root agent: `tiny-swarm-world-lead-architect`.

This is the repository governance identity for Tiny Swarm World agent and skill
work. It is not a new callable role file. It applies root `AGENTS.md`,
`QUALITY.md`, the active workflow, and the owner map before specialist routing.

Tiny Swarm World is currently Docker Swarm first. Tiny Swarm World must remain
Kubernetes-aware but not Kubernetes-first.

Tiny Swarm World is not `forensic_analytics`.
Tiny Swarm World is not forensic analytics.
Tiny Swarm World is not a Spring Boot application.
Tiny Swarm World is not a React frontend project.

### Governance Hierarchy

```text
tiny-swarm-world-lead-architect
|
+-- Agent Workflow Orchestrator / Senior Swarm Orchestrator
+-- Workflow Executor Skill
+-- Senior System Architect
+-- Senior Workflow Architect
+-- Senior Requirement Engineer
+-- Senior Documentation Engineer
+-- Senior Tester
+-- Senior DevOps Engineer
+-- Senior Python Automation Developer
+-- Console/status UI skills
+-- Service-boundary and contract-governance skills
```

### Registry And Owner Map

Canonical audit and navigation paths:

- `documentation/skill-audit/skill-registry.md`
- `documentation/skill-audit/skill-registry.json`
- `documentation/skill-audit/organigramm.md`
- `documentation/skill-audit/owner-map.md`

Repository files remain authoritative. The registry and organigramm are audit,
navigation, and coordination artifacts.

Owner mapping:

- Organigramm Maintainer: Senior Documentation Engineer, reviewed by Skill
  Registry Conflict Auditor, Senior Workflow Architect, and Senior System
  Architect when hierarchy changes affect architecture governance.
- Process Governance Maintainer: Senior Workflow Architect, reviewed by Senior
  Requirement Engineer, Senior Tester, and Engineering Governance.
- Root Architect: Senior System Architect escalation, with requirement,
  security, DevOps, data, contract, release, or quality owners brought in when
  those concerns are primary.
- Typed Error Router: Workflow Executor / Senior Workflow Architect, with
  Senior Execution Orchestrator for lock conflicts and Senior Tester plus
  Quality Gate Orchestrator for quality failures.
- Service Boundary Governance: Senior System Architect plus
  `service-decomposition-bounded-context`,
  `microservice-runtime-readiness-expert`,
  `microservice-migration-safety-gate`, and `contract-governance-expert`.

### Skill Groups

- Governance and documentation: `engineering-governance`,
  `documentation-sync`, `requirement-engineering`,
  `arc42-architecture-governance`, `adr-steward`,
  `skill-registry-conflict-auditor`, and
  `tiny-swarm-world-system-architecture`.
- Workflow execution: `workflow-executor`, `workflow-slice`,
  `workflow-slice-execution`, `workflow-orchestration`,
  `execution-profile-router`, and `s3d-execution-orchestrator`.
- Python automation and quality: `python-automation`,
  `python-senior-developer`, `python-cli-automation`,
  `python-test-automation`, `python-pip-packaging-expert`, `quality-gate`,
  `quality-gate-orchestrator`, `platform-quality-gates`, `tdd-expert`,
  `bdd-expert`, and `acceptance-checks`.
- Platform and runtime: `setup-bootstrap-expert`,
  `linux-host-preparation`, `multipass-vm-provisioning`,
  `network-topology-design`, `docker-engine-installation`,
  `docker-swarm-initialization`, `swarm-node-management`,
  `swarm-stack-deployment`, `swarm-volume-network-governance`,
  `registry-infrastructure`, `image-build-publish`,
  `image-versioning-tagging`, `image-verification`, and service bootstrap
  skills.
- Console/status UI: `frontend-developer`,
  `console-status-ui-developer`, and `terminal-status-dashboard`. These are
  terminal and console skills, not browser or React frontend authority.
- Service boundaries and contracts: `service-decomposition-bounded-context`,
  `microservice-runtime-readiness-expert`,
  `microservice-migration-safety-gate`, `contract-governance-expert`,
  `contract-first-api-steward`, `protobuf-contracts`, `grpc-ingestion`, and
  `grpc-streaming-specialist`.

Do not route Tiny Swarm World work to unrelated Spring Boot, browser React,
forensic analytics, generic backend/frontend, database/vector/graph analytics,
JavaParser scanner, Joern scanner, BTM generation, or removed
`microservice-senior-expert` roles unless a later explicit workflow verifies
that scope from repository evidence.

Project skills are discoverable only as `.agents/skills/<skill-name>/SKILL.md`
unless local skill discovery rules change. Grouped `.md` files are not
authoritative skill entrypoints.

### Workflow Execution Rules

- Exact `workflow execute` uses `.agents/skills/workflow-executor/SKILL.md`.
- Verify the active workflow, branch, slice metadata, locks, and quality gates
  before any write-capable work.
- Use S3/S3D preflight for workflow execution.
- Keep slice edits inside the workflow's allowed files and locks.
- Run targeted checks first, then required `QUALITY.md` gates.
- Classify failures through the Typed Error Router before retries.
- Slice checkpoint push is not `push auto` and must not create or merge a pull
  request.

Stop and report when documented behavior cannot be verified from repository
evidence, governance documents conflict, ownership or quality authority would
require guessing, planned behavior would be documented as implemented behavior,
a workflow would touch product implementation outside its declared scope, live
infrastructure commands would be required without explicit approval, or an
architecture decision or ADR is needed before continuing.

## Command Shortcuts

- If the user sends exactly `cc`, execute the workflow in `commit_push.md`.
