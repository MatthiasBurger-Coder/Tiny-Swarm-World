# Workflow: Linux/WSL-Aware Swarm Setup Migration

## Executive Summary

This workflow replaces the previous `Stable Live Setup` active workflow with a
governed implementation plan for separating Tiny Swarm World setup behavior into
explicit Native Linux, WSL2, WSL1-unsupported, unknown-unsupported, and
sandbox-unverified paths.

The user-provided source draft targets the observed failure shape:

```text
preflight: passed
platform init: failed_to_apply
reason: CommandExecutionFailed
```

The executable workflow must refine that draft against the current repository
baseline. Current source already contains live-consent-gated Multipass runtime
checks, so this workflow does not create a parallel preflight system. It extends
the existing preflight, setup, platform, Multipass, network, evidence, and
documentation boundaries.

Target outcome:

```text
broken host or WSL2 Multipass readiness:
  preflight: failed
  platform init: not_run
  reason: host, Multipass, driver, socket, systemd, snapd, or network readiness

supported and ready Native Linux:
  selected setup path: native_linux
  setup proceeds only after explicit live consent

supported and ready WSL2:
  selected setup path: wsl2
  setup proceeds only after explicit live consent and WSL2-specific checks

sandbox:
  selected setup path: sandbox_unverified
  static and mocked validation allowed
  WSL2 correctness is never inferred from sandbox success
```

No live infrastructure command is part of workflow creation, unit tests, static
checks, or the normal quality gate.

## Target Picture

### Verified Baseline

- Active workflow version: `linux-wsl-swarm-setup-v1.0.0`.
- Active workflow branch:

```bash
fix/linux-wsl-swarm-setup-workprocess-20260525
```

- Root `AGENTS.md` defines Tiny Swarm World as Linux/WSL-only, Python
  automation, hexagonal architecture, and Docker Swarm-first.
- Root `QUALITY.md` defines the authoritative quality gate:

```bash
python3 tools/quality_gate.py quality
```

- Existing active workflow artifacts were regenerated because they described
  the older `Stable Live Setup` workflow.
- `documentation/epics/autonomous-runnable-setup.md` remains the requirement
  baseline for canonical setup.
- `documentation/architecture/adr-autonomous-setup-safety.adoc` accepts the
  fail-closed, live-consent-gated setup contract.
- Current implementation evidence:
  - `PreflightService._host_check` still reports generic Linux/WSL compatibility.
  - `HostPreflightProbe.is_linux_or_wsl` currently checks only
    `platform.system() == "linux"`.
  - live preflight already has a Multipass runtime readiness path for list and
    driver probes; the workflow must extend it rather than duplicate it.
  - setup orchestration refuses missing live consent before setup phases run.
  - setup phase result safety rejects raw command, stdout, stderr, environment,
    token, password, and secret keys.

### Target Outcome

After workflow execution, Tiny Swarm World should provide:

- typed host environment classification with evidence and remediation;
- typed Multipass readiness classification including version, list, driver,
  daemon, socket, permission, timeout, and remediation state;
- typed WSL2 network and port-forwarding planning without committed IPs;
- explicit Native Linux and WSL2 setup path selection before VM creation;
- WSL1 and unknown host environments blocked before platform mutation;
- sandbox/unverified Linux reported as non-live proof only;
- regression-first tests for the observed false-positive failure;
- sanitized evidence and diagnostics that preserve current redaction rules;
- documentation that keeps `infra/swarm` as legacy evidence, not an executable
  product workflow;
- separate operator-approved live validation for sandbox and real WSL2 console.

## Requirement Clarification Record

Original request:

```text
workflow create with subagents
```

Interpreted intent:

```text
Create or regenerate the active Tiny Swarm World workflow from the supplied
Linux/WSL-aware swarm setup draft, using subagents for role review.
```

Change type:

```text
fix / architecture hardening / setup migration / installation validation
```

Affected process strand:

```text
workflow authoring, setup preflight, platform setup, Multipass readiness,
network forwarding, evidence, documentation, quality gates
```

Affected architecture area:

```text
Platform boundary, setup orchestration, preflight domain and ports,
infrastructure preflight adapters, network planning, command diagnostics,
console/status output, documentation and arc42 governance
```

Explicit requirements:

- detect Native Linux, WSL2, WSL1 unsupported, unknown unsupported, and sandbox
  unverified environments;
- block WSL1 and unknown hosts before live mutation;
- stop treating sandbox Linux as proof of WSL2 correctness;
- migrate useful `infra/swarm` knowledge behind typed Python contracts;
- preserve `infra/swarm` as legacy evidence only;
- fail preflight before `platform init` when Multipass is unusable;
- keep separate Native Linux and WSL2 setup paths;
- keep normal tests and quality gates mocked or static;
- require real WSL2 console validation before claiming WSL2 live success.

Implicit requirements:

- reconcile the draft with existing preflight and setup code;
- keep package changes inside existing architecture-test boundaries unless a
  deliberate architecture documentation and test update is included;
- avoid raw command or host evidence persistence;
- avoid new browser React scope;
- keep live remediation commands operator-approved and outside default gates.

Assumptions accepted for workflow creation:

- the supplied draft replaces the older `Stable Live Setup` workflow;
- the active branch remains the branch named in the source draft;
- real WSL2 validation is operator-provided evidence if Codex cannot access the
  real WSL2 console;
- `netsh` remains documentation-only or operator-confirmed troubleshooting, not
  a new Windows-native automation path;
- full live installation success and host-prerequisite blocked outcomes are
  reported separately.

Non-goals:

- no Java, Maven, Spring Boot, Kubernetes-first, browser React, npm, Vite,
  Next.js, TypeScript frontend, or new package-manager tooling;
- no direct promotion of `infra/swarm` scripts as canonical setup entry points;
- no automatic host package installation, socket chmod/chown, driver changes,
  `iptables`, `netsh`, or `socat` mutation without explicit operator approval
  and a later ADR where required;
- no live infrastructure commands during unit tests, architecture checks,
  type checks, docs checks, or normal quality gates;
- no committed host-specific IPs, usernames, absolute paths, tokens, passwords,
  raw stdout, raw stderr, raw environment payloads, or Swarm join tokens.

Risks:

- the source draft described some behavior as absent even though current code
  already has partial live preflight readiness probes;
- new service directories such as `application/services/host` or
  `application/services/swarm` would conflict with current architecture tests;
- the installation matrix can overclaim if static preflight is treated as live
  Multipass readiness;
- live evidence can leak local host details unless redaction is explicit.

Open questions:

- who will run and approve real WSL2 live validation and cleanup;
- whether a later ADR should authorize automatic host preparation or keep it as
  documentation/remediation only.

Blocking questions:

```text
None for workflow authoring. Live execution remains blocked until the
workflow-execute preflight confirms branch, locks, slice metadata, and operator
approval for any live validation phase.
```

Confidence level:

```text
84 percent
```

Decision:

```text
PROCEED_WITH_ACCEPTED_ASSUMPTIONS
```

## Subagent Review Summary

Five mandatory workflow-creation roles reviewed the source draft.

| Role | Decision | Workflow impact |
| --- | --- | --- |
| Senior Requirement Engineer | `PROCEED_WITH_ACCEPTED_ASSUMPTIONS` | Requirement is complete enough after recording replacement, WSL2 operator evidence, and `netsh` assumptions. |
| Senior System Architect | `REQUIRES_REFINEMENT` for the source draft | Refined workflow must reconcile existing preflight code, avoid new forbidden service directories, and tighten evidence redaction. |
| Senior Python Automation Developer | Proceed only after tightening | Refined workflow must extend current preflight rather than create a parallel system. |
| Senior React Frontend Developer | `READY_FOR_WORKFLOW` as N/A guard | No React/browser scope; only console/status output may be affected. |
| Senior Tester | `REQUIRES_REFINEMENT` for the source draft | Refined workflow must add YAML slice metadata, command semantics, targeted tests, and live/static boundary rules. |

The generated workflow incorporates those refinements. The source draft itself
must not be executed directly.

## Architecture Constraints

- Preserve hexagonal architecture.
- Domain code must remain independent from application and infrastructure.
- Application services may orchestrate ports and domain objects, but must not
  embed subprocess, filesystem, Docker, HTTP, curses, YAML parser, or live
  host details directly.
- Infrastructure adapters own `/proc`, environment, filesystem, subprocess,
  Multipass, Docker, `socat`, and host-probing details.
- Keep standard runtime wiring in
  `src/tiny_swarm_world/infrastructure/composition.py`.
- Prefer extending existing package areas:
  - `domain/preflight`
  - `domain/multipass`
  - `domain/network`
  - `application/ports/preflight`
  - `application/services/platform`
  - `application/services/setup`
  - `application/services/network`
  - `infrastructure/adapters/preflight`
  - `infrastructure/adapters/command_runner`
  - `infrastructure/adapters/repositories`
- Do not introduce `application/services/host` or `application/services/swarm`
  unless a slice deliberately updates architecture docs and tests.
- `infra/swarm` is a migration evidence source only. Do not call its scripts.

## Python Automation Assessment

Implementation should extend current contracts:

- `PreflightService` should receive typed host environment and runtime reports.
- `HostPreflightProbe` should be split internally into deterministic, testable
  probes while preserving the public port until compatibility slices update it.
- Multipass readiness should add `version` probing, socket evidence, qemu driver
  checks, and explicit timeout classification while preserving argument-list
  subprocess calls.
- Setup/platform orchestration should convert failed preflight into
  `not_run` downstream phases rather than late `failed_to_apply`.
- Diagnostics must use sanitized classification and excerpts only when allowed
  by the current safe-text contract. Raw `command`, `stdout`, `stderr`,
  `environment`, `token`, `password`, and `secret` keys are forbidden in setup
  phase results and committed artifacts.

## Frontend Assessment

Tiny Swarm World is not a React frontend project. This workflow forbids browser
frontend scope:

- no `package.json`;
- no npm, pnpm, yarn, Vite, Next.js, TypeScript frontend, `.tsx`, or `.jsx`;
- no browser route or browser state work.

Frontend impact is limited to console/status semantics and operator-readable
messages for preflight, setup, remediation, and installation summaries.

## Test Strategy

Use regression-first, mocked tests before implementation changes. Live
infrastructure checks are not part of the normal quality gate.

Targeted tests for implementation slices:

```bash
PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_preflight_service
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.preflight.test_host_preflight_probe
PYTHONPATH=src python3 -m unittest tests.application.services.setup.test_setup_workflow
PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_platform_workflows
PYTHONPATH=src python3 -m unittest tests.test_package_entrypoint
```

Required final quality gate when practical:

```bash
python3 tools/quality_gate.py quality
```

Documentation-only workflow creation gate:

```bash
git diff --check
```

## Resilience Requirements

- Fail closed when the environment cannot be classified.
- WSL1 and unknown environments must stop before `platform init`.
- WSL2 without required systemd, snapd when needed, reachable Multipass daemon,
  qemu driver, socket access, or supported network strategy must stop before
  VM creation.
- Sandbox/unverified Linux may run static and mocked validation only; it cannot
  prove WSL2 live behavior.
- Read-only probes must use timeouts and argument-list subprocess APIs.
- Host repair actions are remediation guidance unless a later ADR and explicit
  operator live consent authorize mutation.
- Evidence must be redacted, summary-oriented, and stored under ignored local
  state.
- Cleanup commands require explicit operator confirmation and must report
  remaining resources when skipped.

## Ordered Slices

### Slice 01: Legacy Swarm Migration Analysis

Purpose: document `infra/swarm` behavior as migration evidence before any
runtime behavior changes.

```yaml
slice_id: "01"
profile: "documentation"
owner: "Senior Documentation Engineer"
secondary_reviewers:
  - "Senior System Architect"
  - "Senior Python Automation Developer"
affected_files:
  - "documentation/architecture/legacy-swarm-setup-migration.md"
affected_modules: []
affected_contracts:
  - "legacy live-operation surface classification"
dependencies: []
parallel_group: "A"
file_locks:
  - "documentation/architecture/legacy-swarm-setup-migration.md"
contract_locks:
  - "infra/swarm remains legacy evidence only"
architecture_locks:
  - "no direct script promotion"
quality_gates:
  targeted:
    - "git diff --check"
  required:
    - "git diff --check"
documentation:
  arc42: "checked; no behavior claim until implementation slices"
  adr: "documentation/architecture/adr-autonomous-setup-safety.adoc checked"
stop_conditions:
  - "legacy scripts would be called or promoted as canonical setup"
  - "host-specific values would be copied into product configuration"
```

Done criteria:

- migration document classifies each required legacy behavior as `MIGRATE`,
  `MIGRATE_WITH_CHANGES`, `DOCUMENT_ONLY`, or `REJECT`;
- direct execution from `infra/swarm` remains forbidden.

### Slice 02: Host Environment Domain Model

Purpose: add typed environment reports and setup path concepts inside existing
domain boundaries.

```yaml
slice_id: "02"
profile: "implementation"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "src/tiny_swarm_world/domain/preflight/**"
  - "src/tiny_swarm_world/domain/multipass/**"
  - "src/tiny_swarm_world/domain/network/**"
  - "tests/domain/preflight/**"
  - "tests/domain/network/**"
affected_modules:
  - "tiny_swarm_world.domain.preflight"
  - "tiny_swarm_world.domain.multipass"
  - "tiny_swarm_world.domain.network"
affected_contracts:
  - "host environment report"
  - "multipass readiness report"
  - "port forwarding plan"
dependencies:
  - "01"
parallel_group: "B"
file_locks:
  - "src/tiny_swarm_world/domain/preflight/**"
  - "src/tiny_swarm_world/domain/multipass/**"
  - "src/tiny_swarm_world/domain/network/**"
contract_locks:
  - "domain has no application or infrastructure imports"
architecture_locks:
  - "hexagonal domain independence"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.domain.preflight tests.domain.network"
  required:
    - "python3 tools/quality_gate.py arch-tests"
documentation:
  arc42: "update if domain concepts become architecture-visible"
  adr: "no new ADR unless evidence semantics change"
stop_conditions:
  - "domain imports application or infrastructure"
  - "host-specific evidence is modeled as committed configuration"
```

Done criteria:

- host environment enum covers `native_linux`, `wsl2`, `wsl1_unsupported`,
  `unknown_unsupported`, and `sandbox_unverified`;
- reports include evidence and remediation without raw host payloads.

### Slice 03: Extend Preflight Ports And Service Contract

Purpose: extend the existing preflight port and service without introducing a
parallel preflight subsystem.

```yaml
slice_id: "03"
profile: "implementation"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "src/tiny_swarm_world/application/ports/preflight/**"
  - "src/tiny_swarm_world/application/services/platform/preflight_service.py"
  - "tests/application/services/platform/test_preflight_service.py"
affected_modules:
  - "tiny_swarm_world.application.ports.preflight"
  - "tiny_swarm_world.application.services.platform"
affected_contracts:
  - "preflight host check"
  - "preflight runtime readiness"
dependencies:
  - "02"
parallel_group: "C"
file_locks:
  - "src/tiny_swarm_world/application/ports/preflight/**"
  - "src/tiny_swarm_world/application/services/platform/preflight_service.py"
contract_locks:
  - "PreflightService remains application orchestration"
architecture_locks:
  - "application services depend on ports, not infrastructure adapters"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_preflight_service"
  required:
    - "python3 tools/quality_gate.py arch-tests"
documentation:
  arc42: "runtime/preflight view must be updated in documentation slice"
  adr: "adr-autonomous-setup-safety must remain satisfied"
stop_conditions:
  - "new preflight service duplicates existing platform preflight behavior"
  - "static --preflight is documented as live Multipass readiness proof"
```

Done criteria:

- generic `Host is Linux or WSL compatible` no longer has empty evidence;
- static and live-consent runtime checks have distinct semantics.

### Slice 04: Implement Linux And Sandbox Host Probe

Purpose: classify native Linux and sandbox/unverified Linux through the
infrastructure preflight adapter with mocked tests.

```yaml
slice_id: "04"
profile: "implementation"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Tester"
  - "Senior System Architect"
affected_files:
  - "src/tiny_swarm_world/infrastructure/adapters/preflight/**"
  - "tests/infrastructure/adapters/preflight/test_host_preflight_probe.py"
affected_modules:
  - "tiny_swarm_world.infrastructure.adapters.preflight"
affected_contracts:
  - "host environment probe"
dependencies:
  - "03"
parallel_group: "D"
file_locks:
  - "src/tiny_swarm_world/infrastructure/adapters/preflight/**"
  - "tests/infrastructure/adapters/preflight/**"
contract_locks:
  - "no live infrastructure mutation from probes"
architecture_locks:
  - "infrastructure owns platform, /proc, environment, filesystem probes"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.preflight.test_host_preflight_probe"
  required:
    - "python3 tools/quality_gate.py test"
documentation:
  arc42: "record sandbox boundary in runtime/deployment docs"
  adr: "no new ADR expected"
stop_conditions:
  - "probe runs mutating host commands"
  - "sandbox is treated as WSL2 evidence"
```

Done criteria:

- native Linux and sandbox/unverified Linux are distinguishable in reports;
- tests mock filesystem, platform, and environment signals.

### Slice 05: Implement WSL Host Probe

Purpose: detect WSL2 and WSL1 through multiple signals and block unsupported
or unknown environments before platform mutation.

```yaml
slice_id: "05"
profile: "implementation"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Tester"
  - "Senior System Architect"
affected_files:
  - "src/tiny_swarm_world/infrastructure/adapters/preflight/**"
  - "tests/infrastructure/adapters/preflight/test_host_preflight_probe.py"
affected_modules:
  - "tiny_swarm_world.infrastructure.adapters.preflight"
affected_contracts:
  - "WSL host detection"
  - "unsupported host blocking"
dependencies:
  - "04"
parallel_group: "E"
file_locks:
  - "src/tiny_swarm_world/infrastructure/adapters/preflight/**"
  - "tests/infrastructure/adapters/preflight/**"
contract_locks:
  - "WSL2 requires multiple detection signals"
architecture_locks:
  - "Windows host commands are not default automation"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.preflight.test_host_preflight_probe"
  required:
    - "python3 tools/quality_gate.py test"
documentation:
  arc42: "update runtime view for WSL2 and WSL1 paths"
  adr: "no new ADR unless Windows-host mutation is automated"
stop_conditions:
  - "single fragile signal is the only WSL2 proof"
  - "WSL1 proceeds past preflight"
  - "unknown environment proceeds past preflight"
```

Done criteria:

- WSL2, WSL1 unsupported, and unknown unsupported behavior is covered by
  deterministic tests;
- WSL-specific remediation is actionable and non-mutating.

### Slice 06: Refine Multipass Readiness

Purpose: migrate the useful Multipass readiness concepts from legacy scripts
behind the current preflight adapter and reject unsafe legacy behavior.

```yaml
slice_id: "06"
profile: "implementation"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Tester"
  - "Senior Security/Sandbox Engineer"
affected_files:
  - "src/tiny_swarm_world/domain/preflight/**"
  - "src/tiny_swarm_world/infrastructure/adapters/preflight/host_preflight_probe.py"
  - "infra/config/multipass/**"
  - "tests/application/services/platform/test_preflight_service.py"
  - "tests/infrastructure/adapters/preflight/test_host_preflight_probe.py"
affected_modules:
  - "tiny_swarm_world.domain.preflight"
  - "tiny_swarm_world.infrastructure.adapters.preflight"
affected_contracts:
  - "Multipass readiness"
  - "live preflight runtime readiness"
dependencies:
  - "05"
parallel_group: "F"
file_locks:
  - "src/tiny_swarm_world/domain/preflight/**"
  - "src/tiny_swarm_world/infrastructure/adapters/preflight/host_preflight_probe.py"
  - "infra/config/multipass/**"
contract_locks:
  - "read-only probes only"
  - "no static passphrase"
architecture_locks:
  - "subprocess details remain infrastructure-only"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_preflight_service tests.infrastructure.adapters.preflight.test_host_preflight_probe"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "update risks if readiness semantics change materially"
  adr: "adr-autonomous-setup-safety checked; new ADR if host repair is automated"
stop_conditions:
  - "multipass launch is used in preflight"
  - "shell=True is introduced for new probes"
  - "static Multipass passphrase remains reachable from canonical setup"
  - "driver mismatch does not block before platform init"
```

Done criteria:

- readiness includes version, list, driver, daemon/socket/permission, timeout,
  and remediation signals;
- broken daemon or non-qemu driver blocks before mutation.

### Slice 07: WSL2 Network Forwarding Planning

Purpose: migrate WSL networking concepts into typed planning without blind host
network mutation.

```yaml
slice_id: "07"
profile: "implementation"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior DevOps Engineer"
  - "Senior Security/Sandbox Engineer"
affected_files:
  - "src/tiny_swarm_world/domain/network/**"
  - "src/tiny_swarm_world/application/services/network/**"
  - "src/tiny_swarm_world/infrastructure/adapters/preflight/**"
  - "tests/domain/network/**"
  - "tests/application/services/network/**"
affected_modules:
  - "tiny_swarm_world.domain.network"
  - "tiny_swarm_world.application.services.network"
affected_contracts:
  - "port forwarding plan"
  - "network readiness"
dependencies:
  - "05"
parallel_group: "F"
file_locks:
  - "src/tiny_swarm_world/domain/network/**"
  - "src/tiny_swarm_world/application/services/network/**"
  - "tests/domain/network/**"
  - "tests/application/services/network/**"
contract_locks:
  - "no committed IP addresses"
  - "no blind socat, iptables, or netsh mutation"
architecture_locks:
  - "network service depends on typed ports and domain models"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.domain.network tests.application.services.network"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "update deployment/runtime view for WSL2 forwarding strategies"
  adr: "new ADR required before automatic host network mutation"
stop_conditions:
  - "hardcoded VM, WSL, gateway, or Windows IP is committed"
  - "netsh or iptables becomes default automation"
```

Done criteria:

- forwarding strategies are explicit: `NATIVE_LINUX_DIRECT`, `WSL2_SOCAT`,
  `WSL2_NETSH_DOCUMENTED`, `WSL2_IPTABLES_OPTIONAL`, `UNSUPPORTED`;
- default WSL2 behavior is planning and verification, not blind mutation.

### Slice 08: Setup And Platform Guard Integration

Purpose: ensure selected host path and preflight status govern setup/platform
phase ordering before VM creation.

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
  - "setup phase ordering"
  - "platform init pre-apply guard"
  - "CLI status semantics"
dependencies:
  - "03"
  - "06"
  - "07"
parallel_group: "G"
file_locks:
  - "src/tiny_swarm_world/application/services/setup/**"
  - "src/tiny_swarm_world/application/services/platform/**"
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "src/tiny_swarm_world/__main__.py"
contract_locks:
  - "missing live consent refuses before setup construction"
  - "failed preflight marks downstream phases not_run"
architecture_locks:
  - "entry point remains thin"
  - "composition root owns adapter construction"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.application.services.setup.test_setup_workflow tests.application.services.platform.test_platform_workflows tests.test_package_entrypoint"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "runtime view and quality requirements must be updated"
  adr: "adr-autonomous-setup-safety must remain satisfied"
stop_conditions:
  - "platform init can bypass host readiness guard"
  - "setup run without live consent mutates infrastructure"
  - "console output claims WSL2 readiness from sandbox"
```

Done criteria:

- old failure shape is covered by a regression test;
- downstream setup phases are `not_run` when host preflight fails.

### Slice 09: Sanitized Diagnostics And Evidence

Purpose: improve failure diagnostics without violating safe-text or evidence
redaction contracts.

```yaml
slice_id: "09"
profile: "implementation"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Tester"
  - "Senior Security/Sandbox Engineer"
  - "Console/status UI reviewer"
affected_files:
  - "src/tiny_swarm_world/domain/inventory/**"
  - "src/tiny_swarm_world/domain/command/**"
  - "src/tiny_swarm_world/infrastructure/adapters/command_runner/**"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/verification_evidence_local_repository.py"
  - "tests/domain/inventory/**"
  - "tests/infrastructure/adapters/command_runner/**"
affected_modules:
  - "tiny_swarm_world.domain.inventory"
  - "tiny_swarm_world.domain.command"
  - "tiny_swarm_world.infrastructure.adapters.command_runner"
affected_contracts:
  - "safe diagnostic summary"
  - "verification evidence redaction"
dependencies:
  - "08"
parallel_group: "H"
file_locks:
  - "src/tiny_swarm_world/domain/inventory/**"
  - "src/tiny_swarm_world/domain/command/**"
  - "src/tiny_swarm_world/infrastructure/adapters/command_runner/**"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/verification_evidence_local_repository.py"
contract_locks:
  - "no raw command/stdout/stderr/environment/token/password/secret persistence"
architecture_locks:
  - "diagnostics stay sanitized and summary-oriented"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.domain.inventory tests.infrastructure.adapters.command_runner"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "update quality and risks if evidence semantics change"
  adr: "new ADR required for material evidence semantic change"
stop_conditions:
  - "raw output or host-specific payload is persisted"
  - "setup phase result safety is weakened"
```

Done criteria:

- errors expose actionable classification and sanitized evidence only;
- no safety guard is relaxed to carry raw command output.

### Slice 10: Documentation And Architecture Synchronization

Purpose: align README, system docs, user guide, arc42, and ADR references with
implemented behavior only.

```yaml
slice_id: "10"
profile: "documentation"
owner: "Senior Documentation Engineer"
secondary_reviewers:
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "README.md"
  - "documentation/system/multipass-setup.adoc"
  - "documentation/system/network.adoc"
  - "documentation/system/live-operation-surfaces.adoc"
  - "documentation/system/wsl-host-preflight.adoc"
  - "documentation/user_guide/installation.adoc"
  - "documentation/user_guide/troubleshooting.adoc"
  - "documentation/deployment/system.adoc"
  - "documentation/arc42/**"
  - "documentation/architecture/adr-autonomous-setup-safety.adoc"
affected_modules: []
affected_contracts:
  - "operator documentation"
  - "arc42 runtime and deployment views"
dependencies:
  - "08"
  - "09"
parallel_group: "I"
file_locks:
  - "README.md"
  - "documentation/system/**"
  - "documentation/user_guide/**"
  - "documentation/deployment/**"
  - "documentation/arc42/**"
  - "documentation/architecture/adr-autonomous-setup-safety.adoc"
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
  adr: "update or add ADR only for accepted architecture decisions"
stop_conditions:
  - "docs claim full WSL2 success without WSL2 evidence"
  - "Windows-native automation is documented as default product behavior"
```

Done criteria:

- docs distinguish Native Linux, WSL2, WSL1 unsupported, unknown unsupported,
  and sandbox/unverified Linux;
- `infra/swarm` remains legacy.

### Slice 11: Quality And Installation Validation Matrix

Purpose: run final static/mocked quality gates and collect separate operator
validation evidence for sandbox and real WSL2 console.

```yaml
slice_id: "11"
profile: "verification"
owner: "Senior Tester"
secondary_reviewers:
  - "Senior DevOps Engineer"
  - "Senior Documentation Engineer"
  - "Senior System Architect"
affected_files:
  - ".tiny-swarm-world/evidence/installation-tests/**"
  - "documentation/workflow/execution-report.md"
affected_modules: []
affected_contracts:
  - "QUALITY.md gate evidence"
  - "operator-approved live validation evidence"
dependencies:
  - "10"
parallel_group: "J"
file_locks:
  - "documentation/workflow/execution-report.md"
contract_locks:
  - "live infrastructure requires explicit operator approval"
  - "local evidence remains ignored"
architecture_locks:
  - "sandbox evidence cannot prove WSL2 behavior"
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
  - "WSL2 validation is reported from sandbox"
  - "local evidence contains secrets, raw output, usernames, host paths, or IPs in committed files"
```

Done criteria:

- full quality gate result is recorded;
- sandbox and WSL2 evidence are evaluated separately;
- final report states whether the original false-positive condition is
  eliminated.

## Dependency Graph

```text
01
 |
02
 |
03
 |
04 -> 05
      | \
      |  +-> 07
      +-> 06
            \
             +-> 08 -> 09 -> 10 -> 11
```

Parallelization:

- Slice 01 can run independently first.
- Slice 02 must finish before preflight/service/adapter implementation.
- Slice 06 and Slice 07 may run in parallel after Slice 05 if their file locks
  remain disjoint.
- Documentation drafting in Slice 10 may begin as notes during implementation
  but must not claim behavior until implementation and tests exist.

## Role Ownership Map

| Concern | Owner | Secondary review |
| --- | --- | --- |
| Workflow dependency ordering | Senior Workflow Architect | Senior Swarm Orchestrator |
| Requirement and EPIC drift | Senior Requirement Engineer | Engineering Governance |
| Architecture boundaries and arc42 | Senior System Architect | arc42 governance |
| Python automation implementation | Senior Python Automation Developer | Senior Tester |
| Console/status output semantics | Console/status UI skills | Senior React Frontend Developer as N/A React guard |
| Live platform safety | Senior DevOps Engineer | Security/Sandbox Engineer |
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
Docker, Multipass, or deployment CI commands.

## Installation Validation Boundary

Static preflight:

```bash
PYTHONPATH=src python3 -m tiny_swarm_world --preflight
```

Static preflight is configuration and host-classification evidence only until
runtime readiness checks are explicitly included. It must not be treated as
proof that Multipass daemon, qemu driver, VM creation, Docker Swarm, or WSL2
forwarding works.

Consent-boundary setup command:

```bash
PYTHONPATH=src python3 -m tiny_swarm_world setup run
```

Without `--live`, this is expected to refuse before mutation. Treat the result
as consent-boundary evidence, not a dry-run installation pass.

Operator-approved live validation commands may be run only after explicit
approval in a disposable or recoverable environment:

```bash
PYTHONPATH=src python3 -m tiny_swarm_world setup run --live
```

Live validation results:

- `PASSED_FULL_INSTALLATION`: full live installation was verified.
- `BLOCKED_SANDBOX_CAPABILITY_MISSING`: sandbox lacks live infrastructure
  capability; this is not a full pass.
- `BLOCKED_WSL2_HOST_PREREQUISITE`: real WSL2 preflight blocked before
  mutation with actionable remediation; this proves fail-closed safety but not
  full installation success.
- `FAILED`: live validation failed after an approved live phase.
- `NOT_RUN`: required environment validation was not run.

Full WSL2 installation success may be claimed only for
`PASSED_FULL_INSTALLATION` from a real WSL2 console. A preflight-blocked WSL2
result may close the safety regression when it blocks before `platform init`,
but it must not be reported as full installation success.

Evidence paths are local and ignored:

```text
.tiny-swarm-world/evidence/installation-tests/sandbox/
.tiny-swarm-world/evidence/installation-tests/wsl2/
.tiny-swarm-world/evidence/installation-tests/comparison-report.md
```

Committed reports may summarize sanitized status only.

## Documentation Synchronization Points

Update documentation only when behavior is implemented or clearly marked as
planned workflow behavior:

- `README.md`
- `documentation/architecture/legacy-swarm-setup-migration.md`
- `documentation/architecture/adr-autonomous-setup-safety.adoc`
- `documentation/system/multipass-setup.adoc`
- `documentation/system/network.adoc`
- `documentation/system/live-operation-surfaces.adoc`
- `documentation/system/wsl-host-preflight.adoc`
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

- active branch is not `fix/linux-wsl-swarm-setup-workprocess-20260525`;
- workflow slice metadata or locks are missing;
- implementation would touch files outside the active slice scope;
- direct `infra/swarm` scripts would be executed or promoted;
- live infrastructure commands would run without explicit operator approval;
- WSL2 behavior would be inferred from sandbox evidence;
- raw command strings, stdout, stderr, environment payloads, tokens, passwords,
  Swarm join tokens, usernames, host paths, or host-specific IPs would be
  committed or persisted in unsafe evidence;
- architecture tests would need to be weakened;
- new host package installation, socket repair, `netsh`, `iptables`, or
  automatic `socat` mutation is required without ADR approval;
- planned behavior would be documented as implemented behavior.

## Definition Of Done

- `documentation/workflow/workflow.md` contains complete slice metadata and is
  consistent with `AGENTS.md`, `QUALITY.md`, EPICs, ADRs, and arc42.
- Legacy `infra/swarm` behavior is analyzed and classified.
- Host environment classification is typed, tested, and wired into preflight.
- WSL1 and unknown hosts block before platform mutation.
- Sandbox/unverified Linux cannot be used as WSL2 proof.
- Multipass readiness distinguishes executable presence from daemon, socket,
  permission, timeout, version, list, and qemu driver readiness.
- WSL2 network planning avoids hardcoded IPs and blind host mutation.
- Setup/platform phase ordering blocks before VM creation when preflight fails.
- The observed false-positive regression has a deterministic test.
- Documentation is synchronized without overclaiming live success.
- `python3 tools/quality_gate.py quality` passes or any failure is routed
  through the Typed Error Router.
- Sandbox and WSL2 live validation are recorded separately when operator
  approval is granted.

## Commit And Push Plan

Suggested commit message after implementation and verification:

```text
fix: split swarm setup into native Linux and WSL2 host paths
```

Do not push or create a pull request during slice checkpoints unless the user
explicitly asks for that action.

## Handoff To Workflow Execute

Before `workflow execute`:

1. Verify branch:

```bash
git show-ref --verify --quiet refs/heads/fix/linux-wsl-swarm-setup-workprocess-20260525
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
workflow authoring because this is a plan, not implementation. Slice 10 must
update arc42 once behavior changes are implemented and verified.
