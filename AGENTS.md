# AGENTS.md

## Project Identity

Tiny Swarm World is a Linux/WSL-only local infrastructure automation project.
It provisions and operates a production-like Docker Swarm environment on
Multipass virtual machines and ships ready-to-use service stacks such as
Portainer, Nexus, Jenkins, RabbitMQ, SonarQube, and Swagger/NGINX.

The project is primarily a Python automation codebase using a hexagonal
architecture. Java code under `src/main/java` is a deployment example
application for the finished local system and must not drive the Python
automation architecture.

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
- `infra/config`: YAML command, VM, network, and compose configuration data.
- `infra/compose`: compose stacks and related Dockerfiles.
- `infra/prepare`: one-off preparation scripts for local services.
- `infra/swarm`: swarm setup and helper scripts.
- `tests`: unit tests organized by architecture layer.
- `documentation`: arc42, deployment, system, and user guide documentation.

## Architecture Rules

- Preserve the existing hexagonal architecture.
- Keep domain code independent from infrastructure concerns.
- Domain modules must not import command runners, file managers, HTTP clients,
  Docker clients, UI adapters, YAML parsers, logging setup, or dependency
  injection containers.
- Application services may orchestrate ports and domain objects, but should not
  embed low-level shell, filesystem, HTTP, curses, or Docker details directly.
- Infrastructure adapters implement ports and contain technology-specific
  details.
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

## Command Shortcuts

- If the user sends exactly `cc`, execute the workflow in `commit_push.md`.
