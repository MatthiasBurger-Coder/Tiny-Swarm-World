# Workflow: Tasklist Remediation Conversion

## Executive Summary

This workflow converts `TASKLIST.md` into the active governed remediation
workflow for Tiny Swarm World. The original task list was derived from
`AUDIT_REPORT.md`, but it contained stale `docker/` path assumptions,
duplicated findings and obsolete `pytest -q` verification commands. This
workflow preserves the useful audit intent, normalizes it to the current
repository shape and removes `TASKLIST.md` after successful conversion.

The active implementation baseline is Python automation under
`src/tiny_swarm_world`, infrastructure assets under `infra`, tests under
`tests`, documentation under `documentation` and quality gates from
`QUALITY.md`.

## Conversion Status

`TASKLIST.md` was successfully converted into this workflow and then removed
from the repository so stale task planning does not compete with
`documentation/workflow/**`.

Original source hash:

```text
TASKLIST.md sha256=96295c760ceaee6217e7987ff0b7bbd034479332d3f3d8341d2bcc4e55df9f48
AUDIT_REPORT.md sha256=b6714f0898a5ae2eca750516e920a1f412584f43ebc6e195b5d5d61c741c0816
```

## Requirement Clarification Record

Original request:

```text
workflow create with subagents
nachdem die Tasklist.md erfolgreich in einen workflow umgewandelt wurde, datei loeschen
```

Interpreted intent:

- Convert `TASKLIST.md` into a complete executable workflow.
- Preserve audit finding traceability from `AUDIT_REPORT.md`.
- Normalize stale task assumptions before workflow execution.
- Delete `TASKLIST.md` after successful conversion.
- Use subagents for requirement, architecture, Python, testing, frontend and
  DevOps review.

Change type:

- Workflow creation and documentation governance.
- Source planning artifact deletion after conversion.

Affected process strand:

- `workflow create`.

Affected architecture area:

- Python hexagonal automation governance.
- Platform, networking, Docker, Swarm and deployment remediation planning.
- Documentation and quality-gate governance.

Explicit requirements:

- Use subagents.
- Convert `TASKLIST.md` into a workflow.
- Delete `TASKLIST.md` only after the conversion succeeds.

Implicit requirements:

- Preserve `AGENTS.md` and `QUALITY.md` authority.
- Do not copy stale `docker/` and `pytest -q` assumptions into the active
  workflow.
- Collapse duplicated task-list entries into executable slices.
- Keep live infrastructure commands disabled unless explicitly requested.
- Keep Java deployment-example files out of this workflow unless a slice
  explicitly targets them.

Assumptions:

- `AUDIT_REPORT.md` and the removed `TASKLIST.md` are intake evidence, not
  verified current implementation truth.
- No `documentation/epics` source exists. EPIC traceability is recorded as a
  gap and does not block this workflow creation.
- `docker/` is legacy audit context. Active remediation must verify current
  paths before changing code.
- The default quality gate is `python3 tools/quality_gate.py quality`.

Non-goals:

- No runtime implementation during workflow creation.
- No live Multipass, Docker Swarm, compose deployment, netplan, `socat`,
  Portainer, Nexus, Jenkins, RabbitMQ, SonarQube or Swagger/NGINX execution.
- No direct preservation of duplicated task entries.
- No required use of `pytest`.
- No cleanup of legacy files before workflow execution proves references and
  replacement paths.

Risks:

- The audit was written against an older repository shape.
- Several original tasks referenced findings instead of concrete task or slice
  IDs.
- Placeholder commands such as `<canonical_entrypoint>` are not executable
  acceptance criteria.
- Live infrastructure behavior cannot be proven without explicit live-run
  authorization.
- arc42 runtime, deployment and risk sections remain placeholder-level.

Open questions:

- Which future EPIC should own long-term operational-readiness remediation?
- Which live infrastructure smoke tests should be authorized after mocked and
  static gates pass?

Blocking questions:

- None for workflow creation. The open questions are recorded as traceability
  and live-validation gaps for later workflow execution.

Confidence level:

- 84 percent.

Decision:

```text
PROCEED_WITH_ACCEPTED_ASSUMPTIONS
```

## Verified Baseline

- Branch:
  `architecture/workflow-tasklist-remediation-20260523`
- Repository root:
  `D:/Projects/Tiny-Swarm-World`
- Current Python source root:
  `src/tiny_swarm_world`
- Current infrastructure asset root:
  `infra`
- Current quality gate:
  `python3 tools/quality_gate.py quality`
- Current full gate order:
  `lint`, `arch-lint`, `arch-tests`, `typecheck`, `test`
- Architecture checks:
  `.importlinter` and `tests.architecture.test_hexagonal_imports`
- Frontend package tooling:
  not present
- EPIC source:
  not present
- Tasklist source:
  converted and deleted

## Target Picture

After workflow execution, Tiny Swarm World should have:

- one current, supported Python entrypoint and composition root;
- no stale task-list file outside the governed workflow;
- safe, non-destructive platform lifecycle behavior;
- deterministic network and netplan handling;
- Docker readiness checks before Swarm operations;
- idempotent Swarm bootstrap and validated parsing;
- an explicit deployment/compose flow with VM/Swarm-compatible assets;
- validated configuration and secret handling;
- reliable tests and architecture gates;
- operational documentation that distinguishes safe local checks from live
  infrastructure commands.

## Scope

In scope for workflow execution:

- `src/tiny_swarm_world/**`
- `infra/config/**`
- `infra/compose/**`
- `infra/prepare/**`
- `infra/swarm/**`
- `tests/**`
- `.importlinter`
- `tools/quality_gate.py` only when a slice explicitly changes gate behavior
- `QUALITY.md` only when a slice explicitly changes quality policy
- `README.md`
- `documentation/**`

Out of scope unless a slice is refined:

- `src/main/java/**`
- live infrastructure execution
- new frontend package tooling
- speculative microservice extraction
- direct restoration of `TASKLIST.md`

## Converted Task Traceability

| Finding | Original task IDs | Workflow slice |
|---|---|---|
| F-001 Python package/import model | T-001, T-004, T-007 | Slice 01 |
| F-003 active/dead orchestration mix | T-002, T-011 | Slice 01 and Slice 08 |
| F-014 hidden command failures | T-009, T-021 | Slice 01 and Slice 05 |
| F-012 test suite readiness | T-005, T-020 | Slice 01 and Slice 08 |
| F-013 config contracts | T-006, T-019 | Slice 02 and Slice 07 |
| F-002 destructive VM lifecycle | T-010 | Slice 03 |
| F-004 netplan path assumptions | T-012 | Slice 04 |
| F-005 WSL/Linux networking lifecycle | T-013 | Slice 04 |
| F-006 Docker readiness | T-014 | Slice 05 |
| F-007 Swarm bootstrap | T-015 | Slice 05 |
| F-008 missing stack deployment | T-008, T-016 | Slice 06 |
| F-010 compose/VM context mismatch | T-017 | Slice 06 |
| F-009 hardcoded credentials | T-018 | Slice 07 |
| F-011 outdated documentation | T-003, T-022 | Slice 08 |
| F-015 non-production leftovers | T-023 | Slice 08 |

## Architecture Constraints

- Preserve the Python hexagonal architecture.
- Domain code must remain independent from application and infrastructure.
- Application services depend on ports and domain objects, not concrete
  adapters.
- Infrastructure adapters own command execution, YAML parsing, filesystem
  access, HTTP clients, Docker, Multipass and shell details.
- Runtime wiring stays in
  `src/tiny_swarm_world/infrastructure/composition.py`.
- Entry-point code stays thin.
- Use structured YAML handling or existing YAML adapters.
- Do not expand Windows-native behavior.
- Do not run live infrastructure commands without explicit user approval.

## Python Automation Assessment

The remediation is Python-first. Implementation slices must use current package
imports under `tiny_swarm_world`, not legacy top-level `application`,
`domain` or `infrastructure` imports from the old audit baseline.

Command orchestration and failure propagation must be modeled through domain
objects, application ports and infrastructure adapters. Tests must mock external
commands, VM operations, network mutation, Docker operations and service
bootstrap calls by default.

## Frontend Assessment

Status: not applicable for implementation.

No frontend module or package tooling is present. The Senior React Frontend
Developer role is included for mandatory workflow-create coverage only and
records no implementation impact. Do not add React, TypeScript,
`package.json`, frontend build tooling, UI components, API client layers or
frontend tests unless a future requirement introduces a verified frontend
module and tooling conventions.

Python UI adapters remain Python automation and infrastructure adapter scope.

## Test Strategy

Use `QUALITY.md` as the source of truth:

```bash
python3 tools/quality_gate.py lint
python3 tools/quality_gate.py arch-lint
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py typecheck
python3 tools/quality_gate.py test
python3 tools/quality_gate.py quality
```

For documentation-only changes:

```bash
git diff --check
```

Focused Python tests may use `unittest` with `PYTHONPATH=src`, for example:

```bash
PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition
```

Do not use `pytest -q` as the default gate.

## Resilience Requirements

- Destructive VM reset must be explicit, never default.
- Docker and Swarm flows need readiness checks, retry limits, timeout policy
  and clear diagnostics.
- Command failures must fail critical workflows instead of being hidden behind
  progress UI.
- Network setup must be idempotent and have cleanup semantics.
- Deployment checks must distinguish mocked/static verification from live smoke
  tests.
- Secret and config validation must fail fast with actionable errors.

## Execution Profile

```text
executionProfile=FULL_PATH
reason=The workflow governs product remediation across Python source, infrastructure assets, tests, documentation, quality gates and live-infrastructure safety.
requiredFullReviews=Senior Requirement Engineer, Senior System Architect, Senior Python Automation Developer, Senior React Frontend Developer, Senior Tester, Senior DevOps Engineer, Senior Documentation Engineer
allowedImpactChecks=Senior React Frontend Developer may record N/A implementation impact because no frontend module exists
requiredQualityChecks=git diff --check; python3 tools/quality_gate.py arch-lint; python3 tools/quality_gate.py arch-tests; python3 tools/quality_gate.py quality when practical
stopConditions=stale docker paths copied without verification, pytest used as default gate, live infrastructure command executed without approval, slice dependencies unclear
```

## Ordered Slices

### Slice 01: Baseline, Entrypoint And Failure Semantics

Purpose:

Verify or repair the current Python entrypoint, package/import readiness,
composition root, dead orchestration classification and command failure
semantics. This slice also establishes the minimum test baseline used by later
infrastructure slices.

```yaml
slice_id: "01"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "src/tiny_swarm_world/__main__.py"
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "src/tiny_swarm_world/domain/command/**"
  - "src/tiny_swarm_world/application/ports/commands/**"
  - "src/tiny_swarm_world/application/services/commands/**"
  - "src/tiny_swarm_world/infrastructure/adapters/command_runner/**"
  - "tests/application/**"
  - "tests/infrastructure/**"
  - "tests/architecture/**"
  - "README.md"
  - "documentation/**"
affected_modules:
  - "src/tiny_swarm_world"
  - "tests"
  - "documentation"
affected_contracts: []
dependencies: []
parallel_group: "A"
file_locks:
  - "src/tiny_swarm_world/__main__.py"
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "src/tiny_swarm_world/domain/command/**"
  - "src/tiny_swarm_world/application/ports/commands/**"
  - "src/tiny_swarm_world/application/services/commands/**"
  - "src/tiny_swarm_world/infrastructure/adapters/command_runner/**"
architecture_locks:
  - "python-hexagonal-boundaries"
contract_locks: []
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition"
    - "python3 tools/quality_gate.py arch-lint"
    - "python3 tools/quality_gate.py arch-tests"
    - "python3 tools/quality_gate.py test"
  required:
    - "git diff --check"
    - "python3 tools/quality_gate.py arch-lint"
    - "python3 tools/quality_gate.py arch-tests"
    - "python3 tools/quality_gate.py test"
documentation:
  arc42: "check building blocks and runtime view"
  adr: "not required unless entrypoint strategy changes materially"
stop_conditions:
  - "canonical entrypoint cannot be verified"
  - "application imports infrastructure"
  - "command failures would be hidden"
  - "legacy docker path is treated as current source root without verification"
```

Task traceability:

- F-001: T-001, T-004, T-007
- F-003: T-002, T-011
- F-014: T-009, T-021
- F-012: T-005, T-020

Done criteria:

- `PYTHONPATH=src python3 -m tiny_swarm_world` is either verified or repaired.
- `__main__.py` remains thin.
- Critical command failure policy is explicit and tested.
- Dead or legacy orchestration surfaces are classified, not silently expanded.

### Slice 02: Configuration Contract Foundation

Purpose:

Create or verify typed configuration contracts, deterministic repository-root
path handling, YAML validation boundaries and environment override
expectations before live-infrastructure-facing slices depend on configuration.

```yaml
slice_id: "02"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior System Architect"
  - "Senior Tester"
  - "Senior DevOps Engineer"
affected_files:
  - "src/tiny_swarm_world/domain/**"
  - "src/tiny_swarm_world/application/ports/repositories/**"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/**"
  - "src/tiny_swarm_world/infrastructure/adapters/yaml/**"
  - "src/tiny_swarm_world/infrastructure/project_paths.py"
  - "infra/config/**"
  - "tests/**"
  - "documentation/**"
affected_modules:
  - "src/tiny_swarm_world/domain"
  - "src/tiny_swarm_world/application"
  - "src/tiny_swarm_world/infrastructure"
  - "infra/config"
affected_contracts:
  - "configuration schema and override behavior"
dependencies:
  - "01"
parallel_group: "B"
file_locks:
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/**"
  - "src/tiny_swarm_world/infrastructure/adapters/yaml/**"
  - "infra/config/**"
architecture_locks:
  - "configuration-boundary"
contract_locks:
  - "configuration-contract"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml"
    - "python3 tools/quality_gate.py arch-lint"
    - "python3 tools/quality_gate.py arch-tests"
    - "python3 tools/quality_gate.py typecheck"
  required:
    - "git diff --check"
    - "python3 tools/quality_gate.py arch-lint"
    - "python3 tools/quality_gate.py arch-tests"
    - "python3 tools/quality_gate.py typecheck"
documentation:
  arc42: "check constraints and concepts"
  adr: "required only if config authority changes"
stop_conditions:
  - "configuration keys cannot be verified"
  - "host-specific paths or secrets would be committed"
  - "YAML is modified by ad hoc string manipulation"
```

Task traceability:

- F-013: T-006, T-019

Done criteria:

- Required configuration contracts are explicit and testable.
- Path resolution is repository-root aware where needed.
- Overrides and examples are documented without secrets.

### Slice 03: Multipass Lifecycle Safety

Purpose:

Make VM lifecycle behavior state-aware and non-destructive by default. Any
reset path must be explicit and separately validated.

```yaml
slice_id: "03"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior DevOps Engineer"
  - "Senior Tester"
  - "Senior Security Sandbox Engineer"
affected_files:
  - "src/tiny_swarm_world/domain/multipass/**"
  - "src/tiny_swarm_world/application/services/multipass/**"
  - "src/tiny_swarm_world/application/services/vm/**"
  - "src/tiny_swarm_world/application/services/platform/**"
  - "src/tiny_swarm_world/application/ports/repositories/port_vm_repository.py"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/vm_repository_yaml.py"
  - "infra/config/multipass/**"
  - "infra/config/vm/**"
  - "tests/application/services/multipass/**"
  - "tests/domain/**"
  - "documentation/**"
affected_modules:
  - "multipass"
  - "vm"
  - "platform"
affected_contracts:
  - "VM lifecycle command contract"
dependencies:
  - "01"
  - "02"
parallel_group: "C"
file_locks:
  - "src/tiny_swarm_world/domain/multipass/**"
  - "src/tiny_swarm_world/application/services/multipass/**"
  - "src/tiny_swarm_world/application/services/vm/**"
  - "infra/config/multipass/**"
  - "infra/config/vm/**"
architecture_locks:
  - "live-infrastructure-safety"
contract_locks:
  - "multipass-command-contract"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.application.services.multipass.test_multipass_init_vms"
    - "python3 tools/quality_gate.py arch-lint"
    - "python3 tools/quality_gate.py arch-tests"
    - "python3 tools/quality_gate.py test"
  required:
    - "git diff --check"
    - "python3 tools/quality_gate.py arch-lint"
    - "python3 tools/quality_gate.py arch-tests"
    - "python3 tools/quality_gate.py test"
documentation:
  arc42: "update runtime and risks when lifecycle behavior changes"
  adr: "consider if default reset behavior changes"
stop_conditions:
  - "multipass command would run live"
  - "default path still deletes or purges VMs"
  - "reset behavior lacks explicit user intent"
```

Task traceability:

- F-002: T-010

Done criteria:

- Default lifecycle behavior does not destroy VMs.
- Explicit reset path is separated from reconcile/bootstrap behavior.
- Tests use mocked command execution.

### Slice 04: Networking, WSL2 And Netplan

Purpose:

Make netplan generation, transfer path handling and WSL/Linux networking
procedures deterministic, idempotent and safe to validate without live network
mutation.

```yaml
slice_id: "04"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior DevOps Engineer"
  - "Senior Tester"
  - "Senior Security Sandbox Engineer"
affected_files:
  - "src/tiny_swarm_world/domain/network/**"
  - "src/tiny_swarm_world/application/services/network/**"
  - "src/tiny_swarm_world/application/services/vm/**"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/netplan_repository.py"
  - "infra/config/network/**"
  - "infra/swarm/**"
  - "tests/application/services/network/**"
  - "tests/domain/network/**"
  - "documentation/system/network.adoc"
  - "documentation/user_guide/troubleshooting.adoc"
affected_modules:
  - "network"
  - "vm"
  - "infra/config/network"
affected_contracts:
  - "netplan artifact and transfer path contract"
dependencies:
  - "02"
  - "03"
parallel_group: "D"
file_locks:
  - "src/tiny_swarm_world/domain/network/**"
  - "src/tiny_swarm_world/application/services/network/**"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/netplan_repository.py"
  - "infra/config/network/**"
  - "infra/swarm/**"
architecture_locks:
  - "network-live-safety"
contract_locks:
  - "netplan-contract"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.application.services.network.test_network_service"
    - "python3 tools/quality_gate.py arch-lint"
    - "python3 tools/quality_gate.py arch-tests"
    - "python3 tools/quality_gate.py test"
  required:
    - "git diff --check"
    - "python3 tools/quality_gate.py arch-lint"
    - "python3 tools/quality_gate.py arch-tests"
    - "python3 tools/quality_gate.py test"
documentation:
  arc42: "update runtime view and deployment view when network flow changes"
  adr: "not required unless network state model changes materially"
stop_conditions:
  - "netplan changes would be applied live"
  - "socat or iptables command would run live"
  - "generated file path cannot be verified"
```

Task traceability:

- F-004: T-012
- F-005: T-013

Done criteria:

- Netplan save and transfer paths resolve to the same deterministic artifact.
- WSL/Linux networking setup has prepare, verify and cleanup semantics.
- Live mutation remains opt-in only.

### Slice 05: Docker Readiness And Swarm Bootstrap

Purpose:

Add Docker daemon readiness semantics, robust retry/timeout behavior, state-aware
Swarm init/join and validated parsing without running Docker or Swarm live by
default.

```yaml
slice_id: "05"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior DevOps Engineer"
  - "Senior Tester"
affected_files:
  - "src/tiny_swarm_world/domain/command/**"
  - "src/tiny_swarm_world/application/services/multipass/**"
  - "src/tiny_swarm_world/application/services/platform/**"
  - "src/tiny_swarm_world/infrastructure/adapters/command_runner/**"
  - "infra/config/docker/**"
  - "infra/config/multipass/**"
  - "tests/application/services/multipass/**"
  - "tests/infrastructure/adapters/command_runner/**"
  - "documentation/**"
affected_modules:
  - "docker-readiness"
  - "swarm-bootstrap"
  - "command-runner"
affected_contracts:
  - "Docker readiness command contract"
  - "Swarm token and node verification contract"
dependencies:
  - "03"
  - "04"
parallel_group: "E"
file_locks:
  - "src/tiny_swarm_world/application/services/multipass/**"
  - "src/tiny_swarm_world/application/services/platform/**"
  - "src/tiny_swarm_world/infrastructure/adapters/command_runner/**"
  - "infra/config/docker/**"
architecture_locks:
  - "docker-swarm-live-safety"
contract_locks:
  - "swarm-command-contract"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.command_runner.test_command_workflow_configuration"
    - "python3 tools/quality_gate.py arch-lint"
    - "python3 tools/quality_gate.py arch-tests"
    - "python3 tools/quality_gate.py test"
  required:
    - "git diff --check"
    - "python3 tools/quality_gate.py arch-lint"
    - "python3 tools/quality_gate.py arch-tests"
    - "python3 tools/quality_gate.py test"
documentation:
  arc42: "update runtime and risks for readiness and bootstrap behavior"
  adr: "consider if retry/failure policy becomes cross-cutting"
stop_conditions:
  - "docker or docker swarm command would run live"
  - "token parsing remains positional and unvalidated"
  - "critical command failure still reports success"
```

Task traceability:

- F-006: T-014
- F-007: T-015
- F-014: T-009, T-021

Done criteria:

- Docker install blocks on daemon readiness in mocked tests.
- Swarm init/join handles already-active states.
- Token/IP parsing is explicit and validated.
- Critical failures propagate.

### Slice 06: Deployment Stack And Compose Flow

Purpose:

Separate platform provisioning from stack deployment, integrate deployment into
the canonical flow or document the handoff, and fix compose assumptions that
conflict with VM/Swarm execution.

```yaml
slice_id: "06"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior DevOps Engineer"
  - "Senior Tester"
  - "Senior System Architect"
affected_files:
  - "src/tiny_swarm_world/domain/deployment/**"
  - "src/tiny_swarm_world/application/services/deployment/**"
  - "src/tiny_swarm_world/application/ports/clients/port_portainer_client.py"
  - "src/tiny_swarm_world/application/ports/repositories/port_compose_file_repository.py"
  - "src/tiny_swarm_world/infrastructure/adapters/clients/portainer_http_client.py"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py"
  - "infra/config/compose/**"
  - "infra/compose/**"
  - "tests/application/services/deployment/**"
  - "tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py"
  - "documentation/**"
affected_modules:
  - "deployment"
  - "compose"
  - "portainer-client"
affected_contracts:
  - "deployment stack contract"
dependencies:
  - "05"
parallel_group: "F"
file_locks:
  - "src/tiny_swarm_world/domain/deployment/**"
  - "src/tiny_swarm_world/application/services/deployment/**"
  - "src/tiny_swarm_world/infrastructure/adapters/clients/portainer_http_client.py"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py"
  - "infra/config/compose/**"
  - "infra/compose/**"
architecture_locks:
  - "deployment-boundary"
contract_locks:
  - "compose-stack-contract"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml"
    - "python3 tools/quality_gate.py arch-lint"
    - "python3 tools/quality_gate.py arch-tests"
    - "python3 tools/quality_gate.py test"
  required:
    - "git diff --check"
    - "python3 tools/quality_gate.py arch-lint"
    - "python3 tools/quality_gate.py arch-tests"
    - "python3 tools/quality_gate.py test"
documentation:
  arc42: "update deployment view"
  adr: "consider if canonical deployment strategy changes"
stop_conditions:
  - "compose deployment would run live"
  - "stack deploy command lacks dry-run or mocked verification"
  - "host-local compose assumptions remain unclassified"
```

Task traceability:

- F-008: T-008, T-016
- F-010: T-017

Done criteria:

- Deployment is a deliberate stage with verification.
- Compose assets are classified as VM/Swarm-compatible or explicitly legacy.
- No live deployment runs without approval.

### Slice 07: Secrets, Nexus And Configuration Contracts

Purpose:

Remove hardcoded credentials from active automation paths, define secret/config
inputs and validate Nexus/Portainer/bootstrap configuration without committing
real secrets.

```yaml
slice_id: "07"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior DevOps Engineer"
  - "Senior Security Sandbox Engineer"
  - "Senior Tester"
affected_files:
  - "src/tiny_swarm_world/domain/nexus/**"
  - "src/tiny_swarm_world/application/services/nexus/**"
  - "src/tiny_swarm_world/application/services/artifacts/**"
  - "src/tiny_swarm_world/application/ports/clients/port_nexus_client.py"
  - "src/tiny_swarm_world/infrastructure/adapters/clients/nexus_http_client.py"
  - "infra/prepare/nexus/**"
  - "infra/prepare/portainer/**"
  - "infra/config/**"
  - "tests/application/services/nexus/**"
  - "documentation/**"
affected_modules:
  - "nexus"
  - "artifacts"
  - "secrets"
affected_contracts:
  - "secret and environment input contract"
dependencies:
  - "02"
  - "06"
parallel_group: "G"
file_locks:
  - "src/tiny_swarm_world/domain/nexus/**"
  - "src/tiny_swarm_world/application/services/nexus/**"
  - "src/tiny_swarm_world/application/services/artifacts/**"
  - "src/tiny_swarm_world/infrastructure/adapters/clients/nexus_http_client.py"
  - "infra/prepare/nexus/**"
  - "infra/prepare/portainer/**"
  - "infra/config/**"
architecture_locks:
  - "secret-safety"
contract_locks:
  - "secret-input-contract"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.application.services.nexus.test_bootstrap_nexus"
    - "python3 tools/quality_gate.py arch-lint"
    - "python3 tools/quality_gate.py arch-tests"
    - "python3 tools/quality_gate.py test"
  required:
    - "git diff --check"
    - "python3 tools/quality_gate.py arch-lint"
    - "python3 tools/quality_gate.py arch-tests"
    - "python3 tools/quality_gate.py test"
documentation:
  arc42: "update concepts and risks for secret handling"
  adr: "required if secret ownership model changes materially"
stop_conditions:
  - "real credential would be committed"
  - "script defaults to insecure admin credentials"
  - "bootstrap endpoint is called live"
```

Task traceability:

- F-009: T-018
- F-013: T-006, T-019

Done criteria:

- No tracked active automation path embeds real credentials.
- Missing secrets fail fast.
- Example templates contain placeholders only.

### Slice 08: Test Gate Cleanup And Operational Documentation

Purpose:

Complete test curation, architecture-gate alignment, operational documentation
and legacy surface cleanup. This slice updates docs and arc42 after the
implementation slices establish verified behavior.

```yaml
slice_id: "08"
profile: "FULL_PATH"
owner: "Senior Documentation Engineer"
secondary_reviewers:
  - "Senior Tester"
  - "Senior System Architect"
  - "Senior Python Automation Developer"
  - "Senior DevOps Engineer"
affected_files:
  - "tests/**"
  - ".importlinter"
  - "tools/quality_gate.py"
  - "QUALITY.md"
  - "README.md"
  - "documentation/arc42/**"
  - "documentation/user_guide/**"
  - "documentation/system/**"
  - "documentation/deployment/**"
  - "documentation/process/**"
  - "infra/swarm/**"
  - "infra/prepare/**/README.md"
affected_modules:
  - "tests"
  - "documentation"
  - "quality-gate"
  - "legacy-surface"
affected_contracts:
  - "quality-gate policy when changed"
dependencies:
  - "01"
  - "02"
  - "03"
  - "04"
  - "05"
  - "06"
  - "07"
parallel_group: "H"
file_locks:
  - "tests/**"
  - ".importlinter"
  - "tools/quality_gate.py"
  - "QUALITY.md"
  - "README.md"
  - "documentation/**"
  - "infra/swarm/**"
architecture_locks:
  - "documentation-governance"
  - "quality-gate-authority"
contract_locks:
  - "quality-gate-contract"
quality_gates:
  targeted:
    - "git diff --check"
    - "python3 tools/quality_gate.py arch-lint"
    - "python3 tools/quality_gate.py arch-tests"
    - "python3 tools/quality_gate.py test"
  required:
    - "git diff --check"
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "update constraints, runtime view, deployment view, quality requirements and risks"
  adr: "required if quality policy or runtime strategy changes materially"
stop_conditions:
  - "quality gate is weakened"
  - "documentation claims live behavior that was not verified"
  - "legacy script is removed before references are checked"
```

Task traceability:

- F-011: T-003, T-022
- F-012: T-005, T-020
- F-015: T-023
- F-003: T-002, T-011

Done criteria:

- `pytest` references are no longer described as the default gate.
- Documentation provides current safe checks and explicitly marks live
  infrastructure commands as opt-in.
- arc42 placeholder sections touched by remediation are updated or have
  documented no-change rationale.
- Legacy surfaces are removed only after reference checks or are clearly
  documented as unsupported.

## Slice Dependency Graph

```text
01 -> 02 -> 03 -> 04 -> 05 -> 06 -> 07 -> 08
```

Parallelization:

- This workflow is intentionally sequential. The original task list contained
  cross-phase duplicate findings and finding-ID dependencies. Sequential
  execution keeps ownership, evidence and rollback clear.

## Role And Subagent Ownership Map

| Area | Owner | Supporting roles |
|---|---|---|
| Workflow conversion | Senior Workflow Architect | Senior Requirement Engineer |
| Python implementation | Senior Python Automation Developer | Senior System Architect, Senior Tester |
| Architecture boundaries | Senior System Architect | quality architecture validation |
| Quality gates | Senior Tester | quality-gate skill |
| Multipass, Docker, Swarm and shell assets | Senior DevOps Engineer | Security Sandbox Engineer |
| Secret handling | Senior Security Sandbox Engineer | Senior DevOps, Senior Tester |
| Documentation and arc42 | Senior Documentation Engineer | Senior System Architect |
| Frontend assessment | Senior React Frontend Developer | N/A implementation impact |

## Quality-Gate Expectations

All slices:

```bash
git diff --check
```

Architecture-sensitive slices:

```bash
python3 tools/quality_gate.py arch-lint
python3 tools/quality_gate.py arch-tests
```

Implementation slices:

```bash
python3 tools/quality_gate.py test
```

Final readiness when practical:

```bash
python3 tools/quality_gate.py quality
```

Optional static Bash syntax check for shell slices:

```bash
find infra -name '*.sh' -print0 | xargs -0 bash -n
```

Do not run `multipass`, `docker swarm`, compose deployments, netplan changes,
`socat` forwarding or service bootstrap scripts unless the user explicitly
authorizes live infrastructure execution.

## Documentation Synchronization Points

- Update `documentation/arc42/02_constraints.adoc` when constraints change.
- Update `documentation/arc42/06_runtime_view.adoc` when runtime flow changes.
- Update `documentation/arc42/07_deployment_view.adoc` when deployment flow
  changes.
- Update `documentation/arc42/10_quality_requirements.adoc` when quality gates
  or verification expectations change.
- Update `documentation/arc42/11_risks_and_debt.adoc` when operational risks
  change.
- Update README and user guides only with verified commands and explicit live
  run caveats.

## Stop Conditions

Stop workflow execution if:

- active branch is not
  `architecture/workflow-tasklist-remediation-20260523`;
- a deleted `TASKLIST.md` entry cannot be traced through this workflow;
- a slice copies stale `docker/` source assumptions without verifying current
  paths;
- `pytest` is used as the default gate instead of `tools/quality_gate.py`;
- live infrastructure commands would run without explicit user approval;
- quality gates fail or would need to be weakened;
- architecture boundaries are unclear;
- a slice cannot map affected files to a single owner;
- secrets would be committed;
- documentation claims verified live behavior without live-run evidence.

## Uncertainty Escalation Rules

- Missing EPIC ownership routes to Senior Requirement Engineer.
- Architecture ambiguity routes to Senior System Architect.
- Quality command ambiguity routes to Senior Tester and `quality-gate`.
- Live-infrastructure ambiguity routes to Senior DevOps and Security Sandbox
  Engineer.
- Secret-handling ambiguity routes to Security Sandbox Engineer.
- Any unclassified slice routes to Root Architect through Senior System
  Architect.

## Commit And Push Plan

Workflow creation may be committed and pushed when requested. Workflow execute
must create slice-scoped commits only after required gates pass or documented
skip reasons are accepted by the active workflow.

Do not combine implementation slices in one commit. Do not push directly to
`main`. Do not run `push auto` unless explicitly requested and allowed by the
repository governance.

## Definition Of Done

- `TASKLIST.md` is deleted after conversion.
- This workflow and context pack are present.
- Every original task ID has traceability to a slice.
- Stale task-list commands and paths are normalized.
- Required roles and stop conditions are explicit.
- The workflow can be consumed by `workflow execute`.
- Documentation and arc42 impact are checked.
- Required validation for this workflow creation passes.

## Handoff To Workflow Execute

`workflow execute` may start after:

- `documentation/workflow/workflow.md` and `context-pack.*` are present;
- `TASKLIST.md` deletion is visible in git diff;
- the active branch is verified;
- S3/S3D validates slice metadata and dependencies;
- the executor accepts the EPIC traceability gap and stale audit baseline as
  documented assumptions.

Use `.agents/skills/workflow-executor/SKILL.md` as the active executor.

## arc42 Check Status

arc42 was checked during workflow creation.

Current findings:

- `documentation/arc42/05_building_blocks.adoc` already records the current
  Python automation, infrastructure asset and deployment-example split.
- `documentation/arc42/06_runtime_view.adoc`,
  `documentation/arc42/07_deployment_view.adoc`,
  `documentation/arc42/10_quality_requirements.adoc` and
  `documentation/arc42/11_risks_and_debt.adoc` remain placeholder-level for
  this remediation scope.

Slice 08 must update those sections or record explicit no-change rationale
after implementation evidence exists.
