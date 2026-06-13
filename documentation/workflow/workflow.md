# Workflow: Configuration Contract Validation For Issue 24

```yaml
workflow_id: config-contract-validation-issue-24-20260613
workflow_version: 1.0.0
branch: feature/workflow-config-contracts-20260613
execution_profile: FULL_PATH
released_for_workflow_execute: true
created_utc: "2026-06-13T00:00:00Z"
issue: "https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/24"
request: "Create a workflow for Issue #24, Configuration contracts are implicit and unvalidated, and push it."
decision: READY_FOR_WORKFLOW
confidence: 92
```

## Executive Summary

Issue #24 reports that required configuration parameters are implicit,
partially hardcoded, and not validated through a single documented contract.
The repository already has important pieces: node-provider YAML validation,
command catalog validation, setup-manifest secret requirements, and guarded
preflight checks. The gap is that the full operator-facing configuration
surface is not inventoried, not exposed through a versioned template, and not
validated consistently before live setup or deployment paths consume it.

This workflow creates an executable implementation plan for a typed
configuration contract. The target is deliberately small and fail-closed:
inventory the current config surface, add a typed contract for supported
`TSW_*` settings and product YAML files, provide a tracked example template,
wire validation into static and live preflight before mutation, update
operator documentation, and prove behavior with focused unit tests plus the
repository quality gate.

No live LXD, Incus, LXC, Docker Swarm, compose deployment, Portainer, Nexus,
Jenkins, RabbitMQ, SonarQube, Infisical, Traefik, or browser smoke run is part
of workflow creation. Future workflow execution must keep those operations
mocked unless the user explicitly grants live infrastructure consent.

## Requirement Clarification Gate

Original request:

- Create and push a workflow for GitHub Issue #24.
- The referenced local `.tiny-swarm-world/local/live-installation.env` is a
  local runtime secret file and must not be committed.

Interpreted intent:

- Replace the active workflow under `documentation/workflow` with a
  repository-compliant workflow for Issue #24.
- Make the workflow ready for `workflow execute`.
- Keep changes limited to workflow documentation in this commit.
- Push the workflow branch after commit.

Change type:

- Workflow creation.
- Future Python automation changes.
- Future configuration contract and preflight behavior changes.
- Future documentation and example-template changes.

Affected process strand:

- Workflow authoring.
- Future workflow execution.
- Configuration governance.
- Platform preflight.
- Deployment and setup safety.
- Documentation synchronization.

Affected architecture area:

- `documentation/workflow/**`
- Future `src/tiny_swarm_world/domain/configuration/**`
- Future `src/tiny_swarm_world/application/services/configuration/**`
- Future `src/tiny_swarm_world/application/ports/**`
- Future `src/tiny_swarm_world/infrastructure/adapters/**`
- Future `src/tiny_swarm_world/infrastructure/composition.py`
- Future `infra/config/**`
- Future example template and documentation files
- Future `tests/**`

Explicit requirements:

- Address Issue #24 acceptance criteria:
  - config schema validates before execution;
  - example env or config template is provided;
  - overrides are documented.
- Preserve Linux/WSL-only operating assumptions.
- Preserve Python 3.12 compatibility.
- Preserve hexagonal architecture.
- Do not commit local secrets, generated runtime env files, evidence, logs, or
  host-specific values.
- Keep live infrastructure commands out of default verification.
- Push the workflow branch.

Implicit requirements:

- Existing validated repositories must be reused or extended instead of
  bypassed.
- `infra/config` remains product behavior, not throwaway examples.
- Environment overrides must be allowlisted and typed.
- Secret values must be checked for presence and policy without logging raw
  values.
- Defaults must be explicit and documented.
- Local runtime files such as `.tiny-swarm-world/local/live-installation.env`
  remain ignored.

Assumptions:

- A tracked shell-style example file is acceptable for the installer-facing
  local env contract.
- The existing setup manifest remains the source of required secret names
  unless a slice explicitly changes that contract.
- The first implementation should cover currently consumed `TSW_*` settings
  and product YAML files before adding new configuration surfaces.
- The local duplicate `TSW_SONARQUBE_ADMIN_PASSWORD` entry is operator-local
  cleanup and is not part of this commit.

Non-goals:

- No live infrastructure mutation.
- No secret value migration from the user's local env file.
- No Kubernetes-first configuration model.
- No Java, Maven, Spring Boot, React, TypeScript, Vite, or browser frontend
  project.
- No broad rewrite of existing deployment, artifact, or platform workflows.
- No committed raw environment payloads.

Risks:

- Centralizing config validation can accidentally change runtime defaults if
  not introduced with compatibility tests.
- Compose variable parsing can become brittle if implemented with ad hoc string
  handling.
- Treating secret values as normal config can leak credentials through logs or
  evidence.
- Preflight integration can block existing greenpath runs if required values
  are over-scoped.
- Documentation can drift if the template and runtime allowlist are not tested
  against each other.

Open questions:

- Whether the final tracked template should live at the repository root as
  `.env.example` or under `documentation/configuration/` as a shell-sourceable
  `live-installation.env.example`.
- Whether non-secret local values currently generated by `install.sh` should be
  represented as optional config or installer-owned derived values.

Blocking questions:

- None for workflow authoring. Open questions are slice decisions with explicit
  stop conditions.

Confidence level: 92 percent.

Decision: `READY_FOR_WORKFLOW`.

## Execution Profile

```text
executionProfile=FULL_PATH
reason=The workflow creates future product configuration, preflight, documentation, branch, commit, and push work that can affect runtime setup safety.
requiredFullReviews=Senior Requirement Engineer, Senior System Architect, Senior Python Automation Developer, Senior React Frontend Developer, Senior Tester, Senior Documentation Engineer, Security review for secret-handling behavior.
allowedImpactChecks=Senior React Frontend Developer may return no browser/React impact after verifying no frontend module is introduced.
requiredQualityChecks=git diff --check; targeted unittest files for changed config/preflight behavior; python3 tools/quality_gate.py quality before merge when practical.
stopConditions=Unclear config ownership, secret leakage risk, architecture boundary violation, live infrastructure requirement without consent, or missing template-to-contract verification.
```

## Three Amigos Review

Senior Requirement Engineer:

- The issue goal is clear and testable: validation before execution, a tracked
  example template, and documented overrides.
- Does the implementation still match the EPIC? Yes, it supports the
  autonomous runnable setup EPIC by failing closed on configuration blockers
  before mutation.

Senior System Architect:

- The contract must preserve hexagonal boundaries. Domain models define typed
  values and policy, application services orchestrate validation, and
  infrastructure adapters read environment and YAML sources.
- Concrete env access must not spread further through application services.
  Standard wiring remains in `infrastructure/composition.py`.

Senior Python Automation Developer:

- Use small typed value objects and deterministic parsers.
- Reuse `ruamel.yaml` or existing YAML helpers for product YAML files.
- Keep command, Docker, LXC, HTTP, and filesystem side effects mocked in tests.

Senior React Frontend Developer:

- No React or browser frontend work is authorized. Any UI impact is limited to
  CLI/preflight output text and must remain terminal-oriented.

Senior Tester:

- Acceptance is provable with unit tests for valid, missing, invalid, duplicate,
  undocumented, and secret-redacted configuration cases.
- Default verification must remain non-mutating.

Dependency / Deadlock Validator:

- Slice dependencies are linear where shared contracts are introduced, then
  partially parallel for documentation once the config key inventory stabilizes.
- No slice may write implementation files outside its declared file locks.

## Target Picture

Tiny Swarm World has a documented, typed configuration contract for the
operator-facing setup and deployment configuration surface. Static and live
preflight validate required configuration before any mutation. The tracked
example template lists supported overrides without secrets. Documentation
explains defaults, required values, source precedence, and secret handling. The
contract is test-backed and aligned with current compose, setup, and
composition behavior.

## Verified Baseline

- GitHub Issue #24 is open and has no comments at workflow creation time.
- The repository already validates node-provider config through
  `NodeProviderConfigYamlRepository`.
- The command catalog repository has typed contract validation, although
  product command YAML files are currently retired.
- Setup preflight checks required secret presence from `SetupManifest`.
- Many operator values are still read directly from environment helper
  functions in `infrastructure/composition.py`.
- No tracked `.env.example`, `live-installation.env.example`, or equivalent
  complete config template exists.
- The local `.tiny-swarm-world/local/live-installation.env` file is ignored and
  must not be committed.

## Scope

In scope for workflow execution:

- Inventory all currently consumed `TSW_*` environment variables from source,
  compose files, installer script, tests, and documentation.
- Define typed config contract models with source precedence, requiredness,
  defaults, secret classification, validation rules, and redaction policy.
- Add infrastructure loading for environment and optional local env files
  without committing secret values.
- Add static preflight checks that validate config contracts before live setup
  or deployment mutation.
- Add a tracked example template with placeholder values only.
- Update README, deployment docs, user guide, and arc42 where behavior changes.
- Add focused tests and run repository quality gates.

Out of scope:

- Executing live setup, reset, or deployment.
- Modifying the user's local env file.
- Rotating or generating real credentials in committed files.
- Introducing external static-analysis CI.
- Replacing existing node-provider config validation.
- Reintroducing Multipass as a supported provider.

## Architecture Constraints

- Domain configuration types must not import infrastructure, OS env access,
  YAML libraries, logging, Docker, HTTP, command runners, or composition code.
- Application services may depend on ports and domain types only.
- Infrastructure adapters own environment reads, shell env parsing, YAML
  loading, and file path handling.
- `infrastructure/composition.py` remains the standard construction point for
  concrete adapters.
- Secrets must never appear in verification evidence, logs, exceptions,
  templates with real values, or committed test fixtures.
- Product YAML under `infra/config` must be parsed through structured APIs.

## Python Automation Assessment

The future implementation is Python automation work. It should add focused
domain/application contracts and infrastructure adapters rather than extending
ad hoc environment lookups. Use `unittest`, mocks, and deterministic fixtures.
Keep compatibility with Python 3.12.

## Frontend Assessment

No browser or React frontend work is authorized. If preflight output changes,
keep it concise, terminal-safe, and secret-redacted.

## Test Strategy

- Unit-test contract parsing and validation in domain/application layers.
- Unit-test environment adapter source precedence without reading real local
  secret files.
- Unit-test template coverage against the allowlisted config contract.
- Unit-test preflight behavior for valid config, missing required secrets,
  invalid integers, invalid URLs, invalid secret-name values, and redaction.
- Keep Docker, LXC, Portainer, Nexus, Jenkins, RabbitMQ, SonarQube, Infisical,
  Traefik, and browser checks mocked unless explicitly approved as live tests.

## Resilience Requirements

- Validation must fail closed before mutation.
- Error messages must name the config key and remediation without disclosing
  raw secret values.
- Unknown env keys may be ignored globally, but keys documented as supported
  must be contract-tested.
- Duplicate keys in shell env files should produce a clear warning or failure
  policy before the local file is trusted by automation.
- Optional defaults must be explicit, typed, and documented.

## Ordered Slices

### Slice 01: Config Surface Inventory

Purpose:

- Produce a repository-evidence inventory of current `TSW_*` env variables,
  product YAML files, compose placeholders, installer-generated values, and
  direct env lookups.
- Decide the template path and contract ownership before implementation.

```yaml
slice_id: S01
profile: FULL_PATH
owner: Senior Requirement Engineer
secondary_reviewers:
  - Senior System Architect
  - Senior Tester
affected_files:
  - documentation/configuration/config-contract-inventory.md
  - documentation/workflow/workflow.md
affected_modules:
  - documentation
affected_contracts:
  - configuration_contract_inventory
dependencies: []
parallel_group: inventory
file_locks:
  - documentation/configuration/
  - documentation/workflow/workflow.md
contract_locks:
  - configuration_contract_inventory
architecture_locks:
  - hexagonal_configuration_boundary
quality_gates:
  targeted:
    - git diff --check
  required:
    - git diff --check
documentation:
  arc42: checked-no-change-unless-new-contract-decision-is-needed
  adr: checked-no-change-unless-config-source-precedence-decision-is-needed
stop_conditions:
  - Current configuration surface cannot be verified from repository evidence.
  - Template path or source precedence requires an ADR before implementation.
```

Done criteria:

- Inventory lists each supported key, source file, default, requiredness,
  secret classification, and consumer.
- The workflow records whether root `.env.example` or
  `documentation/configuration/live-installation.env.example` is the chosen
  tracked template.
- No secret values or host-specific values are copied into documentation.

Verification commands:

```bash
git diff --check
```

### Slice 02: Typed Configuration Contract Model

Purpose:

- Add domain/application configuration contract types and validation result
  models for supported operator config values.

```yaml
slice_id: S02
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers:
  - Senior System Architect
  - Senior Tester
affected_files:
  - src/tiny_swarm_world/domain/configuration/**
  - src/tiny_swarm_world/application/services/configuration/**
  - src/tiny_swarm_world/application/ports/configuration/**
  - tests/domain/configuration/**
  - tests/application/services/configuration/**
affected_modules:
  - domain.configuration
  - application.services.configuration
  - application.ports.configuration
affected_contracts:
  - typed_configuration_contract
dependencies:
  - S01
parallel_group: contract
file_locks:
  - src/tiny_swarm_world/domain/configuration/
  - src/tiny_swarm_world/application/services/configuration/
  - src/tiny_swarm_world/application/ports/configuration/
  - tests/domain/configuration/
  - tests/application/services/configuration/
contract_locks:
  - typed_configuration_contract
  - secret_redaction_contract
architecture_locks:
  - domain_independence
  - application_depends_on_ports
quality_gates:
  targeted:
    - PYTHONPATH=src python3 -m unittest tests.domain.configuration
    - PYTHONPATH=src python3 -m unittest tests.application.services.configuration
  required:
    - python3 tools/quality_gate.py test
documentation:
  arc42: checked-for-building-block-update
  adr: checked-no-change-unless-source-precedence-policy-changes
stop_conditions:
  - Domain code needs infrastructure imports.
  - Secret values would be represented in persisted validation evidence.
  - Validation cannot distinguish secret value, secret name, URL, integer, boolean, and image reference kinds.
```

Done criteria:

- Contract definitions cover required and optional values from S01.
- Validation results are structured and redacted.
- Tests prove missing, invalid, defaulted, and secret-classified values.

Verification commands:

```bash
PYTHONPATH=src python3 -m unittest tests.domain.configuration
PYTHONPATH=src python3 -m unittest tests.application.services.configuration
python3 tools/quality_gate.py test
```

### Slice 03: Infrastructure Loader And Source Precedence

Purpose:

- Implement infrastructure adapters that read environment and optional local
  shell env files through the typed contract without leaking secret values.

```yaml
slice_id: S03
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers:
  - Senior Security Sandbox Engineer
  - Senior Tester
affected_files:
  - src/tiny_swarm_world/infrastructure/adapters/configuration/**
  - src/tiny_swarm_world/infrastructure/composition.py
  - tests/infrastructure/adapters/configuration/**
  - tests/infrastructure/test_composition.py
affected_modules:
  - infrastructure.adapters.configuration
  - infrastructure.composition
affected_contracts:
  - configuration_source_precedence
  - secret_redaction_contract
dependencies:
  - S02
parallel_group: loader
file_locks:
  - src/tiny_swarm_world/infrastructure/adapters/configuration/
  - src/tiny_swarm_world/infrastructure/composition.py
  - tests/infrastructure/adapters/configuration/
  - tests/infrastructure/test_composition.py
contract_locks:
  - configuration_source_precedence
  - composition_wiring
architecture_locks:
  - composition_root_only
  - infrastructure_owns_env_and_file_io
quality_gates:
  targeted:
    - PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.configuration
    - PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition
  required:
    - python3 tools/quality_gate.py test
documentation:
  arc42: checked-for-runtime-view-update
  adr: checked-no-change-unless-source-precedence-policy-changes
stop_conditions:
  - Loader reads live infrastructure state.
  - Loader logs or persists raw secrets.
  - Composition starts constructing adapters inside application services.
```

Done criteria:

- Source precedence is deterministic and tested.
- Duplicate local env key policy is explicit and tested.
- Existing composition consumers get values from the contract loader or a
  compatibility wrapper with tests.

Verification commands:

```bash
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.configuration
PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition
python3 tools/quality_gate.py test
```

### Slice 04: Preflight Integration

Purpose:

- Add a preflight configuration-contract check that runs before live mutation
  and reports redacted blockers.

```yaml
slice_id: S04
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers:
  - Senior Tester
  - Senior System Architect
affected_files:
  - src/tiny_swarm_world/application/services/platform/preflight_service.py
  - src/tiny_swarm_world/domain/preflight/**
  - src/tiny_swarm_world/infrastructure/composition.py
  - tests/application/services/platform/test_preflight_service.py
  - tests/domain/preflight/test_preflight_result.py
affected_modules:
  - application.services.platform
  - domain.preflight
  - infrastructure.composition
affected_contracts:
  - preflight_configuration_validation
  - setup_manifest_secret_requirements
dependencies:
  - S03
parallel_group: preflight
file_locks:
  - src/tiny_swarm_world/application/services/platform/preflight_service.py
  - src/tiny_swarm_world/domain/preflight/
  - src/tiny_swarm_world/infrastructure/composition.py
  - tests/application/services/platform/test_preflight_service.py
  - tests/domain/preflight/test_preflight_result.py
contract_locks:
  - preflight_configuration_validation
  - setup_manifest_secret_requirements
architecture_locks:
  - application_orchestrates_ports
  - fail_closed_before_mutation
quality_gates:
  targeted:
    - PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_preflight_service
    - PYTHONPATH=src python3 -m unittest tests.domain.preflight.test_preflight_result
  required:
    - python3 tools/quality_gate.py test
documentation:
  arc42: documentation/arc42/10_quality_requirements.adoc
  adr: checked-no-change-unless-preflight-safety-policy-changes
stop_conditions:
  - Static preflight requires live Docker, LXC, HTTP, or browser access.
  - Preflight output includes raw env values or secret values.
  - Existing setup manifest secret checks are weakened.
```

Done criteria:

- Preflight includes a configuration contract category or equivalent structured
  checks.
- Missing or invalid config fails before live mutation.
- Preflight evidence remains summary-only and secret-redacted.

Verification commands:

```bash
PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_preflight_service
PYTHONPATH=src python3 -m unittest tests.domain.preflight.test_preflight_result
python3 tools/quality_gate.py test
```

### Slice 05: Template And Documentation Synchronization

Purpose:

- Add the tracked example template and synchronize operator documentation with
  the validated override contract.

```yaml
slice_id: S05
profile: NORMAL_PATH
owner: Senior Documentation Engineer
secondary_reviewers:
  - Senior Requirement Engineer
  - Senior Tester
affected_files:
  - .env.example
  - documentation/configuration/**
  - documentation/deployment/system.adoc
  - documentation/user_guide/installation.adoc
  - documentation/user_guide/usage.adoc
  - README.md
  - tests/architecture/test_repository_hygiene.py
affected_modules:
  - documentation
  - repository_hygiene_tests
affected_contracts:
  - operator_override_documentation
  - example_env_template
dependencies:
  - S01
  - S02
parallel_group: docs
file_locks:
  - .env.example
  - documentation/configuration/
  - documentation/deployment/system.adoc
  - documentation/user_guide/installation.adoc
  - documentation/user_guide/usage.adoc
  - README.md
  - tests/architecture/test_repository_hygiene.py
contract_locks:
  - operator_override_documentation
  - example_env_template
architecture_locks:
  - linux_wsl_only_documentation
  - no_committed_secret_values
quality_gates:
  targeted:
    - git diff --check
    - PYTHONPATH=src python3 -m unittest tests.architecture.test_repository_hygiene
  required:
    - python3 tools/quality_gate.py test
documentation:
  arc42: checked-for-quality-requirements-update
  adr: checked-no-change-unless-template-location-policy-changes
stop_conditions:
  - Template includes real secrets, local IPs, host paths, user names, or credentials.
  - Documentation expands Windows-native setup behavior.
  - Template and typed contract disagree.
```

Done criteria:

- A tracked example template exists and contains placeholders only.
- Documentation describes required values, optional overrides, defaults,
  source precedence, local env file handling, and redaction behavior.
- Tests or static checks prove template coverage against the contract.

Verification commands:

```bash
git diff --check
PYTHONPATH=src python3 -m unittest tests.architecture.test_repository_hygiene
python3 tools/quality_gate.py test
```

### Slice 06: Final Quality Gate And Issue Closure Evidence

Purpose:

- Run final verification, update workflow status if needed, and prepare
  evidence for Issue #24 closure.

```yaml
slice_id: S06
profile: FULL_PATH
owner: Senior Tester
secondary_reviewers:
  - Senior Documentation Engineer
  - Senior System Architect
affected_files:
  - documentation/workflow/workflow.md
  - documentation/workflow/context-pack.md
  - documentation/workflow/context-pack.json
affected_modules:
  - workflow_documentation
affected_contracts:
  - issue_24_acceptance_evidence
dependencies:
  - S03
  - S04
  - S05
parallel_group: closeout
file_locks:
  - documentation/workflow/
contract_locks:
  - issue_24_acceptance_evidence
architecture_locks:
  - quality_gate_integrity
quality_gates:
  targeted:
    - git diff --check
  required:
    - python3 tools/quality_gate.py quality
documentation:
  arc42: checked-updated-if-behavior-changed
  adr: checked-updated-if-config-policy-changed
stop_conditions:
  - Full quality gate fails without documented and accepted blocker.
  - Acceptance evidence cannot map to Issue #24 criteria.
  - Workflow changes include unclassified implementation drift.
```

Done criteria:

- Issue #24 acceptance criteria map to committed files and verification
  evidence.
- `python3 tools/quality_gate.py quality` passes or any blocker is documented
  and routed before merge.
- No local env file, secret value, generated evidence, cache, or IDE state is
  staged.

Verification commands:

```bash
git diff --check
python3 tools/quality_gate.py quality
```

## Slice Dependency Graph

```text
S01
 |
 +--> S02
       |
       +--> S03 --> S04 --+
       |                  |
       +--> S05 ----------+--> S06
```

## Parallelization Opportunities

- S05 documentation can start after S01 and S02 once the key inventory and
  typed contract names stabilize.
- S03 and S05 may proceed in parallel only if the template coverage contract is
  locked and both slices avoid editing the same files.
- S04 waits for S03 because preflight wiring must consume the loader contract.

## Automatic Work Distribution Policy

During `workflow execute`, Codex must automatically inspect every slice and
determine whether it can be split into specialist execution streams. Codex
must prefer automatic work distribution when the slice contains clearly
separable concerns, without replacing Three Amigos, S3/S3D, evidence,
quality-gate, SonarQube, branch, PR, or merge protections.

Codex must use real Codex subagents where supported. If real subagents are
unavailable or not visible, Codex must perform explicit role-based fallback
review in the main execution thread and record the fallback in evidence.

| Stream | Scope |
|---|---|
| backend | Java/Python backend, domain logic, ports, adapters, service code |
| frontend | UI, UX, frontend components, frontend tests |
| tests | unit, component, integration, acceptance tests, fixtures |
| runtime | Docker, LXD/LXC, install.sh, deployment, CI/CD, platform scripts |
| documentation | arc42, README, workflow.md, ADR, evidence, process documentation |
| quality | SonarQube, linting, coverage, static analysis, quality gate repair |
| architecture | boundaries, module structure, hexagonal architecture, SCA/SCAP constraints |
| security | secrets, permissions, credentials, network exposure, risky automation |

Do not split work if the slice modifies the same files across multiple
streams, the architectural boundary is unclear, the workflow contains
contradictory requirements, implementation order is mandatory, a shared
migration step must happen first, database/schema changes require strict
sequencing, generated files would create merge conflicts, the Three Amigos
gate marks the slice as not safely parallelizable, secrets or credentials
handling is unclear, or safety guards would be weakened.

For every slice, create `.codex/evidence/slice-<number>-distribution.md`
before implementation. For every implemented slice, create or update
`.codex/evidence/slice-<number>-consolidation.md`. Codex remains the final
integration owner for consolidation, tests, evidence, PR, and merge readiness.

## Git Worktree Execution Rule

Parallel execution must use isolated Git worktrees. Each stream must use its
own branch and worktree.

Branch names must follow this pattern:

```text
<workflow-branch>-slice-<number>-<stream>
```

Examples:

```text
feature/workflow-refactor-config-20260613-slice-01-backend
feature/workflow-refactor-config-20260613-slice-01-tests
feature/workflow-refactor-config-20260613-slice-01-docs
```

Stream branches may only be merged back after stream-specific tests pass, file
ownership conflicts are resolved, evidence is written, and consolidation
review accepts the changes. Subagents and stream workers must not merge
directly to the main workflow branch.

## Role And Ownership Map

- Senior Workflow Architect: workflow dependency ordering and handoff.
- Senior Requirement Engineer: Issue #24 acceptance traceability.
- Senior System Architect: hexagonal boundary and arc42 impact.
- Senior Python Automation Developer: typed contract, loader, and preflight
  implementation.
- Senior React Frontend Developer: no-impact verification for browser/React
  scope.
- Senior Documentation Engineer: template and operator documentation.
- Senior Security Sandbox Engineer: secret classification, redaction, and local-file safety review.
- Senior Tester: regression design and final quality evidence.

## Quality-Gate Expectations

Workflow creation commit:

```bash
git diff --check
```

Workflow execution targeted gates:

```bash
PYTHONPATH=src python3 -m unittest tests.domain.configuration
PYTHONPATH=src python3 -m unittest tests.application.services.configuration
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.configuration
PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_preflight_service
PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition
PYTHONPATH=src python3 -m unittest tests.architecture.test_repository_hygiene
```

Required before merge when practical:

```bash
python3 tools/quality_gate.py quality
```

Live tests are not required for Issue #24 unless a future slice explicitly
changes live deployment behavior and the user grants live infrastructure
consent.

## Documentation Synchronization Points

- Update README when the operator setup path or template location changes.
- Update `documentation/deployment/system.adoc` and user guide pages when
  override defaults or source precedence change.
- Update arc42 quality/runtime/building-block sections if preflight or config
  ownership changes.
- Add or update ADR only if source precedence, template location, or config
  ownership becomes an architectural decision rather than implementation detail.

## Stop Conditions

Stop workflow execution and report when:

- repository evidence cannot prove a config key is supported;
- a planned check requires live infrastructure without explicit consent;
- a secret value would be committed, logged, persisted, or echoed;
- domain code needs infrastructure imports;
- application services need direct `os.environ`, file IO, YAML parser, HTTP,
  Docker, LXC, or command-runner access;
- template and contract definitions drift;
- quality gates fail and the failure is not understood;
- Issue #24 acceptance criteria cannot be mapped to tests and documentation.

## Uncertainty Escalation Rules

- Escalate source-precedence policy changes to Senior System Architect and ADR
  Steward.
- Escalate new secret handling semantics to Security Engineer and Senior
  Tester.
- Escalate broad composition rewiring to Senior System Architect.
- Escalate quality-gate uncertainty to Quality Gate Orchestrator.
- Escalate documentation mismatch to Documentation Sync.

## Commit And Push Plan

Workflow creation:

- Branch: `feature/workflow-config-contracts-20260613`.
- Commit type: `docs(workflow)`.
- Stage only `documentation/workflow/**`.
- Run `git diff --check`.
- Push branch to `origin`.

Future workflow execution:

- Use this branch unless a later workflow-execute preflight requires a
  successor branch.
- Commit each completed slice or logical set only after scoped diff review and
  required verification.
- Never push directly to `main`.

## Definition Of Done

Workflow creation is done when:

- `documentation/workflow/workflow.md` describes Issue #24 with executable
  slice metadata.
- `documentation/workflow/context-pack.md` and
  `documentation/workflow/context-pack.json` are updated.
- The workflow records arc42 and ADR check status.
- `git diff --check` passes.
- The branch is committed and pushed.

Issue #24 implementation is done when:

- config schema validates before execution;
- an example env/config template is tracked;
- overrides are documented;
- focused tests prove the config contract and preflight integration;
- full quality gate passes or an accepted blocker is documented before merge.

## Workflow Execution Evidence

Execution status: `COMPLETED_WITH_EVIDENCE`.

Slice checkpoints pushed to `origin/feature/workflow-config-contracts-20260613`:

| Slice | Commit | Evidence |
|---|---|---|
| S01 | `c819847` | `documentation/configuration/config-contract-inventory.md` inventories required keys, optional overrides, validation gaps, and local-file policy without secret values. |
| S02 | `9bb2f75` | `src/tiny_swarm_world/domain/configuration/**` and application ports/services define the typed configuration contract and redacted validation result. |
| S03 | `7ca805d` | `src/tiny_swarm_world/infrastructure/adapters/configuration/**` loads process and local env sources with duplicate-key and shell-syntax fail-closed behavior. |
| S04 | `57f36dd` | `PreflightService` maps configuration findings to `CONFIGURATION` checks before setup phases and keeps evidence summary-only. |
| S05 | `a0f8741` | `.env.example` and operator documentation describe required values, optional overrides, defaults, source precedence, local env file handling, and redaction. |

Issue #24 acceptance mapping:

- Config schema validates before execution: `ConfigurationValidationService`
  validates `default_configuration_contract()` and `setup run` injects it into
  preflight before mutating setup phases.
- Example env/config template: `.env.example` is tracked and covered by
  `tests.architecture.test_repository_hygiene`.
- Overrides documented: `documentation/configuration/operator-configuration-contract.md`
  is linked from README, installation, deployment, and usage docs.

Verification evidence:

```bash
git diff --check
PYTHONPATH=src python3 -m unittest tests.domain.configuration tests.application.services.configuration
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.configuration tests.infrastructure.test_composition
PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_preflight_service tests.domain.preflight.test_preflight_result
PYTHONPATH=src python3 -m unittest tests.architecture.test_repository_hygiene
python3 tools/quality_gate.py test
.venv/bin/python tools/quality_gate.py quality
```

The system `python3 tools/quality_gate.py quality` attempt stopped at missing
tooling (`ruff` was not installed for system Python). The repository-local
`.venv` contains Ruff and mypy, and `.venv/bin/python tools/quality_gate.py
quality` completed successfully.

## Handoff To Workflow Execute

To execute this workflow, run the repository's `workflow execute` procedure
against `documentation/workflow/workflow.md`. The executor must verify the
active branch, context-pack hashes, slice metadata, locks, and quality gates
before any write-capable implementation work.

## arc42 Check Status

- `documentation/arc42/05_building_blocks.adoc`: checked. Future update likely
  needed when the configuration contract module is implemented.
- `documentation/arc42/06_runtime_view.adoc`: checked. Future update likely
  needed when preflight consumes the config contract.
- `documentation/arc42/10_quality_requirements.adoc`: checked. Future update
  likely needed when config blockers become an explicit preflight quality
  behavior.
- ADR status: checked. No ADR is required for workflow creation. Future ADR
  may be required if template location or source precedence becomes
  architecture-significant.
