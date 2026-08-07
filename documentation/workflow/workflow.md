# Workflow: Issue #232 Artifact and Container-Image Installation Preflight

Version: `issue-232-v1.0.0`
Workflow ID: `issue-232-20260808`
Branch: `feature/workflow-issue-232-artifact-preflight-20260808`
Status: `READY_FOR_EXECUTION`
Execution profile: `FULL_PATH`
Issue: [#232 Implement complete artifact and container-image installation preflight](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/232)

This workflow is a plan for implementation and verification. It does not
claim that Issue #232 is implemented, that a registry is reachable, or that
live installation has been verified.

## Executive Summary

Issue #232 closes the artifact-phase gap left by Issue #218. The current
repository already has a typed `ContainerImageContract`, Compose repositories,
artifact workflows, Nexus repository contracts, image-publication ports and
local file storage. The missing behavior is the complete, profile-aware
preflight that connects those boundaries before any image or dependent stack
mutation.

The workflow introduces the smallest executable path that can:

* derive the required image inventory from the selected service profile;
* validate one-to-one Compose/image-contract alignment, immutable references,
  source semantics and uniqueness;
* resolve all supported `TSW_*_IMAGE` overrides once and reuse the effective
  references for Compose rendering and artifact preparation;
* perform a non-mutating static check before live artifact work;
* perform a separate, bounded and explicit-consent-gated readiness check after
  Nexus/registry bootstrap and before image build, pull, push or dependent
  deployment;
* return typed, redacted results with remediation and preserve fail-closed
  sequencing.

The default quality gate remains local and mocked. No Incus, Docker Swarm,
Compose deployment, registry bootstrap, service bootstrap, credentials or
network mutation may run as part of static verification.

## Requirement Clarification Gate

### Original Request

`workflow create für ISSUE #232 [@port_local_file_storage.py](file:///D:/Projects/Tiny-Swarm-World/src/tiny_swarm_world/application/ports/file_management/port_local_file_storage.py)`

### Interpreted Intent

Create an executable, issue-driven implementation workflow for the complete
artifact and container-image installation preflight described in GitHub Issue
#232, with particular attention to the local file-storage application port and
its adapter boundary.

### Change Type

Functional artifact-preflight feature, architecture-boundary extension,
resilience/readiness hardening, test and evidence work, and synchronized
documentation.

### Affected Process Strand

`workflow create` -> guarded workflow publication -> later `workflow execute`.
The workflow is serial because the image contract, effective-image resolution,
Compose inventory, preflight result and phase gate are shared contracts.

### Affected Architecture Area

`domain/artifacts`, application artifact/preflight services and ports,
`PortLocalFileStorage`, Compose/YAML repositories, Docker/registry/Nexus
adapters, composition wiring, setup/deployment sequencing, tests,
`infra/config/compose`, `infra/config/services.yml`, and artifact/install/
troubleshooting documentation.

### Explicit Requirements

The complete requirement matrix is maintained at
`.tiny-swarm/evidence/issue-232/requirement_matrix.md`. It contains one stable
requirement ID for every issue requirement and acceptance statement. The
implementation may not begin until that matrix remains present and is reviewed
by the Requirement Lead, System Architect Reviewer and Test/Evidence Reviewer.

Coverage is explicit: Slice 01 owns REQ-001, REQ-003, REQ-005, REQ-018; Slice
02 owns REQ-004, REQ-009, REQ-011, REQ-017; Slice 03 owns REQ-001, REQ-002,
REQ-004, REQ-006, REQ-014, REQ-015, REQ-016; Slice 04 owns REQ-007, REQ-010,
REQ-013; Slice 05 owns REQ-008, REQ-009, REQ-021; Slice 06 owns REQ-010,
REQ-019, REQ-022; Slice 07 owns REQ-009, REQ-020, REQ-023, REQ-024; Slice 08
owns REQ-008, REQ-019, REQ-020, REQ-021; and Slice 09 owns REQ-012,
REQ-023, REQ-024. Each row remains independently auditable.

### Implicit Requirements

* Existing Platform and WSL2 host-preflight behavior from Issue #218 must not
  move into the artifact boundary.
* The selected service profile is the source of required deployment services;
  hard-coded inventory that ignores the profile is invalid.
* Static validation must be deterministic and non-mutating.
* Live checks must have bounded timeouts, explicit result states, safe
  remediation and no secret-bearing evidence.
* A failed or unknown mandatory prerequisite must stop later artifact and
  deployment phases.
* The current POSIX/Linux/WSL operating model and hexagonal architecture remain
  authoritative.

### Assumptions

* The issue text at the linked GitHub issue is the requirement source; no
  separate EPIC was named or found for this artifact-preflight concern.
* The current `ContainerImageContract`, service-stack contracts, Compose YAML
  repository, `PortLocalFileStorage`, and composition root are the starting
  points, not replacement APIs to be discarded.
* The repository's approved immutable-reference strategy is an explicit tag or
  digest already represented by the contract model; implementation must verify
  the accepted policy from current code/configuration before changing it.
* The live readiness gate is part of the workflow design but is not executed
  during workflow creation and is not automatically authorized during later
  execution.

### Non-Goals

* No new microservice, REST API, browser React frontend or persistence service.
* No change to the Incus provider, WSL2 host boundary, native Linux routing,
  Docker Swarm topology or service ownership established by Issue #218.
* No automatic registry/Nexus bootstrap, Docker build/pull/push, Compose or
  Swarm deployment during static tests or ordinary local quality gates.
* No committed credentials, tokens, host-specific absolute paths, generated
  live evidence, raw command output or secret values.
* No silent fallback to `latest`, no implicit registry source, and no
  compatibility alias that hides contract drift.

### Risks

* Compose, `services.yml`, default image contracts and environment overrides can
  currently evolve through separate paths and drift.
* The existing contract model derives artifact target IDs from build contexts;
  duplicate contexts or conflicting image references must become explicit
  validation failures.
* The existing unit tests intentionally use a `latest` contract in at least one
  artifact service test; tests and behavior must be aligned without weakening
  the no-implicit-`latest` rule.
* Registry, Docker and build-input checks are external and can be slow,
  unavailable or partially observable; readiness must distinguish those states
  from static contract failures.
* A new port capability can accidentally move filesystem, Docker, YAML or HTTP
  details into the domain/application layers.

### Open Questions

1. Which exact immutable image-reference policy is already approved for pull
   contracts: versioned tags only, digests, or both? The implementation slice
   must answer this from current configuration and tests before changing the
   domain rule.
2. Which existing service-profile source is authoritative when
   `services.yml`, service-stack contracts and Compose YAML disagree? The
   workflow requires a deterministic source-of-truth decision in Slice 03 and
   an escalation if repository evidence does not resolve it.
3. Which existing Docker/Nexus/registry ports can provide all readiness facts
   without introducing a new cross-boundary client? Slice 05 must reuse or
   extend verified ports and record the decision.

### Blocking Questions

None remain for workflow authoring. The open questions are implementation
decisions constrained by repository evidence; they must not be guessed or
silently resolved. If evidence cannot answer one, the affected slice is
`BLOCKED` and escalates to the System Architect.

### Confidence and Decision

Confidence: `94%`

Decision: `READY_FOR_WORKFLOW`

The issue has an explicit goal, scope, acceptance criteria, affected boundary,
quality command and safety model. The requirement matrix, slice dependencies,
role owners and evidence paths are defined below.

## Verified Baseline

The following facts were checked before authoring this workflow:

* `ContainerImageContract` currently validates image-name, tag, build-context
  and `build`/`pull` syntax, and exposes image, artifact-target and serialized
  evidence values.
* `DEFAULT_CONTAINER_IMAGE_CONTRACTS` currently contains the repository's
  default build and pull contracts; the contract set is not yet selected from
  a profile-aware Compose inventory.
* `ArtifactPrepareWorkflow` and `ArtifactVerifyWorkflow` already fail closed
  when their required contracts or evidence are absent, but no complete static
  artifact preflight is wired ahead of those phases.
* `PortComposeFileRepository` exposes stack definitions and Compose service
  definitions; `ComposeFileRepositoryYaml` reads repository Compose assets.
* `PortLocalFileStorage` currently owns YAML loading, optional text reads,
  deterministic text scanning, atomic text writes, directory creation and
  existence checks. Its concrete adapter is POSIX-oriented and belongs in
  infrastructure.
* `composition.py` constructs artifact services and defines the supported image
  environment names, including the `TSW_*_IMAGE` family. The effective image
  resolution is not yet guaranteed to be the same for Compose and artifact
  preparation.
* `infra/config/services.yml` declares enabled services, stacks, phases and
  required services, while `infra/config/compose/**` contains the service image
  references and build contexts.
* Existing tests cover the image contract, artifact workflows, image
  publication, Compose repository parsing, source readiness and architecture
  boundaries, but do not cover the complete Issue #232 matrix.
* `QUALITY.md` defines the authoritative commands as the local Python quality
  gate and its targeted sub-gates; all project Python commands are documented
  for Linux/WSL.

## Target Picture

```text
selected service profile
        |
        v
Compose/services inventory + effective TSW_*_IMAGE overrides
        |
        v
static contract preflight (domain + application ports)
        |-- failed/unknown --> redacted result + remediation; stop
        v
consent-gated artifact phase after Nexus/registry bootstrap
        |
        v
bounded live readiness checks
        |-- failed/unknown --> redacted result; no build/pull/push/deploy
        v
artifacts prepare -> artifacts verify -> dependent deployment phases
```

The final result model must distinguish at least static contract failure,
static success, live-not-run/consent-missing, live prerequisite failure,
live readiness failure, live readiness success, remediation-required and
unknown/unobservable states. It must never serialize credentials, tokens, raw
command output, HTTP bodies or host-specific secrets.

## Scope and Architecture Constraints

### In Scope

* Domain validation and profile-aware artifact inventory concepts.
* Application ports and typed results for local contract inspection and live
  readiness.
* `PortLocalFileStorage` changes only when a verified use case needs a missing
  capability; filesystem behavior remains in its infrastructure adapter.
* Compose/service-profile extraction and common effective-image resolution.
* Static preflight and phase-local live readiness orchestration.
* Composition, setup/deployment fail-closed sequencing, deterministic tests,
  architecture/type/lint checks, evidence, and documentation.

### Hexagonal Constraints

* Domain modules remain free of filesystem, Docker, HTTP, YAML, command-runner,
  logging and dependency-injection imports.
* Application services depend on ports and typed domain values, never concrete
  adapters. They orchestrate checks and phase decisions only.
* Infrastructure adapters own filesystem access, YAML parsing, Docker commands,
  HTTP/Nexus/registry calls, timeout implementation, redaction at the external
  boundary and composition wiring.
* `src/tiny_swarm_world/infrastructure/composition.py` remains the standard
  runtime wiring root; `__main__.py` remains thin.
* Artifact readiness is an in-process boundary, not a new deployable service or
  a reclassification of Platform/Deployment ownership.

### Safety and Resilience Constraints

* Static checks are read-only, deterministic and safe to run without Docker or
  live credentials.
* Live readiness checks require explicit operator consent, bounded deadlines,
  bounded retry budgets where retries are safe, cancellation handling and
  explicit unknown/degraded results.
* No build, pull, push, image publication or dependent deployment starts until
  every mandatory prerequisite is verified.
* A check that cannot observe the required state is not success.
* Retries are allowed only for read-only or idempotent readiness probes and must
  preserve attempt/failure classification without leaking payloads.

## Python Automation Assessment

This is a Python automation change affecting domain models, application ports
and services, infrastructure adapters, composition and tests. The primary
implementation owner is Senior Python Automation Developer. The existing
`PortLocalFileStorage` is an explicit application boundary and may be extended
only with a narrow, test-backed capability required by build-context or local
evidence checks.

Required implementation checks include Python unit tests, type checking,
architecture import checks, adapter mocks, temporary-directory filesystem
fixtures, and full local quality verification. No live infrastructure command
is part of the default gate.

## Frontend Assessment

`NOT_APPLICABLE`. Issue #232 has no browser, React, frontend package, terminal
presentation, accessibility or progress-output requirement. Browser React
review is forbidden for this workflow.

## Verification-State Classification

| Check | Classification | Workflow policy |
|---|---|---|
| Domain/static inventory and contract validation | `APPLICABLE_LOCAL` | Deterministic unit/application tests; non-mutating. |
| Compose/config alignment | `APPLICABLE_LOCAL` | YAML/repository fixtures and static assertions. |
| Docker, registry, Nexus and build-input readiness | `APPLICABLE_LIVE` | Consent-gated, bounded, mocked by default; no automatic live run. |
| Full installation/live artifact acceptance | `APPLICABLE_LIVE` | Separate explicit operator approval and redacted evidence required. |
| Browser/Selenium | `NOT_APPLICABLE` | No browser surface is changed. |
| SonarQube/external quality result | `EXTERNAL_GATE_NOT_APPLICABLE` for local workflow authoring | If repository publication later requires an external check, report its actual observed state separately. |

Static or mocked success must never be described as live readiness or external
quality success. Without explicit live consent, the live slice remains
`LIVE_CONSENT_MISSING` or `LIVE_NOT_APPLICABLE` according to the selected
execution profile.

## Ordered Slices

All slices are serial. They use stable two-digit IDs and concrete dependencies.
No slice may silently widen its allowed write scope.

### Slice 01 — Domain image-contract and inventory invariants

```yaml
slice_id: "01"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers: ["Senior System Architect", "Senior Requirement Engineer", "Senior Tester"]
affected_files: ["src/tiny_swarm_world/domain/artifacts/**", "tests/domain/artifacts/**", "tests/domain/deployment/**"]
affected_modules: ["artifact image contracts", "profile-aware image inventory", "immutable reference policy"]
affected_contracts: ["ContainerImageContract", "artifact image inventory", "safe contract diagnostics"]
dependencies: []
parallel_group: "serial"
file_locks: ["domain/artifacts", "domain artifact tests"]
contract_locks: ["image reference semantics", "artifact target identity"]
architecture_locks: ["domain has no infrastructure imports"]
quality_gates:
  targeted: ["python3 tools/quality_gate.py test", "python3 tools/quality_gate.py typecheck"]
  required: ["python3 tools/quality_gate.py quality"]
documentation:
  arc42: "check planned-vs-implemented artifact boundary; update only from verified behavior"
  adr: "required only if the approved immutable-reference policy changes"
stop_conditions: ["reference policy cannot be verified", "domain imports infrastructure", "duplicate identity remains ambiguous"]
```

Purpose: make image-reference, source, target identity, duplicate and
profile-inventory invariants explicit and parser-independent.

Done criteria:

* implicit `latest`, untagged references and disallowed mutable references fail
  closed according to the verified repository policy;
* build and pull semantics are explicit, including the required upstream
  expectation for pull contracts;
* duplicate target IDs, logical contexts and conflicting image references are
  deterministic validation failures;
* domain results contain safe categories/remediation codes and no I/O details;
* focused unit tests cover valid, missing, stale, duplicate, mismatched,
  conflicting and unsafe references.

Evidence: `.codex/evidence/slice-01-distribution.md`,
`.codex/evidence/slice-01-consolidation.md`, and issue evidence references for
REQ-001 through REQ-005, REQ-013, REQ-017 and REQ-018.

### Slice 02 — Application ports and local file-storage boundary

```yaml
slice_id: "02"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers: ["Senior System Architect", "Senior Tester", "Senior Requirement Engineer"]
affected_files: ["src/tiny_swarm_world/application/ports/file_management/port_local_file_storage.py", "src/tiny_swarm_world/application/ports/**", "src/tiny_swarm_world/domain/inventory/**", "tests/application/ports/**", "tests/infrastructure/adapters/file_management/**", "tests/architecture/**"]
affected_modules: ["local file storage port", "artifact preflight ports", "typed readiness result"]
affected_contracts: ["PortLocalFileStorage", "static artifact preflight port", "Docker/registry readiness port", "typed check result"]
dependencies: ["01"]
parallel_group: "serial"
file_locks: ["application ports", "local file storage contract", "port tests"]
contract_locks: ["filesystem capability contract", "readiness result schema"]
architecture_locks: ["application depends inward on ports", "domain isolation"]
quality_gates:
  targeted: ["python3 tools/quality_gate.py arch-tests", "python3 tools/quality_gate.py typecheck", "python3 tools/quality_gate.py test"]
  required: ["python3 tools/quality_gate.py quality"]
documentation:
  arc42: "check building-block and crosscutting-concept boundary"
  adr: "none unless a new ownership or persistence decision is required"
stop_conditions: ["filesystem/Docker/HTTP detail leaks into application contracts", "port capability is broader than the verified use case", "secret-bearing result fields are introduced"]
```

Purpose: define the inward-facing ports needed for static local inspection and
consent-gated live readiness, including the smallest justified change to
`port_local_file_storage.py`.

Done criteria:

* local storage exposes only named, typed capabilities required by the
  preflight; concrete `Path`, YAML, permissions and atomic-write details remain
  in infrastructure;
* live Docker, registry and Nexus observations cross application ports with
  typed, redacted outcomes and bounded-operation parameters;
* `VerificationResult` or its verified successor can distinguish static and
  live evidence without claiming readiness from configuration alone;
* port fakes and architecture tests prove application code does not import
  concrete adapters.

Evidence: port contract diff, architecture-test output and focused unit tests.

### Slice 03 — Profile inventory, Compose alignment and override resolution

```yaml
slice_id: "03"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers: ["Senior System Architect", "Senior Tester", "Senior Requirement Engineer"]
affected_files: ["src/tiny_swarm_world/application/ports/repositories/port_compose_file_repository.py", "src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py", "src/tiny_swarm_world/infrastructure/composition.py", "infra/config/services.yml", "infra/config/compose/**", "tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py", "tests/infrastructure/test_composition.py", "tests/application/services/deployment/**"]
affected_modules: ["Compose service inventory", "service profile selection", "effective image resolution"]
affected_contracts: ["Compose image inventory", "service-profile-to-contract mapping", "TSW_*_IMAGE override resolution"]
dependencies: ["02"]
parallel_group: "serial"
file_locks: ["Compose repository", "composition image settings", "Compose config"]
contract_locks: ["effective image reference", "profile inventory"]
architecture_locks: ["YAML parsing in infrastructure", "composition root ownership"]
quality_gates:
  targeted: ["python3 tools/quality_gate.py test", "python3 tools/quality_gate.py typecheck"]
  required: ["python3 tools/quality_gate.py quality"]
documentation:
  arc42: "check building blocks and runtime flow; do not claim alignment before tests"
  adr: "required if source-of-truth precedence cannot be resolved without a new decision"
stop_conditions: ["Compose and artifact paths resolve different effective images", "profile selection is inferred from unrelated runtime state", "source-of-truth conflict is unresolved"]
```

Purpose: derive the exact required image inventory for the selected service
profile and make Compose rendering and artifact preparation consume the same
effective image references.

Done criteria:

* every enabled required Compose service resolves to one image contract and
  every selected contract is consumed;
* all supported `TSW_*_IMAGE` settings are enumerated from repository evidence,
  validated and applied identically to both consumers;
* missing, stale, duplicate, mismatched and conflicting Compose/contract data
  fail before any mutation;
* build-context paths are resolved relative to the verified repository/compose
  roots and remain safe for local build inputs;
* deterministic tests cover default and non-default service profiles, every
  supported override, Compose drift, duplicate use and missing context.

### Slice 04 — Static artifact-contract preflight service

```yaml
slice_id: "04"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers: ["Senior System Architect", "Senior Tester", "Senior Requirement Engineer"]
affected_files: ["src/tiny_swarm_world/application/services/artifacts/**", "src/tiny_swarm_world/application/services/platform/**", "src/tiny_swarm_world/infrastructure/composition.py", "src/tiny_swarm_world/__main__.py", "tests/application/services/artifacts/**", "tests/application/services/platform/**", "tests/test_package_entrypoint.py"]
affected_modules: ["static artifact preflight", "CLI preflight dispatch", "artifact service composition"]
affected_contracts: ["static preflight result", "preflight CLI outcome", "artifact inventory request"]
dependencies: ["03"]
parallel_group: "serial"
file_locks: ["artifact application services", "entry-point dispatch", "composition artifact bundle"]
contract_locks: ["preflight outcome", "static validation lifecycle"]
architecture_locks: ["thin entry point", "application orchestration through ports"]
quality_gates:
  targeted: ["python3 tools/quality_gate.py test", "python3 tools/quality_gate.py typecheck", "python3 tools/quality_gate.py arch-tests"]
  required: ["python3 tools/quality_gate.py quality"]
documentation:
  arc42: "update runtime view only after behavior is implemented and verified"
  adr: "none unless the preflight becomes a new deployable boundary"
stop_conditions: ["static check invokes live mutation", "preflight result cannot identify remediation", "CLI constructs unrelated live services"]
```

Purpose: expose a non-mutating static artifact check as an installation
preflight operation and make its result machine-readable.

Done criteria:

* static preflight runs before `artifacts prepare`, `artifacts verify` and
  dependent deployment phases;
* all missing, stale, duplicate and mismatched contracts are reported with
  stable safe target IDs and remediation codes;
* no Docker, HTTP, registry, Nexus, Compose deployment or credential access is
  performed by the static path;
* CLI/application tests prove success, failure, blocked and unknown outcomes
  and verify no later phase is entered after a failed static check.

### Slice 05 — Infrastructure adapters for bounded live readiness

```yaml
slice_id: "05"
profile: "FULL_PATH"
owner: "Senior DevOps Engineer"
secondary_reviewers: ["Senior Python Automation Developer", "Senior System Architect", "Senior Tester"]
affected_files: ["src/tiny_swarm_world/infrastructure/adapters/clients/**", "src/tiny_swarm_world/infrastructure/adapters/preflight/**", "src/tiny_swarm_world/infrastructure/adapters/file_management/local_file_storage.py", "src/tiny_swarm_world/infrastructure/composition.py", "tests/infrastructure/adapters/clients/**", "tests/infrastructure/adapters/preflight/**", "tests/infrastructure/adapters/file_management/**"]
affected_modules: ["manager Docker readiness", "registry/Nexus endpoint readiness", "repository state", "build-input and storage checks"]
affected_contracts: ["live readiness adapter results", "bounded HTTP/Docker probes", "safe remediation evidence"]
dependencies: ["02", "03", "04"]
parallel_group: "serial"
file_locks: ["readiness adapters", "composition live clients", "adapter tests"]
contract_locks: ["live readiness result", "probe timeout semantics"]
architecture_locks: ["external I/O in infrastructure only", "redacted evidence boundary"]
quality_gates:
  targeted: ["python3 tools/quality_gate.py test", "python3 tools/quality_gate.py typecheck", "python3 tools/quality_gate.py arch-lint"]
  required: ["python3 tools/quality_gate.py quality"]
documentation:
  arc42: "check runtime and crosscutting resilience sections"
  adr: "required if registry readiness ownership or retry policy changes architecture"
stop_conditions: ["unbounded external call", "real infrastructure used in default tests", "credentials/raw output enter evidence", "readiness is inferred from static config"]
```

Purpose: implement concrete adapters for the live phase-local checks requested
by Issue #232 while keeping external details out of domain/application code.

Done criteria:

* manager Docker readiness, required registry/Nexus endpoint reachability,
  repository/readiness state, manager storage, available build inputs and
  public pull prerequisites each have explicit check outcomes;
* requests and command operations are bounded and safe to retry only where
  read-only/idempotent; unavailable, timed-out and unknown results remain
  distinct from success;
* normal tests use mocks and temporary repositories, never live infrastructure;
* evidence contains only safe target IDs, check categories, status,
  remediation and non-sensitive metadata.

### Slice 06 — Phase-local readiness gate and fail-closed sequencing

```yaml
slice_id: "06"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers: ["Senior System Architect", "Senior Tester", "Senior DevOps Engineer"]
affected_files: ["src/tiny_swarm_world/application/services/artifacts/workflows.py", "src/tiny_swarm_world/application/services/setup/**", "src/tiny_swarm_world/application/services/deployment/**", "src/tiny_swarm_world/infrastructure/composition.py", "src/tiny_swarm_world/__main__.py", "tests/application/services/artifacts/test_artifact_workflows.py", "tests/application/services/setup/test_setup_workflow.py", "tests/application/services/deployment/**", "tests/test_package_entrypoint.py"]
affected_modules: ["artifact readiness gate", "setup phase sequencing", "deployment dependency guard"]
affected_contracts: ["preparation gate", "artifact workflow status", "dependent deployment stop contract"]
dependencies: ["05"]
parallel_group: "serial"
file_locks: ["artifact workflow orchestration", "setup sequencing", "deployment gate"]
contract_locks: ["phase transition contract", "fail-closed terminal states"]
architecture_locks: ["Platform/Artifacts/Deployment separation", "live consent boundary"]
quality_gates:
  targeted: ["python3 tools/quality_gate.py test", "python3 tools/quality_gate.py typecheck", "python3 tools/quality_gate.py arch-tests"]
  required: ["python3 tools/quality_gate.py quality"]
documentation:
  arc42: "update runtime view and quality scenarios from verified behavior"
  adr: "none unless phase ownership changes"
stop_conditions: ["build/pull/push starts after failed prerequisite", "deployment starts after failed artifact gate", "consent bypass is possible", "unknown readiness is treated as success"]
```

Purpose: place the live gate after required Nexus/registry bootstrap and before
image mutation, and prevent `artifacts prepare`, `artifacts verify` or
dependent deployment from running when mandatory prerequisites fail.

Done criteria:

* successful static preflight is required before live readiness;
* successful required Nexus/registry bootstrap is required before phase-local
  readiness checks;
* failed, blocked, unknown or incomplete readiness prevents image build/pull/
  push/publication and dependent deployment;
* direct artifact CLI workflows preserve their explicit result semantics and
  do not accidentally construct unrelated Platform services;
* tests prove each stop path and prove native Linux/WSL2 host-preflight paths
  remain unchanged.

### Slice 07 — Safe evidence, remediation and acceptance mapping

```yaml
slice_id: "07"
profile: "FULL_PATH"
owner: "Senior Tester"
secondary_reviewers: ["Senior Python Automation Developer", "Senior System Architect", "Senior Requirement Engineer"]
affected_files: ["src/tiny_swarm_world/domain/inventory/**", "src/tiny_swarm_world/application/services/artifacts/**", "src/tiny_swarm_world/infrastructure/adapters/preflight/**", "tests/domain/inventory/**", "tests/application/services/artifacts/**", "tests/infrastructure/adapters/preflight/**", ".tiny-swarm/evidence/issue-232/**"]
affected_modules: ["typed evidence", "redaction", "remediation", "requirement traceability"]
affected_contracts: ["machine-readable preflight evidence", "safe remediation", "issue evidence package"]
dependencies: ["06"]
parallel_group: "serial"
file_locks: ["evidence result model", "redaction tests", "issue evidence"]
contract_locks: ["safe evidence schema", "acceptance mapping"]
architecture_locks: ["evidence ownership", "no raw external payloads"]
quality_gates:
  targeted: ["python3 tools/quality_gate.py test", "python3 tools/quality_gate.py arch-tests"]
  required: ["python3 tools/quality_gate.py quality"]
documentation:
  arc42: "check evidence and quality requirements; distinguish planned/live states"
  adr: "none unless evidence persistence semantics change"
stop_conditions: ["secret/token/raw output in evidence", "requirement lacks verification mapping", "live success claimed without redacted evidence"]
```

Purpose: make the issue-level requirement matrix, implementation summary,
changed-file map, test results, risks and acceptance checklist complete and
consistent with the implementation.

Done criteria:

* every requirement has implementation evidence and test/check/evidence
  verification;
* successful readiness evidence identifies contracts, targets and status but
  not credentials, tokens, command output, HTTP bodies or host secrets;
* live consent, prerequisite, partial, degraded and unavailable states are
  recorded according to `verification-state-policy.md`;
* all six required issue evidence files exist before any completion audit.

### Slice 08 — Optional consent-gated live artifact acceptance

```yaml
slice_id: "08"
profile: "FULL_PATH"
owner: "Senior DevOps Engineer"
secondary_reviewers: ["Senior Tester", "Senior System Architect", "Senior Requirement Engineer"]
affected_files: [".tiny-swarm/evidence/issue-232/**", ".codex/evidence/**", "documentation/**"]
affected_modules: ["live artifact readiness", "redacted operator evidence", "rollback/stop reporting"]
affected_contracts: ["LIVE_* verification state", "bounded readiness acceptance"]
dependencies: ["07"]
parallel_group: "serial"
file_locks: ["live evidence", "shared Docker/registry runtime"]
contract_locks: ["live readiness status", "operator consent evidence"]
architecture_locks: ["live consent boundary", "cleanup and evidence retention"]
quality_gates:
  targeted: ["bounded, explicitly authorized live readiness command(s)"]
  required: ["python3 tools/quality_gate.py quality", "authorized live acceptance when applicable"]
documentation:
  arc42: "final check against observed evidence; never convert a planned state to implemented without evidence"
  adr: "none unless observed behavior requires a new architecture decision"
stop_conditions: ["explicit consent missing", "live prerequisite missing", "mutation starts outside approved scope", "unredacted evidence", "cleanup ownership is unclear"]
```

Purpose: provide a separate live validation path for the readiness gate when an
operator explicitly authorizes it. This slice is not a prerequisite for local
static implementation verification when the live prerequisite is absent; its
state must then remain `LIVE_CONSENT_MISSING` or
`LIVE_PREREQUISITE_MISSING`, never pass.

Done criteria when applicable:

* evidence records the exact bounded scenario, consent state, selected profile,
  readiness result, redaction status, exit result and any blocker;
* no claim exceeds the observed scope; a registry probe is not a full service
  installation claim;
* failure after mutation is `LIVE_FAILED_AFTER_MUTATION` and blocks completion
  until repaired or explicitly handled under repository policy.

### Slice 09 — Documentation, full quality gate and independent audit handoff

```yaml
slice_id: "09"
profile: "FULL_PATH"
owner: "Senior Documentation Engineer"
secondary_reviewers: ["Senior Requirement Engineer", "Senior System Architect", "Senior Tester", "Issue Completion Auditor"]
affected_files: ["documentation/user_guide/installation.adoc", "documentation/user_guide/troubleshooting.adoc", "documentation/system/**", "documentation/arc42/**", "documentation/arc42/08_configuration/**", ".tiny-swarm/evidence/issue-232/**", ".codex/evidence/**"]
affected_modules: ["artifact preflight documentation", "arc42 synchronization", "completion audit handoff"]
affected_contracts: ["documented static/live state semantics", "issue completion package"]
dependencies: ["08"]
parallel_group: "serial"
file_locks: ["artifact documentation", "arc42 notes", "issue evidence", "audit handoff"]
contract_locks: ["completion evidence", "documentation behavior claims"]
architecture_locks: ["planned-vs-implemented distinction", "independent audit authority"]
quality_gates:
  targeted: ["git diff --check", "python3 tools/quality_gate.py test"]
  required: ["python3 tools/quality_gate.py quality"]
documentation:
  arc42: "required final check of sections 03, 05, 06, 08, 10 and 11"
  adr: "check all related ADR references; do not rewrite ADR history"
stop_conditions: ["documentation claims unverified readiness", "required evidence file missing", "full gate fails", "implementer is the only completion authority"]
```

Purpose: synchronize user/system/troubleshooting documentation and arc42 with
verified behavior, then hand the completed issue to the independent
`issue-completion-auditor`.

Done criteria:

* documentation explains static validation, live consent, bounded readiness,
  fail-closed sequencing and remediation without promising live success;
* arc42 reflects the implemented boundary only after source/tests/evidence are
  verified; ADR intent is preserved;
* full local quality gate and documentation checks have exact recorded results;
* Requirement Lead, System Architect Reviewer and Test/Evidence Reviewer have
  signed the requirement matrix/evidence package;
* Issue Completion Auditor receives the package and decides `PASS`,
  `INCOMPLETE`, `BLOCKED` or `REJECTED`.

## Dependency Graph

```text
01 domain invariants
  -> 02 ports and local storage boundary
  -> 03 profile/Compose/override alignment
  -> 04 static preflight service
  -> 05 live readiness adapters
  -> 06 phase gate and fail-closed sequencing
  -> 07 evidence and acceptance mapping
  -> 08 optional consent-gated live acceptance
  -> 09 docs, quality and independent audit handoff
```

The graph is acyclic. Every dependency is a concrete slice ID. Slices 02–06
share contract and composition locks, so they are intentionally serialized.
Slice 08 is logically optional for local execution but remains ordered after
the implemented behavior and before final claims when live applicability is
accepted.

## Parallel Execution

- Can this workflow run in parallel? `No` for implementation; all executable
  slices are serial because they modify shared domain/application contracts,
  composition, setup sequencing, tests, evidence or documentation. Read-only
  role reviews may be concurrent only when their file scopes are disjoint.
- Conflicting workflows: Any workflow changing artifact contracts, Compose
  images, `services.yml`, `composition.py`, artifact/preflight services,
  `PortLocalFileStorage`, Nexus/registry readiness or setup phase sequencing;
  Issue #218 is a completed baseline and must not be reopened by this workflow.
- Shared files: `src/tiny_swarm_world/infrastructure/composition.py`,
  `src/tiny_swarm_world/__main__.py`, application ports, artifact workflows,
  Compose repository/configuration, tests, issue evidence and arc42.
- Shared infrastructure: local repository tree, Docker/registry/Nexus
  endpoints, provider runtime and any live evidence directory.
- Requires isolated worktree: `Yes`, for every implementation slice and any
  specialist stream.
- Requires serialized live validation: `Yes`; live Docker/registry/Nexus
  validation uses shared state and explicit operator consent.
- Merge-order constraints: 01 -> 02 -> 03 -> 04 -> 05 -> 06 -> 07 -> 08 -> 09;
  no stream worker may merge directly to the workflow branch.

Parallel execution is allowed only after a Three-Amigos review confirms
independence. The current decision is not safely parallelizable because the
contracts and phase ordering are shared.

## Automatic Work Distribution Policy

`workflow execute` must automatically analyze every slice for safe specialist
stream decomposition before implementation. It must use real Codex subagents
where supported and perform an explicit role-based fallback review when they
are unavailable or not visible. Codex remains the final integration owner.

Before write-capable work, each slice requires
`.codex/evidence/slice-<number>-distribution.md`; after implementation it
requires `.codex/evidence/slice-<number>-consolidation.md`. These files must
state the selected streams, locks, owner, reviewed changes, tests and
consolidation decision.

Stream map:

* backend: Senior Python Automation Developer;
* frontend: `NOT_APPLICABLE`; no React/browser work;
* tests: Senior Tester;
* runtime/live: Senior DevOps Engineer, serialized and consent-gated;
* documentation: Senior Documentation Engineer;
* quality: quality-gate skills and Senior Tester;
* architecture: Senior System Architect;
* security/evidence: Senior Security Sandbox Engineer or the repository
  security skills when secret handling or untrusted external output is in
  scope.

Do not parallelize when files, contracts, modules or architecture locks
overlap; requirements conflict; ordering is mandatory; a shared migration or
strict schema sequence exists; generated files can conflict; Three Amigos says
the slice is unsafe; secrets handling is unclear; or a safety guard could be
weakened. Any such condition is a serial execution decision, not a reason to
guess.

## Git Worktree Execution Rule

Every slice requires an isolated Git worktree for write-capable specialist
execution. Stream branches must be named:

`feature/workflow-issue-232-artifact-preflight-20260808-slice-<number>-<stream>`

Workers must verify that their branch belongs to this workflow and must not
modify `main`, `master`, `develop` or a shared branch. Workers must not merge
or publish directly. Codex consolidates accepted changes only after
distribution evidence, consolidation evidence, targeted checks and lock
validation pass.

## Role and Ownership Map

| Responsibility | Owner | Reviewers / handoff |
|---|---|---|
| Workflow creation and dependency order | Senior Workflow Architect | Root Architect escalation if blocked |
| Issue decomposition and EPIC drift | Senior Requirement Engineer | Requirement matrix sign-off |
| Hexagonal boundaries, service ownership and arc42 | Senior System Architect | Architecture tests; ADR escalation if needed |
| Domain/application/port/adapter implementation | Senior Python Automation Developer | System Architect and Senior Tester |
| Docker/registry/Nexus live adapter and consent path | Senior DevOps Engineer | Python Automation, System Architect, live-evidence review |
| Tests, regression and quality evidence | Senior Tester | Requirement Lead and System Architect |
| Documentation and arc42 synchronization | Senior Documentation Engineer | Requirement Engineer and System Architect |
| Final completion decision | Issue Completion Auditor | Must be independent of implementer |

Mandatory workflow-create Three-Amigos roles are Senior Requirement Engineer,
Senior System Architect, Senior Python Automation Developer and Senior Tester.
The conditional Console/status UI reviewer is `N/A` for this scope.

## Issue Completion Discipline

- Requirement matrix path: `.tiny-swarm/evidence/issue-232/requirement_matrix.md`
- Required evidence path: `.tiny-swarm/evidence/issue-232/`
- Required evidence files: `requirement_matrix.md`,
  `implementation_summary.md`, `changed_files.md`, `test_results.md`,
  `remaining_risks.md`, `acceptance_checklist.md`; live evidence is added only
  when Slice 08 is applicable.
- Requirement Lead review: required before final audit.
- System Architect Reviewer review: required before final audit.
- Test / Evidence Reviewer review: required before final audit.
- Issue Completion Auditor review: required and independent after Slice 09.
- DONE blocking rule: any open or unverified requirement forces `INCOMPLETE`,
  `BLOCKED` or `FAILED`; only complete implementation, verification and
  evidence may be reported as `DONE`.

The implementer cannot decide issue completion alone. Planned behavior,
static success, live consent, live result and external quality state must remain
separate in the evidence.

## Quality-Gate Expectations

The commands below are taken from `QUALITY.md` and must be run from the
repository root in Linux/WSL:

```bash
python3 tools/quality_gate.py lint
python3 tools/quality_gate.py arch-lint
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py typecheck
python3 tools/quality_gate.py test
python3 tools/quality_gate.py quality
git diff --check
```

Use the nearest targeted gate first. The full `quality` gate is required for
implementation readiness and workflow publication when practical. A skipped or
unavailable live/external check must be recorded with its canonical state and
must not be called a pass.

## Documentation Synchronization Points

* `documentation/arc42/05_building_blocks.adoc`: artifact boundary and port/
  adapter ownership, only after verified implementation.
* `documentation/arc42/06_runtime_view.adoc`: static-before-live and
  readiness-before-mutation flow, only from verified behavior.
* `documentation/arc42/08_concepts.adoc` and
  `documentation/arc42/10_quality_requirements.adoc`: safe evidence,
  resilience, quality scenarios and state semantics.
* `documentation/arc42/11_risks_and_debt.adoc`: Issue #232 is currently
  recorded as planned/open debt; execution updates this only after evidence.
* User/system/install/troubleshooting documentation: static checks, live
  consent, remediation and no-overclaim language.
* ADRs: review references; create an ADR only if execution introduces a new
  architecture decision not covered by the current repository baseline.

## Stop Conditions and Escalation

Stop the affected slice and report the exact blocker when:

* issue text, requirement matrix, architecture source or quality command cannot
  be verified;
* the immutable-reference policy or profile source of truth remains ambiguous;
* Compose and artifact consumers cannot share one effective image resolution;
* domain/application code would need filesystem, YAML, Docker, HTTP or command
  runner details;
* live checks lack explicit consent, bounded timeouts, safe retry semantics,
  redaction or observable result states;
* a mandatory prerequisite can be unknown while later mutation continues;
* host/WSL2 Platform behavior or service ownership would be changed;
* any test, architecture gate, type check or full quality gate fails;
* a required evidence file or independent review is missing;
* documentation would present planned behavior or static configuration as live
  success.

Route architecture ambiguity to Senior System Architect/Root Architect,
requirement ambiguity to Senior Requirement Engineer, test/quality failure to
Senior Tester and the Typed Error Router, live/readiness issues to Senior
DevOps Engineer, and evidence/documentation drift to Senior Documentation
Engineer and the Issue Completion Auditor.

## Commit and Push Plan

For this `workflow create` request, publication is guarded workflow
publication only:

1. review the workflow, matrix, arc42 risk note and `git diff --check`;
2. stage only workflow-authoring files and directly required governance
   synchronization files;
3. create one workflow-authoring commit on
   `feature/workflow-issue-232-artifact-preflight-20260808`;
4. push only `HEAD` to `origin/feature/workflow-issue-232-artifact-preflight-20260808`;
5. record branch, commit SHA, push target and verification in the handoff.

This is not `push auto`: do not create/merge a PR, delete branches, force-push
or clean up. If publication is not explicitly authorized by the surrounding
execution policy, stop after the checked local artifacts and report the
publication step as pending.

## Definition of Done

### Workflow-authoring completion

* the dedicated branch is active and verified;
* `documentation/workflow/workflow.md` is complete and contains all mandatory
  sections and machine-readable slice metadata;
* the issue requirement matrix exists and is complete;
* relevant arc42 documentation was checked and the open risk is recorded
  without claiming implementation;
* dependency graph is acyclic, locks are explicit and quality commands are
  verified from `QUALITY.md`;
* `git diff --check` passes;
* guarded workflow publication is completed or explicitly reported pending.

### Issue-execution completion

* all matrix requirements are implemented and verified;
* static checks remain non-mutating and live checks are separately classified;
* every mandatory artifact prerequisite gates build/pull/push/deployment;
* safe evidence and remediation are complete;
* required local quality gates pass and optional live/external states are
  reported honestly;
* documentation and arc42 are synchronized from verified behavior;
* the independent Issue Completion Auditor returns `PASS`.

## Handoff to workflow execute

`workflow execute` may start only from the checked workflow branch after
confirming branch identity, clean/conflict-free scope, requirement matrix,
Three-Amigos role decisions, S3/S3D metadata validation and required locks.
Execution must begin at Slice 01, create distribution evidence before any
write-capable stream, keep all live checks consent-gated, and use the Typed
Error Router before retries.

The executor must not infer missing slice IDs, source-of-truth precedence,
reference policy, live consent or evidence semantics. Missing information is a
stop condition.

## Arc42 Check Status

Reviewed before workflow authoring: `03_solution_strategy.adoc`,
`04_context_and_scope.adoc`, `05_building_blocks.adoc`,
`06_runtime_view.adoc`, `08_concepts.adoc`, `10_quality_requirements.adoc`,
and `11_risks_and_debt.adoc`.

The current architecture already documents the in-process Platform,
Artifacts and Deployment boundaries, application ports, infrastructure
adapters, local evidence safety and live-consent policy. A small update was
made to `11_risks_and_debt.adoc` to record Issue #232 as planned/open artifact
preflight debt. No new ADR is required for workflow authoring. Runtime and
quality-section updates are deferred to execution until implementation and
verification evidence exist.

## Workflow Handoff Record

* Gate decision: `READY_FOR_WORKFLOW`.
* Execution profile: `FULL_PATH`.
* Branch: `feature/workflow-issue-232-artifact-preflight-20260808`.
* Workflow publication: guarded branch publication only; PR merge and cleanup
  are out of scope for `workflow create`.
* Live validation: applicable to the readiness behavior, but consent-gated and
  not executed by workflow creation.
* Independent completion authority: `issue-completion-auditor`.
