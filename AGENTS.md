# AGENTS.md

## Project Identity

Tiny Swarm World is a Linux/WSL-only local infrastructure automation project.
Its default node-provider direction is managed LXC through LXD or Incus for a
Docker Swarm target environment. It ships guarded workflow boundaries and
service-stack configuration for Portainer, Nexus, Jenkins, Apache Pulsar,
SonarQube, and Swagger/NGINX. Multipass is not a supported node provider.

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
- `infra/config`: YAML command, node-provider, network, and compose stack
  configuration data.
- `infra/config/compose`: image build contexts and related Dockerfiles for stack services.
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
- Prefer typed value objects and small domain classes for command,
  node-provider, VM legacy, network, deployment, and Nexus concepts.

## Configuration And YAML

- Treat files under `infra/config` as part of the product behavior, not as
  throwaway examples.
- Use structured YAML APIs or existing YAML adapter helpers instead of ad hoc
  string manipulation.
- Keep command templates readable and deterministic.
- Avoid embedding host-specific absolute paths, user names, IP addresses, or
  secrets in committed configuration.
- Preserve service stack boundaries under `infra/config/compose`.

## External System Safety

Many project commands can create provider nodes, change networking, install
Docker, or deploy stacks. Do not run these unless the user explicitly asks for
live infrastructure changes:

- `incus`
- `lxc`
- LXD or Incus daemon initialization, profile, storage, or network changes
- `docker swarm`
- compose deployments
- netplan changes
- `socat` port forwarding
- Nexus, Jenkins, Portainer, Apache Pulsar, or SonarQube bootstrap scripts

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
- Mock command execution, network calls, node-provider or VM operations, and
  Docker operations unless the task explicitly requests an integration run.
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
Issue-driven work also applies
`documentation/process/issue-completion-discipline.md` as the completion
authority for requirement extraction, evidence, verification and final status.

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
  `skill-registry-conflict-auditor`,
  `issue-completion-auditor`,
  `audit-evidence-manager`, `qms-light-governance-expert`,
  `traceability-engineer`, `documentation-audience-architect`,
  `release-baseline-governance-expert`, and
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
  `linux-host-preparation`,
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
- Security and audit remediation: `isms-light-security-governance-expert`,
  `owasp-asvs-local-infrastructure-expert`,
  `supply-chain-security-expert`, `live-evidence-validation-expert`, and
  `branch-ci-governance-expert`.

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
- Issue-driven work must follow
  `documentation/process/issue-completion-discipline.md`: extract a
  requirement matrix before implementation, map every requirement to
  implementation and verification evidence, and block `DONE` when any
  requirement is open or unverified.
- Completion of issue-driven work requires `issue-completion-auditor` review.
  The implementer must not be the only authority deciding that an issue is
  done.
- Verify the active workflow, branch, slice metadata, locks, and quality gates
  before any write-capable work.
- Use S3/S3D preflight for workflow execution.
- During every `workflow execute`, inspect each executable slice and decide
  automatically whether it can be split into specialist execution streams.
- Prefer automatic work distribution when backend, frontend, tests, runtime,
  documentation, quality, architecture, or security concerns are clearly
  separable.
- Use real Codex subagents where supported. If real subagents are unavailable
  or not visible, perform an explicit role-based fallback review in the main
  execution thread and record that fallback in evidence.
- Parallel stream work must use isolated Git worktrees and stream branches.
- Do not parallelize unsafe slices, including overlapping files, unclear
  architecture boundaries, contradictory requirements, mandatory ordering,
  shared migrations, strict database/schema sequencing, generated-file merge
  conflicts, unclear secrets handling, weakened safety guards, or a Three
  Amigos decision that marks the slice as not safely parallelizable.
- Codex remains the final integration owner for consolidation, tests,
  evidence, PR readiness, and merge readiness.
- `workflow execute` must never call `workflow create` backwards.
- Each slice commit must represent exactly one slice; multi-slice commits are
  forbidden.
- External AI, subagents, or stream workers may advise or produce isolated
  stream changes, but Codex remains the final executor and decision owner.
- Subagents or stream workers must not directly merge to the main workflow
  branch without consolidation.
- Keep slice edits inside the workflow's allowed files and locks.
- Run targeted checks first, then required `QUALITY.md` gates.
- Classify failures through the Typed Error Router before retries.
- Slice checkpoint push is not `push auto` and must not create or merge a pull
  request.
- Workflow-create publication is not `push auto`; after `workflow create`, the
  default publication action is a guarded commit and branch push to
  `origin/<workflow-branch>` without PR merge, branch deletion, or cleanup.
- Exact `push auto` may publish and automatically merge any task-scoped
  implementation change, including Python product code and Python
  product-behavior tests. It is blocked for workflow-create-only branches
  unless the user explicitly confirms a workflow-documentation-only PR merge
  after the workflow-create guard is reported.
- `push auto` must run the full guarded lifecycle: create the commit, push the
  branch, create or reuse a pull request, wait or retry until required checks
  are green including SonarQube when configured, merge the pull request, delete
  the merged remote head branch, and clean up the local branch.
- `push auto` must stop on unrelated changes, sensitive files, generated local
  artifacts, failed or unverifiable required checks, failed or unverifiable
  SonarQube status, unknown mergeability, or unverifiable branch cleanup.

Stop and report when documented behavior cannot be verified from repository
evidence, governance documents conflict, ownership or quality authority would
require guessing, planned behavior would be documented as implemented behavior,
a workflow would touch product implementation outside its declared scope, live
infrastructure commands would be required without explicit approval, or an
architecture decision or ADR is needed before continuing.

## Command Shortcuts

- If the user sends exactly `cc`, execute the workflow in `commit_push.md`.
