# Workflow: Issue #154 Real Docker Swarm Cluster Installation Phase

Version: `issue-154-v1.0.0`
Workflow ID: `issue-154-20260808`
Branch: `feature/workflow-issue-154-real-cluster-phase-20260808`
Status: `READY_FOR_EXECUTION`
Execution profile: `FULL_PATH`
Issue: [#154 Installer: Extract and enforce the real Docker Swarm cluster phase](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/154)

This workflow is an implementation and verification plan. It does not claim
that Issue #154 is implemented, that a managed LXC/Incus cluster is reachable,
or that live Docker Swarm installation has been verified.

## Executive Summary

Issue #154 closes the remaining installation-order gap for the default
`lxc_native` provider. The repository already contains Docker-in-LXC
installation, Swarm bootstrap, typed runtime outcomes, host preparation,
artifact preflight, generic fail-closed setup execution and safe phase-result
reporting. The gap is ownership: Docker and Swarm work is still appended to
`platform init`, while the declarative `cluster` installation phase has no
executable workflow phases.

The workflow extracts the existing Docker and Swarm responsibilities into
explicit cluster-owned phases, aligns the domain and YAML installation plans,
hardens cluster verification against structured state observed from the
managed Swarm environment, and proves that downstream routing, artifact and
deployment phases remain `not_run` after a cluster failure. It resolves the
logical service-phase representation without redesigning deployment.

Default verification is local, deterministic and mocked. No Incus, Docker,
Docker Swarm, networking, service deployment or credential-backed live
operation is authorized by this workflow creation.

## Requirement Clarification Gate

### Original Request

`Workflow create issue #154` with the referenced
`src/tiny_swarm_world/application/ports/file_management/port_local_file_storage.py`.

### Interpreted Intent

Create a complete, executable workflow for GitHub Issue #154. Inspect the
referenced local-storage port as repository context, but keep it out of scope
unless an implementation slice proves that the cluster phase requires a
missing storage capability. The issue itself is the authoritative requirement
source.

### Change Type

Functional installation-phase extraction, application orchestration and
provider-runtime contract hardening, installation-plan synchronization,
regression testing, evidence and documentation.

### Affected Process Strand

`workflow create` -> guarded workflow publication -> later `workflow execute`.
Implementation slices are serial because composition, setup phase names,
installation-plan contracts and cluster verification results are shared.

### Affected Architecture Area

The existing hexagonal path across `domain/preflight`, `domain/node_provider`,
application platform workflows and ports, managed LXC/Incus adapters,
`infrastructure/composition.py`, setup orchestration, focused tests and
installation/runtime Arc42 documentation.

The referenced `PortLocalFileStorage` is an inspected application port, not a
planned change, because Issue #154 does not describe filesystem behavior or an
artifact-preflight requirement.

### Explicit Requirements

The complete stable requirement matrix is at
`.tiny-swarm/evidence/issue-154/requirement_matrix.md`. It covers every issue
slice, acceptance criterion, named file, test expectation, architecture
constraint and completion-evidence expectation. Implementation may not begin
until the matrix is reviewed by the Requirement Lead, System Architect
Reviewer and Test/Evidence Reviewer.

The core requirements are to:

* make `cluster` a real executable phase for the default `lxc_native` provider;
* keep `platform init` and `platform reconcile` responsible for the LXC/Incus
  node layer only;
* execute Docker work, Swarm manager bootstrap, worker joining and cluster
  verification in cluster-owned phases;
* require a valid worker token, manager-before-worker ordering, every expected
  node, Docker readiness, Swarm membership, `Ready` and `Active` state, and the
  contract-defined manager/leader state;
* align `InstallationPlan` and `infra/config/installation-plan.yaml` with the
  actual setup sequence and gate `network-routing` on cluster verification;
* make `cicd`, `quality`, `messaging`, `control`, `docs` and `validation`
  consistently represent executable boundaries or declarative metadata;
* preserve Issue #218 host-preflight and Issue #232 artifact-preflight behavior;
* add deterministic focused tests and pass the repository quality gate.

### Implicit Requirements

* Reuse existing Docker/Swarm services, ports, DTOs and generic setup stop
  behavior; do not duplicate implementation.
* Verify the managed LXC/Incus Swarm environment, never the host Docker daemon.
* Prefer structured DTO/state parsing over fragile substring parsing.
* Keep phase names stable across plan, YAML, composition, setup and tests.
* Keep verification read-only, live mutation consent-gated and evidence safe.
* Preserve the Linux/WSL-only and Docker Swarm-first operating model.

### Assumptions

* The GitHub issue is the requirement source; no matching EPIC was found under
  `documentation/epics`.
* Issue #218 and Issue #232 behavior on the current branch is the regression
  baseline, not new implementation scope.
* Existing `SwarmNodeReadinessEvidence` and related DTOs are the starting point
  for structured verification; exact fields must be confirmed before changes.
* Logical service entries will use executable names only for actual setup
  boundaries and metadata for services that do not own executable phases. The
  terminal validation mapping must remain explicit and ordered.
* Live validation is optional and serialized; it is not needed for local
  workflow approval.

### Non-Goals

* No Issue #218 WSL2 host-preflight redesign or Issue #232 artifact/image
  preflight redesign.
* No reimplementation of generic fail-closed or `not_run` reporting.
* No LXD/Incus host installation, central port allocation or Traefik redesign.
* No Kubernetes, new microservice, REST/gRPC contract or browser React work.
* No broad SOLID refactor of `lxc_swarm_runtime.py`, `lxc_node_provider.py` or
  `composition.py` beyond the minimum extraction and wiring.
* No live infrastructure mutation during local tests or quality gates.
* No `PortLocalFileStorage` change without a verified Issue #154 requirement.

### Risks

* Moving steps can change provider lifecycle, consent boundaries or final
  platform verification ownership.
* The domain plan includes `host-preparation`, while the YAML currently omits
  it and goes directly from `preflight` to `platform`.
* Current Swarm adapters expose local manager/worker state but may not yet
  expose the manager-observed node table needed for `Ready`, `Active` and
  manager/leader checks.
* The adapter can return a placeholder for an unavailable token; accepting it
  would violate the issue.
* Duplicate stop logic could diverge from the existing generic setup contract.
* Shared composition/setup tests make parallel execution unsafe.

### Open Questions

1. Which existing structured port/DTO contract is authoritative for manager-
   observed `Ready`, `Active` and manager/leader state?
2. Does the existing cluster contract call the required manager state `leader`,
   or define an equivalent state that must be preserved?
3. Should final `platform verify` retain only node/exposure/Portainer checks
   after cluster checks move earlier, or reuse one read-only result?

These are implementation decisions constrained by repository evidence. If the
evidence cannot resolve one, the affected slice is `BLOCKED` and escalates to
the System Architect; no behavior may be guessed.

### Blocking Questions

None. The issue supplies a clear goal, target sequence, acceptance criteria,
non-goals, architecture constraints, tests and quality command.

### Confidence and Decision

Confidence: `96%`. Decision: `READY_FOR_WORKFLOW`.

The mandatory Four-Role Three-Amigos review is represented by Senior
Requirement Engineer, Senior System Architect, Senior Python Automation
Developer and Senior Tester. Console/status UI review is `NOT_APPLICABLE` and
Browser React review is forbidden for this scope.

## Verified Baseline

* `lxc_docker_install.py` contains `LxcDockerInstallService`,
  `LxcDockerInstallStep` and `LxcDockerVerifyStep`.
* `lxc_swarm_bootstrap.py` contains `LxcSwarmBootstrapService`,
  `LxcSwarmBootstrapStep` and `LxcSwarmVerifyStep`.
* `infrastructure/composition.py` currently appends Docker-install and
  Swarm-bootstrap steps to `_platform_init_steps`, and includes Docker/Swarm
  verification in `_platform_verify_steps`.
* The setup phase tuple currently has no `cluster docker`, `cluster swarm
  bootstrap` or `cluster verify` phases; `platform expose` follows platform
  reconcile directly.
* `domain/preflight/installation_plan.py` declares `cluster` with Docker and
  Swarm services but no workflow phase names. Its default plan includes
  `host-preparation` and orders cluster before network routing.
* `infra/config/installation-plan.yaml` has an empty cluster workflow list and
  omits the domain default's host-preparation phase.
* `SetupWorkflow` already orders from `InstallationPlan`, stops on a
  non-success result and returns later phases as `not_run`.
* Existing typed models include `ContainerDockerReadiness`,
  `SwarmManagerBootstrapOutcome`, `SwarmWorkerJoinOutcome` and
  `SwarmNodeReadinessEvidence`; existing ports keep command details out of the
  application layer.
* Focused platform, setup and plan tests already cover portions of Docker
  readiness, manager-before-worker bootstrap, missing results and fail-closed
  execution. The remaining gaps are enumerated in the matrix.
* Arc42 building-block, runtime, quality and risk sections were checked, and
  `QUALITY.md` defines the authoritative local gates.

## Target Picture

```text
preflight -> artifact contract preflight -> host prepare -> host verify
  -> platform init/reconcile (managed node layer)
  -> cluster docker (Docker in every expected node)
  -> cluster swarm bootstrap (manager, valid token, workers)
  -> cluster verify (managed structured membership, Ready/Active/leader)
  -> network-routing/platform expose
  -> secrets/artifacts/deployment
  -> final platform verification
```

The plan and executable setup workflow must express the same boundaries. Any
non-success cluster subphase must leave every later executable phase `not_run`
through the existing generic setup contract.

## Scope and Architecture Constraints

### In Scope

Cluster-owned Docker and Swarm phases, structured managed-cluster verification,
existing port/DTO extensions when necessary, composition/setup/plan parity,
logical phase synchronization, deterministic tests, evidence and documentation.

### Hexagonal Constraints

Domain code remains free of shell, filesystem, Docker, Incus, YAML, HTTP,
logging and dependency-injection concerns. Application services orchestrate
ports and typed outcomes. Infrastructure owns command construction, parsing,
timeouts and redaction. `infrastructure/composition.py` remains the wiring
root, and no new deployable service or cross-service contract is introduced.

### Safety and Resilience Constraints

Local tests use mocks/fakes and do not execute Incus, Docker or Swarm.
Verification is read-only; mutation stays behind existing live consent.
Timeouts/retries remain bounded. Missing, invalid or unobservable state is a
non-success result. Tokens, credentials, raw stdout/stderr and sensitive host
data never enter result or evidence payloads.

## Python Automation Assessment

This is a Python automation change across domain models, application ports and
services, infrastructure adapters, YAML configuration and tests. Senior Python
Automation Developer owns implementation, with System Architect and Tester
review. The referenced local-storage port is not an implementation target
unless a verified cluster requirement appears.

## Frontend Assessment

`NOT_APPLICABLE`. No browser, React or terminal presentation behavior is in
scope. Unexpected progress/UI impact stops the affected slice for review.

## Verification-State Classification

| Check | Applicability | State/rule |
|---|---|---|
| Plan structure and setup ordering | `APPLICABLE_LOCAL` | Static and mocked tests are authoritative. |
| Docker/Swarm contracts and adapters | `APPLICABLE_LOCAL` | Unit tests use fakes; no live commands. |
| Issue #218 host-preflight regression | `APPLICABLE_LOCAL` | Existing host tests remain in the gate. |
| Issue #232 artifact/readiness regression | `APPLICABLE_LOCAL` | Existing artifact tests remain in the gate. |
| Live LXC/Incus/Docker/Swarm verification | `APPLICABLE_LIVE` | `LIVE_CONSENT_MISSING` until separately authorized. |
| Browser/Selenium verification | `NOT_APPLICABLE` | No browser behavior changes. |
| External quality result | `EXTERNAL_GATE_NOT_APPLICABLE` for authoring | Local results are not external success. |

## Ordered Slices

### Slice 01 — Extract Docker and Swarm ownership from platform phases

```yaml
slice_id: "01"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers: ["Senior System Architect", "Senior Tester", "Senior Requirement Engineer"]
affected_files: ["src/tiny_swarm_world/infrastructure/composition.py", "src/tiny_swarm_world/application/services/platform/incus/lxc_docker_install.py", "src/tiny_swarm_world/application/services/platform/incus/lxc_swarm_bootstrap.py", "src/tiny_swarm_world/application/services/platform/workflow/**", "tests/application/services/platform/test_lxc_docker_install.py", "tests/application/services/platform/test_lxc_swarm_bootstrap.py", "tests/infrastructure/test_composition.py"]
affected_modules: ["platform node lifecycle", "cluster Docker phase", "cluster Swarm bootstrap phase", "platform verification ownership"]
affected_contracts: ["SetupWorkflowPhase names", "PlatformWorkflowResult", "Docker install/verify results", "Swarm bootstrap/verify results"]
dependencies: []
parallel_group: "serial"
file_locks: ["composition root", "platform workflow assembly", "Docker/Swarm step ownership"]
contract_locks: ["cluster phase names", "platform versus cluster result ownership"]
architecture_locks: ["application ports", "infrastructure-only command execution", "no duplicate Docker/Swarm services"]
quality_gates:
  targeted: ["python3 tools/quality_gate.py test", "python3 tools/quality_gate.py typecheck", "python3 tools/quality_gate.py arch-tests"]
  required: ["python3 tools/quality_gate.py quality"]
documentation:
  arc42: "check building-block/runtime ownership; update after verified implementation in Slice 06"
  adr: "none unless new architecture ownership is required"
stop_conditions: ["platform init still owns Docker/Swarm", "logic is duplicated", "phase names are unstable", "host Docker becomes runtime", "application code executes shell"]
```

Purpose: move existing Docker installation and Swarm bootstrap out of
`platform init` into explicit cluster-owned phases such as `cluster docker`,
`cluster swarm bootstrap` and `cluster verify`.

Prerequisites: baseline and matrix review. Reuse existing services, ports and
typed results. Allowed writes are the listed platform/composition modules and
focused tests; host preparation, artifacts, deployment, network topology and
local storage are forbidden.

Done criteria: platform init/reconcile own only managed node operations;
Docker and Swarm are assembled once under cluster ownership; final platform
verification ownership is explicit; focused ownership tests pass.

Requirement mapping: `REQ-001`–`REQ-009`, `REQ-022`, `REQ-025`. Verify with the
targeted gates in the YAML block and static inspection of the assembled phase
list.

### Slice 02 — Align domain/YAML plan and logical service phases

```yaml
slice_id: "02"
profile: "FULL_PATH"
owner: "Senior System Architect"
secondary_reviewers: ["Senior Python Automation Developer", "Senior Tester", "Senior Requirement Engineer"]
affected_files: ["src/tiny_swarm_world/domain/preflight/installation_plan.py", "infra/config/installation-plan.yaml", "tests/domain/preflight/test_preflight_result.py", "tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py", "tests/application/services/setup/test_setup_workflow.py"]
affected_modules: ["installation dependency graph", "domain/YAML plan parity", "logical service-phase metadata"]
affected_contracts: ["InstallationPhase.workflow_phase_names", "InstallationPlan.ordered_workflow_phase_names", "platform -> cluster -> network-routing"]
dependencies: ["01"]
parallel_group: "serial"
file_locks: ["domain installation plan", "installation-plan.yaml", "plan parity tests"]
contract_locks: ["cluster executable mapping", "host-preparation mapping", "logical phase representation"]
architecture_locks: ["declarative plan versus executable setup boundary"]
quality_gates:
  targeted: ["python3 tools/quality_gate.py test", "python3 tools/quality_gate.py typecheck", "python3 tools/quality_gate.py arch-tests"]
  required: ["python3 tools/quality_gate.py quality"]
documentation:
  arc42: "check runtime/configuration views; synchronize in Slice 06"
  adr: "none unless plan ownership changes beyond issue scope"
stop_conditions: ["domain/YAML disagree", "cluster is metadata-only", "routing can bypass cluster verify", "logical phases imply nonexistent execution", "service ordering changes"]
```

Purpose: make `cluster` own executable phase names and make both plan sources
match the setup workflow. Reconcile the observed YAML omission of
`host-preparation` with the domain default. Use the dependency-metadata model
for logical service entries that do not own executable setup phases; keep any
terminal validation mapping only when confirmed as an actual setup phase and
make its ownership explicit.

Allowed writes are the two plan sources and plan/setup tests. Done criteria:
stable cluster names, `platform -> cluster -> network-routing`, no misleading
logical-phase graph, unchanged service ordering and plan parity.

Requirement mapping: `REQ-010`–`REQ-014`, `REQ-018`, `REQ-020`, `REQ-023`,
`REQ-024`, `REQ-026`, `REQ-027`. Verify with targeted `test`, `typecheck`,
`arch-tests`, then the full `quality` gate.

### Slice 03 — Harden structured managed-cluster verification

```yaml
slice_id: "03"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers: ["Senior System Architect", "Senior Tester", "Senior DevOps Engineer"]
affected_files: ["src/tiny_swarm_world/domain/node_provider/docker_swarm_lxc.py", "src/tiny_swarm_world/application/ports/node_provider/port_container_swarm_bootstrap.py", "src/tiny_swarm_world/application/services/platform/incus/lxc_docker_install.py", "src/tiny_swarm_world/application/services/platform/incus/lxc_swarm_bootstrap.py", "src/tiny_swarm_world/application/services/platform/docker_swarm_lxc_contract.py", "src/tiny_swarm_world/infrastructure/adapters/clients/lxc_container_swarm_bootstrap.py", "src/tiny_swarm_world/infrastructure/adapters/clients/lxc_container_docker_runtime.py", "tests/application/services/platform/test_lxc_docker_install.py", "tests/application/services/platform/test_lxc_swarm_bootstrap.py", "tests/domain/node_provider/**", "tests/infrastructure/adapters/clients/**"]
affected_modules: ["Docker readiness", "Swarm bootstrap", "join-token validation", "manager-observed node table", "structured verification"]
affected_contracts: ["ContainerDockerReadiness", "SwarmManagerBootstrapOutcome", "SwarmWorkerJoinOutcome", "SwarmNodeReadinessEvidence", "PortContainerSwarmBootstrap"]
dependencies: ["01", "02"]
parallel_group: "serial"
file_locks: ["node-provider DTOs", "Swarm port/adapter", "cluster verification service"]
contract_locks: ["Ready/Active state", "manager/leader state", "expected-node completeness", "valid join token"]
architecture_locks: ["managed LXC/Incus runtime", "structured parsing", "safe evidence"]
quality_gates:
  targeted: ["python3 tools/quality_gate.py test", "python3 tools/quality_gate.py typecheck", "python3 tools/quality_gate.py arch-lint", "python3 tools/quality_gate.py arch-tests"]
  required: ["python3 tools/quality_gate.py quality"]
documentation:
  arc42: "check resilience/runtime/risk sections; synchronize after verification"
  adr: "required only if existing contracts cannot express ownership"
stop_conditions: ["host Docker is queried", "placeholder token accepted", "manager/worker ordering bypassed", "missing node succeeds", "fragile parsing replaces available structured state", "token/raw output enters evidence"]
```

Purpose: satisfy the managed structured contract for cluster Docker, Swarm
bootstrap and cluster verification. Characterize current DTOs first; extend a
port/DTO only when needed for expected-node count, `Ready`, `Active`,
manager/leader or valid-token state.

Done criteria: Docker is ready in every expected node; manager initialization
precedes workers; unavailable token blocks joins; manager-observed structured
membership fails for missing/unready/inactive/uninitialized/wrong-manager
states; results are typed, bounded and redacted. Allowed writes are the listed
domain, application, adapter and focused test paths; no provider-wide refactor.

Requirement mapping: `REQ-003`–`REQ-009`, `REQ-013`–`REQ-020`, `REQ-025`,
`REQ-028`. Verify with targeted `test`, `typecheck`, `arch-lint`,
`arch-tests`, then `quality`; normal tests use fakes only.

### Slice 04 — Wire setup boundaries and downstream `not_run`

```yaml
slice_id: "04"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers: ["Senior Tester", "Senior System Architect", "Senior Requirement Engineer"]
affected_files: ["src/tiny_swarm_world/infrastructure/composition.py", "src/tiny_swarm_world/application/services/setup/workflow.py", "tests/application/services/setup/test_setup_workflow.py", "tests/infrastructure/test_composition.py"]
affected_modules: ["SetupWorkflow phase assembly", "cluster-to-network boundary", "artifact/deployment downstream guard"]
affected_contracts: ["SetupWorkflow phase status", "not_run propagation", "cluster verification gate"]
dependencies: ["03"]
parallel_group: "serial"
file_locks: ["setup phase tuple", "composition root", "downstream stop tests"]
contract_locks: ["cluster verify success boundary", "not_run order"]
architecture_locks: ["composition wiring", "generic fail-closed reuse"]
quality_gates:
  targeted: ["python3 tools/quality_gate.py test", "python3 tools/quality_gate.py typecheck", "python3 tools/quality_gate.py arch-tests"]
  required: ["python3 tools/quality_gate.py quality"]
documentation:
  arc42: "record verified sequence in Slice 06"
  adr: "none unless existing workflows cannot express the boundary"
stop_conditions: ["routing starts after cluster failure", "artifact/deployment runs after failure", "not_run logic is duplicated", "cluster phases are not after reconcile"]
```

Purpose: assemble the real setup sequence and prove that cluster verification
controls all later executable work. Reuse `SetupWorkflow` and
`InstallationPlan.arrange_workflow_phases`; do not add a second stop mechanism.

Done criteria: Docker follows reconcile, Swarm follows Docker success, cluster
verify precedes expose, and cluster failure marks expose, deployment bootstrap,
artifact bootstrap/readiness/prepare/verify, deployment apply/verify and final
platform verify as `not_run`. Success permits the next phase.

Requirement mapping: `REQ-002`, `REQ-005`, `REQ-007`, `REQ-012`, `REQ-021`,
`REQ-022`, `REQ-028`, `REQ-039`, `REQ-040`. Verify with targeted `test`,
`typecheck`, `arch-tests`, then `quality`.

### Slice 05 — Regression coverage for #218, #232 and #154

```yaml
slice_id: "05"
profile: "FULL_PATH"
owner: "Senior Tester"
secondary_reviewers: ["Senior Python Automation Developer", "Senior System Architect", "Senior Requirement Engineer"]
affected_files: ["tests/application/services/setup/test_setup_workflow.py", "tests/application/services/platform/test_lxc_docker_install.py", "tests/application/services/platform/test_lxc_swarm_bootstrap.py", "tests/domain/preflight/test_preflight_result.py", "tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py", "tests/application/services/platform/host/test_prepare_host.py", "tests/application/services/platform/test_preflight_service.py", "tests/application/services/artifacts/test_static_contract_preflight.py", "tests/application/services/artifacts/test_artifact_workflows.py", "tests/infrastructure/test_composition.py"]
affected_modules: ["ordering regression", "cluster failure matrix", "Issue #218 host-preflight", "Issue #232 artifact/readiness"]
affected_contracts: ["Issue #154 acceptance tests", "prior issue regression baseline"]
dependencies: ["04"]
parallel_group: "serial"
file_locks: ["shared setup tests", "platform tests", "plan tests", "host/artifact regression tests"]
contract_locks: ["acceptance evidence", "regression baseline"]
architecture_locks: ["deterministic fakes", "no live default gate"]
quality_gates:
  targeted: ["python3 tools/quality_gate.py test", "python3 tools/quality_gate.py typecheck", "python3 tools/quality_gate.py arch-tests"]
  required: ["python3 tools/quality_gate.py quality"]
documentation:
  arc42: "no update unless a verified behavior/documentation mismatch appears"
  adr: "none"
stop_conditions: ["tests invoke live infrastructure", "#218 or #232 regresses", "acceptance row has no named verification", "safety assertions are weakened"]
```

Purpose: implement the issue's focused checklist: phase ownership, ordering,
manager-before-worker, missing token, expected nodes, `Ready`, `Active`,
manager state, routing gate, downstream `not_run`, plan parity and logical
phase consistency. Preserve the #218 host and #232 artifact/readiness suites.

Allowed writes are tests/fixtures in the listed paths; product fixes belong to
their owning preceding slice. Requirement mapping: all matrix rows, with
primary ownership of `REQ-030`–`REQ-045`. Verify with targeted `test`,
`typecheck`, `arch-tests`, then `quality`.

### Slice 06 — Documentation, evidence, quality and independent audit

```yaml
slice_id: "06"
profile: "FULL_PATH"
owner: "Senior Documentation Engineer"
secondary_reviewers: ["Senior Requirement Engineer", "Senior System Architect", "Senior Tester", "Issue Completion Auditor"]
affected_files: ["documentation/arc42/05_building_blocks.adoc", "documentation/arc42/06_runtime_view.adoc", "documentation/arc42/10_quality_requirements.adoc", "documentation/arc42/11_risks_and_debt.adoc", "documentation/user_guide/installation.adoc", ".tiny-swarm/evidence/issue-154/**", ".codex/evidence/issue-154/**"]
affected_modules: ["installation sequence docs", "Arc42 synchronization", "issue completion evidence"]
affected_contracts: ["planned-versus-implemented docs", "requirement matrix", "completion evidence package"]
dependencies: ["05"]
parallel_group: "serial"
file_locks: ["Arc42/installation docs", "issue evidence", "distribution/consolidation evidence"]
contract_locks: ["documented sequence", "requirement-to-evidence mapping", "completion status"]
architecture_locks: ["Arc42 synchronization", "independent completion authority"]
quality_gates:
  targeted: ["git diff --check", "python3 tools/quality_gate.py test"]
  required: ["python3 tools/quality_gate.py quality"]
documentation:
  arc42: "update only sections whose verified sequence/ownership changed"
  adr: "review existing LXC-native, consent and setup-safety ADRs; create none without a decision"
stop_conditions: ["docs claim live success without LIVE_VERIFIED evidence", "required evidence missing", "full gate fails", "implementer is sole completion authority", "Arc42 contradicts source/tests"]
```

Purpose: update only documentation affected by verified behavior, complete
`.tiny-swarm/evidence/issue-154/` and hand off to the independent auditor.
Execution must produce `requirement_matrix.md`, `implementation_summary.md`,
`changed_files.md`, `test_results.md`, `remaining_risks.md` and
`acceptance_checklist.md`. Per-slice distribution and consolidation records
belong under `.codex/evidence/issue-154/`. Optional live runs must record the
exact `LIVE_*` state; missing consent is never `LIVE_VERIFIED`.

Requirement mapping: `REQ-046`–`REQ-050` and final evidence for all earlier
rows. Verify with `git diff --check`, focused tests and full `quality`.

## Dependency Graph

```text
01 ownership -> 02 plan/YAML -> 03 structured verification
  -> 04 setup boundary -> 05 regression coverage -> 06 docs/evidence/audit
```

The graph is acyclic. Slices 01–05 share composition, setup, plan and DTO
contracts, so they are serial. Slice 06 cannot claim completion before all
implementation and regression evidence exists.

## Parallel Execution

- Can this workflow run in parallel? `No` for implementation; shared
  composition, setup phase names, plans, DTOs, tests and evidence overlap.
- Conflicting workflows: any workflow changing `composition.py`, setup phase
  sequencing, `InstallationPlan`, `installation-plan.yaml`, LXC Docker/Swarm
  adapters or shared setup tests. #218 and #232 are completed baselines.
- Shared files: composition, installation plans, platform DTO/port/adapter
  modules, setup/platform tests and issue evidence.
- Shared infrastructure: repository tree, Incus/LXC provider, Docker/Swarm,
  network state and shared evidence directories.
- Requires isolated worktree: `Yes` for every write-capable slice/stream.
- Requires serialized live validation: `Yes`; live provider state is shared and
  consent-gated.
- Merge-order constraints: `01 -> 02 -> 03 -> 04 -> 05 -> 06`; stream workers
  never merge directly to the workflow branch.

Read-only role reviews may be concurrent only with disjoint scopes. The current
Three-Amigos decision is not safely parallelizable.

## Automatic Work Distribution Policy

`workflow execute` must analyze every slice for safe specialist decomposition
before implementation, use real Codex subagents where supported, and perform
explicit role-based fallback review when unavailable. Codex remains final
integration owner.

Before write-capable work require
`.codex/evidence/issue-154/slice-<number>-distribution.md`; after
implementation require
`.codex/evidence/issue-154/slice-<number>-consolidation.md`. These issue-scoped
paths preserve historical evidence while fulfilling the distribution and
consolidation contract.

Stream map: backend -> Senior Python Automation Developer; frontend ->
`NOT_APPLICABLE`; tests -> Senior Tester; runtime/live -> Senior DevOps
Engineer, serialized and consent-gated; documentation -> Senior Documentation
Engineer; quality -> quality-gate skills and Senior Tester; architecture ->
Senior System Architect; security/evidence -> Senior Security Sandbox Engineer
and repository security skills.

Do not parallelize overlapping files/contracts/package structures, contradictory
requirements, mandatory ordering, shared migrations, strict schema sequencing,
generated-file conflicts, an unsafe Three-Amigos decision, unclear secret
handling or any guard-weakening change.

## Git Worktree Execution Rule

Every slice requires an isolated Git worktree for write-capable specialist
execution. Stream branches use:

`feature/workflow-issue-154-real-cluster-phase-20260808-slice-<number>-<stream>`

Workers must verify the branch belongs to this workflow and must not modify
`main`, `master`, `develop` or another shared branch. Workers do not merge or
publish directly; Codex consolidates after evidence, tests and lock checks.

## Role and Ownership Map

| Responsibility | Owner | Review/handoff |
|---|---|---|
| Workflow creation and ordering | Senior Workflow Architect | Root Architect if blocked |
| Issue decomposition and drift | Senior Requirement Engineer | Matrix sign-off |
| Hexagonal boundaries, phase ownership, Arc42 | Senior System Architect | Architecture tests/ADR escalation |
| Python domain/application/adapter work | Senior Python Automation Developer | Architect and Tester |
| Docker/Incus/Swarm runtime/live review | Senior DevOps Engineer | Python, Architect, live-evidence review |
| Regression tests and quality evidence | Senior Tester | Requirement and Architect review |
| Documentation and evidence | Senior Documentation Engineer | Requirement and Architect review |
| Final completion decision | Issue Completion Auditor | Independent of implementer |

Mandatory workflow-create roles are Senior Requirement Engineer, Senior System
Architect, Senior Python Automation Developer and Senior Tester. Console/status
UI is `NOT_APPLICABLE`; Browser React review is forbidden.

## Issue Completion Discipline

- Requirement matrix path: `.tiny-swarm/evidence/issue-154/requirement_matrix.md`
- Required evidence path: `.tiny-swarm/evidence/issue-154/`
- Required evidence files: `requirement_matrix.md`, `implementation_summary.md`,
  `changed_files.md`, `test_results.md`, `remaining_risks.md`,
  `acceptance_checklist.md`
- Requirement Lead review: Senior Requirement Engineer signs final traceability.
- System Architect Reviewer review: Senior System Architect signs phase
  ownership, runtime source-of-truth, architecture and Arc42.
- Test / Evidence Reviewer review: Senior Tester signs named verification for
  every row and gate integrity.
- Issue Completion Auditor review: independent auditor decides `PASS`,
  `INCOMPLETE`, `BLOCKED` or `REJECTED`.
- DONE blocking rule: any open, partial or unverified requirement forces
  `INCOMPLETE`, `BLOCKED` or `FAILED`.

## Quality-Gate Expectations

Use WSL/Linux and the commands authorized by `QUALITY.md`:

```bash
python3 tools/quality_gate.py lint
python3 tools/quality_gate.py arch-lint
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py typecheck
python3 tools/quality_gate.py test
python3 tools/quality_gate.py quality
git diff --check
```

Run focused gates first and the full gate before execution completion. The
workflow-create branch changes governance artifacts and the requirement
matrix, so its publication gate is `git diff --check`; any skipped full Python
gate must be recorded. Local quality is never live or external success.

## Documentation Synchronization Points

Arc42 building-block, runtime, quality and risk sections were checked during
authoring. Slice 06 updates only claims supported by verified source, tests and
evidence, and explains the before/after executable sequence. Existing #218 and
#232 documentation is out of scope except for terminology/no-regression checks.
No ADR is created unless implementation reveals a decision not covered by the
existing LXC-native, setup-safety or consent ADRs.

## Stop Conditions and Escalation

Stop and report `BLOCKED` if a required symbol, file, DTO field, command
contract or quality command cannot be verified; plan/YAML/setup/Arc42 disagree;
managed structured state ownership is unresolved; host Docker is queried;
invalid/missing state succeeds; live side effects or secrets enter local tests
or evidence; locks overlap; #218/#232 regress; required gates fail; a matrix
row lacks evidence; or docs would present planned behavior as implemented.

Route architecture/ownership/DTO questions to Senior System Architect,
requirements to Senior Requirement Engineer, tests/gates to Senior Tester and
quality owner, locks to the execution orchestrator and final completeness to
the independent Issue Completion Auditor.

## Commit and Push Plan

Workflow creation uses guarded publication:

1. Verify status and the dedicated workflow branch.
2. Stage only `documentation/workflow/**` and
   `.tiny-swarm/evidence/issue-154/requirement_matrix.md`.
3. Run `git diff --cached --check` and review the staged diff.
4. Create one Issue #154 workflow-authoring commit.
5. Push only `HEAD` to
   `origin/feature/workflow-issue-154-real-cluster-phase-20260808`.
6. Record SHA, branch, target and verification in the handoff.

This is guarded branch publication, not `push auto`: no PR merge, branch
deletion, force-push or cleanup is permitted. Later `workflow execute` uses
the declared branch and slice-scoped commits.

## Definition of Done

### Workflow-authoring completion

The dedicated branch is active; workflow/context-pack artifacts are complete;
the requirement matrix covers every issue requirement; Arc42 was checked;
`git diff --check` passes; and the workflow branch is guarded-published.

### Issue-execution completion

All matrix rows are implemented, verified and evidenced; cluster phases are
explicit and plan-parity is green; structured managed-cluster verification is
fail-closed; downstream phases are `not_run` after failure; #218/#232 regressions
remain green; full quality passes; six issue evidence files exist; and the
three review perspectives plus independent auditor have decided completion.

## Handoff to workflow execute

The workflow is ready for a later exact `workflow execute` on
`feature/workflow-issue-154-real-cluster-phase-20260808`. The executor must
read this workflow/context pack, verify branch/locks/matrix and S3/S3D preflight,
create per-slice distribution evidence, execute serially in isolated worktrees,
run targeted then required gates, consolidate after evidence and route failures
through the Typed Error Router. No live installation is implied.

## Arc42 Check Status

Checked: `documentation/arc42/05_building_blocks.adoc` for responsibility;
`06_runtime_view.adoc` for sequence; `10_quality_requirements.adoc` for safety,
evidence and ordering; and `11_risks_and_debt.adoc` for LXC-native/setup risks.

No Arc42 file is changed during workflow authoring because planned behavior is
not implementation evidence. Slice 06 owns post-implementation synchronization
only. No matching EPIC was found; the issue is the traceability source and the
gap is recorded rather than silently filled.

## Workflow Handoff Record

- Workflow ID: `issue-154-20260808`
- Branch: `feature/workflow-issue-154-real-cluster-phase-20260808`
- Branch verified before artifact creation: `yes`
- Requirement decision: `READY_FOR_WORKFLOW`
- Execution profile: `FULL_PATH`
- Parallelization: `not safely parallelizable`
- Live validation: `APPLICABLE_LIVE`, consent not granted during authoring
- External quality: not claimed
- Publication: guarded commit and push required by process
