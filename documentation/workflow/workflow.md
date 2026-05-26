# Workflow: LXC Native Node Provider Migration

## Executive Summary

This workflow replaces the active Multipass repair direction with a governed
provider migration plan:

```text
Default node provider: LXC-native through LXD or Incus
Raw LXC low-level commands: not the first implementation path
Multipass: optional legacy/fallback provider only
```

The workflow does not execute live infrastructure commands. It plans the
migration from Multipass virtual machines to managed LXC containers while
preserving Tiny Swarm World's Linux/WSL-only operating model, Docker
Swarm-first target, Python automation codebase, hexagonal architecture,
live-consent safety model, and default mocked/static quality gates.

The default product path after workflow execution should be:

```text
setup run:
  selects provider family: lxc_native
  selects backend: explicit Incus or LXD when configured
  auto-detects only when exactly one managed backend is usable
  blocks before mutation when backend readiness is absent or ambiguous

setup run --node-provider multipass_legacy:
  allowed only as explicit fallback
  never selected as silent automatic fallback
  remains governed by the same live-consent and verification gates
```

## Target Picture

### Verified Baseline

- Active workflow creation branch:

```bash
feature/workflow-lxc-node-provider-20260526
```

- Root `AGENTS.md` currently identifies Tiny Swarm World as a
  Multipass-backed Docker Swarm automation project. The user request changes
  that product direction, so later workflow slices must update governance and
  documentation after the architecture decision is recorded.
- Root `QUALITY.md` defines the authoritative quality gate:

```bash
python3 tools/quality_gate.py quality
```

- Current source contains Multipass-specific platform services, command
  configuration, infrastructure clients, and documentation:
  - `src/tiny_swarm_world/application/services/multipass/**`
  - `src/tiny_swarm_world/domain/multipass/**`
  - `src/tiny_swarm_world/infrastructure/adapters/clients/multipass_*.py`
  - `infra/config/multipass/**`
  - `infra/config/docker/command_multipass_*.yaml`
  - `documentation/system/multipass-setup.adoc`
- Current setup safety is fail-closed and live-consent gated through
  `documentation/architecture/adr-autonomous-setup-safety.adoc`.
- Current arc42 runtime and deployment views describe Multipass readiness as
  the platform guard. Those views are no longer target-state documentation for
  the new provider direction until updated by an implementation slice.
- Existing architecture tests forbid new undeclared application service
  directories. Provider orchestration should stay in existing Platform
  boundaries unless a slice deliberately updates architecture documentation
  and tests.

### Target Outcome

After workflow execution, Tiny Swarm World should provide:

- a provider-neutral node model for manager and worker nodes;
- `lxc_native` as the default provider family;
- managed LXC backends through LXD and/or Incus, not raw `lxc-*` command
  automation as the first implementation;
- explicit backend selection semantics:
  - configured backend wins;
  - exactly one usable backend may be selected automatically;
  - multiple usable backends without configured preference block with
    remediation;
  - no usable backend blocks before platform mutation;
- non-mutating LXD/Incus readiness checks with timeouts and sanitized evidence;
- explicit container profile requirements for Docker-in-container and Swarm
  operation;
- setup and platform workflows that create/reconcile LXC nodes only after live
  consent, provider readiness, profile validation, and verify-after-apply
  contracts are satisfied;
- Multipass retained only behind an explicit `multipass_legacy` provider path;
- documentation, EPICs, ADR references, and arc42 synchronized so planned
  behavior is not documented as implemented behavior;
- tests that mock LXD, Incus, Multipass, Docker, networking, and filesystem
  interactions by default.

## Requirement Clarification Record

Original request:

```text
wir aendern vom mulitpass zu nativ LXC provider:
workflow create:
Ja. Dann ist die neue Richtung:

LXC/LXD wird der Standardpfad.
Multipass wird nicht mehr primaer repariert.
Multipass wird optionaler Legacy-/Fallback-Provider.

Wichtig: Ich wuerde nicht "raw LXC only" als erste Implementierung nehmen,
sondern LXC-native ueber LXD/Incus.

Default Node Provider:
  LXC / LXD / Incu
```

Interpreted intent:

```text
Create a new executable workflow that makes managed LXC through LXD/Incus the
default node provider for Tiny Swarm World and demotes Multipass to an explicit
legacy/fallback provider.
```

Change type:

```text
architecture migration / platform provider migration / setup runtime strategy
```

Affected process strand:

```text
workflow authoring, provider architecture, setup preflight, platform setup,
node lifecycle, Docker Swarm bootstrap, network planning, evidence,
documentation, quality validation
```

Affected architecture area:

```text
Platform boundary, provider domain model, application ports, infrastructure
adapters, command/YAML configuration, setup orchestration, composition root,
CLI semantics, console/status output, documentation and arc42 governance
```

Explicit requirements:

- LXC/LXD becomes the standard path.
- Multipass is no longer the primary repair target.
- Multipass remains optional legacy/fallback provider.
- First implementation should use LXD/Incus as the management layer over LXC,
  not raw LXC-only automation.
- LXC containment properties matter to the design, but low-level kernel
  details must stay behind infrastructure/provider abstractions.

Implicit requirements:

- introduce provider-neutral terminology without a disruptive big-bang rename;
- preserve Docker Swarm as the runtime target;
- preserve live-consent and fail-closed setup semantics;
- add provider selection to CLI/configuration without silently selecting
  Multipass when LXD/Incus readiness fails;
- keep LXD/Incus subprocess, filesystem, socket, profile, and network details
  in infrastructure adapters;
- keep default tests and quality gates mocked/static;
- update EPIC, ADR and arc42 material once provider behavior changes.

Assumptions accepted for workflow creation:

- `Incu` in the user request means `Incus`.
- `LXC-native` means managed LXC containers through LXD or Incus.
- The provider family default is `lxc_native`; backend preference is explicit
  configuration when both LXD and Incus are available.
- Native Linux is the primary target for the first LXC-native live path.
- WSL2 remains Linux/WSL in scope, but LXD/Incus support on WSL2 is
  capability-gated and must not be claimed from sandbox or native Linux tests.
- Existing Multipass code is migrated behind an explicit legacy provider
  boundary before removal is considered.
- Any automatic host package installation, daemon repair, privileged container
  profile, or host networking mutation requires explicit live consent and may
  require a later ADR.

Non-goals:

- no raw low-level LXC-only provider as the first implementation;
- no Kubernetes-first direction;
- no Java, Maven, Spring Boot, Gradle, JUnit or ArchUnit build surface;
- no browser React frontend, npm, Vite, Next.js, TypeScript, `.tsx`, or `.jsx`
  scope;
- no live LXD, Incus, Multipass, Docker Swarm, compose, network, Portainer,
  Nexus, Jenkins, RabbitMQ, SonarQube, or Swagger/NGINX execution during
  workflow creation, unit tests, architecture tests, type checks, docs checks,
  or default quality gates;
- no committed host IPs, usernames, absolute paths, tokens, passwords, raw
  command strings, stdout, stderr, environment payloads, or Swarm join tokens;
- no silent automatic fallback to Multipass when the default LXC-native path
  is not ready;
- no removal of Multipass code until compatibility and documentation
  boundaries are verified.

Risks:

- Docker Swarm inside LXD/Incus containers can require nesting, cgroup, AppArmor
  and capability decisions that must be explicit and security-reviewed.
- Privileged containers or broad host mounts could make local setup easier but
  would weaken the safety model if enabled silently.
- WSL2 support for managed LXC may be more constrained than native Linux; the
  workflow must not overclaim WSL2 success.
- Existing code and tests are named around Multipass and VM concepts, so a
  provider-neutral migration needs compatibility shims and staged naming.
- Existing architecture tests reject undeclared application service
  directories.
- Documentation currently presents Multipass as the baseline; docs must be
  changed only when behavior is implemented or clearly marked as planned.

Open questions:

- Should Incus or LXD be preferred when both are installed and no explicit
  backend is configured?
- Which LXD/Incus container profile is accepted for Docker Swarm-in-container:
  unprivileged with nesting, privileged local-dev profile, or both with
  explicit risk labeling?
- Is WSL2 intended to be a first live LXD/Incus target, or a
  capability-gated secondary path after native Linux works?
- What is the operator-facing name of the provider flag: `--node-provider`,
  `--provider`, or existing setup profile configuration?

Blocking questions:

```text
None for workflow authoring. The open questions are resolved inside explicit
architecture and implementation slices before live behavior is claimed.
```

Confidence level:

```text
86 percent
```

Decision:

```text
PROCEED_WITH_ACCEPTED_ASSUMPTIONS
```

## External Documentation Baseline

External provider and WSL documentation was checked so WSL2 behavior is treated
as a capability-gated path rather than an inferred success case. The checked
source list and planning facts are recorded in:

```text
documentation/workflow/reports/03-external-wsl-provider-sources.md
```

Key workflow constraints from those sources:

- WSL2 is the only WSL baseline for this provider direction; WSL1 remains
  unsupported.
- systemd must be verified for daemon-managed LXD/Incus behavior in WSL.
- LXD installation uses Snap and requires `snapd`.
- local LXD access requires root or membership in the `lxd` group.
- LXD can be initialized with `lxd init --minimal` for a default local setup.
- Docker-in-container requires explicit nesting/profile configuration.
- privileged containers are not accepted as a silent default.
- WSL2 LXD/Incus success must be validated from a real WSL2 environment, not
  inferred from native Linux or sandbox evidence.

## Execution Profile

```text
executionProfile=FULL_PATH
reason=The request changes provider architecture, platform runtime behavior,
deployment assumptions, workflow structure, documentation governance, and
quality-sensitive live infrastructure boundaries.
requiredFullReviews=Senior Requirement Engineer, Senior System Architect,
Senior Python Automation Developer, Senior Tester, Senior Workflow Architect
allowedImpactChecks=Senior React Frontend Developer as N/A browser frontend
guard
requiredQualityChecks=git diff --check for workflow creation; targeted Python
tests and python3 tools/quality_gate.py quality during implementation slices
stopConditions=branch mismatch, missing provider decision, unclear
architecture ownership, live command requirement without approval, or planned
behavior documented as implemented behavior
```

## Five-Role Review Summary

| Role | Decision | Workflow impact |
| --- | --- | --- |
| Senior Requirement Engineer | `PROCEED_WITH_ACCEPTED_ASSUMPTIONS` | Requirement is clear enough for workflow creation after recording LXD/Incus backend preference and WSL2 capability assumptions. |
| Senior System Architect | `PROCEED_WITH_ACCEPTED_ASSUMPTIONS` | Requires ADR/arc42 synchronization and provider-neutral Platform boundary without new undeclared application service directories. |
| Senior Python Automation Developer | `PROCEED_WITH_ACCEPTED_ASSUMPTIONS` | Requires ports-first provider abstraction, mocked LXD/Incus tests, structured YAML, and composition-root wiring. |
| Senior React Frontend Developer | `READY_FOR_WORKFLOW` as N/A guard | No browser frontend scope. Console/status wording only. |
| Senior Tester | `PROCEED_WITH_ACCEPTED_ASSUMPTIONS` | Requires regression-first tests for provider selection, LXD/Incus readiness, fail-closed setup, and Multipass explicit fallback. |

Dependency/deadlock validation:

```text
Provider decision and domain model must precede adapter and setup integration.
LXD/Incus adapter work and Multipass legacy wrapping may proceed in parallel
after the provider port contract is stable. Documentation may draft early but
must not claim implemented behavior before implementation slices pass.
No cyclic slice dependency detected.
```

Mandatory EPIC question:

```text
Does the implementation still match the EPIC?
```

Current answer:

```text
PARTIALLY, WITH PLANNED PROVIDER DRIFT.
```

The autonomous runnable setup EPIC currently names Multipass as the platform
state provider. This workflow intentionally changes that provider direction.
Slice 01 must record the architecture decision and update EPIC/arc42 references
before implementation slices claim the new baseline.

## Architecture Constraints

- Preserve hexagonal architecture.
- Domain code must remain independent from application and infrastructure.
- Application services may orchestrate provider ports and domain objects, but
  must not embed subprocess, filesystem, socket, Docker, LXD, Incus, raw LXC,
  curses, YAML parser, or host-networking details directly.
- Infrastructure adapters own LXD/Incus CLI calls, sockets, filesystem probes,
  profile inspection, command timeouts, Docker CLI calls, and legacy Multipass
  subprocess details.
- Keep standard runtime wiring in
  `src/tiny_swarm_world/infrastructure/composition.py`.
- Keep entry-point code thin. CLI parses provider intent, enforces consent, and
  delegates to composed services.
- Do not introduce `application/services/lxc`,
  `application/services/incus`, or `application/services/lxd` unless a slice
  deliberately updates architecture docs and tests. Prefer existing Platform
  service boundaries for provider orchestration.
- Prefer new provider-neutral ports and domain models over extending
  Multipass-specific names as the long-term contract.
- Keep Multipass code as explicit legacy compatibility until replacement
  coverage and docs are verified.
- Do not execute direct `infra/swarm` scripts.
- Do not make raw LXC low-level commands such as `lxc-start`, `lxc-create`, or
  `lxc-attach` the default provider surface in the first implementation.

## Python Automation Assessment

Implementation should introduce a provider-neutral layer while keeping changes
small:

- `NodeProviderKind` or equivalent domain value object with
  `lxc_native`, `multipass_legacy`, and `unsupported`.
- `ManagedLxcBackend` or equivalent value object for `incus` and `lxd`.
- `NodeSpec`, `NodeRole`, `NodeState`, `ProviderReadiness`, and
  `ProviderSelection` domain concepts that do not import infrastructure.
- Application ports for provider detection, readiness, node lifecycle, command
  execution inside a node, and provider-specific verification.
- Infrastructure adapters for Incus CLI and LXD CLI using argument-list
  subprocess APIs where new code bypasses shell-oriented legacy command
  templates.
- Structured YAML configuration under `infra/config` for provider defaults,
  node profiles, container images, resource settings, and verification
  metadata.
- Composition-root provider selection so `setup run` and platform workflows use
  the same selected provider.
- Legacy Multipass adapters wrapped behind the same provider port only when the
  operator explicitly selects `multipass_legacy`.

## Frontend Assessment

Tiny Swarm World is not a React frontend project. This workflow forbids browser
frontend scope:

- no `package.json`;
- no npm, pnpm, yarn, Vite, Next.js, TypeScript frontend, `.tsx`, or `.jsx`;
- no browser route or browser state work.

Frontend impact is limited to terminal/console status semantics and
operator-readable provider messages.

## Test Strategy

Use regression-first, mocked tests before implementation changes. Live
infrastructure checks are not part of the normal quality gate.

Documentation-only workflow creation gate:

```bash
git diff --check
```

Representative targeted gates for implementation slices:

```bash
PYTHONPATH=src python3 -m unittest tests.domain.node_provider
PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_node_provider_selection
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.preflight.test_lxc_provider_preflight
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_lxc_node_provider
PYTHONPATH=src python3 -m unittest tests.application.services.setup.test_setup_workflow
PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_platform_workflows
PYTHONPATH=src python3 -m unittest tests.test_package_entrypoint
```

Required final quality gate when practical:

```bash
python3 tools/quality_gate.py quality
```

## Resilience Requirements

- Fail closed when provider selection is absent, ambiguous, or unsupported.
- Default LXC-native path must block before mutation when LXD/Incus readiness
  cannot be verified.
- Multipass fallback requires explicit operator selection and must not mask an
  LXD/Incus failure.
- Read-only probes must use timeouts and sanitized classification.
- Host repair, package installation, daemon start/restart, group membership,
  privileged profile enablement, bridge changes, firewall changes, and Docker
  Swarm mutation remain operator-approved live actions.
- Container profile requirements for Docker-in-container must be explicit,
  test-backed where possible, and risk-labeled.
- Evidence must stay summary-oriented and redacted.
- WSL2 capability must be validated separately from native Linux and sandbox
  evidence.

## Ordered Slices

### Slice 01: Provider Decision And Governance Baseline

Purpose: record the architecture decision, requirement drift, and documentation
authority for making LXC-native through LXD/Incus the default node provider.

```yaml
slice_id: "01"
profile: "architecture-documentation"
owner: "Senior Requirement Engineer"
secondary_reviewers:
  - "Senior System Architect"
  - "Senior Documentation Engineer"
  - "Senior Tester"
affected_files:
  - "documentation/architecture/adr-lxc-native-node-provider.adoc"
  - "documentation/epics/autonomous-runnable-setup.md"
  - "documentation/epics/system-unification.md"
  - "documentation/arc42/02_constraints.adoc"
  - "documentation/arc42/06_runtime_view.adoc"
  - "documentation/arc42/07_deployment_view.adoc"
  - "documentation/arc42/09_architecture_decisions.adoc"
  - "documentation/arc42/11_risks_and_debt.adoc"
  - "documentation/workflow/workflow.md"
  - "documentation/workflow/context-pack.md"
  - "documentation/workflow/context-pack.json"
affected_modules: []
affected_contracts:
  - "provider architecture decision"
  - "autonomous setup provider baseline"
  - "external WSL/LXD/Incus source baseline"
dependencies: []
parallel_group: "A"
file_locks:
  - "documentation/architecture/adr-lxc-native-node-provider.adoc"
  - "documentation/epics/autonomous-runnable-setup.md"
  - "documentation/epics/system-unification.md"
  - "documentation/arc42/09_architecture_decisions.adoc"
  - "documentation/arc42/**"
  - "documentation/workflow/workflow.md"
  - "documentation/workflow/context-pack.md"
  - "documentation/workflow/context-pack.json"
contract_locks:
  - "default provider changes only after ADR is recorded"
architecture_locks:
  - "Linux/WSL-only"
  - "Docker Swarm-first"
  - "Python hexagonal architecture"
quality_gates:
  targeted:
    - "git diff --check"
  required:
    - "git diff --check"
documentation:
  arc42: "update provider baseline and risk/debt sections"
  adr: "create ADR for LXC-native provider default and Multipass legacy fallback"
stop_conditions:
  - "EPIC and ADR disagree on default provider"
  - "documentation claims live LXD/Incus setup before implementation exists"
  - "WSL2 support is claimed without external-source-backed capability gates"
```

Done criteria:

- ADR records `lxc_native` through LXD/Incus as the default path.
- Multipass is documented as explicit legacy/fallback only.
- EPIC drift is resolved or explicitly tracked.
- External WSL/LXD/Incus documentation baseline is referenced by the ADR or
  architecture notes.

### Slice 02: Provider-Neutral Domain Model

Purpose: add provider-neutral node and readiness concepts without importing
application or infrastructure concerns.

```yaml
slice_id: "02"
profile: "implementation"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "src/tiny_swarm_world/domain/node_provider/**"
  - "src/tiny_swarm_world/domain/preflight/**"
  - "tests/domain/node_provider/**"
  - "tests/domain/preflight/**"
affected_modules:
  - "tiny_swarm_world.domain.node_provider"
  - "tiny_swarm_world.domain.preflight"
affected_contracts:
  - "node provider kind"
  - "managed LXC backend"
  - "provider readiness"
  - "node spec and role"
dependencies:
  - "01"
parallel_group: "B"
file_locks:
  - "src/tiny_swarm_world/domain/node_provider/**"
  - "src/tiny_swarm_world/domain/preflight/**"
  - "tests/domain/node_provider/**"
  - "tests/domain/preflight/**"
contract_locks:
  - "domain has no application or infrastructure imports"
architecture_locks:
  - "hexagonal domain independence"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.domain.node_provider tests.domain.preflight"
  required:
    - "python3 tools/quality_gate.py arch-tests"
documentation:
  arc42: "update if new provider concepts become architecture-visible"
  adr: "must satisfy provider ADR from Slice 01"
stop_conditions:
  - "domain imports application or infrastructure"
  - "provider model silently maps failed LXC-native readiness to Multipass"
```

Done criteria:

- Domain model represents `lxc_native`, `multipass_legacy`, and unsupported
  outcomes.
- Managed backend model distinguishes `incus`, `lxd`, ambiguous, missing, and
  unsupported states.
- Tests cover selection and failure classification without live commands.

### Slice 03: Provider Ports And Selection Contract

Purpose: define application ports and Platform-level provider selection while
keeping low-level details out of application services.

```yaml
slice_id: "03"
profile: "implementation"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "src/tiny_swarm_world/application/ports/node_provider/**"
  - "src/tiny_swarm_world/application/ports/preflight/**"
  - "src/tiny_swarm_world/application/services/platform/**"
  - "tests/application/services/platform/test_node_provider_selection.py"
affected_modules:
  - "tiny_swarm_world.application.ports.node_provider"
  - "tiny_swarm_world.application.ports.preflight"
  - "tiny_swarm_world.application.services.platform"
affected_contracts:
  - "provider selection"
  - "provider readiness port"
  - "node lifecycle port"
dependencies:
  - "02"
parallel_group: "C"
file_locks:
  - "src/tiny_swarm_world/application/ports/node_provider/**"
  - "src/tiny_swarm_world/application/ports/preflight/**"
  - "src/tiny_swarm_world/application/services/platform/**"
  - "tests/application/services/platform/test_node_provider_selection.py"
contract_locks:
  - "application depends on provider ports, not concrete LXD/Incus adapters"
architecture_locks:
  - "no new undeclared application service directory"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_node_provider_selection"
  required:
    - "python3 tools/quality_gate.py arch-tests"
documentation:
  arc42: "record provider selection in runtime view"
  adr: "provider ADR checked"
stop_conditions:
  - "application service imports infrastructure"
  - "selection contract allows silent automatic Multipass fallback"
```

Done criteria:

- Provider selection priority is explicit.
- Ambiguous Incus/LXD detection blocks with remediation.
- Multipass legacy requires explicit selection.

### Slice 04: LXD/Incus Readiness Preflight Adapter

Purpose: add non-mutating readiness probes for managed LXC backends.

```yaml
slice_id: "04"
profile: "implementation"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Tester"
  - "Senior Security/Sandbox Engineer"
  - "Senior System Architect"
affected_files:
  - "src/tiny_swarm_world/infrastructure/adapters/preflight/**"
  - "tests/infrastructure/adapters/preflight/test_lxc_provider_preflight.py"
affected_modules:
  - "tiny_swarm_world.infrastructure.adapters.preflight"
affected_contracts:
  - "LXD readiness"
  - "Incus readiness"
  - "provider capability report"
  - "WSL2 systemd and daemon capability gate"
dependencies:
  - "03"
parallel_group: "D1"
file_locks:
  - "src/tiny_swarm_world/infrastructure/adapters/preflight/**"
  - "tests/infrastructure/adapters/preflight/test_lxc_provider_preflight.py"
contract_locks:
  - "read-only probes only"
  - "sanitized readiness evidence"
architecture_locks:
  - "infrastructure owns subprocess, socket, filesystem, and daemon probes"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.preflight.test_lxc_provider_preflight"
  required:
    - "python3 tools/quality_gate.py test"
documentation:
  arc42: "runtime view must distinguish static and live provider readiness"
  adr: "new ADR required before host repair is automated"
stop_conditions:
  - "probe starts, creates, deletes, or modifies containers"
  - "probe persists raw command output or host-specific paths"
  - "WSL2 LXD/Incus readiness is inferred from sandbox or native Linux"
  - "systemd or provider daemon access is assumed on WSL2 without verification"
```

Done criteria:

- Tests mock executable availability, version/info commands, timeout, daemon
  unavailable, permission denied, ambiguous backends, and missing backend.
- Reports are summary-only and actionable.
- WSL2 reports distinguish WSL version, systemd readiness, provider daemon
  access, and unsupported capability states.

### Slice 05: LXC-Native Provider Configuration

Purpose: add structured provider configuration for node specs, profiles, and
verification metadata.

```yaml
slice_id: "05"
profile: "configuration"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior DevOps Engineer"
  - "Senior Security/Sandbox Engineer"
  - "Senior Tester"
affected_files:
  - "infra/config/node-providers/**"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/**"
  - "tests/infrastructure/adapters/repositories/**"
affected_modules:
  - "tiny_swarm_world.infrastructure.adapters.repositories"
affected_contracts:
  - "provider configuration repository"
  - "LXD/Incus node profile configuration"
dependencies:
  - "02"
parallel_group: "D2"
file_locks:
  - "infra/config/node-providers/**"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/**"
  - "tests/infrastructure/adapters/repositories/**"
contract_locks:
  - "structured YAML only"
  - "no host-specific absolute paths or IP addresses"
architecture_locks:
  - "infra/config is product behavior"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories"
  required:
    - "python3 tools/quality_gate.py test"
documentation:
  arc42: "deployment view must describe committed provider config"
  adr: "provider ADR checked"
stop_conditions:
  - "configuration embeds host IPs, usernames, secrets, or local paths"
  - "privileged container profile is enabled without explicit risk contract"
```

Done criteria:

- Provider config defines default `lxc_native` family and explicit legacy
  Multipass fallback.
- LXD/Incus profile requirements are named and risk-labeled.
- YAML parsing uses existing structured helpers or equivalent repository
  adapters.

### Slice 06: LXD/Incus Node Lifecycle Adapter

Purpose: implement the managed LXC node lifecycle behind provider ports.

```yaml
slice_id: "06"
profile: "implementation"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior System Architect"
  - "Senior Tester"
  - "Senior DevOps Engineer"
  - "Senior Security/Sandbox Engineer"
affected_files:
  - "src/tiny_swarm_world/infrastructure/adapters/clients/**"
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "tests/infrastructure/adapters/clients/test_lxc_node_provider.py"
  - "tests/infrastructure/test_composition.py"
affected_modules:
  - "tiny_swarm_world.infrastructure.adapters.clients"
  - "tiny_swarm_world.infrastructure.composition"
affected_contracts:
  - "node lifecycle provider"
  - "provider command timeout and result mapping"
dependencies:
  - "03"
  - "04"
  - "05"
parallel_group: "E1"
file_locks:
  - "src/tiny_swarm_world/infrastructure/adapters/clients/**"
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "tests/infrastructure/adapters/clients/test_lxc_node_provider.py"
  - "tests/infrastructure/test_composition.py"
contract_locks:
  - "no live commands in tests"
  - "destructive operations remain guarded"
architecture_locks:
  - "composition root owns concrete adapter construction"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_lxc_node_provider tests.infrastructure.test_composition"
  required:
    - "python3 tools/quality_gate.py arch-tests"
documentation:
  arc42: "runtime and deployment views updated in documentation slice"
  adr: "new ADR required before automatic host repair or privileged default"
stop_conditions:
  - "adapter mutates containers during tests"
  - "shell=True is introduced for new provider commands"
  - "raw command output is persisted as verification evidence"
```

Done criteria:

- Adapter maps Incus and LXD commands through one provider port.
- Apply/verify semantics distinguish created, already present, blocked,
  failed-to-apply, and failed-to-verify.
- Tests use fakes and do not require LXD, Incus, Docker, or Multipass.

### Slice 07: Docker Swarm-In-LXC Contract

Purpose: define and test the minimum container profile and verification model
required to run Docker Swarm nodes inside LXD/Incus containers.

```yaml
slice_id: "07"
profile: "implementation"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior DevOps Engineer"
  - "Senior Security/Sandbox Engineer"
  - "Senior Tester"
affected_files:
  - "src/tiny_swarm_world/domain/node_provider/**"
  - "src/tiny_swarm_world/domain/network/**"
  - "src/tiny_swarm_world/application/services/platform/**"
  - "tests/domain/node_provider/**"
  - "tests/domain/network/**"
  - "tests/application/services/platform/**"
affected_modules:
  - "tiny_swarm_world.domain.node_provider"
  - "tiny_swarm_world.domain.network"
  - "tiny_swarm_world.application.services.platform"
affected_contracts:
  - "Docker-in-container profile"
  - "Swarm node readiness"
  - "container network plan"
dependencies:
  - "06"
parallel_group: "F"
file_locks:
  - "src/tiny_swarm_world/domain/node_provider/**"
  - "src/tiny_swarm_world/domain/network/**"
  - "src/tiny_swarm_world/application/services/platform/**"
  - "tests/domain/node_provider/**"
  - "tests/domain/network/**"
  - "tests/application/services/platform/**"
contract_locks:
  - "profile requirements are explicit and risk-labeled"
  - "no host network mutation without approval"
architecture_locks:
  - "application orchestrates ports; infrastructure owns provider details"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.domain.node_provider tests.domain.network tests.application.services.platform"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "quality and risk views must reflect Docker-in-LXC constraints"
  adr: "new ADR required if privileged containers become default"
stop_conditions:
  - "privileged profile is silently enabled"
  - "host bridge or firewall mutation is automated without approval"
  - "Docker Swarm health is claimed without observed-state evidence"
  - "Docker-in-container nesting requirements are hidden in adapter defaults"
```

Done criteria:

- Required profile capabilities are modeled and validated before node creation.
- Security-sensitive profile choices are visible in setup output and evidence.
- Network plan contains no committed host-specific addresses.
- Privileged container mode is risk-labeled and never the silent default.

### Slice 08: Platform And Setup Integration

Purpose: make setup and platform workflows use the selected provider by default.

```yaml
slice_id: "08"
profile: "implementation"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior System Architect"
  - "Senior Tester"
  - "Console/status UI reviewer"
affected_files:
  - "src/tiny_swarm_world/application/services/setup/**"
  - "src/tiny_swarm_world/application/services/platform/**"
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "src/tiny_swarm_world/__main__.py"
  - "tests/application/services/setup/test_setup_workflow.py"
  - "tests/application/services/platform/test_platform_workflows.py"
  - "tests/test_package_entrypoint.py"
affected_modules:
  - "tiny_swarm_world.application.services.setup"
  - "tiny_swarm_world.application.services.platform"
  - "tiny_swarm_world.infrastructure.composition"
affected_contracts:
  - "setup provider selection"
  - "platform init provider guard"
  - "CLI provider option"
dependencies:
  - "06"
  - "07"
parallel_group: "G"
file_locks:
  - "src/tiny_swarm_world/application/services/setup/**"
  - "src/tiny_swarm_world/application/services/platform/**"
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "src/tiny_swarm_world/__main__.py"
  - "tests/application/services/setup/test_setup_workflow.py"
  - "tests/application/services/platform/test_platform_workflows.py"
  - "tests/test_package_entrypoint.py"
contract_locks:
  - "missing live consent refuses before mutation"
  - "failed provider preflight marks downstream phases not_run"
architecture_locks:
  - "entry point remains thin"
  - "composition root owns adapter construction"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.application.services.setup.test_setup_workflow tests.application.services.platform.test_platform_workflows tests.test_package_entrypoint"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "runtime view updated after implementation"
  adr: "provider ADR checked"
stop_conditions:
  - "setup still prints Multipass as the default target"
  - "platform init can bypass provider readiness"
  - "setup run auto-falls back to Multipass after LXC-native failure"
```

Done criteria:

- CLI and setup summary name LXC-native as the default target.
- Provider preflight failure stops platform mutation and marks later phases
  `not_run`.
- Tests cover explicit Multipass legacy selection separately.

### Slice 09: Multipass Legacy/Fallback Boundary

Purpose: wrap existing Multipass behavior behind an explicit legacy provider
and stop treating it as the default repair path.

```yaml
slice_id: "09"
profile: "implementation"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior System Architect"
  - "Senior Tester"
  - "Senior Documentation Engineer"
affected_files:
  - "src/tiny_swarm_world/domain/multipass/**"
  - "src/tiny_swarm_world/application/services/multipass/**"
  - "src/tiny_swarm_world/infrastructure/adapters/clients/multipass_*.py"
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "src/tiny_swarm_world/__main__.py"
  - "infra/config/multipass/**"
  - "infra/config/docker/command_multipass_*.yaml"
  - "tests/application/services/multipass/**"
  - "tests/infrastructure/adapters/clients/test_multipass_*.py"
  - "tests/infrastructure/test_composition.py"
  - "tests/test_package_entrypoint.py"
affected_modules:
  - "tiny_swarm_world.domain.multipass"
  - "tiny_swarm_world.application.services.multipass"
  - "tiny_swarm_world.infrastructure.adapters.clients"
  - "tiny_swarm_world.infrastructure.composition"
affected_contracts:
  - "multipass legacy provider"
  - "legacy fallback selection"
  - "standalone artifact and deployment provider guard"
dependencies:
  - "03"
  - "08"
parallel_group: "E2"
file_locks:
  - "src/tiny_swarm_world/domain/multipass/**"
  - "src/tiny_swarm_world/application/services/multipass/**"
  - "src/tiny_swarm_world/infrastructure/adapters/clients/multipass_*.py"
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "src/tiny_swarm_world/__main__.py"
  - "infra/config/multipass/**"
  - "infra/config/docker/command_multipass_*.yaml"
  - "tests/application/services/multipass/**"
  - "tests/infrastructure/adapters/clients/test_multipass_*.py"
  - "tests/infrastructure/test_composition.py"
  - "tests/test_package_entrypoint.py"
contract_locks:
  - "Multipass legacy must be explicit"
  - "destructive Multipass cleanup remains guarded"
  - "default artifact/deployment workflows must not construct Multipass clients"
architecture_locks:
  - "legacy adapter remains infrastructure-owned"
  - "entry point remains thin"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.application.services.multipass tests.infrastructure.adapters.clients.test_multipass_swarm_runtime tests.infrastructure.adapters.clients.test_multipass_container_image_publisher tests.infrastructure.adapters.clients.test_multipass_portainer_admin_client tests.infrastructure.test_composition tests.test_package_entrypoint tests.application.services.platform.test_node_provider_selection tests.infrastructure.adapters.repositories.test_node_provider_config_yaml_repository"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "deployment view demotes Multipass in Slice 10 documentation sync"
  adr: "provider ADR checked"
stop_conditions:
  - "Multipass remains default provider"
  - "Multipass repair work expands instead of being isolated"
  - "legacy fallback runs without explicit provider selection"
  - "default artifact or deployment workflows construct Multipass clients"
```

Done criteria:

- Existing Multipass behavior remains test-covered but is no longer default.
- Fallback selection is explicit and operator-visible.
- CLI warnings identify Multipass as legacy/fallback for explicit selection.
- General documentation updates remain deferred to Slice 10.

### Slice 10: Documentation And Governance Synchronization

Purpose: align operator docs, root governance, live-operation catalog, and
arc42 with implemented provider behavior.

```yaml
slice_id: "10"
profile: "documentation"
owner: "Senior Documentation Engineer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "AGENTS.md"
  - "README.md"
  - "documentation/system/multipass-setup.adoc"
  - "documentation/system/lxc-native-setup.adoc"
  - "documentation/system/network.adoc"
  - "documentation/system/live-operation-surfaces.adoc"
  - "documentation/user_guide/installation.adoc"
  - "documentation/user_guide/troubleshooting.adoc"
  - "documentation/deployment/system.adoc"
  - "documentation/arc42/**"
  - "documentation/architecture/adr-lxc-native-node-provider.adoc"
affected_modules: []
affected_contracts:
  - "operator documentation"
  - "governance product identity"
  - "arc42 runtime and deployment views"
dependencies:
  - "08"
  - "09"
parallel_group: "H"
file_locks:
  - "AGENTS.md"
  - "README.md"
  - "documentation/system/**"
  - "documentation/user_guide/**"
  - "documentation/deployment/**"
  - "documentation/arc42/**"
  - "documentation/architecture/adr-lxc-native-node-provider.adoc"
contract_locks:
  - "planned behavior is not documented as implemented behavior"
architecture_locks:
  - "Linux/WSL-only and Docker Swarm-first wording preserved"
quality_gates:
  targeted:
    - "git diff --check"
  required:
    - "git diff --check"
documentation:
  arc42: "update 02, 06, 07, 10, 11 at minimum when behavior changes"
  adr: "provider ADR checked and indexed if ADR index exists"
stop_conditions:
  - "docs claim full LXD/Incus live success without evidence"
  - "docs remove Multipass before legacy fallback is verified"
  - "Windows-native automation is documented as default product behavior"
```

Done criteria:

- Docs name LXC-native through LXD/Incus as the default after implementation.
- Multipass docs are retained as legacy/fallback guidance only.
- Root governance no longer presents Multipass VMs as the primary identity
  once the implementation has changed.

### Slice 11: Quality And Live Validation Matrix

Purpose: run final mocked/static gates and define optional operator live smoke
evidence for native Linux and WSL2.

```yaml
slice_id: "11"
profile: "verification"
owner: "Senior Tester"
secondary_reviewers:
  - "Senior DevOps Engineer"
  - "Senior Security/Sandbox Engineer"
  - "Senior Documentation Engineer"
  - "Senior System Architect"
affected_files:
  - ".tiny-swarm-world/evidence/provider-validation/**"
  - "documentation/workflow/execution-report.md"
affected_modules: []
affected_contracts:
  - "QUALITY.md gate evidence"
  - "provider live smoke evidence"
dependencies:
  - "10"
parallel_group: "I"
file_locks:
  - "documentation/workflow/execution-report.md"
contract_locks:
  - "live infrastructure requires explicit operator approval"
  - "local evidence remains ignored"
architecture_locks:
  - "sandbox evidence cannot prove native Linux or WSL2 LXD/Incus behavior"
quality_gates:
  targeted:
    - "git diff --check"
    - "python3 tools/quality_gate.py lint"
    - "python3 tools/quality_gate.py arch-lint"
    - "python3 tools/quality_gate.py arch-tests"
    - "python3 tools/quality_gate.py typecheck"
    - "python3 tools/quality_gate.py test"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "checked after final behavior"
  adr: "checked after final behavior"
stop_conditions:
  - "live commands would run without explicit operator approval"
  - "WSL2 success is inferred from native Linux or sandbox"
  - "local evidence contains secrets, raw output, usernames, host paths, or IPs in committed files"
```

Done criteria:

- `python3 tools/quality_gate.py quality` passes or failures are routed through
  the Typed Error Router.
- Optional live smoke outcomes are recorded separately for native Linux,
  WSL2, and legacy Multipass fallback when approved.
- Final report states whether LXC-native is default and Multipass is fallback.

## Dependency Graph

```text
01
 |
02
 |
03
 |\
 | +-> 04 -> 06 -> 07 -> 08 -> 10 -> 11
 |       \         \         /
 |        +-> 05 ---+       /
 |                  \      /
 +-----------------> 09 --+
```

Parallelization:

- Slice 04 and Slice 05 may run in parallel after Slice 03 if file locks stay
  disjoint.
- Slice 09 may begin after Slice 03 but must not change default behavior until
  Slice 08 defines the new setup integration.
- Documentation drafting may start after Slice 01, but Slice 10 must not claim
  implemented behavior before implementation slices pass.

## Role Ownership Map

| Concern | Owner | Secondary review |
| --- | --- | --- |
| Workflow dependency ordering | Senior Workflow Architect | Senior Swarm Orchestrator |
| Requirement and EPIC drift | Senior Requirement Engineer | Engineering Governance |
| Architecture boundaries and arc42 | Senior System Architect | arc42 governance |
| Python provider implementation | Senior Python Automation Developer | Senior Tester |
| LXD/Incus and Docker-in-container safety | Senior DevOps Engineer | Security/Sandbox Engineer |
| Console/status output semantics | Console/status UI skills | Senior React Frontend Developer as N/A React guard |
| Test strategy and gates | Senior Tester | Quality Gate Orchestrator |
| Documentation synchronization | Senior Documentation Engineer | Senior System Architect |
| Git/commit readiness | Git commit preparation skills | Git commit reviewer |

Only one implementation worker may modify files in a slice at a time. Read-only
review subagents may run in parallel. Write scopes must remain disjoint before
parallel implementation is authorized.

## Quality Gate Expectations

Verified commands from `QUALITY.md`:

```bash
git diff --check
python3 tools/quality_gate.py lint
python3 tools/quality_gate.py arch-lint
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py typecheck
python3 tools/quality_gate.py test
python3 tools/quality_gate.py quality
```

Do not invent frontend, Java, Maven, Gradle, JUnit, ArchUnit, mutation testing,
Docker, LXD, Incus, Multipass, or deployment CI commands as default gates.

## Optional Live Validation Boundary

Default static preflight remains non-mutating:

```bash
PYTHONPATH=src python3 -m tiny_swarm_world --preflight
```

After implementation, static preflight may classify provider configuration and
host capability. It must not be treated as proof that LXD/Incus containers,
Docker-in-container, Docker Swarm, Portainer, Nexus, Jenkins, RabbitMQ,
SonarQube, or Swagger/NGINX work live.

Operator-approved live validation commands may be run only after explicit
approval in a disposable or recoverable environment:

```bash
PYTHONPATH=src python3 -m tiny_swarm_world setup run --live
```

Expected live validation result classes:

- `PASSED_LXC_NATIVE_FULL_INSTALLATION`
- `BLOCKED_LXC_BACKEND_PREREQUISITE`
- `BLOCKED_CONTAINER_PROFILE_PREREQUISITE`
- `BLOCKED_WSL2_CAPABILITY_MISSING`
- `PASSED_MULTIPASS_LEGACY_FALLBACK`
- `FAILED`
- `NOT_RUN`

Evidence paths are local and ignored:

```text
.tiny-swarm-world/evidence/provider-validation/native-linux/
.tiny-swarm-world/evidence/provider-validation/wsl2/
.tiny-swarm-world/evidence/provider-validation/multipass-legacy/
.tiny-swarm-world/evidence/provider-validation/comparison-report.md
```

Committed reports may summarize sanitized status only.

## Documentation Synchronization Points

Update documentation only when behavior is implemented or clearly marked as
planned workflow behavior:

- `AGENTS.md`
- `README.md`
- `documentation/architecture/adr-lxc-native-node-provider.adoc`
- `documentation/epics/autonomous-runnable-setup.md`
- `documentation/epics/system-unification.md`
- `documentation/system/lxc-native-setup.adoc`
- `documentation/system/multipass-setup.adoc`
- `documentation/system/network.adoc`
- `documentation/system/live-operation-surfaces.adoc`
- `documentation/user_guide/installation.adoc`
- `documentation/user_guide/troubleshooting.adoc`
- `documentation/deployment/system.adoc`
- `documentation/arc42/02_constraints.adoc`
- `documentation/arc42/06_runtime_view.adoc`
- `documentation/arc42/07_deployment_view.adoc`
- `documentation/arc42/10_quality_requirements.adoc`
- `documentation/arc42/11_risks_and_debt.adoc`

## Stop Conditions

Stop and report if:

- active branch is not `feature/workflow-lxc-node-provider-20260526`;
- workflow slice metadata or locks are missing;
- implementation would touch files outside the active slice scope;
- raw low-level LXC becomes the first implementation path;
- direct `infra/swarm` scripts would be executed or promoted;
- live infrastructure commands would run without explicit operator approval;
- LXD/Incus readiness would be inferred from sandbox evidence;
- Multipass fallback would be automatic or silent;
- privileged container profiles, host network changes, daemon repairs, package
  installs, or permission changes would be automated without explicit approval
  and any required ADR;
- raw command strings, stdout, stderr, environment payloads, tokens, passwords,
  Swarm join tokens, usernames, host paths, or host-specific IPs would be
  committed or persisted in unsafe evidence;
- architecture tests would need to be weakened;
- planned behavior would be documented as implemented behavior.

## Definition Of Done

- `documentation/workflow/workflow.md` contains complete slice metadata and is
  consistent with `AGENTS.md`, `QUALITY.md`, EPICs, ADRs, and arc42.
- Provider ADR and EPIC baseline make LXC-native through LXD/Incus the
  accepted default direction.
- Provider-neutral domain and port contracts exist and are tested.
- LXD/Incus readiness is non-mutating, timeout-bound, and sanitized.
- Default setup/platform selection uses `lxc_native` and blocks on missing or
  ambiguous backend readiness.
- Multipass is available only as explicit legacy/fallback.
- Docker Swarm-in-LXC profile and network requirements are explicit and
  security-reviewed.
- Documentation is synchronized without overclaiming live success.
- `python3 tools/quality_gate.py quality` passes or any failure is routed
  through the Typed Error Router.
- Native Linux, WSL2, and Multipass legacy live validation evidence are
  recorded separately when operator approval is granted.

## Commit And Push Plan

Suggested commit message after implementation and verification:

```text
feat: make LXC native provider the default platform path
```

Do not push or create a pull request during slice checkpoints unless the user
explicitly asks for that action.

## Handoff To Workflow Execute

Before `workflow execute`:

1. Verify branch:

```bash
git show-ref --verify --quiet refs/heads/feature/workflow-lxc-node-provider-20260526
git branch --show-current
```

2. Verify no unrelated local changes.
3. Re-read `AGENTS.md`, `QUALITY.md`, this workflow, and
   `documentation/workflow/context-pack.md`.
4. Use S3/S3D workflow-execute preflight.
5. Execute slices in dependency order.
6. Run targeted checks first, then required gates.
7. Route failures through the Typed Error Router before retrying.

## arc42 Check Status

arc42 was checked during workflow creation. No arc42 file was changed during
workflow authoring because this is a plan, not implementation. Slice 01 and
Slice 10 must update arc42 once the provider decision and implementation
behavior are recorded.
