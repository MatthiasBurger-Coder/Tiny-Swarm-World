# ARCH-03.09 — Harden Configuration Parsing Boundary

Workflow ID: issue-352-configuration-parsing-boundary
workflowVersion: 1.0
Status: BLOCKED_SCOPE_APPROVAL; S352-01 through S352-04 accepted
Issue: [#352](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/352)
Parent: [EPIC #313](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/313)
Branch: `architecture/workflow-352-config-parsing-20260925`
Baseline: `33aaafd5b80a3f316f4d650a9a831734dc7077e0`
Execution profile: FULL_PATH (architecture, typed contracts and lifecycle ordering).

## Executive Summary

Parse external configuration at infrastructure boundaries, pass validated internal
values into application orchestration, and fail before the first relevant
lifecycle mutation. This document plans implementation; it does not claim the
new boundary or ordering guarantees already exist.

## Requirement Clarification Gate

- Original Request: workflow create [ARCH-03.09] Harden Configuration Parsing Boundary #352.
- Interpreted Intent: create and publish a complete issue workflow, not execute it.
- Change Type: architecture hardening with supported behavior preservation.
- Affected Process Strand: workflow create, followed by a separate workflow execute.
- Affected Architecture Area: configuration adapters, typed ports/models, composition and lifecycle validation.
- Explicit Requirements: R01–R11 in [requirement-matrix.md](requirement-matrix.md).
- Implicit Requirements: parent EPIC constraints, fail-closed ordering, redaction, safe errors, compatibility and independent evidence review.
- Assumptions: existing supported defaults and precedence are authoritative; legitimate typed mappings remain permitted; configuration not consumed by TSW is classified as infrastructure pass-through.
- Non-Goals: runtime/provider replacement, Java/React/Kubernetes expansion, credential policy changes, parser-library replacement, generic schema framework, unrelated refactors or live infrastructure execution.
- Risks: lazy loading after mutation, permissive coercion, duplicate keys, silent filtering, compatibility drift, validation/use mismatch and accidental secret disclosure.
- Open Questions: no blocking authoring questions; Slice 01 resolves exact per-consumer mutation ordering before implementation.
- Blocking Questions: none. Initial detached HEAD was resolved with explicit user authorization (`ja`) before artifact changes.
- Confidence Level: 94 percent; clarification attempt 1 of maxRetries 3.
- Decision: READY_FOR_WORKFLOW, subject to Slice 01 inventory and per-slice S3/S3D preflight.
- Existing workflow relationship: replace the previous active #252 workflow and indexed issue plans on this isolated branch. Full regeneration is required by workflow-authoring; previous files remain in Git history at the baseline. No unrelated issue is marked complete.

## Verified Baseline and Target Picture

`ruamel.yaml` imports are already infrastructure-only. Application raw-data leakage
exists through `PortLocalFileStorage.load_yaml() -> object` into
`SecretManifestRenderer`; that adapter currently uses PyYAML. Existing inventory,
provider, port-registry, command and Compose repositories have typed results,
but validation/coercion and fail-closed behavior require hardening. Provider
models private to infrastructure need not be moved without a core consumer.

`EnsureSwarmStack.run()` reads Compose immediately before its individual deploy.
A late invalid stack can therefore fail after earlier work. The target is a
validated set of selected inputs held stable through use, before all relevant
mutators, including mutating pre-apply steps. Core invariants remain in domain;
external syntax and shape conversion belong to infrastructure.

## Scope and Configuration Surface Inventory

Slice 01 must classify every source below as an active parsed input, already
validated boundary, dormant compatibility, derived model or infrastructure-only
pass-through. Record concrete consumer and earliest mutation for active inputs.

- `infra/config/node-providers/provider_config.yaml`
- `infra/config/inventory/desired_inventory.yaml`
- `infra/config/ports.yaml`
- `infra/config/services.yml`
- `infra/config/installation-plan.yaml`
- `infra/config/health-checks.yaml`
- `infra/config/validation-plan.yaml`
- `infra/config/secrets/infisical-secrets.yaml`
- `infra/config/compose/**` YAML, including service-owned auxiliary files.
- Operator environment/local-file configuration via configuration_sources and composition_operator_configuration.
- Retained command YAML repository compatibility; no product command YAML catalogue exists at baseline.
- Generic YAML builder/repository APIs and installer/root helpers: classify every actual consumer rather than infer safety from import absence.

Do not silently narrow the issue to secrets. If an active input needs edits
outside declared scopes, stop for a reviewed scope/lock correction. Existing
config assets are read-only compatibility fixtures in this workflow; changing
committed runtime values is not authorized by these slices.

## Architecture Constraints

Preserve domain isolation, application-to-port dependencies and composition at
the edge. Do not import an application-service model into a port. No unchecked
external mappings or parser-specific objects may enter orchestration; typed
environment/metadata mappings and validated opaque Compose text are allowed.
No external command or filesystem mutation in constructors/imports. Preserve
consent, destructive-operation, redaction and credential source guards.
Existing layer contracts already authorize this boundary: no new ADR is needed.
A change to parser library, credential precedence or safety policy requires a
new architecture review and, when applicable, an ADR before execution proceeds.

## Python Automation Assessment

Python 3.12, Linux/WSL, asyncio and existing repository conventions apply.
Reuse existing typed models/ports. New manifest files listed in Slice 02 are
proposed files with verified parent directories, not current implementation.
All other concrete paths must exist at execution preflight.

## Frontend Assessment

No terminal presentation or browser frontend change is planned. Console/status
UI review becomes required if implementation changes user interaction or output
contracts. No React stream is applicable.

## Test Strategy and Resilience Requirements

Use real synthetic YAML through adapters and mocked lifecycle ports. Cover
malformed syntax, duplicate keys, scalar/list/null roots, missing required
fields, wrong member types, bool-vs-integer and string-vs-boolean handling,
nested parser-object leakage, safe diagnostics, and valid committed fixtures.
Null/missing inventory and registry defaults are currently supported; preserve
or explicitly document migration. Preserve accepted numeric strings where
contractually supported. Do not reject Compose extensions, anchors, environment
placeholders or supported port syntax merely to simplify validation.

Failure-order tests provide affirmative consent and assert zero calls to all
relevant mutators, including when a later selected input is malformed. They
must test the composed request path so consent rejection cannot mask defects.
Use a validated immutable snapshot or equivalent stable consumption contract
against changed files between validation and use. Static input validation does
not move runtime-dependent vault resolution before vault readiness. Fail
closed without retries of malformed input or raw secret values in errors.

Local checks: APPLICABLE_LOCAL. Installation/live checks: NOT_APPLICABLE for
this authoring and deterministic boundary verification (LIVE_NOT_APPLICABLE).
Browser/Selenium: NOT_APPLICABLE. External SonarQube: NOT_APPLICABLE to branch-only
authoring publication (EXTERNAL_GATE_NOT_APPLICABLE); reassess repository-required
external gates at a future PR. No live or external success is claimed. If later
review establishes live applicability, require separate consent and report
LIVE_CONSENT_MISSING until supplied; local success remains separate.

## Ordered Slices and Dependency Graph

`S352-01 -> S352-02 -> S352-03 -> S352-04 -> S352-05 -> S352-06`

No cycles. Each slice is a separate commit; never combine slice checkpoints.
Common allowed evidence writes for each slice: `.tiny-swarm/evidence/issue-352/**`,
`.codex/evidence/slice-<number>-distribution.md` and
`.codex/evidence/slice-<number>-consolidation.md`, plus the active workflow's
status/context refresh when required. Product edits remain within its listed
files. Evidence shared across slices is serialized.

### Slice 01 — Inventory configuration consumers and mutation ordering

Purpose: Trace every configuration source listed below to its loader, typed output, consumer, validation point and first possible mutation. Record pass-through and existing validated boundaries explicitly. Audit PortYamlRepository Any methods and all load_yaml callers, including installer helpers; classify dormant compatibility separately.

Prerequisites: verified branch, baseline, requirement matrix and role reviews.

Requirements: R01,R03,R06,R10. Verification mapping: the targeted commands below plus named new regressions in this slice's issue matrix rows.

Allowed write scope and affected modules/contracts are explicit below; new files: `documentation/workflow/configuration-surface-inventory.md`.

```yaml
slice_id: S352-01
profile: FULL_PATH
owner: Senior Requirement Engineer
secondary_reviewers:
- Senior System Architect
- Senior Python Automation Developer
- Senior Tester
affected_files: &id001
- documentation/workflow/configuration-surface-inventory.md
- .tiny-swarm/evidence/issue-352/**
affected_modules:
- configuration
affected_contracts: []
dependencies: []
parallel_group: serial
file_locks: *id001
contract_locks:
- configuration-validation-contract
architecture_locks:
- configuration-to-core-boundary
quality_gates:
  targeted:
  - python3 tools/quality_gate.py arch-tests
  required:
  - git diff --check
documentation:
  arc42: documentation/arc42/05_analysis/arch-03-09-configuration-parsing-boundary.md
  adr: No new ADR; existing layer contract applies
stop_conditions:
- Scope or ownership gap in inventory
- Compatibility or credential policy change without reviewed migration
- Newly introduced unsafe ordering; unresolved validation ordering at Slice 05 completion
- Failed required quality gate
```

Done criteria: Every surface has a verified owner, current compatibility contract and selected-lifecycle mutation map. All gaps fit later allowed scopes; otherwise stop for a reviewed scope correction before implementation. No product edits in this slice.

Parallel execution eligibility: serial implementation due to shared contracts, composition or evidence. Independent read-only review may run concurrently. Requires isolated worktree: yes. Conflicting workflows/shared files: all workflows holding any listed lock. Shared infrastructure: none used. Serialized live validation: required if later separately approved. Merge-order constraint: predecessor first. Parallelization status: NOT_SAFELY_PARALLELIZABLE by default; any later stream split needs verified disjoint locks.

Issue-completion evidence path: `.tiny-swarm/evidence/issue-352/`; record exact requirement implementation/test references and results. Rollback: revert this single slice commit after checking dependent commits, without destructive runtime action.

### Slice 02 — Introduce the typed secret-manifest boundary

Purpose: Define a parser-independent manifest model and typed repository port. Move raw schema conversion from SecretManifestRenderer into an infrastructure adapter. Reuse that boundary in existing consumers and installer manifest helpers without altering credential policy. Preserve service compatibility exports where needed; remove load_yaml only after verifying all consumers. Ports must not import models from application services.

Prerequisites: S352-01 accepted with tests/evidence; recheck locks and context hashes.

Requirements: R01,R02,R03,R05,R06,R07,R09,R10,R11. Verification mapping: the targeted commands below plus named new regressions in this slice's issue matrix rows.

Allowed write scope and affected modules/contracts are explicit below; new files: `src/tiny_swarm_world/domain/configuration/secret_manifest.py`, `src/tiny_swarm_world/application/ports/repositories/port_secret_manifest_repository.py`, `src/tiny_swarm_world/infrastructure/adapters/repositories/secret_manifest_yaml_repository.py`, `tests/infrastructure/adapters/repositories/test_secret_manifest_yaml_repository.py`, `tests/domain/configuration/test_secret_manifest.py`.

```yaml
slice_id: S352-02
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers:
- Senior Requirement Engineer
- Senior System Architect
- Senior Tester
affected_files: &id001
- src/tiny_swarm_world/domain/configuration/secret_manifest.py
- src/tiny_swarm_world/application/ports/repositories/port_secret_manifest_repository.py
- src/tiny_swarm_world/infrastructure/adapters/repositories/secret_manifest_yaml_repository.py
- src/tiny_swarm_world/application/services/deployment/secret_management.py
- src/tiny_swarm_world/application/services/deployment/__init__.py
- src/tiny_swarm_world/application/ports/file_management/port_local_file_storage.py
- src/tiny_swarm_world/infrastructure/adapters/file_management/local_file_storage.py
- src/tiny_swarm_world/infrastructure/composition_deployment.py
- src/tiny_swarm_world/infrastructure/composition_runtime.py
- src/tiny_swarm_world/installer.py
- tests/application/services/deployment/test_secret_management.py
- tests/infrastructure/test_composition.py
- tests/infrastructure/adapters/repositories/test_secret_manifest_yaml_repository.py
- tests/domain/configuration/test_secret_manifest.py
- tests/test_installer.py
affected_modules:
- configuration
affected_contracts:
- typed configuration boundary
- supported config compatibility
dependencies:
- S352-01
parallel_group: serial
file_locks: *id001
contract_locks:
- configuration-validation-contract
architecture_locks:
- configuration-to-core-boundary
quality_gates:
  targeted:
  - PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_secret_management
    tests.infrastructure.test_composition
  - PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_secret_manifest_yaml_repository
    tests.domain.configuration.test_secret_manifest
  required:
  - git diff --check
  - python3 tools/quality_gate.py quality
documentation:
  arc42: documentation/arc42/05_analysis/arch-03-09-configuration-parsing-boundary.md
  adr: No new ADR; existing layer contract applies
stop_conditions:
- Scope or ownership gap in inventory
- Compatibility or credential policy change without reviewed migration
- Newly introduced unsafe ordering; unresolved validation ordering at Slice 05 completion
- Failed required quality gate
```

Done criteria: Valid manifests produce explicit values without parser containers. Malformed members, required booleans and missing values fail safely. Application no longer validates raw YAML shape; constructor/import-time mutation remains absent.

Parallel execution eligibility: serial implementation due to shared contracts, composition or evidence. Independent read-only review may run concurrently. Requires isolated worktree: yes. Conflicting workflows/shared files: all workflows holding any listed lock. Shared infrastructure: none used. Serialized live validation: required if later separately approved. Merge-order constraint: predecessor first. Parallelization status: NOT_SAFELY_PARALLELIZABLE by default; any later stream split needs verified disjoint locks.

Issue-completion evidence path: `.tiny-swarm/evidence/issue-352/`; record exact requirement implementation/test references and results. Rollback: revert this single slice commit after checking dependent commits, without destructive runtime action.

### Slice 03 — Harden existing configuration repository contracts

Purpose: Keep existing typed outputs; validate external shapes and scalar types before model construction. Reject boolean-as-integer and truthiness-as-boolean errors. Retain explicitly supported numeric strings/defaults. Replace any installer line-based parsing of owned fields with the verified boundary where needed. Audit environment parsing without changing precedence. Parser errors must be safe and parser-neutral at the core boundary.

Prerequisites: S352-02 accepted with tests/evidence; recheck locks and context hashes.

Requirements: R01,R02,R03,R04,R05,R06,R09,R10,R11. Verification mapping: the targeted commands below plus named new regressions in this slice's issue matrix rows.

Allowed write scope and affected modules/contracts are explicit below; new files: none.

```yaml
slice_id: S352-03
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers:
- Senior Requirement Engineer
- Senior System Architect
- Senior Tester
affected_files: &id001
- src/tiny_swarm_world/infrastructure/adapters/repositories/command_repository_yaml.py
- src/tiny_swarm_world/infrastructure/adapters/repositories/node_provider_config_yaml_repository.py
- src/tiny_swarm_world/infrastructure/adapters/repositories/desired_inventory_yaml_repository.py
- src/tiny_swarm_world/infrastructure/adapters/repositories/port_registry_yaml_repository.py
- src/tiny_swarm_world/domain/inventory/desired_inventory.py
- src/tiny_swarm_world/infrastructure/adapters/configuration/configuration_sources.py
- src/tiny_swarm_world/infrastructure/composition_operator_configuration.py
- src/tiny_swarm_world/installer.py
- tests/infrastructure/adapters/repositories/test_command_repository_yaml_contract.py
- tests/infrastructure/adapters/repositories/test_node_provider_config_yaml_repository.py
- tests/infrastructure/adapters/repositories/test_inventory_repositories.py
- tests/infrastructure/adapters/repositories/test_port_registry_yaml_repository.py
- tests/domain/inventory/test_inventory_model.py
- tests/infrastructure/adapters/configuration/test_configuration_sources.py
- tests/test_installer.py
affected_modules:
- configuration
affected_contracts:
- typed configuration boundary
- supported config compatibility
dependencies:
- S352-02
parallel_group: serial
file_locks: *id001
contract_locks:
- configuration-validation-contract
architecture_locks:
- configuration-to-core-boundary
quality_gates:
  targeted:
  - PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_command_repository_yaml_contract
    tests.infrastructure.adapters.repositories.test_node_provider_config_yaml_repository
    tests.infrastructure.adapters.repositories.test_inventory_repositories tests.infrastructure.adapters.repositories.test_port_registry_yaml_repository
    tests.domain.inventory.test_inventory_model tests.infrastructure.adapters.configuration.test_configuration_sources tests.test_installer
  required:
  - git diff --check
  - python3 tools/quality_gate.py quality
documentation:
  arc42: documentation/arc42/05_analysis/arch-03-09-configuration-parsing-boundary.md
  adr: No new ADR; existing layer contract applies
stop_conditions:
- Scope or ownership gap in inventory
- Compatibility or credential policy change without reviewed migration
- Newly introduced unsafe ordering; unresolved validation ordering at Slice 05 completion
- Failed required quality gate
```

Done criteria: Each owned schema has valid and malformed fixtures, duplicate-key policy and safe failure coverage. Missing/null inventory and registry defaults remain compatible unless a precise migration is documented. No dormant command catalog or Multipass behavior is reinstated.

Parallel execution eligibility: serial implementation due to shared contracts, composition or evidence. Independent read-only review may run concurrently. Requires isolated worktree: yes. Conflicting workflows/shared files: all workflows holding any listed lock. Shared infrastructure: none used. Serialized live validation: required if later separately approved. Merge-order constraint: predecessor first. Parallelization status: NOT_SAFELY_PARALLELIZABLE by default; any later stream split needs verified disjoint locks.

Issue-completion evidence path: `.tiny-swarm/evidence/issue-352/`; record exact requirement implementation/test references and results. Rollback: revert this single slice commit after checking dependent commits, without destructive runtime action.

### Slice 04 — Validate Compose and service catalogue inputs

Purpose: Reject malformed services.yml and selected Compose structures instead of silently returning empty results or dropping malformed members. Keep external parser objects inside the adapter; retain typed stack/service models and opaque validated Compose text. Add only concrete snapshot contracts required by the later lifecycle consumer.

Prerequisites: S352-03 accepted with tests/evidence; recheck locks and context hashes.

Requirements: R01,R02,R03,R04,R05,R06,R09,R10,R11. Verification mapping: the targeted commands below plus named new regressions in this slice's issue matrix rows.

Allowed write scope and affected modules/contracts are explicit below; new files: none.

```yaml
slice_id: S352-04
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers:
- Senior Requirement Engineer
- Senior System Architect
- Senior Tester
affected_files: &id001
- src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py
- src/tiny_swarm_world/application/ports/repositories/port_compose_file_repository.py
- src/tiny_swarm_world/domain/deployment/stack_definition.py
- tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py
affected_modules:
- configuration
affected_contracts:
- typed configuration boundary
- supported config compatibility
dependencies:
- S352-03
parallel_group: serial
file_locks: *id001
contract_locks:
- configuration-validation-contract
architecture_locks:
- configuration-to-core-boundary
quality_gates:
  targeted:
  - PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml
  required:
  - git diff --check
  - python3 tools/quality_gate.py quality
documentation:
  arc42: documentation/arc42/05_analysis/arch-03-09-configuration-parsing-boundary.md
  adr: No new ADR; existing layer contract applies
stop_conditions:
- Scope or ownership gap in inventory
- Compatibility or credential policy change without reviewed migration
- Newly introduced unsafe ordering; unresolved validation ordering at Slice 05 completion
- Failed required quality gate
```

Done criteria: Committed stacks and supported extensions, anchors, interpolation, short/long port syntax still work. Invalid roots, nested members and required fields fail deterministically. This is validation of TSW-owned fields, not a replacement for the entire Compose specification.

Parallel execution eligibility: serial implementation due to shared contracts, composition or evidence. Independent read-only review may run concurrently. Requires isolated worktree: yes. Conflicting workflows/shared files: all workflows holding any listed lock. Shared infrastructure: none used. Serialized live validation: required if later separately approved. Merge-order constraint: predecessor first. Parallelization status: NOT_SAFELY_PARALLELIZABLE by default; any later stream split needs verified disjoint locks.

Issue-completion evidence path: `.tiny-swarm/evidence/issue-352/`; record exact requirement implementation/test references and results. Rollback: revert this single slice commit after checking dependent commits, without destructive runtime action.

### Slice 05 — Enforce complete selected-input validation before mutation

Purpose: Wire a pure/local validation barrier for all configuration selected by the requested lifecycle, including later phases, before any mutating pre-apply, setup, reset or deployment step. Reuse existing prerequisite hooks/ports. Consume the validated snapshot, not an unchecked second read. Keep runtime-dependent vault readiness and credential resolution at their existing lifecycle point; validate static requirements and source declarations early.

Prerequisites: S352-04 accepted with tests/evidence; recheck locks and context hashes.

Requirements: R01,R03,R04,R06,R08,R10,R11. Verification mapping: the targeted commands below plus named new regressions in this slice's issue matrix rows.

Allowed write scope and affected modules/contracts are explicit below; new files: none.

```yaml
slice_id: S352-05
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers:
- Senior Requirement Engineer
- Senior System Architect
- Senior Tester
affected_files: &id001
- src/tiny_swarm_world/application/services/deployment/workflows.py
- src/tiny_swarm_world/application/services/deployment/ensure_swarm_stack.py
- src/tiny_swarm_world/application/services/deployment/ensure_service_stack.py
- src/tiny_swarm_world/application/services/setup/workflow.py
- src/tiny_swarm_world/application/services/platform/preflight_service.py
- src/tiny_swarm_world/application/services/configuration/configuration_validation_service.py
- src/tiny_swarm_world/infrastructure/composition.py
- src/tiny_swarm_world/infrastructure/composition_deployment.py
- src/tiny_swarm_world/infrastructure/composition_setup.py
- src/tiny_swarm_world/infrastructure/composition_platform.py
- src/tiny_swarm_world/infrastructure/composition_runtime.py
- src/tiny_swarm_world/installer.py
- src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py
- tests/application/services/deployment/test_deployment_workflows.py
- tests/application/services/deployment/test_ensure_swarm_stack.py
- tests/application/services/deployment/test_ensure_service_stack.py
- tests/application/services/setup/test_setup_workflow.py
- tests/application/services/platform/test_preflight_service.py
- tests/infrastructure/test_composition.py
- tests/test_installer.py
affected_modules:
- configuration
- deployment
- platform
- setup
affected_contracts:
- typed configuration boundary
- supported config compatibility
dependencies:
- S352-04
parallel_group: serial
file_locks: *id001
contract_locks:
- configuration-validation-contract
architecture_locks:
- configuration-to-core-boundary
quality_gates:
  targeted:
  - PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_deployment_workflows
    tests.application.services.deployment.test_ensure_swarm_stack tests.application.services.deployment.test_ensure_service_stack
    tests.application.services.setup.test_setup_workflow tests.application.services.platform.test_preflight_service
    tests.infrastructure.test_composition tests.test_installer
  required:
  - git diff --check
  - python3 tools/quality_gate.py quality
documentation:
  arc42: documentation/arc42/05_analysis/arch-03-09-configuration-parsing-boundary.md
  adr: No new ADR; existing layer contract applies
stop_conditions:
- Scope or ownership gap in inventory
- Compatibility or credential policy change without reviewed migration
- Newly introduced unsafe ordering; unresolved validation ordering at Slice 05 completion
- Failed required quality gate
```

Done criteria: With affirmative consent and mocked mutators, malformed later selected configuration produces zero provider/network/Docker/secret-sync/stack/reset mutations. Valid input preserves order and results. File changes after preflight cannot substitute unchecked content. Unselected optional configuration does not unnecessarily block unrelated commands.

Parallel execution eligibility: serial implementation due to shared contracts, composition or evidence. Independent read-only review may run concurrently. Requires isolated worktree: yes. Conflicting workflows/shared files: all workflows holding any listed lock. Shared infrastructure: none used. Serialized live validation: required if later separately approved. Merge-order constraint: predecessor first. Parallelization status: NOT_SAFELY_PARALLELIZABLE by default; any later stream split needs verified disjoint locks.

Issue-completion evidence path: `.tiny-swarm/evidence/issue-352/`; record exact requirement implementation/test references and results. Rollback: revert this single slice commit after checking dependent commits, without destructive runtime action.

### Slice 06 — Guard architecture, synchronize docs and audit acceptance

Purpose: Add forbidden-import probes for ruamel and ruamel.yaml in domain/application without relaxing existing rules. Verify runtime return types in earlier tests. Update architecture and operator compatibility/migration documentation to implemented facts. Require independent Requirement Lead, Architect, Test/Evidence and issue-completion-auditor review.

Prerequisites: S352-05 accepted with tests/evidence; recheck locks and context hashes.

Requirements: R01–R11. Verification mapping: the targeted commands below plus named new regressions in this slice's issue matrix rows.

Allowed write scope and affected modules/contracts are explicit below; new files: none.

```yaml
slice_id: S352-06
profile: FULL_PATH
owner: Senior Tester
secondary_reviewers:
- Senior Requirement Engineer
- Senior System Architect
- Senior Python Automation Developer
affected_files: &id001
- tests/architecture/test_hexagonal_imports.py
- .importlinter
- documentation/arc42/05_analysis/arch-03-09-configuration-parsing-boundary.md
- documentation/arc42/05_building_blocks.adoc
- documentation/arc42/08_concepts.adoc
- documentation/arc42/08_configuration/operator-configuration-contract.md
- documentation/arc42/08_configuration/config-contract-inventory.md
- documentation/workflow/requirement-matrix.md
- .tiny-swarm/evidence/issue-352/**
affected_modules:
- configuration
affected_contracts:
- typed configuration boundary
- supported config compatibility
dependencies:
- S352-05
parallel_group: serial
file_locks: *id001
contract_locks:
- configuration-validation-contract
architecture_locks:
- configuration-to-core-boundary
quality_gates:
  targeted:
  - python3 tools/quality_gate.py arch-lint
  - python3 tools/quality_gate.py arch-tests
  required:
  - git diff --check
  - python3 tools/quality_gate.py quality
documentation:
  arc42: documentation/arc42/05_analysis/arch-03-09-configuration-parsing-boundary.md
  adr: No new ADR; existing layer contract applies
stop_conditions:
- Scope or ownership gap in inventory
- Compatibility or credential policy change without reviewed migration
- Newly introduced unsafe ordering; unresolved validation ordering at Slice 05 completion
- Failed required quality gate
```

Done criteria: All eleven matrix rows have implemented and executed evidence, full quality passes, six issue evidence files are consistent, and an independent auditor returns PASS. Open/unverified requirements force INCOMPLETE, BLOCKED or FAILED; never close #352 from planning alone.

Parallel execution eligibility: serial implementation due to shared contracts, composition or evidence. Independent read-only review may run concurrently. Requires isolated worktree: yes. Conflicting workflows/shared files: all workflows holding any listed lock. Shared infrastructure: none used. Serialized live validation: required if later separately approved. Merge-order constraint: predecessor first. Parallelization status: NOT_SAFELY_PARALLELIZABLE by default; any later stream split needs verified disjoint locks.

Issue-completion evidence path: `.tiny-swarm/evidence/issue-352/`; record exact requirement implementation/test references and results. Rollback: revert this single slice commit after checking dependent commits, without destructive runtime action.

## Parallel Execution

- Can this workflow run in parallel? Read-only reviews may; implementation slices are sequential until S3D proves a disjoint specialist split.
- Conflicting workflows: #252 lifecycle work, other #313 architecture work and any workflow changing configuration, composition, installer, deployment/setup ordering or the same tests/docs. Conflict is determined from actual locks, not issue title alone.
- Shared files: composition_runtime.py, composition_deployment.py, installer.py, configuration contracts, integration tests and issue evidence.
- Shared infrastructure: none used for deterministic checks; any future live targets must be independently isolated or serialized.
- Requires isolated worktree: yes, this workflow has its own worktree.
- Requires serialized live validation: yes if separately authorized.
- Merge-order constraints: follow the six-slice chain; Codex integrates accepted changes.

## Automatic Work Distribution Policy

Every workflow execute automatically analyzes each slice for backend, frontend,
tests, runtime, documentation, quality, architecture and security streams. Use
real Codex subagents when supported; otherwise record explicit role-based
fallback. Require `.codex/evidence/slice-<number>-distribution.md` before
implementation and `.codex/evidence/slice-<number>-consolidation.md` afterward.
Codex remains final integration, verification and publication owner.

| Stream | Owner / applicability |
|---|---|
| Backend | Senior Python Automation Developer; adapters, models, ports and consumers |
| Frontend | N/A; Console/status UI reviewer if verified output impact emerges |
| Tests | Senior Tester; regression and no-mutation coverage |
| Runtime | Senior DevOps review only if runtime contracts are affected; no live execution |
| Documentation | Senior Documentation Engineer; arc42 and compatibility |
| Quality | Senior Tester / Quality Gate Orchestrator |
| Architecture | Senior System Architect; ownership and dependency direction |
| Security | Senior Security Sandbox Engineer if secrets/error redaction changes |

Never parallelize overlapping files, unclear architecture, contradictory
requirements, mandatory ordering, shared migrations, strict database/schema
sequencing, generated-file conflicts, unclear secrets handling, weakened safety
guards or a Three-Amigos not-safely-parallelizable decision. Independent test
work is eligible only after interfaces stabilize and file ownership is disjoint.

## Git Worktree Execution Rule

Execute on the declared workflow branch in its isolated worktree. For approved
parallel streams use isolated worktrees and branches
`<workflow-branch>-slice-<number>-<stream>`. Verify branch and locks before writes;
workers must not merge to the workflow branch. Codex consolidates with tests and
evidence. Do not run on main, master, develop or an unrelated branch.

## Issue Completion Discipline

- Requirement matrix path: `.tiny-swarm/evidence/issue-352/requirement_matrix.md`; seed from `documentation/workflow/requirement-matrix.md` in Slice 01.
- Required evidence path: `.tiny-swarm/evidence/issue-352/`.
- Required evidence files: `requirement_matrix.md`, `implementation_summary.md`, `changed_files.md`, `test_results.md`, `remaining_risks.md`, `acceptance_checklist.md`.
- Requirement Lead review: Slices 01 and 06, every R01–R11 clause.
- System Architect Reviewer review: typed boundaries, no bypasses and final integration.
- Test / Evidence Reviewer review: actual executed checks per requirement and safe failure ordering.
- Issue Completion Auditor review: independent reviewer using issue-completion-auditor in Slice 06; implementer cannot be sole completion authority.
- DONE blocking rule: any open or unverified requirement forces INCOMPLETE, BLOCKED or FAILED. Planning status READY_FOR_WORKFLOW does not mean issue DONE.

## Quality-Gate Expectations

Use QUALITY.md commands: nearest focused unittest tests, then
`python3 tools/quality_gate.py quality` for every implementation slice. This
includes verification-policy, lint, arch-lint, arch-tests, typecheck and test.
Run `git diff --check` for all slices. Manual test commands require PYTHONPATH=src.
Commands naming proposed new tests become executable only after those files exist.
No gate may be weakened and no skipped live/browser/external check is a pass.

## Documentation Synchronization and arc42 Check Status

CHECKED; planned target recorded in
`documentation/arc42/05_analysis/arch-03-09-configuration-parsing-boundary.md`.
Existing layer contracts, building blocks, concepts, configuration contract,
ARCH-03.08 lifecycle notes and accepted consent/provider ADRs govern the plan.
No new ADR is required for enforcing their existing responsibility split.
Only Slice 06 may change the planned analysis to implemented after evidence.
Historical configuration inventory gaps are not assumed current without source
verification. Compatibility/migration docs must reflect actual accepted inputs.

## Stop Conditions and Uncertainty Escalation

Stop for branch mismatch, unrelated edits, stale governing hashes, conflicting
locks, unclassified inputs, undeclared file changes, architecture/ADR decisions,
ambiguous compatibility, unsafe diagnostics, failed gates or missing required
evidence. Route ARCH_VIOLATION to Architect, TEST_FAILURE to Tester,
BUILD_FAILURE to Python/DevOps, DOC_GOVERNANCE_FAILURE to documentation and
requirements, LOCK_CONFLICT to S3D orchestration, UNKNOWN_FAILURE to Root Architect.
Fix ordinary in-scope errors without weakening guards; never call workflow create
backwards from workflow execute. Scope amendments must be reviewed before writing.

## Definition of Done

All R01–R11 implemented, verified and independently audited; explicit typed
models; infrastructure-only parsing; complete selected configuration validated
before mutation; compatible fixtures or documented migration; focused and full
local gates pass; issue evidence complete; arc42 matches implemented facts.
Live and external verification retain their separately classified states.

## Commit and Push Plan

Authoring uses git-commit-preparation and git-commit-message-preparation: review
only regenerated workflow files and the planned arc42 note, commit, then push
HEAD only to origin on the declared branch. No PR creation, merge, force-push,
branch deletion or cleanup. Workflow-only push auto stays guarded. Execution
later creates exactly one checkpoint commit per accepted slice and pushes only
the same workflow branch after required gates.

## Handoff to workflow execute

Verify workflowVersion, branch, actual published authoring commit and clean
worktree; refresh governing hashes; run S3/S3D and lock preflight. Start Slice 01
before product implementation. Reconcile current source inventory with the
baseline and stop on substantive drift. Initial authoring state: all six slices NOT STARTED; Execution Progress below records later checkpoints. The authoring baseline full quality run has
one Windows-bridge/Pester path-translation failure; inspect authoring-review.md.
Execution must resolve or formally classify this environment prerequisite before
claiming a full implementation quality pass.
The user request authorizes authoring publication, not live operations.

Publication branch and target are the Branch above and `origin/<Branch>`.
Record exact commit SHA and remote-ref comparison in the final publication
handoff; resolve the authoring commit from Git rather than embedding a
self-referential commit hash in this file.

## Execution Progress

- S352-01: inventory accepted; architecture tests and diff check passed.
- S352-05–S352-06: NOT STARTED. Issue remains INCOMPLETE.
- User execution preference: normal project checkout and branches only; no new worktrees or parallel writes.
- Normal-checkout Windows bridge assets: 11 tests passed; prior path blocker resolved without code changes.

- S352-02: ACCEPTED — Typed immutable secret-manifest model and repository port; PyYAML adapter validates syntax, shape, duplicate keys and scalar types with safe errors. Renderer and installer consume typed entries; raw load_yaml removed. Supported defaults, unknown sources and YAML merge/boolean compatibility retained.

- S352-03: ACCEPTED — Hardened command, provider, inventory, port-registry and operator-source parsing with safe diagnostics, duplicate/cycle/type rejection and immutable opt-in provider snapshots. Installer bridge ports use the typed registry. Required port lists and supported numeric-string indexes remain compatible.

- S352-04: ACCEPTED — Validated service catalogue and TSW-consumed Compose structures with sanitized failures, preserving supported anchors/extensions/interpolation/port forms. Added immutable typed selected-stack snapshots and atomic cached content/service metadata; changed or deleted source files cannot replace selected snapshots.

### Execution blocker before S352-05

Independent architecture and requirement review identified a necessary scope correction: add `src/tiny_swarm_world/infrastructure/adapters/repositories/installer_configuration_repository.py` and `tests/infrastructure/adapters/repositories/test_installer_configuration_repository.py` to S352-05. The cohesive adapter validates staged selected installer configuration before reset, using existing typed repositories and validators. It avoids forbidden installer imports and avoids assigning unrelated provider/environment validation to the Compose repository. No ADR or architecture allowlist change is needed. User approval requested; allowed files/locks remain unchanged until approved. S352-05 and S352-06 are not started.
