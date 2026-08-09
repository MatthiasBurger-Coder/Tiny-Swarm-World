# Workflow: Issue #188 — Shared Process Runners

Workflow ID: `issue-188-20260809`

Workflow version: `issue-188-v1.0.0`

Status: `READY_FOR_EXECUTION`

Authoring branch: `feature/workflow-issue-188-shared-command-runners-20260809`

Implementation branch requested by the issue: `feature/issue-188-shared-command-runners`

Execution profile: `FULL_PATH`

## Executive Summary

Issue #188 finishes the remaining direct process-execution centralization on
the current Python `main` baseline. It introduces one reusable,
infrastructure-only process-runner abstraction and migrates the five minimum
adapter targets named by the issue while preserving each adapter's existing
business policy, timeout behavior, compatibility surface, diagnostics, and
error model.

The workflow is a follow-on to Issue #183. It reuses the existing
`LxcManagerShellGateway`; it does not extract a second LXC gateway, redo the
Issue #183 decomposition, change application/domain ports, or create a service.
The first execution slice must inventory every production process-spawn site
and classify minimum-target migrations, justified exceptions, test-only calls,
and tooling/CLI calls before implementation proceeds.

The workflow was admitted through the required Four-Role Three-Amigos gate:
Senior Requirement Engineer, Senior System Architect, Senior Python
Automation Developer, and Senior Tester. The gate decision is
`READY_FOR_WORKFLOW` with 95% confidence. A dependency/deadlock pass is also
required because the shared runner contract is consumed by multiple adapters.

## Requirement Clarification Record

- Original Request: `workflow create issue #188`.
- Interpreted Intent: create and publish an executable, issue-traceable
  workflow for the public Issue #188 refactor; do not implement the refactor
  in this authoring step.
- Change Type: issue-driven architecture-sensitive Python infrastructure
  refactor plan with regression and architecture-test gates.
- Affected Process Strand: `workflow-create-to-workflow-execute`.
- Affected Architecture Area: infrastructure process execution, Docker/LXC
  adapters, host preflight, composition wiring, architecture enforcement, and
  Arc42 quality/risk documentation.
- Explicit Requirements: recorded in
  `.tiny-swarm/evidence/solid-command-runner/requirement_matrix.md`.
- Implicit Requirements: stable application-port behavior, dependency
  injection through the composition root, bounded and deterministic process
  failures, safe diagnostics, no live infrastructure mutation in local gates,
  and independent completion auditing.
- Assumptions: the implementation branch starts from the current `main`
  commit; the new runner remains infrastructure-only; existing direct calls
  outside the five minimum targets are not migrated without inventory-based
  classification; the issue's requested `.tiny-swarm-world` Three-Amigos path
  is retained while repository completion evidence remains under
  `.tiny-swarm/evidence`.
- Non-Goals: Issue #183 rework; Issue #187 strategy-registry work; Issue #189
  backend-CLI mapping; Issue #190 stack prerequisite strategies; Issue #192
  HTTP wrapper separation; Issue #184 node-provider decomposition; Issue #195
  broad composition decomposition; Java/Maven/Spring Boot; React/browser UI;
  live Docker, Incus/LXC, Swarm, registry, network, or service mutation.
- Risks: a generic runner may absorb adapter policy; text/byte transfer may
  regress; existing tests may depend on module-level patch seams; shell
  wrappers may be broadened; the broader baseline inventory may expose a
  scope conflict; secret-bearing output may leak through a new result or log.
- Open Questions: exact package placement (`infrastructure/process` versus a
  dependency-safe equivalent), exact result type versus a compatible
  `CompletedProcess`-shaped value, and the final allowlist of pre-existing
  exceptional process boundaries. These are implementation design decisions
  constrained by Slice 01 and are not blockers to authoring.
- Blocking Questions: none at authoring time. Any unclassified production
  spawn site, changed public port contract, or required new architecture
  decision blocks execution at the relevant slice.
- Confidence Level: 95%.
- Decision: `READY_FOR_WORKFLOW`.

## Target Picture

The target implementation has one small, reusable infrastructure process
runner with deterministic result and failure semantics. It executes argv with
`shell=False` by default, supports the required cwd/environment/input and
text/byte variants, bounds execution with timeouts, captures return code,
stdout, and stderr, maps launch and timeout failures deterministically, and
never logs raw secrets.

Adapter code remains responsible for policy: Docker fatality decisions, LXC
manager/node targeting and retry classification, image-publisher diagnostics
and rate-limit handling, and fail-soft Git preflight behavior. The composition
root supplies concrete runner dependencies. Domain and application packages
remain unaware of subprocess mechanics and concrete infrastructure runners.

## Verified Baseline

- Repository root: `D:/Projects/Tiny-Swarm-World`.
- Baseline branch before authoring: `main`.
- Baseline commit: `3642367` (`refactor: split LXC swarm runtime into cohesive clients (#238)`).
- Working tree before authoring: clean.
- Existing command-runner package:
  `src/tiny_swarm_world/infrastructure/adapters/command_runner/` contains the
  application command-runner adapters, including an async shell runner; it is
  not assumed to satisfy Issue #188's infrastructure-only sync argv/text/bytes
  contract.
- Minimum production targets verified on the baseline:
  `docker_cli_runtime.py`, `lxc/command/manager_shell_gateway.py`,
  `lxc/docker/lxc_container_runtime.py`,
  `lxc/images/lxc_container_image_publisher.py`, and
  `preflight/host_preflight_probe.py`.
- Existing tests verified near the targets:
  `test_docker_cli_runtime.py`, `lxc/command/test_manager_shell_gateway.py`,
  `lxc/docker/test_lxc_container_runtime.py`,
  `lxc/images/test_lxc_container_image_publisher.py`,
  `test_host_preflight_probe.py`, and architecture tests under `tests/architecture`.
- The baseline also contains other production process-spawn sites. The
  initial static inventory is recorded at
  `.tiny-swarm/evidence/solid-command-runner/process-spawn-inventory-before.md`.
  Slice 01 must confirm the complete inventory and classify every site before
  any migration slice is accepted.
- Arc42 has an implemented Issue #183 LXC decomposition status. Issue #188 is
  documented as planned work only until execution evidence proves otherwise.
- No `documentation/adr` directory or active process-runner ADR was found.
  No ADR is required for the bounded infrastructure-only refactor as currently
  specified; a newly discovered boundary or compatibility decision that cannot
  be resolved from the issue requires an architecture stop and ADR review.

## Scope

### In scope

- A reusable infrastructure process-runner contract and implementation.
- Deterministic process result, launch-failure, timeout, input, output, and
  redaction semantics.
- Composition-root wiring for the migrated adapter dependencies.
- `DockerCliRuntime` migration.
- Existing `LxcManagerShellGateway` delegation to the shared runner while
  retaining LXC-specific retry and diagnostics policy.
- `LxcContainerRuntime` migration.
- `LxcContainerImagePublisher` migration for text and byte process paths,
  including host Docker/cache transfer.
- `HostPreflightProbe` Git inspection migration with fail-soft behavior.
- Before/after process-spawn inventories and an architecture/static guard for
  new unapproved production direct spawning.
- Focused regression tests, architecture tests, local quality gates, and
  planned-versus-implemented Arc42 synchronization.

### Explicit non-goals

- No new LXC gateway and no reimplementation of Issue #183.
- No application-port or domain-model redesign.
- No duplication of Issue #189 backend CLI mapping or shared LXC utilities.
- No HostPreflightProbe strategy registry from Issue #187.
- No stack prerequisite strategy work from Issue #190.
- No LXC HTTP service-wrapper extraction from Issue #192.
- No `lxc_node_provider.py` decomposition from Issue #184.
- No broad `composition.py` decomposition from Issue #195.
- No migration of tests, `tools/`, Windows legacy surfaces, or installer code
  unless Slice 01 proves that a named Issue #188 acceptance criterion requires
  it and the scope is explicitly approved.
- No live infrastructure, installation, browser, registry, SonarQube, or
  external acceptance run is required by this workflow.

## Architecture Constraints

- Preserve the existing hexagonal architecture and inward dependency
  direction.
- Keep process execution in infrastructure. Domain and application code must
  not import `subprocess`, `asyncio` process APIs, or concrete runner classes.
- Keep composition in
  `src/tiny_swarm_world/infrastructure/composition.py`; adapters receive
  explicit dependencies where construction paths require wiring changes.
- Use argv and `shell=False` by default. A shell wrapper is an explicit,
  adapter-owned compatibility operation and must remain bounded and justified.
- Keep adapter policy outside the generic runner.
- Preserve public application-port signatures and behavior unless a verified
  compatibility-preserving change is strictly required.
- Preserve safe/redacted diagnostics. Credentials, tokens, environment
  payloads, raw sensitive output, and command payloads must not enter logs or
  evidence.
- Do not centralize Issue #189 backend CLI mapping in this workflow.
- Keep local tests fake/mock based and never invoke live Docker, Incus/LXC,
  Swarm, network, registry, or service bootstrap operations.

## Python Automation Assessment

This is a Python infrastructure-adapter change. The implementation owner must
use typed value/result objects or protocols as appropriate, keep the generic
runner small, preserve Python 3.12 compatibility, and avoid import-time or
constructor side effects. Existing test seams may be retained only where they
are proven compatibility requirements; dependency injection is preferred.

Composition changes must be limited to supplying the shared infrastructure
runner and preserving existing adapter construction. No domain, application,
or public port change is planned.

## Frontend Assessment

Console/status UI impact is `NOT_APPLICABLE`: the issue changes process
execution mechanics and adapter diagnostics, not terminal presentation or
interaction. Browser React review is `FORBIDDEN` because this repository has no
verified browser React product module for this scope.

## Test Strategy

Use deterministic unit and architecture tests with fakes/mocks. Tests must
prove the shared runner's result and failure contract, text and byte input/
output handling, timeout and executable-not-found mapping, each adapter's
existing behavior, redaction guarantees, fail-soft Git inspection, composition
wiring, and the production-spawn architecture guard.

Run focused tests for each slice first. Before workflow-authoring publication,
run `git diff --check`; implementation slices must use the required local
quality gates from `QUALITY.md`, with `python3 tools/quality_gate.py quality`
as the default full gate. Local success must not be reported as live or
external success.

## Resilience Requirements

- Every shared process call has a bounded timeout and explicit cancellation or
  failure behavior where the existing adapter supports it.
- Launch failures and timeouts map deterministically without leaking raw
  command data.
- Existing retries remain adapter-owned, bounded, and observable. The generic
  runner must not add unreviewed retries or duplicate side effects.
- Image cache transfer and byte-stream paths must preserve incomplete/failure
  states and must not turn a failed load into a cache hit.
- Host Git inspection remains fail-soft: unavailable Git must not hang
  preflight, `path_ignored_by_git()` remains false on unavailable inspection,
  and tracked-file fallback remains available.
- Diagnostics remain sanitized and safe operator actions remain intact.

## Ordered Slices

### Slice 01 — Baseline inventory and shared-runner contract

Purpose: create the execution baseline, complete the before-inventory of all
production process-spawn sites, classify minimum migrations and explicit
exceptions, and freeze the infrastructure-only runner contract before code is
written.

Prerequisites: workflow branch, requirement matrix, and Four-Role Three-Amigos
gate are present.

Allowed write scope: issue evidence files only. Source and test inventory is
read-only in this slice.

Done criteria:

- Every production `subprocess.run`, `subprocess.Popen`,
  `asyncio.create_subprocess_exec`, and
  `asyncio.create_subprocess_shell` call in the verified baseline is listed.
- Each call is classified as migrate in #188, intentional documented
  exception, test-only, or tooling/CLI outside infrastructure runtime scope.
- The five minimum targets are explicitly mapped to later slices.
- The generic runner contract and adapter-owned policy boundaries are reviewed
  by the Requirement Lead, System Architect, Python Automation Developer, and
  Tester.
- Any newly discovered scope, architecture, or compatibility blocker is
  marked `BLOCKED` and stops later implementation slices.

```yaml
slice_id: S01
profile: FULL_PATH
owner: Senior Requirement Engineer
secondary_reviewers: [Senior System Architect, Senior Python Automation Developer, Senior Tester, Senior Execution Orchestrator]
affected_files: [.tiny-swarm/evidence/solid-command-runner/requirement_matrix.md, .tiny-swarm/evidence/solid-command-runner/process-spawn-inventory-before.md, .tiny-swarm-world/evidence/solid-command-runner/three-amigos.md]
affected_modules: [infrastructure process execution inventory]
affected_contracts: [issue requirement matrix, shared runner responsibility boundary]
dependencies: []
parallel_group: SERIAL-BASELINE
file_locks: [.tiny-swarm/evidence/solid-command-runner/**, .tiny-swarm-world/evidence/solid-command-runner/**]
contract_locks: [shared-process-runner-contract]
architecture_locks: [infrastructure-only-process-boundary]
quality_gates:
  targeted: [git diff --check]
  required: [git diff --check]
documentation:
  arc42: reviewed; no implementation claim
  adr: none unless a new boundary decision is discovered
stop_conditions: [incomplete production inventory, ambiguous scope, missing requirement mapping, contradictory architecture evidence]
```

### Slice 02 — Implement the reusable infrastructure process runner

Purpose: implement the shared result and runner mechanics, including argv
execution with `shell=False` by default, cwd/environment/input support,
text/bytes, timeout, result capture, deterministic launch/timeout errors, and
sanitized diagnostics. Wire the runner through the composition root where the
target adapters are constructed.

Prerequisites: S01 `READY` with no blocking inventory or contract question.

Allowed write scope: the new dependency-safe infrastructure process package,
its focused tests, and narrowly required composition wiring.

Done criteria:

- The runner is infrastructure-only and does not add application/domain
  dependencies.
- Text and byte input/output variants are test-covered.
- Return code/stdout/stderr results are deterministic.
- Timeout and executable-not-found failures are deterministic and sanitized.
- `shell=False` is the default; explicit shell wrappers are not silently
  introduced.
- No generic runner code owns Docker/LXC/image/preflight business decisions.

```yaml
slice_id: S02
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior System Architect, Senior Tester, Senior Security Sandbox Engineer]
affected_files: [src/tiny_swarm_world/infrastructure/process/**, src/tiny_swarm_world/infrastructure/composition.py, tests/infrastructure/process/**, tests/infrastructure/test_composition.py]
affected_modules: [infrastructure.process, infrastructure.composition]
affected_contracts: [shared process runner result contract, composition wiring]
dependencies: [S01]
parallel_group: SERIAL-CONTRACT
file_locks: [src/tiny_swarm_world/infrastructure/process/**, src/tiny_swarm_world/infrastructure/composition.py, tests/infrastructure/process/**, tests/infrastructure/test_composition.py]
contract_locks: [shared-process-runner-contract]
architecture_locks: [infrastructure-only-process-boundary, composition-root-wiring]
quality_gates:
  targeted: [python3 tools/quality_gate.py lint, python3 tools/quality_gate.py typecheck, python3 tools/quality_gate.py test, python3 tools/quality_gate.py arch-lint, python3 tools/quality_gate.py arch-tests]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: planned process-runner boundary and quality scenarios
  adr: none unless contract placement cannot be resolved
stop_conditions: [domain/application import, unbounded process call, raw secret diagnostics, contract instability, composition scope expansion]
```

### Slice 03 — Migrate `DockerCliRuntime`

Purpose: replace the direct `subprocess.run` call in
`docker_cli_runtime.py` with the shared runner while preserving timeout,
stdout parsing, `check=True`/`check=False`, and operator-safe `RuntimeError`
messages.

Prerequisites: S02 complete and the shared result contract is stable.

Allowed write scope: `docker_cli_runtime.py`, its focused test, and any
slice-local evidence.

Done criteria: no direct process spawn remains in the target; all existing
Docker runtime tests pass against injected fake runner results; no public
container-runtime port behavior changes.

```yaml
slice_id: S03
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Tester, Senior System Architect]
affected_files: [src/tiny_swarm_world/infrastructure/adapters/clients/docker_cli_runtime.py, tests/infrastructure/adapters/clients/test_docker_cli_runtime.py]
affected_modules: [infrastructure.adapters.clients.docker_cli_runtime]
affected_contracts: [PortContainerRuntime behavior, Docker runtime error semantics]
dependencies: [S02]
parallel_group: ADAPTER-MIGRATIONS
file_locks: [src/tiny_swarm_world/infrastructure/adapters/clients/docker_cli_runtime.py, tests/infrastructure/adapters/clients/test_docker_cli_runtime.py]
contract_locks: [shared-process-runner-contract, PortContainerRuntime]
architecture_locks: [infrastructure-only-process-boundary]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_docker_cli_runtime]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: no new implementation claim until final synchronization
  adr: none
stop_conditions: [changed timeout semantics, changed stdout parsing, changed public error contract]
```

### Slice 04 — Migrate the existing LXC manager shell gateway

Purpose: inject/delegate the shared runner beneath
`LxcManagerShellGateway`. Keep Incus/LXD command composition, manager/node
behavior, bounded retry policy, safe diagnostics, and LXC-specific error
wording in the gateway. Retain compatibility test seams only when verified.

Prerequisites: S02 complete; S01 confirms the gateway is the #188 target and
Issue #183 remains the source of the existing gateway behavior.

Allowed write scope: `lxc/command/manager_shell_gateway.py`, its focused tests,
and narrowly required package exports.

Done criteria: the gateway no longer directly resolves `subprocess.run`; retry
and redaction tests remain green; manager/node and timeout behavior are
unchanged; no second gateway is introduced.

```yaml
slice_id: S04
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior System Architect, Senior Tester, Senior Security Sandbox Engineer]
affected_files: [src/tiny_swarm_world/infrastructure/adapters/clients/lxc/command/manager_shell_gateway.py, src/tiny_swarm_world/infrastructure/adapters/clients/lxc/command/__init__.py, tests/infrastructure/adapters/clients/lxc/command/test_manager_shell_gateway.py]
affected_modules: [infrastructure.adapters.clients.lxc.command]
affected_contracts: [LxcManagerShellGateway compatibility seam, LXC retry and redaction semantics]
dependencies: [S02]
parallel_group: ADAPTER-MIGRATIONS
file_locks: [src/tiny_swarm_world/infrastructure/adapters/clients/lxc/command/**, tests/infrastructure/adapters/clients/lxc/command/test_manager_shell_gateway.py]
contract_locks: [shared-process-runner-contract, LxcManagerShellGateway]
architecture_locks: [infrastructure-only-process-boundary, issue-183-compatibility]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.lxc.command.test_manager_shell_gateway]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: preserve Issue #183 implemented status; add #188 status only in final slice
  adr: none
stop_conditions: [retry policy moved into generic runner, unsafe diagnostics, compatibility patch paths lost]
```

### Slice 05 — Migrate LXC Docker/container access

Purpose: replace direct process execution in `lxc_container_runtime.py` with
the shared runner or the existing LXC command boundary without centralizing
Issue #189 backend CLI mapping.

Prerequisites: S02 complete; S01 confirms the target and compatibility
behavior.

Allowed write scope: `lxc/docker/lxc_container_runtime.py` and its focused
tests.

Done criteria: multi-node discovery, node-qualified references, timeout and
exit-code behavior, and the current application port contract remain intact;
the target has no direct process spawn.

```yaml
slice_id: S05
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Tester, Senior System Architect]
affected_files: [src/tiny_swarm_world/infrastructure/adapters/clients/lxc/docker/lxc_container_runtime.py, tests/infrastructure/adapters/clients/lxc/docker/test_lxc_container_runtime.py, tests/infrastructure/adapters/clients/test_lxc_swarm_runtime.py]
affected_modules: [infrastructure.adapters.clients.lxc.docker]
affected_contracts: [PortContainerRuntime behavior, node-qualified container references]
dependencies: [S02]
parallel_group: ADAPTER-MIGRATIONS
file_locks: [src/tiny_swarm_world/infrastructure/adapters/clients/lxc/docker/lxc_container_runtime.py, tests/infrastructure/adapters/clients/lxc/docker/test_lxc_container_runtime.py, tests/infrastructure/adapters/clients/test_lxc_swarm_runtime.py]
contract_locks: [shared-process-runner-contract, PortContainerRuntime]
architecture_locks: [infrastructure-only-process-boundary, issue-189-boundary]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.lxc.docker.test_lxc_container_runtime tests.infrastructure.adapters.clients.test_lxc_swarm_runtime]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: final status only after behavior evidence
  adr: none
stop_conditions: [backend CLI mapping duplication, node reference regression, changed application-port behavior]
```

### Slice 06 — Migrate image-publisher process execution

Purpose: replace direct process execution in
`lxc_container_image_publisher.py`, including host Docker inspection, Docker
save/cache transfer, manager shell text commands, and manager shell byte-stream
transfer.

Prerequisites: S02 complete; S01 confirms exact text/byte paths and secret
handling requirements.

Allowed write scope: image publisher source, its focused tests, and no generic
runner policy changes.

Done criteria: typed `ImagePublisherOperationRejected` and
`PublicImagePullRejected` behavior, operation diagnostics, registry-rate-limit
detection, safe operator actions, cache/build/pull behavior, and no credential
or raw-output leakage remain intact; no direct process spawn remains in the
target.

```yaml
slice_id: S06
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Tester, Senior Security Sandbox Engineer, Senior System Architect]
affected_files: [src/tiny_swarm_world/infrastructure/adapters/clients/lxc/images/lxc_container_image_publisher.py, tests/infrastructure/adapters/clients/lxc/images/test_lxc_container_image_publisher.py, tests/infrastructure/adapters/clients/test_lxc_swarm_runtime.py]
affected_modules: [infrastructure.adapters.clients.lxc.images]
affected_contracts: [PortContainerImagePublisher, image-publisher typed errors and diagnostics]
dependencies: [S02]
parallel_group: ADAPTER-MIGRATIONS
file_locks: [src/tiny_swarm_world/infrastructure/adapters/clients/lxc/images/lxc_container_image_publisher.py, tests/infrastructure/adapters/clients/lxc/images/test_lxc_container_image_publisher.py, tests/infrastructure/adapters/clients/test_lxc_swarm_runtime.py]
contract_locks: [shared-process-runner-contract, image-publisher-error-model]
architecture_locks: [infrastructure-only-process-boundary, secret-redaction-boundary]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.lxc.images.test_lxc_container_image_publisher tests.infrastructure.adapters.clients.test_lxc_swarm_runtime]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: final status only after redaction and byte-transfer evidence
  adr: none
stop_conditions: [raw credentials/output exposed, byte stream corruption, cache failure converted to success, image policy moved into generic runner]
```

### Slice 07 — Migrate HostPreflightProbe Git probes

Purpose: replace direct Git subprocess calls in `HostPreflightProbe` for
`git check-ignore` and `git ls-files` while preserving fail-soft behavior and
tracked-file fallback scanning.

Prerequisites: S02 complete; S01 confirms no service-fingerprint strategy
change is needed.

Allowed write scope: `host_preflight_probe.py` and its focused tests.

Done criteria: missing or unresponsive Git cannot hang preflight;
`path_ignored_by_git()` remains false when inspection is unavailable;
tracked-file fallback remains available; no live mutation is introduced; the
target has no direct process spawn.

```yaml
slice_id: S07
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Tester, Senior System Architect]
affected_files: [src/tiny_swarm_world/infrastructure/adapters/preflight/host_preflight_probe.py, tests/infrastructure/adapters/preflight/test_host_preflight_probe.py]
affected_modules: [infrastructure.adapters.preflight.host_preflight_probe]
affected_contracts: [PortHostPreflightProbe fail-soft Git inspection behavior]
dependencies: [S02]
parallel_group: ADAPTER-MIGRATIONS
file_locks: [src/tiny_swarm_world/infrastructure/adapters/preflight/host_preflight_probe.py, tests/infrastructure/adapters/preflight/test_host_preflight_probe.py]
contract_locks: [shared-process-runner-contract, HostPreflightProbe-fail-soft-contract]
architecture_locks: [infrastructure-only-process-boundary, issue-187-boundary]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.preflight.test_host_preflight_probe]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: final status only after fallback evidence
  adr: none
stop_conditions: [Git unavailability becomes fatal, fallback removed, service-fingerprint strategy scope introduced]
```

### Slice 08 — Architecture enforcement, after-inventory, documentation, and audit handoff

Purpose: add the static/architecture guard for unapproved direct production
process spawning, complete the after-inventory, synchronize Arc42 with verified
implementation status, assemble issue evidence, and obtain independent
completion review.

Prerequisites: S03, S04, S05, S06, and S07 complete; all focused tests pass.

Allowed write scope: new or narrowly updated architecture tests, issue
evidence, and the Arc42 files named in the workflow. Do not weaken existing
architecture tests or expand the allowlist without a documented rationale.

Done criteria:

- The guard covers at least `subprocess.run`, `subprocess.Popen`,
  `asyncio.create_subprocess_exec`, and
  `asyncio.create_subprocess_shell`.
- It rejects new unapproved direct spawning in production infrastructure
  adapters while excluding intentional tests/tools and explicitly documented
  compatibility/runner boundaries.
- Before and after inventories are complete and consistent.
- All issue requirements map to implementation and verification evidence.
- Arc42 distinguishes planned and implemented Issue #188 behavior.
- Requirement Lead, System Architect Reviewer, and Test/Evidence Reviewer sign
  off before the independent Issue Completion Auditor.

```yaml
slice_id: S08
profile: FULL_PATH
owner: Senior System Architect
secondary_reviewers: [Senior Tester, Senior Requirement Engineer, Senior Documentation Engineer, Issue Completion Auditor]
affected_files: [tests/architecture/test_process_spawn_boundaries.py, .tiny-swarm/evidence/solid-command-runner/**, .tiny-swarm-world/evidence/solid-command-runner/**, documentation/arc42/05_building_blocks.adoc, documentation/arc42/08_concepts.adoc, documentation/arc42/10_quality_requirements.adoc, documentation/arc42/11_risks_and_debt.adoc]
affected_modules: [architecture tests, issue evidence, Arc42]
affected_contracts: [production process-spawn allowlist, issue completion evidence contract]
dependencies: [S03, S04, S05, S06, S07]
parallel_group: SERIAL-AUDIT
file_locks: [tests/architecture/test_process_spawn_boundaries.py, .tiny-swarm/evidence/solid-command-runner/**, .tiny-swarm-world/evidence/solid-command-runner/**, documentation/arc42/05_building_blocks.adoc, documentation/arc42/08_concepts.adoc, documentation/arc42/10_quality_requirements.adoc, documentation/arc42/11_risks_and_debt.adoc]
contract_locks: [production-process-spawn-allowlist, issue-completion-evidence]
architecture_locks: [hexagonal-boundaries, architecture-enforcement, planned-vs-implemented-documentation]
quality_gates:
  targeted: [python3 tools/quality_gate.py arch-lint, python3 tools/quality_gate.py arch-tests, python3 tools/quality_gate.py test, git diff --check]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: update only from verified implementation evidence
  adr: review; create only if a new architecture decision is unavoidable
stop_conditions: [unverified exception, weakened guard, missing evidence, Arc42 overclaim, failed independent audit]
```

## Slice Dependency Graph

```text
S01 -> S02
S02 -> S03
S02 -> S04
S02 -> S05
S02 -> S06
S02 -> S07
S03 -> S08
S04 -> S08
S05 -> S08
S06 -> S08
S07 -> S08
```

Topological execution groups:

1. `S01` — serial baseline and contract gate.
2. `S02` — serial shared runner and composition contract.
3. `S03`, `S04`, `S05`, `S06`, `S07` — eligible adapter streams after S3D
   validates disjoint locks and stable contracts.
4. `S08` — serial architecture, documentation, evidence, and audit handoff.

## Parallel Execution

- Can this workflow run in parallel? Yes, only for S03–S07 after S01/S02 and
  S3D confirm independence; S01, S02, and S08 are serial.
- Conflicting workflows: any workflow modifying the shared infrastructure
  process contract, the five target adapters, `composition.py`, architecture
  tests, or the same issue evidence paths; specifically concurrent execution
  of Issues #187, #189, #190, #192, #184, or #195 is not allowed when locks
  overlap.
- Shared files: the shared runner contract, composition wiring, issue evidence
  package, architecture tests, and Arc42 files.
- Shared infrastructure: none is required for local tests; live validation is
  not part of the default workflow.
- Requires isolated worktree: yes for every execution slice, and mandatory for
  every parallel stream.
- Requires serialized live validation: yes by default; this workflow has no
  live validation gate and does not authorize infrastructure mutation.
- Merge-order constraints: S01 before S02; S02 before all adapter streams;
  all adapter streams before S08; Codex consolidates streams and owns the
  final integration decision.

## Automatic Work Distribution Policy

`workflow execute` must automatically analyze every executable slice for safe
specialist stream decomposition. It uses real Codex subagents where supported;
when callable subagents are unavailable or not visible, it performs the same
review through explicit role-based fallback in the main execution thread and
records that fallback.

Before implementation, each slice requires
`.codex/evidence/slice-<number>-distribution.md`. Each implemented slice
requires `.codex/evidence/slice-<number>-consolidation.md`. Codex remains the
final integration owner for consolidation, tests, evidence, PR readiness, and
merge readiness.

Stream map:

- backend: Senior Python Automation Developer;
- frontend: Console/status UI skills only when a verified terminal impact
  exists; browser React is forbidden here;
- tests: Senior Tester;
- runtime: Senior DevOps Engineer, limited to non-live runtime review;
- documentation: Senior Documentation Engineer;
- quality: quality-gate skills and Senior Tester;
- architecture: Senior System Architect;
- security: Senior Security Sandbox Engineer and relevant security skills.

Do not parallelize overlapping files, unclear architecture boundaries,
contradictory requirements, mandatory ordering, shared migrations, strict
database/schema sequencing, generated-file conflicts, a Three-Amigos
not-safely-parallelizable decision, unclear secrets handling, or weakened
safety guards. Shared runner contract work and final architecture/evidence
work are mandatory serial boundaries.

## Git Worktree Execution Rule

Every workflow execution requires an isolated Git worktree. Parallel stream
branches must be named:

`<workflow-branch>-slice-<number>-<stream>`

Stream workers must verify that their active branch belongs to this workflow
before writing, must not work on `main`, `master`, `develop`, or another shared
branch, and must not merge directly to the workflow or implementation branch.
Codex consolidates accepted stream results only after distribution evidence,
stream-specific checks, locks, and requirements are reviewed.

## Role and Ownership Map

- Senior Workflow Architect: workflow creation, slice ordering, dependency
  graph, locks, and handoff.
- Senior Requirement Engineer: issue decomposition, requirement matrix,
  before/after inventory completeness, and drift review.
- Senior System Architect: infrastructure-only process boundary, composition
  wiring, architecture guard, Arc42, and stop decisions.
- Senior Python Automation Developer: runner and adapter implementation slices.
- Senior Tester: focused regression tests, architecture tests, quality gates,
  and evidence verification.
- Senior Documentation Engineer: Arc42 and planned-versus-implemented wording.
- Senior Security Sandbox Engineer: command, timeout, shell, credential,
  diagnostic, and evidence-redaction review.
- Senior DevOps Engineer: non-live runtime and operational safety review.
- Issue Completion Auditor: independent final PASS/INCOMPLETE/BLOCKED/REJECTED
  decision; the implementer cannot self-approve completion.
- Console/status UI reviewer: `NOT_APPLICABLE`.
- Browser React reviewer: `FORBIDDEN_UNLESS_SEPARATE_FRONTEND_WORKFLOW`.

## Issue Completion Discipline

- Requirement matrix path: `.tiny-swarm/evidence/solid-command-runner/requirement_matrix.md`.
- Required evidence path: `.tiny-swarm/evidence/solid-command-runner/`.
- Issue-requested Three-Amigos path:
  `.tiny-swarm-world/evidence/solid-command-runner/three-amigos.md`.
- Required evidence files: `requirement_matrix.md`,
  `implementation_summary.md`, `changed_files.md`, `test_results.md`,
  `remaining_risks.md`, `acceptance_checklist.md`, `three-amigos.md`,
  `process-spawn-inventory-before.md`, `process-spawn-inventory-after.md`,
  and `issue-completion-audit.md`; live or external evidence is optional and
  must use the verification-state policy if separately authorized.
- Requirement Lead review: Senior Requirement Engineer before implementation,
  after the final inventory, and before completion.
- System Architect Reviewer review: Senior System Architect before runner
  implementation and after architecture enforcement/documentation.
- Test / Evidence Reviewer review: Senior Tester after focused tests and full
  quality gate; local checks do not imply live or external success.
- Issue Completion Auditor review: required after all evidence is assembled.
- DONE blocking rule: any open, partially implemented, unverified,
  unavailable-required, or unevidenced requirement forces `INCOMPLETE`,
  `BLOCKED`, or `FAILED`; it must never be reported as `DONE`.

## Quality-Gate Expectations

Use only the commands authorized by `QUALITY.md`:

```bash
python3 tools/quality_gate.py lint
python3 tools/quality_gate.py arch-lint
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py typecheck
python3 tools/quality_gate.py test
python3 tools/quality_gate.py quality
git diff --check
```

Python commands and quality gates run in WSL/Linux. Focused tests use
`PYTHONPATH=src`. The full local quality gate is the default authority for
local completion. No live Incus, LXC, Docker, Swarm, networking, registry,
service bootstrap, browser, or SonarQube success is claimed by this workflow.

Authoring validation: `git diff --check` passed. The full WSL quality command
was attempted but timed out after 120 seconds; it is not reported as passed.
Because this workflow-authoring diff contains no Python source or test changes,
the timeout is recorded as a non-success informational result for authoring;
`workflow execute` must run and record the full quality gate for implementation
readiness.

## Documentation Synchronization Points

- S01 records the requirement matrix, Three-Amigos gate, and complete before
  process-spawn inventory.
- S02 records the planned shared infrastructure boundary and composition
  wiring without changing domain/application architecture.
- S08 updates `documentation/arc42/05_building_blocks.adoc`,
  `08_concepts.adoc`, `10_quality_requirements.adoc`, and
  `11_risks_and_debt.adoc` only from verified implementation evidence.
- Arc42 must distinguish Issue #188 planned state during authoring from
  implemented state during execution.
- No ADR is created unless execution discovers a new architecture decision
  that cannot be resolved from this issue and existing repository authority.

## Stop Conditions and Uncertainty Escalation

Stop and report rather than guess when:

- the issue body, public port contract, or current baseline cannot be read;
- the complete production inventory cannot be established;
- a spawn site cannot be classified without changing scope;
- the shared runner contract would require application/domain imports;
- adapter policy would move into the generic runner;
- shell, timeout, retry, byte-stream, cleanup, redaction, or error semantics
  cannot be proven unchanged;
- application ports or Issue #189 backend-CLI ownership would change;
- architecture locks overlap or S3D finds a cycle/unknown dependency;
- local quality gates fail and cannot be repaired within the declared scope;
- required evidence is missing or a requirement has no verification mapping;
- Arc42 would need to describe planned behavior as implemented;
- live infrastructure mutation or unavailable external evidence would be
  required for a local completion claim.

Typed failures route through the repository policy: architecture failures to
the System Architect/Root Architect path; Python lint/type/build failures to
the Python owner and quality-gate owner; test failures to Senior Tester; doc
governance failures to Senior Documentation Engineer and Requirement Lead;
lock conflicts to execution orchestration; and unknown failures to Root
Architect escalation.

## Commit and Push Plan

Workflow authoring output is committed only on
`feature/workflow-issue-188-shared-command-runners-20260809` after workflow,
context-pack, issue evidence, Arc42 checks, and `git diff --check` pass. The
default publication target is only
`origin/feature/workflow-issue-188-shared-command-runners-20260809`.

This is guarded workflow publication: no pull request creation or merge,
remote branch deletion, local cleanup, force-push, or push to `main`. The
implementation branch `feature/issue-188-shared-command-runners` is handed to
`workflow execute` and is not created or implemented by this workflow-create
step. `push auto` is not part of workflow-create publication.

## Definition of Done

### Workflow-authoring completion

- Dedicated workflow branch exists, is active, and has a local ref.
- `documentation/workflow/workflow.md` is complete and validated.
- `documentation/workflow/context-pack.md` and `.json` are present and hash
  governing inputs.
- Requirement matrix, Four-Role Three-Amigos gate, and initial inventory
  evidence exist.
- Arc42 architecture documentation is checked/updated with planned wording.
- Every slice has metadata, dependencies, locks, stop conditions, evidence
  paths, and quality commands.
- The workflow branch is committed and guarded-pushed to its matching origin
  branch.

### Issue-execution completion

- All requirements in the matrix are implemented without silent scope
  reduction.
- All five minimum adapters are migrated with compatibility behavior proved.
- Complete before/after process inventories are consistent.
- Architecture/static enforcement rejects new unapproved direct spawning.
- Local quality is green, with exact commands recorded.
- Required evidence files exist and map every requirement to verification.
- The Issue Completion Auditor returns `PASS`; otherwise status remains
  `INCOMPLETE`, `BLOCKED`, `FAILED`, or `REJECTED`.

## Handoff to `workflow execute`

Before implementation, the executor must re-check the issue, active workflow,
implementation branch, requirement matrix, Three-Amigos note, baseline commit,
Arc42 notes, all locks, and the complete process-spawn inventory. It must run
S01, then S02, then only the disjoint adapter streams authorized by S3D, then
S08. It must not call `workflow create` backwards.

No live infrastructure command is authorized by this workflow. If live or
external verification is separately requested later, it must use explicit
consent, prerequisite, redaction, and `LIVE_*`/`EXTERNAL_GATE_*` state
classification under `documentation/process/verification-state-policy.md`.

## Arc42 Check Status

`documentation/arc42/05_building_blocks.adoc`,
`08_concepts.adoc`, `10_quality_requirements.adoc`, and
`11_risks_and_debt.adoc` were reviewed and updated with planned Issue #188
process-runner, quality, and risk notes. No implementation claim is made by
this workflow. Existing Issue #183 LXC decomposition and command safety
documentation remain authoritative. No ADR is required at authoring time.

## Workflow Handoff Record

- Workflow ID: `issue-188-20260809`.
- Workflow version: `issue-188-v1.0.0`.
- Authoring branch: `feature/workflow-issue-188-shared-command-runners-20260809`.
- Implementation branch: `feature/issue-188-shared-command-runners` (issue-requested; verify at execution).
- Requirement matrix: `.tiny-swarm/evidence/solid-command-runner/requirement_matrix.md`.
- Three-Amigos note: `.tiny-swarm-world/evidence/solid-command-runner/three-amigos.md`.
- Before-inventory: `.tiny-swarm/evidence/solid-command-runner/process-spawn-inventory-before.md`.
- Required after-inventory: `.tiny-swarm/evidence/solid-command-runner/process-spawn-inventory-after.md`.
- Local quality authority: `python3 tools/quality_gate.py quality`.
- Live/external gates: not unconditional; no success claimed during authoring.
- Publication target: `origin/feature/workflow-issue-188-shared-command-runners-20260809`.
- Authoring commit SHA: `54ae7fe55312693a4739014620491b50ea62df84`.
- Guarded publication verification: `PASS`; remote ref
  `refs/heads/feature/workflow-issue-188-shared-command-runners-20260809`
  resolves to the authoring commit above. No PR merge, branch deletion, or
  cleanup was performed.
