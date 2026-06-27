# Workflow: Centralize Project Paths As Injectable Infrastructure Configuration

Version: `workflow-project-paths-di-v1.0.0`
Workflow ID: `workflow-project-paths-di-20260627`
Created: `2026-06-27`
Branch: `architecture/workflow-project-paths-di-20260627`
Status: `CREATED_READY_FOR_EXECUTION`
Evidence Root: `.codex/evidence/workflow-project-paths-di-20260627/`

## Executive Summary

Introduce `ProjectPaths` as an immutable infrastructure configuration value
object and make repository, infra, config, local-state, and log paths centrally
managed from the composition root. Keep existing `project_paths.py` free
functions as a compatibility facade until direct adapter imports are migrated.
The workflow must improve single point of impact and testability without
turning path lookup into a broad DI-container rewrite.

## Requirement Clarification Gate

Original Request:

- Create a `workflow create` for turning the current `project_paths.py`
  function surface into centrally managed `ProjectPaths` configuration.
- The user prefers the "single point of impact" direction.

Interpreted Intent:

- Author an executable workflow that adds an immutable `ProjectPaths` value
  object, central default construction, composition-root ownership, adapter
  injection where practical, tests, and documentation synchronization.

Change Type:

- Architecture refactoring and infrastructure configuration cleanup.

Affected Process Strand:

- `workflow create`, followed by a later `workflow execute`.

Affected Architecture Area:

- Shared infrastructure path configuration.
- Infrastructure adapter construction.
- Composition root wiring.
- Tests for path behavior and repository adapter defaults.

Explicit Requirements:

- Preserve Linux/WSL-only product direction.
- Preserve hexagonal architecture boundaries.
- Keep path behavior centralized.
- Do not introduce a heavy DI container rewrite for this change.
- Keep `TSW_REPOSITORY_ROOT` and `TSW_INFRA_ROOT` overrides.
- Do not remove existing function callers before safe migration.

Implicit Requirements:

- Keep domain and application code independent from filesystem and
  infrastructure path details.
- Use `composition.py` as the runtime composition root.
- Preserve current defaults for `repository_root`, `infra_root`, `config_root`,
  `local_state_root`, and `logs_root`.
- Add or update tests because path handling, repositories, adapters, and
  composition behavior are affected.
- Do not run live LXD, Incus, LXC, Docker Swarm, compose, socat, netplan, or
  service bootstrap commands.

Assumptions:

- `source_root()` is not a primary runtime dependency and can stay as
  compatibility surface unless execution proves otherwise.
- Existing path defaults are correct product behavior and should be preserved.
- Adapter constructors can be migrated incrementally by accepting an optional
  `ProjectPaths` argument while retaining existing explicit `path` arguments.
- The existing `infra_core_container` is not the target of this workflow; the
  change should use explicit constructor dependencies and `composition.py`.

Non-Goals:

- No new general-purpose DI framework.
- No rewrite of `infra_core_container`.
- No service extraction, microservice boundary, React frontend, Java, Maven, or
  Spring Boot work.
- No live infrastructure validation.
- No removal of compatibility functions until all direct imports are migrated
  and tests prove no users remain.
- No broad reorganization of repository adapters outside path injection.

Risks:

- Migrating too many constructors at once could create noisy unrelated changes.
- Global helper functions might still be used by tests or uncomposed legacy
  adapter paths.
- Environment override precedence could drift if the factory and compatibility
  functions are not tested together.
- `LoggerFactory` is a class-level helper and may need a narrower migration
  path than repository adapters.

Open Questions:

- None blocking for workflow creation.

Blocking Questions:

- None.

Confidence Level:

- 90 percent.

Decision:

- `READY_FOR_WORKFLOW`

## Five-Role Review

Senior Requirement Engineer:

- The target is clear: centralize path calculation and injection while
  preserving current behavior and compatibility.

Senior System Architect:

- The change belongs in infrastructure and composition. Domain and application
  layers must not import `ProjectPaths` directly. A value object plus explicit
  wiring matches the existing architecture better than expanding the existing
  container.

Senior Python Automation Developer:

- Implement the change incrementally: add `ProjectPaths`, factory methods, and
  compatibility functions first; then migrate direct infrastructure consumers
  with focused tests.

Senior React Frontend Developer:

- No browser or React frontend scope exists. The repository explicitly is not a
  React frontend project.

Senior Tester:

- Tests must prove environment overrides, default root discovery, derived path
  values, and migrated adapter defaults. Full quality gate is required because
  path handling and repositories are affected.

## Target Picture

Verified baseline:

- Active branch:
  `architecture/workflow-project-paths-di-20260627`.
- `src/tiny_swarm_world/infrastructure/project_paths.py` currently exposes
  free functions for repository, source, infra, config, local-state, and log
  paths.
- Production imports exist in infrastructure logging, file-management,
  repository, preflight, and LXC swarm runtime adapters.
- Documentation records `TSW_REPOSITORY_ROOT` and `TSW_INFRA_ROOT` as
  `project_paths.py` contracts.
- `composition.py` is the documented runtime wiring root.

Target outcome:

- `ProjectPaths` is an immutable infrastructure value object with derived path
  construction and environment-aware default factory.
- Existing free functions in `project_paths.py` delegate to the same default
  path configuration until removed by a later cleanup.
- Composition root creates or passes `ProjectPaths` explicitly for migrated
  infrastructure adapters.
- Migrated adapters accept optional `ProjectPaths` without losing their
  explicit test path override behavior.
- Tests and documentation confirm the single point of impact.

## Scope

In scope:

- `src/tiny_swarm_world/infrastructure/project_paths.py`
- `src/tiny_swarm_world/infrastructure/composition.py`
- Infrastructure adapters currently importing `project_paths.py`
- `src/tiny_swarm_world/infrastructure/logging/logger_factory.py`
- Relevant tests under `tests/infrastructure/**` and `tests/architecture/**`
- `documentation/configuration/config-contract-inventory.md`
- `documentation/architecture/responsibility-separation-analysis.md`
- `documentation/arc42/05_building_blocks.adoc`
- `documentation/workflow/**`
- `.codex/evidence/workflow-project-paths-di-20260627/**`

Out of scope:

- Domain and application layer changes except tests that prove boundaries.
- Replacing or redesigning `infra_core_container`.
- Live infrastructure commands.
- Changing actual repository layout.
- Removing `TSW_REPOSITORY_ROOT` or `TSW_INFRA_ROOT`.
- Removing all free functions in this workflow unless execution proves every
  caller has been migrated safely.

Architecture constraints:

- Preserve hexagonal dependency direction.
- Keep concrete adapter construction in `composition.py`.
- Keep filesystem path calculation inside infrastructure.
- Application services may receive ports and services, not concrete path
  adapters or filesystem helpers.
- Tests must continue to use Linux/WSL path expectations.

## Python Automation Assessment

This workflow is Python infrastructure refactoring. It should add a small
immutable value object, not a new framework. Constructor injection should be
targeted to adapters that already own file, YAML, logging, local-state, or
compose path behavior.

## Frontend Assessment

No frontend or browser work is included. Console/status UI behavior is not
expected to change.

## Test Strategy

Targeted verification:

- `PYTHONPATH=src python3 -m unittest tests.infrastructure.test_project_paths`
- `PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition`
- `PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_command_repository_yaml_contract`
- `PYTHONPATH=src python3 -m unittest tests.architecture.test_local_state_storage`
- `python3 tools/quality_gate.py arch-tests`
- `git diff --check`

Required final verification:

- `python3 tools/quality_gate.py quality`

If a targeted test file does not yet exist, execution must create or update the
nearest relevant test file instead of claiming the command passed.

## Resilience Requirements

- Default path construction must be deterministic and idempotent.
- Environment overrides must remain explicit and testable.
- No constructor may execute external commands or mutate the filesystem merely
  by receiving `ProjectPaths`.
- Rerunning the workflow after a partial implementation must not change
  unrelated paths or docs.

## Ordered Slices

### Slice 01 - Baseline Audit And Path Contract Tests

Purpose:

- Reconfirm current imports, document execution distribution, and add focused
  tests for `ProjectPaths` behavior before migrating consumers.

Prerequisites:

- Active branch is `architecture/workflow-project-paths-di-20260627`.
- Working tree changes are understood and task-scoped.

```yaml
slice_id: "01"
profile: "NORMAL_PATH"
owner: "Senior Tester"
secondary_reviewers:
  - "Senior Python Automation Developer"
  - "Senior System Architect"
affected_files:
  - "tests/infrastructure/test_project_paths.py"
  - ".codex/evidence/workflow-project-paths-di-20260627/slice-01-distribution.md"
  - ".codex/evidence/workflow-project-paths-di-20260627/slice-01-consolidation.md"
affected_modules:
  - "tiny_swarm_world.infrastructure.project_paths"
affected_contracts:
  - "TSW_REPOSITORY_ROOT"
  - "TSW_INFRA_ROOT"
dependencies: []
parallel_group: "serial-path-config"
file_locks:
  - "src/tiny_swarm_world/infrastructure/project_paths.py"
  - "tests/infrastructure/test_project_paths.py"
  - ".codex/evidence/workflow-project-paths-di-20260627/**"
contract_locks:
  - "Repository and infra root path derivation"
architecture_locks:
  - "Path configuration remains infrastructure-owned"
quality_gates:
  targeted:
    - "rg -n \"project_paths|ProjectPaths|TSW_REPOSITORY_ROOT|TSW_INFRA_ROOT|config_root\\(|infra_root\\(|repository_root\\(|logs_root\\(\" src tests documentation infra README.md AGENTS.md QUALITY.md"
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.test_project_paths"
  required: []
documentation:
  arc42: "Checked; no edit before implementation unless central path ownership changes architecture text."
  adr: "No ADR expected for value-object refactoring."
stop_conditions:
  - "Stop if active consumers are found outside infrastructure/tests/documentation."
  - "Stop if path behavior cannot be preserved with environment overrides."
  - "Stop if tests require Windows-specific behavior."
```

Done criteria:

- Baseline imports are classified.
- Tests prove default and override path derivation for the new or planned
  `ProjectPaths` contract.

### Slice 02 - Add ProjectPaths And Compatibility Facade

Purpose:

- Implement `ProjectPaths` in `project_paths.py` and keep existing free
  functions delegating to the same central default configuration.

Prerequisites:

- Slice 01 tests describe expected behavior.

```yaml
slice_id: "02"
profile: "NORMAL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Tester"
  - "Senior System Architect"
affected_files:
  - "src/tiny_swarm_world/infrastructure/project_paths.py"
  - "tests/infrastructure/test_project_paths.py"
  - ".codex/evidence/workflow-project-paths-di-20260627/slice-02-distribution.md"
  - ".codex/evidence/workflow-project-paths-di-20260627/slice-02-consolidation.md"
affected_modules:
  - "tiny_swarm_world.infrastructure.project_paths"
affected_contracts:
  - "ProjectPaths default factory"
  - "project_paths compatibility functions"
dependencies:
  - "01"
parallel_group: "serial-path-config"
file_locks:
  - "src/tiny_swarm_world/infrastructure/project_paths.py"
  - "tests/infrastructure/test_project_paths.py"
contract_locks:
  - "Existing path helper behavior must remain compatible"
architecture_locks:
  - "No domain/application dependency on infrastructure path value object"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.test_project_paths"
  required: []
documentation:
  arc42: "No immediate arc42 edit expected."
  adr: "No ADR expected unless execution changes path ownership semantics."
stop_conditions:
  - "Stop if compatibility functions cannot preserve existing return values."
  - "Stop if a global mutable singleton is introduced."
  - "Stop if import-time side effects are added."
```

Done criteria:

- `ProjectPaths` is immutable.
- Default factory preserves `TSW_REPOSITORY_ROOT` and `TSW_INFRA_ROOT`.
- Existing helper functions still work through the central default.

### Slice 03 - Wire ProjectPaths Through Composition And Adapters

Purpose:

- Move selected direct infrastructure consumers from global path helpers to
  explicit `ProjectPaths` injection while retaining constructor defaults for
  compatibility.

Prerequisites:

- Slice 02 completed and tests pass.

```yaml
slice_id: "03"
profile: "NORMAL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "src/tiny_swarm_world/infrastructure/adapters/file_management/file_manager.py"
  - "src/tiny_swarm_world/infrastructure/adapters/file_management/file_locator.py"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/desired_inventory_yaml_repository.py"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/node_provider_config_yaml_repository.py"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/port_registry_yaml_repository.py"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/local_state_paths.py"
  - "src/tiny_swarm_world/infrastructure/adapters/preflight/host_preflight_probe.py"
  - "src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py"
  - "src/tiny_swarm_world/infrastructure/logging/logger_factory.py"
  - "tests/infrastructure/test_composition.py"
  - "tests/infrastructure/adapters/repositories/test_command_repository_yaml_contract.py"
  - "tests/architecture/test_local_state_storage.py"
  - ".codex/evidence/workflow-project-paths-di-20260627/slice-03-distribution.md"
  - ".codex/evidence/workflow-project-paths-di-20260627/slice-03-consolidation.md"
affected_modules:
  - "tiny_swarm_world.infrastructure.composition"
  - "tiny_swarm_world.infrastructure.adapters"
  - "tiny_swarm_world.infrastructure.logging"
affected_contracts:
  - "Infrastructure adapter default path construction"
dependencies:
  - "02"
parallel_group: "serial-path-config"
file_locks:
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "src/tiny_swarm_world/infrastructure/adapters/**"
  - "src/tiny_swarm_world/infrastructure/logging/logger_factory.py"
  - "tests/infrastructure/**"
  - "tests/architecture/test_local_state_storage.py"
contract_locks:
  - "Adapter explicit path override behavior"
  - "Composition root owns default ProjectPaths construction"
architecture_locks:
  - "Application services must not construct infrastructure paths"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition"
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_command_repository_yaml_contract"
    - "PYTHONPATH=src python3 -m unittest tests.architecture.test_local_state_storage"
    - "python3 tools/quality_gate.py arch-tests"
  required: []
documentation:
  arc42: "Update building-block text only if composition/path ownership wording changes."
  adr: "No ADR expected; stop if execution changes public architecture policy."
stop_conditions:
  - "Stop if constructor migration would require application-layer imports from infrastructure."
  - "Stop if migration would remove explicit test path overrides."
  - "Stop if LoggerFactory requires a broad logging redesign."
```

Done criteria:

- Composition root can create or pass `ProjectPaths` explicitly.
- Migrated adapters use injected paths or compatibility defaults.
- No new domain or application import of infrastructure path configuration
  appears.

### Slice 04 - Documentation Sync And Final Quality Gate

Purpose:

- Synchronize documentation and run final verification.

Prerequisites:

- Slices 01 through 03 completed or stopped with evidence.

```yaml
slice_id: "04"
profile: "NORMAL_PATH"
owner: "Senior Documentation Engineer"
secondary_reviewers:
  - "Senior Tester"
  - "Senior System Architect"
affected_files:
  - "documentation/configuration/config-contract-inventory.md"
  - "documentation/architecture/responsibility-separation-analysis.md"
  - "documentation/arc42/05_building_blocks.adoc"
  - "documentation/workflow/workflow.md"
  - "documentation/workflow/context-pack.md"
  - "documentation/workflow/context-pack.json"
  - ".codex/evidence/workflow-project-paths-di-20260627/slice-04-distribution.md"
  - ".codex/evidence/workflow-project-paths-di-20260627/slice-04-consolidation.md"
affected_modules:
  - "documentation"
affected_contracts:
  - "Path configuration ownership documentation"
dependencies:
  - "03"
parallel_group: "serial-path-config"
file_locks:
  - "documentation/configuration/config-contract-inventory.md"
  - "documentation/architecture/responsibility-separation-analysis.md"
  - "documentation/arc42/05_building_blocks.adoc"
  - "documentation/workflow/**"
  - ".codex/evidence/workflow-project-paths-di-20260627/**"
contract_locks:
  - "Documentation must describe implemented behavior only"
architecture_locks:
  - "arc42 and responsibility analysis stay aligned with source evidence"
quality_gates:
  targeted:
    - "rg -n \"project_paths|ProjectPaths|TSW_REPOSITORY_ROOT|TSW_INFRA_ROOT|config_root\\(|infra_root\\(|repository_root\\(|logs_root\\(\" src tests documentation infra README.md AGENTS.md QUALITY.md"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "Update if Slice 03 changes composition/path ownership wording."
  adr: "No ADR expected unless central path ownership becomes a new architecture decision."
stop_conditions:
  - "Stop if documentation would claim full migration while compatibility functions remain active."
  - "Stop if final quality gate fails for unrelated reasons that cannot be isolated."
  - "Stop if an ADR is needed before continuing."
```

Done criteria:

- Documentation reflects the implemented migration state.
- Full quality gate passes or failures are classified with exact evidence.

## Slice Dependency Graph

```text
01 Baseline Audit And Path Contract Tests
  -> 02 Add ProjectPaths And Compatibility Facade
    -> 03 Wire ProjectPaths Through Composition And Adapters
      -> 04 Documentation Sync And Final Quality Gate
```

## Parallel Execution

- Can this workflow run in parallel? No write-capable parallel execution.
- Conflicting workflows: any workflow touching `project_paths.py`,
  `composition.py`, infrastructure adapter constructors, logging path defaults,
  repository path defaults, or `documentation/workflow/**`.
- Shared files: `src/tiny_swarm_world/infrastructure/project_paths.py`,
  `src/tiny_swarm_world/infrastructure/composition.py`, infrastructure
  adapters, tests, and workflow documentation.
- Shared infrastructure: none; no live infrastructure may be used.
- Requires isolated worktree: yes for any concurrent workflow execution.
- Requires serialized live validation: live validation is forbidden.
- Merge-order constraints: execute slices in order 01, 02, 03, 04.

## Automatic Work Distribution Policy

`workflow execute` must automatically inspect each slice for safe specialist
stream decomposition. Real Codex subagents may be used where supported. If
subagents are unavailable, execute the same checks through explicit role-based
fallback in the main thread and record that fallback in evidence.

Required evidence before implementation:

- `.codex/evidence/workflow-project-paths-di-20260627/slice-<number>-distribution.md`

Required evidence after implemented slices:

- `.codex/evidence/workflow-project-paths-di-20260627/slice-<number>-consolidation.md`

Stream map:

- Backend/Python: Slices 01, 02, and 03.
- Frontend/React: not applicable.
- Tests: Slices 01, 02, 03, and 04.
- Runtime/DevOps: safety review only; no live commands.
- Documentation: Slice 04.
- Quality: Slice 04.
- Architecture: Slices 01, 03, and 04.
- Security: verify no secrets or host-specific absolute paths are introduced.

Non-parallelization rules:

- Do not parallelize overlapping file edits.
- Do not parallelize unclear architecture ownership.
- Do not parallelize contradictory requirements.
- Do not parallelize mandatory ordered test-first refactoring.
- Do not parallelize generated-file conflict resolution.
- Do not parallelize if Three Amigos marks the slice not safely
  parallelizable.
- Do not proceed with unclear secrets handling or weakened safety guards.

Codex remains the final integration owner for consolidation, tests, evidence,
PR readiness, and merge readiness.

## Git Worktree Execution Rule

Execute this workflow only from branch
`architecture/workflow-project-paths-di-20260627` or from an isolated worktree
branch explicitly derived for this workflow. Subagents or stream workers must
verify the active branch before writing files and must not merge directly.
Codex consolidates accepted changes after evidence and tests pass.

## Role Ownership Map

- Senior Workflow Architect: workflow structure, dependency ordering, and
  execution policy.
- Senior Requirement Engineer: requirement drift, assumptions, and non-goals.
- Senior System Architect: hexagonal boundaries, composition-root ownership,
  and ADR/arc42 consistency.
- Senior Python Automation Developer: `ProjectPaths` implementation and
  adapter migration.
- Senior Documentation Engineer: documentation synchronization.
- Senior Tester: targeted tests and final quality gate.
- Senior React Frontend Developer: confirms no frontend scope.
- Senior DevOps Engineer: confirms no live infrastructure execution.

## Quality-Gate Expectations

From `QUALITY.md`:

- Preferred full gate: `python3 tools/quality_gate.py quality`
- Targeted gates during development:
  - `python3 tools/quality_gate.py test`
  - `python3 tools/quality_gate.py arch-tests`
  - `git diff --check`

The full gate is required for final readiness because the workflow changes
path handling, repository adapters, composition wiring, tests, and
documentation.

## Documentation Synchronization Points

- Update configuration contract inventory for `ProjectPaths` ownership after
  implementation.
- Update responsibility separation analysis if `project_paths.py` changes from
  free helper functions to an injectable shared-infrastructure config object.
- Update arc42 building-block text only when source changes make the central
  path configuration part of the documented composition-root behavior.
- Do not document complete removal of compatibility functions unless execution
  actually removes them.

## Stop Conditions

Stop and report if:

- Git repository context or active branch cannot be verified.
- Unrelated uncommitted changes appear.
- Domain or application code would need to import infrastructure path
  configuration.
- Environment override behavior cannot be preserved.
- Explicit test path overrides would be removed.
- Implementation requires redesigning the DI container.
- Documentation would present planned behavior as implemented.
- An ADR is needed before continuing.
- Any step would require live LXD, Incus, LXC, Docker Swarm, compose, netplan,
  socat, or service bootstrap commands.

## Uncertainty Escalation Rules

- If a consumer cannot be migrated cleanly, keep the compatibility facade and
  document the remaining direct import.
- If central path configuration affects public runtime behavior, escalate to
  Senior System Architect and ADR steward before claiming completion.
- If quality failures indicate hidden path coupling, stop and reassess slice
  boundaries instead of broadening the refactor.

## Commit And Push Plan

- No commit or push is authorized by this workflow creation request.
- If later requested, commit workflow creation separately from workflow
  execution changes.
- Each executed slice must be represented by exactly one slice commit when the
  workflow execution policy requests commits.

## Definition Of Done

- Workflow branch exists and is active.
- `documentation/workflow/workflow.md`,
  `documentation/workflow/context-pack.md`, and
  `documentation/workflow/context-pack.json` describe this workflow.
- Workflow contains ordered slices with machine-readable metadata.
- Path ownership, compatibility strategy, quality gates, and stop conditions
  are explicit.
- arc42 status is checked and documented.
- Handoff to `workflow execute` is clear.

## Handoff To Workflow Execute

Run `workflow execute` only after confirming:

- active branch:
  `architecture/workflow-project-paths-di-20260627`
- workflow status: `CREATED_READY_FOR_EXECUTION`
- context pack hashes are current
- no unrelated working-tree changes exist

## arc42 Check Status

- `documentation/arc42/05_building_blocks.adoc` was checked because it defines
  `composition.py` as the local composition root.
- `documentation/arc42/08_concepts.adoc` was checked because it documents
  workflow execution and shared infrastructure concepts.
- No immediate arc42 edit is required for workflow creation. Execution must
  update arc42 only if source changes make `ProjectPaths` an implemented
  documented composition-root behavior.
