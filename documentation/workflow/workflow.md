# Workflow: Unify Tiny Swarm World System Boundaries

## Executive Summary

This workflow creates the governed execution plan for checking Tiny Swarm
World for completeness and unifying the system around its accepted
responsibility model: Platform, Artifacts, Deployment, and Shared.

The workflow supersedes the completed skills-and-agents workflow that was
previously active under `documentation/workflow`. It is a FULL_PATH workflow
because it may touch product architecture, Python automation, tests,
documentation, workflow governance, and quality gates. It must not run live
Multipass, Docker Swarm, compose, netplan, socat, Portainer, Nexus, Jenkins,
RabbitMQ, SonarQube, or Swagger/NGINX commands.

The subagent review found that the repository is coherent but incomplete in
specific areas:

- Artifacts and Deployment are declared as boundaries but are not wired as
  executable workflow bundles.
- CLI entries for `artifacts` and `deployment` exist but currently return
  blocked results.
- Mutating platform workflows are protected by verify-after-apply, but the
  composed platform steps do not yet expose verification contracts.
- Command metadata is safety-classified, but command-backed verification is not
  wired through the catalog; current command specs rely on manual verification
  declarations.
- Desired inventory repository support exists, but no default
  `infra/config/inventory/desired_inventory.yaml` baseline exists.
- Responsibility-boundary tests exist only partially; broad hexagonal rules are
  covered, but Platform/Artifacts/Deployment/Shared ownership checks need to be
  strengthened.
- Console/status UI is the only UI surface; no React or browser frontend module
  exists.
- Direct scripts under `infra/prepare`, `infra/compose`, and `infra/swarm`
  remain live-operation surfaces outside the CLI consent guard.

## Target Picture

### Verified Baseline At Workflow Creation

- Active workflow version:

```text
system-unification-v1.0.0
```

- Active workflow branch:

```bash
codex/workflow-system-unification-20260524
```

- Root `AGENTS.md` defines Tiny Swarm World as a Linux/WSL-only Python
  automation project with hexagonal architecture.
- Root `QUALITY.md` defines the preferred full gate:

```bash
python3 tools/quality_gate.py quality
```

- `documentation/epics/` is absent at workflow creation time. This workflow
  treats the user request plus existing architecture documents as the initial
  requirement source and creates a formal EPIC baseline in Slice 01 before
  product implementation slices.
- `documentation/adr/` is absent. ADR-like material currently lives under
  `documentation/architecture/adr-*.adoc`; the workflow must either preserve
  that convention explicitly or create an ADR index/path decision before adding
  new decisions.
- `src/tiny_swarm_world/infrastructure/composition.py` exposes
  `PlatformServices`, empty `ArtifactServices`, and empty
  `DeploymentServices`.
- `src/tiny_swarm_world/__main__.py` declares `artifacts prepare`,
  `artifacts verify`, `deployment apply`, and `deployment verify`, but these
  entries are not implemented and return blocked results.
- `documentation/architecture/adr-separate-platform-artifacts-deployment.adoc`
  is accepted as the current responsibility direction and marks implementation
  as partial.
- `documentation/arc42/05_building_blocks.adoc`,
  `documentation/arc42/06_runtime_view.adoc`, and
  `documentation/arc42/11_risks_and_debt.adoc` already document that
  artifact/deployment wiring and reset/destroy retention semantics remain
  planned work.
- `python` and `python3` are not available from the current PowerShell shell,
  but WSL is available and reports Python 3.12.3. Workflow execution must
  document Linux/WSL commands and use `python3` as the authoritative command
  form from `QUALITY.md`.

### Target Outcome

The completed workflow must produce:

- a formal system-unification EPIC or requirement baseline;
- a refreshed completeness inventory that distinguishes implemented, planned,
  blocked, transitional, and legacy surfaces;
- a resolved ADR storage convention or documented architecture-decision index;
- stronger static responsibility checks for Platform, Artifacts, Deployment,
  Shared, and Console/status UI boundaries;
- mutating Platform workflow steps that either expose verification contracts or
  remain deliberately blocked with exact reasons;
- explicit Artifact and Deployment workflow contracts, with wiring or deliberate
  blocked states backed by tests;
- console/status UI behavior aligned with runner status values;
- direct live scripts classified as supported, transitional, deprecated, or
  quarantined without executing them;
- README, arc42, architecture docs, user/deployment docs, and workflow reports
  synchronized with actual behavior;
- exact targeted and full quality-gate evidence;
- one slice-scoped checkpoint commit and push per executed slice when required
  gates pass.

## Requirement Clarification Record

Original request:

```text
workflow create with subagents:
ueberpruefe das system auf vollstaendigkeit und schlage einen workflow vor um
das system zu vereinheitlichen. Falls der Workflow zu 90% okey ist kannst du
pushen und danach in den workflow execute with subagents gehen.
```

Interpreted intent:

- Create a new active workflow with delegated subagent review.
- Check system completeness across code, docs, tests, runtime wiring, workflow
  governance, and quality gates.
- Propose an executable unification workflow.
- If the workflow is at least 90 percent ready, commit/push the workflow branch
  and release it for `workflow execute with subagents`.

Change type:

- Workflow creation and system-unification planning.

Affected process strand:

- FULL_PATH system unification: requirements, architecture, Python automation,
  runtime boundaries, tests, documentation, quality gates, and workflow
  execution governance.

Affected architecture area:

- Platform, Artifacts, Deployment, Shared, CLI workflow contracts,
  verify-after-apply, console/status UI, legacy live-operation surfaces,
  architecture documentation, and quality boundaries.

Explicit requirements:

- Use subagents.
- Check the system for completeness.
- Suggest a workflow to unify the system.
- Push only if the workflow is at least 90 percent acceptable.
- Enter workflow execution with subagents after push when release conditions
  are met.

Implicit requirements:

- Preserve Linux/WSL-only operation and POSIX command examples.
- Preserve hexagonal architecture and application-to-port dependencies.
- Keep concrete adapter construction in
  `src/tiny_swarm_world/infrastructure/composition.py`.
- Do not run live infrastructure commands.
- Use `QUALITY.md` as the quality-command authority.
- Treat console/status UI as terminal UI, not React/browser frontend.
- Keep Java under `src/main/java` as deployment example surface only.

Assumptions:

- "System unification" means completing and aligning the accepted
  Platform/Artifacts/Deployment/Shared model rather than introducing a new
  architecture.
- The missing EPIC is non-blocking for workflow creation because the user
  explicitly asked for a workflow proposal; Slice 01 must create the EPIC before
  implementation slices continue.
- The existing architecture ADR under `documentation/architecture/` is accepted
  as the current architecture baseline until Slice 02 resolves ADR path
  governance.
- Push permission applies only to the workflow branch and only after quality
  checks for the created workflow artifacts pass or a justified documentation
  gate limitation is recorded.

Non-goals:

- No live infrastructure execution.
- No big-bang package move.
- No Kubernetes-first pivot.
- No Spring Boot, browser React, forensic analytics, generic microservice
  extraction, vector database, graph database, JavaParser, or Joern-driven
  architecture.
- No weakening of `.importlinter`, architecture tests, or `QUALITY.md`.
- No direct execution of scripts under `infra/prepare`, `infra/compose`, or
  `infra/swarm`.

Risks:

- Missing `documentation/epics/` lowers traceability until Slice 01 completes.
- The local shell cannot run `python3`; quality evidence must distinguish the
  authoritative Linux/WSL command from any environment-specific fallback.
- Wiring artifact/deployment workflows too early could blur Portainer stack
  lifecycle and Nexus repository configuration.
- Adding verification to mutating platform steps may expose missing observed
  inventory or evidence ports.
- Legacy live scripts contain destructive or credential-sensitive behavior and
  must be inspected statically only.
- Console UI status semantics may hide aggregate failures if not tested against
  the real adapters.

Open questions:

- None blocking for workflow creation.

Blocking questions:

- None for workflow creation.
- Workflow execution must stop after Slice 01 if the EPIC baseline cannot be
  written or cannot align with the existing architecture decision.

Confidence level:

```text
91 percent
```

Decision:

```text
READY_FOR_WORKFLOW
```

Rationale:

- The requested goal is broad, but the repository already contains accepted
  architecture direction, documented risks, tests, and subagent findings that
  identify a concrete unification path.
- The missing EPIC is converted into an explicit first slice and is therefore a
  controlled execution prerequisite rather than an unbounded guess.

## Execution Profile

```text
executionProfile=FULL_PATH
reason=The workflow can affect architecture boundaries, runtime workflow wiring,
quality gates, branch/push behavior, and documentation governance.
requiredFullReviews=senior_requirement_engineer, senior_system_architect,
senior_python_automation_developer, senior_react_frontend as console-scope
guard, senior_tester, senior_workflow_architect
allowedImpactChecks=senior_react_frontend may report N/A for browser React
scope only
requiredQualityChecks=git diff --check, targeted unit/static gates by slice,
and python3 tools/quality_gate.py quality before release or push when practical
stopConditions=unverified branch, stale workflow context, live infrastructure
need, unclear ADR convention, missing quality command evidence, architecture
contract weakening, or scope drift outside Platform/Artifacts/Deployment/Shared
```

## Scope

### Allowed Write Scope

The workflow may change:

```text
documentation/epics/**
documentation/workflow/**
documentation/architecture/**
documentation/arc42/**
documentation/deployment/**
documentation/system/**
documentation/user_guide/**
README.md
AGENTS.md only if root governance must be corrected
QUALITY.md only if quality authority is explicitly wrong
.importlinter only with Senior Tester and Senior System Architect approval
tests/**
src/tiny_swarm_world/domain/**
src/tiny_swarm_world/application/**
src/tiny_swarm_world/infrastructure/composition.py
src/tiny_swarm_world/infrastructure/adapters/**
infra/** only for static classification, README/status docs, compatibility
metadata, or path-safe non-executed reorganization slices
```

### Forbidden Write Scope

The workflow must not change:

```text
src/main/java/**
pom.xml
external static-analysis CI files
generated caches
local virtual environments
logs
IDE state
```

Direct modification of live scripts under `infra/prepare`, `infra/compose`, or
`infra/swarm` is allowed only when the active slice explicitly owns legacy
quarantine or path compatibility and verification remains static.

## Architecture Constraints

- Preserve the hexagonal architecture.
- Domain must not import application or infrastructure.
- Application services must depend on ports, not concrete adapters.
- Infrastructure adapters implement ports and contain technology-specific
  behavior.
- `src/tiny_swarm_world/infrastructure/composition.py` remains the standard
  composition root.
- `src/tiny_swarm_world/__main__.py` remains thin.
- Platform, Artifacts, Deployment, and Shared are responsibility boundaries
  inside the Python automation process, not independent microservices.
- Console/status UI is terminal UI only.
- Java remains a deployment example.

## Python Automation Assessment

Python automation is the primary implementation surface. The workflow must
address these incomplete areas in small slices:

- `PlatformServices` is wired, but mutating steps must expose verification
  contracts or remain blocked before apply.
- `ArtifactServices` exists as an empty bundle while artifact services are
  available through the Nexus namespace and artifact compatibility exports.
- `DeploymentServices` exists as an empty bundle while `EnsureNexusStack` is
  implemented in the deployment namespace.
- CLI workflow declarations for artifacts and deployment currently return
  blocked results.
- Architecture tests document target responsibility boundaries but need
  stronger regression checks for actual ownership.
- Command catalog entries require a verification foundation before they can
  drive verify-after-apply. A read-classified Swarm join-token command also
  emits credential material and needs explicit redaction/evidence semantics.
- Desired inventory support exists in code, but the committed baseline
  inventory file is absent.

## Frontend And Console UI Assessment

No React or browser frontend exists. The mandatory frontend review role is a
scope guard and must route implementation only to console/status UI. The
workflow may address console gaps:

- aggregate `instance="all"` updates can be ignored by `PortUI.update_status`
  when `all` is not a known instance;
- status values from command-runner UI wrappers use lowercase
  `success`/`error`, while Linux UI completion checks uppercase
  `Success`/`Error`;
- tests currently validate recording calls more than real console adapter
  completion behavior.

## Test Strategy

- Start each implementation slice with the nearest focused tests.
- Keep all live infrastructure effects mocked or statically inspected.
- Use `python3 tools/quality_gate.py arch-lint`,
  `python3 tools/quality_gate.py arch-tests`,
  `python3 tools/quality_gate.py test`, and the full quality gate from
  `QUALITY.md` as slice risk increases.
- For documentation-only workflow creation, run `git diff --check` and record
  any reason the full gate is skipped.
- Do not claim `python3 tools/quality_gate.py quality` passed unless it was
  executed successfully in a suitable Python environment.

## Resilience And Safety Requirements

- No live infrastructure commands during workflow creation or default
  execution.
- Mutating workflows must fail closed when verification evidence is missing.
- Reset/destroy retention semantics require an ADR or explicit decision before
  implementation.
- Secret-bearing values must not be committed or captured in verification
  evidence.
- Direct scripts must remain clearly marked as live operations unless and until
  a slice safely replaces them.

## Ordered Slices

### Slice 01: EPIC Baseline And Completeness Criteria

Purpose:

- Create the system-unification EPIC baseline and acceptance criteria before
  product implementation.

```yaml
slice_id: "01"
profile: "FULL_PATH"
owner: "senior_requirement_engineer"
secondary_reviewers:
  - "senior_system_architect"
  - "senior_tester"
affected_files:
  - "documentation/epics/system-unification.md"
  - "documentation/workflow/reports/01-system-completeness-baseline.md"
affected_modules: []
affected_contracts:
  - "system-unification-requirement"
dependencies: []
parallel_group: "A"
file_locks:
  - "documentation/epics/**"
  - "documentation/workflow/reports/01-system-completeness-baseline.md"
contract_locks:
  - "system-unification-requirement"
architecture_locks:
  - "Platform-Artifacts-Deployment-Shared"
quality_gates:
  targeted:
    - "git diff --check"
  required: []
documentation:
  arc42: "checked, no update expected unless EPIC contradicts arc42"
  adr: "checked via documentation/architecture/adr-separate-platform-artifacts-deployment.adoc"
stop_conditions:
  - "EPIC cannot align with existing architecture decision"
  - "acceptance criteria remain untestable"
  - "business goal becomes broader than Platform/Artifacts/Deployment/Shared"
```

Done criteria:

- `documentation/epics/system-unification.md` exists.
- Completeness categories are explicit: implemented, planned, blocked,
  transitional, legacy, and out of scope.
- The EPIC answers whether implementation still matches the intended system.

### Slice 02: ADR And arc42 Alignment

Purpose:

- Resolve the ADR location convention and align arc42 with the active
  unification baseline.

```yaml
slice_id: "02"
profile: "FULL_PATH"
owner: "senior_system_architect"
secondary_reviewers:
  - "senior_documentation_engineer"
  - "adr-steward"
affected_files:
  - "documentation/architecture/**"
  - "documentation/adr/**"
  - "documentation/arc42/05_building_blocks.adoc"
  - "documentation/arc42/06_runtime_view.adoc"
  - "documentation/arc42/09_architecture_decisions.adoc"
  - "documentation/arc42/11_risks_and_debt.adoc"
affected_modules: []
affected_contracts:
  - "architecture-decision-convention"
  - "arc42-system-boundary-view"
dependencies:
  - "01"
parallel_group: "B"
file_locks:
  - "documentation/architecture/**"
  - "documentation/adr/**"
  - "documentation/arc42/**"
contract_locks:
  - "architecture-decision-convention"
architecture_locks:
  - "Platform-Artifacts-Deployment-Shared"
quality_gates:
  targeted:
    - "git diff --check"
    - "python3 tools/quality_gate.py arch-tests"
  required: []
documentation:
  arc42: "update if convention or responsibility status changes"
  adr: "resolve path convention before new ADRs"
stop_conditions:
  - "ADR convention cannot be resolved"
  - "arc42 would document planned behavior as implemented"
  - "architecture decision requires user approval before implementation"
```

Done criteria:

- ADR convention is explicit.
- arc42 accurately distinguishes implemented, planned, and blocked behavior.

### Slice 03: Responsibility Boundary Quality Coverage

Purpose:

- Strengthen tests for Platform, Artifacts, Deployment, Shared, Console/status
  UI, and legacy live-operation boundaries.

```yaml
slice_id: "03"
profile: "FULL_PATH"
owner: "senior_tester"
secondary_reviewers:
  - "senior_system_architect"
  - "quality_archunit_reviewer"
affected_files:
  - "tests/architecture/**"
  - ".importlinter"
  - "documentation/architecture/**"
affected_modules:
  - "tiny_swarm_world.domain"
  - "tiny_swarm_world.application"
  - "tiny_swarm_world.infrastructure"
affected_contracts:
  - "hexagonal-import-boundaries"
  - "responsibility-boundary-tests"
dependencies:
  - "02"
parallel_group: "C"
file_locks:
  - "tests/architecture/**"
  - ".importlinter"
  - "documentation/architecture/**"
contract_locks:
  - "quality-gate"
  - "hexagonal-import-boundaries"
architecture_locks:
  - "Platform-Artifacts-Deployment-Shared"
quality_gates:
  targeted:
    - "python3 tools/quality_gate.py arch-lint"
    - "python3 tools/quality_gate.py arch-tests"
  required:
    - "python3 tools/quality_gate.py test"
documentation:
  arc42: "not expected unless tests change documented responsibility semantics"
  adr: "not expected"
stop_conditions:
  - ".importlinter would be weakened"
  - "tests require live infrastructure"
  - "known transitional conflicts cannot be documented precisely"
```

Done criteria:

- New or updated tests catch responsibility drift without requiring a big-bang
  move.
- Existing hexagonal gates still pass.

### Slice 04: Command Catalog, Inventory, And Evidence Foundation

Purpose:

- Establish the command-verification and desired-inventory foundation needed
  before platform workflow steps can safely continue after apply.

```yaml
slice_id: "04"
profile: "FULL_PATH"
owner: "senior_python_automation_developer"
secondary_reviewers:
  - "senior_system_architect"
  - "senior_tester"
  - "observability-runtime-diagnostics"
  - "secrets-and-config-management"
affected_files:
  - "src/tiny_swarm_world/domain/command/**"
  - "src/tiny_swarm_world/domain/inventory/**"
  - "src/tiny_swarm_world/application/ports/commands/**"
  - "src/tiny_swarm_world/application/ports/repositories/**"
  - "src/tiny_swarm_world/infrastructure/adapters/command_runner/**"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/**"
  - "infra/config/**/command_*.yaml"
  - "infra/config/inventory/**"
  - "tests/domain/command/**"
  - "tests/domain/inventory/**"
  - "tests/infrastructure/adapters/command_runner/**"
  - "tests/infrastructure/adapters/repositories/**"
affected_modules:
  - "tiny_swarm_world.domain.command"
  - "tiny_swarm_world.domain.inventory"
  - "tiny_swarm_world.application.ports.commands"
  - "tiny_swarm_world.infrastructure.adapters.command_runner"
  - "tiny_swarm_world.infrastructure.adapters.repositories"
affected_contracts:
  - "command-verification-contract"
  - "desired-inventory-contract"
  - "verification-evidence-redaction"
dependencies:
  - "03"
parallel_group: "D"
file_locks:
  - "src/tiny_swarm_world/domain/command/**"
  - "src/tiny_swarm_world/domain/inventory/**"
  - "src/tiny_swarm_world/application/ports/commands/**"
  - "src/tiny_swarm_world/application/ports/repositories/**"
  - "src/tiny_swarm_world/infrastructure/adapters/command_runner/**"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/**"
  - "infra/config/**/command_*.yaml"
  - "infra/config/inventory/**"
  - "tests/domain/command/**"
  - "tests/domain/inventory/**"
  - "tests/infrastructure/adapters/command_runner/**"
  - "tests/infrastructure/adapters/repositories/**"
contract_locks:
  - "command-verification-contract"
  - "desired-inventory-contract"
  - "verification-evidence-redaction"
architecture_locks:
  - "Shared"
  - "Platform"
  - "hexagonal-architecture"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.command_runner.test_command_workflow_configuration"
    - "PYTHONPATH=src python3 -m unittest tests.domain.command.test_command_spec"
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_inventory_repositories"
    - "python3 tools/quality_gate.py arch-tests"
  required:
    - "python3 tools/quality_gate.py test"
documentation:
  arc42: "update concepts, quality requirements, and risks if verification semantics change"
  adr: "new ADR only if command verification semantics change materially"
stop_conditions:
  - "manual verification would be treated as passed evidence"
  - "credential-bearing command output would be stored as evidence"
  - "desired inventory requires host-specific IPs, user names, or secrets"
  - "verification support would execute live infrastructure in tests"
```

Done criteria:

- Command verification support is explicit and test-backed, or still blocked
  with exact reasons.
- Credential-bearing command outputs have redaction/evidence rules.
- Desired inventory baseline is either introduced safely or documented as a
  deliberate blocker.

### Slice 05: Platform Verify-After-Apply Contracts

Purpose:

- Make mutating platform workflows either executable under verify-after-apply
  or explicitly blocked with tested, operator-safe reasons.

```yaml
slice_id: "05"
profile: "FULL_PATH"
owner: "senior_python_automation_developer"
secondary_reviewers:
  - "senior_system_architect"
  - "senior_tester"
  - "resilience-engineering"
affected_files:
  - "src/tiny_swarm_world/application/services/platform/**"
  - "src/tiny_swarm_world/application/services/multipass/**"
  - "src/tiny_swarm_world/application/services/network/**"
  - "src/tiny_swarm_world/application/services/vm/**"
  - "src/tiny_swarm_world/application/ports/repositories/**"
  - "src/tiny_swarm_world/domain/inventory/**"
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "tests/application/services/platform/**"
  - "tests/application/services/multipass/**"
  - "tests/application/services/network/**"
  - "tests/infrastructure/test_composition.py"
affected_modules:
  - "tiny_swarm_world.application.services.platform"
  - "tiny_swarm_world.application.services.multipass"
  - "tiny_swarm_world.application.services.network"
  - "tiny_swarm_world.application.services.vm"
affected_contracts:
  - "verify-after-apply"
  - "platform-workflow-contract"
dependencies:
  - "04"
parallel_group: "E"
file_locks:
  - "src/tiny_swarm_world/application/services/platform/**"
  - "src/tiny_swarm_world/application/services/multipass/**"
  - "src/tiny_swarm_world/application/services/network/**"
  - "src/tiny_swarm_world/application/services/vm/**"
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "tests/application/services/platform/**"
  - "tests/application/services/multipass/**"
  - "tests/application/services/network/**"
  - "tests/infrastructure/test_composition.py"
contract_locks:
  - "verify-after-apply"
  - "platform-workflow-contract"
architecture_locks:
  - "hexagonal-architecture"
  - "Platform"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_platform_workflows"
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition"
    - "python3 tools/quality_gate.py arch-tests"
  required:
    - "python3 tools/quality_gate.py test"
documentation:
  arc42: "update runtime view and risks if platform execution status changes"
  adr: "new ADR only if retention or verification semantics change materially"
stop_conditions:
  - "implementation requires live Multipass, Docker Swarm, netplan, or socat"
  - "verification evidence semantics are unclear"
  - "application service would import infrastructure"
```

Done criteria:

- Mutating platform workflow behavior is tested without live commands.
- Any remaining blocked state has an explicit reason and operator-facing test.

### Slice 06: Artifact And Deployment Workflow Contracts

Purpose:

- Turn blocked artifact/deployment CLI entries into explicit contract-backed
  workflows or keep them blocked with stronger tested reasons.

```yaml
slice_id: "06"
profile: "FULL_PATH"
owner: "senior_python_automation_developer"
secondary_reviewers:
  - "senior_system_architect"
  - "senior_devops"
  - "senior_tester"
affected_files:
  - "src/tiny_swarm_world/__main__.py"
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "src/tiny_swarm_world/application/services/artifacts/**"
  - "src/tiny_swarm_world/application/services/deployment/**"
  - "src/tiny_swarm_world/application/services/nexus/**"
  - "src/tiny_swarm_world/application/ports/clients/**"
  - "src/tiny_swarm_world/application/ports/repositories/**"
  - "src/tiny_swarm_world/domain/deployment/**"
  - "src/tiny_swarm_world/domain/nexus/**"
  - "tests/test_package_entrypoint.py"
  - "tests/infrastructure/test_composition.py"
  - "tests/application/services/artifacts/**"
  - "tests/application/services/deployment/**"
  - "tests/application/services/nexus/**"
affected_modules:
  - "tiny_swarm_world.application.services.artifacts"
  - "tiny_swarm_world.application.services.deployment"
  - "tiny_swarm_world.application.services.nexus"
  - "tiny_swarm_world.infrastructure.composition"
affected_contracts:
  - "artifact-workflow-contract"
  - "deployment-workflow-contract"
  - "cli-workflow-contract"
dependencies:
  - "05"
parallel_group: "F"
file_locks:
  - "src/tiny_swarm_world/__main__.py"
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "src/tiny_swarm_world/application/services/artifacts/**"
  - "src/tiny_swarm_world/application/services/deployment/**"
  - "src/tiny_swarm_world/application/services/nexus/**"
  - "tests/test_package_entrypoint.py"
  - "tests/infrastructure/test_composition.py"
  - "tests/application/services/artifacts/**"
  - "tests/application/services/deployment/**"
  - "tests/application/services/nexus/**"
contract_locks:
  - "artifact-workflow-contract"
  - "deployment-workflow-contract"
  - "cli-workflow-contract"
architecture_locks:
  - "Artifacts"
  - "Deployment"
  - "hexagonal-architecture"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.test_package_entrypoint"
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition"
    - "PYTHONPATH=src python3 -m unittest tests.application.services.artifacts"
    - "PYTHONPATH=src python3 -m unittest tests.application.services.deployment"
    - "PYTHONPATH=src python3 -m unittest tests.application.services.nexus"
    - "python3 tools/quality_gate.py arch-tests"
  required:
    - "python3 tools/quality_gate.py test"
documentation:
  arc42: "update building blocks, runtime view, deployment view, and risks if wiring changes"
  adr: "new ADR only if workflow semantics change beyond accepted split"
stop_conditions:
  - "work requires a real Portainer, Nexus, Docker registry, or image push"
  - "Nexus repository configuration and stack deployment ownership cannot be separated"
  - "artifact or deployment workflow would bypass live-consent controls"
  - "application code would depend on infrastructure adapters"
```

Done criteria:

- CLI behavior for artifact/deployment workflows is explicit and test-backed.
- Artifact and Deployment boundaries are clearer than the baseline.

### Slice 07: Console Status UI Consistency

Purpose:

- Align console/status UI behavior with command-runner status values and
  aggregate status updates.

```yaml
slice_id: "07"
profile: "NORMAL_PATH"
owner: "senior_python_automation_developer"
secondary_reviewers:
  - "senior_react_frontend"
  - "console-status-ui-developer"
  - "senior_tester"
affected_files:
  - "src/tiny_swarm_world/application/ports/ui/**"
  - "src/tiny_swarm_world/infrastructure/adapters/ui/**"
  - "tests/infrastructure/adapters/ui/**"
affected_modules:
  - "tiny_swarm_world.application.ports.ui"
  - "tiny_swarm_world.infrastructure.adapters.ui"
affected_contracts:
  - "console-status-contract"
dependencies:
  - "03"
parallel_group: "F"
file_locks:
  - "src/tiny_swarm_world/application/ports/ui/**"
  - "src/tiny_swarm_world/infrastructure/adapters/ui/**"
  - "tests/infrastructure/adapters/ui/**"
contract_locks:
  - "console-status-contract"
architecture_locks:
  - "Console-status-UI"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.ui.test_linux_ui"
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.ui.test_command_runner_ui_failure_semantics"
    - "PYTHONPATH=src python3 -m unittest tests.application.services.commands.test_command_executer"
  required:
    - "python3 tools/quality_gate.py test"
documentation:
  arc42: "not expected unless UI evidence semantics change"
  adr: "not expected"
stop_conditions:
  - "work introduces package.json, React, browser routes, TSX, JSX, or browser state"
  - "status values collapse verified evidence and recommendations into ambiguous strings"
```

Done criteria:

- Real console adapters handle aggregate and terminal status consistently.
- No browser frontend scope is introduced.

### Slice 08: Legacy Live-Surface Quarantine

Purpose:

- Classify and, when safe, quarantine direct live-operation scripts without
  executing them.

```yaml
slice_id: "08"
profile: "FULL_PATH"
owner: "senior_devops"
secondary_reviewers:
  - "senior_system_architect"
  - "senior_security_sandbox_engineer"
  - "senior_tester"
affected_files:
  - "infra/prepare/**"
  - "infra/compose/**"
  - "infra/swarm/**"
  - "documentation/deployment/**"
  - "documentation/user_guide/**"
  - "documentation/system/**"
  - "README.md"
  - "tests/architecture/**"
affected_modules: []
affected_contracts:
  - "live-operation-surface"
  - "operator-safety-documentation"
dependencies:
  - "03"
parallel_group: "G"
file_locks:
  - "infra/prepare/**"
  - "infra/compose/**"
  - "infra/swarm/**"
  - "documentation/deployment/**"
  - "documentation/user_guide/**"
  - "documentation/system/**"
  - "README.md"
  - "tests/architecture/**"
contract_locks:
  - "live-operation-surface"
architecture_locks:
  - "operator-safety"
quality_gates:
  targeted:
    - "git diff --check"
    - "python3 tools/quality_gate.py arch-tests"
  required:
    - "python3 tools/quality_gate.py test"
documentation:
  arc42: "update risks/debt and deployment view if support status changes"
  adr: "required before removing supported live-operation entry points"
stop_conditions:
  - "a validation step would run live infrastructure"
  - "a script removal would break a documented supported workflow"
  - "credentials or host-specific data would be committed"
```

Done criteria:

- Supported, transitional, deprecated, and legacy live surfaces are explicitly
  classified.
- No live command is executed.

### Slice 09: Documentation Sync, Quality Gate, And Execution Report

Purpose:

- Synchronize docs and record final workflow execution evidence.

```yaml
slice_id: "09"
profile: "FULL_PATH"
owner: "senior_documentation_engineer"
secondary_reviewers:
  - "senior_workflow_architect"
  - "senior_requirement_engineer"
  - "senior_system_architect"
  - "senior_tester"
  - "git_commit_reviewer"
affected_files:
  - "README.md"
  - "documentation/workflow/**"
  - "documentation/epics/**"
  - "documentation/architecture/**"
  - "documentation/arc42/**"
  - "documentation/deployment/**"
  - "documentation/system/**"
  - "documentation/user_guide/**"
affected_modules: []
affected_contracts:
  - "workflow-execution-report"
  - "documentation-sync"
dependencies:
  - "06"
  - "07"
  - "08"
parallel_group: "H"
file_locks:
  - "README.md"
  - "documentation/**"
contract_locks:
  - "documentation-sync"
  - "quality-evidence"
architecture_locks:
  - "Platform-Artifacts-Deployment-Shared"
quality_gates:
  targeted:
    - "git diff --check"
    - "python3 tools/quality_gate.py arch-lint"
    - "python3 tools/quality_gate.py arch-tests"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "final checked or updated status required"
  adr: "final ADR convention and any new decisions recorded"
stop_conditions:
  - "quality results are missing"
  - "docs claim unimplemented behavior is implemented"
  - "execution report does not record blockers and skipped gates"
```

Done criteria:

- Docs match actual files and behavior.
- Exact quality commands and results are recorded.
- Remaining blocked surfaces are named with owners and next actions.

## Slice Dependency Graph

```text
01 -> 02 -> 03 -> 04 -> 05 -> 06 -> 09
              \---------------> 07 ------/
              \---------------> 08 ------/
```

## Parallelization Opportunities

- Slices 04, 07, and 08 have different primary write scopes after Slice 03,
  but Slice 05 must wait for the command/evidence foundation in Slice 04.
- S3D must still verify locks before any parallel work.
- Default execution should use one write-capable implementation worker at a
  time unless S3D proves file, contract, and architecture locks are disjoint.

## Role And Subagent Ownership Map

- Senior Workflow Architect: workflow integrity, dependencies, S3/S3D handoff.
- Senior Requirement Engineer: EPIC baseline and acceptance criteria.
- Senior System Architect: Platform/Artifacts/Deployment/Shared boundaries,
  ADR and arc42 governance.
- Senior Python Automation Developer: Python implementation slices.
- Senior React Frontend: read-only guard confirming browser/React scope is
  absent; console UI implementation routes to console/status skills.
- Senior Tester: tests, quality gates, failure classification.
- Senior DevOps: live-surface quarantine and Docker/Swarm safety review.
- Senior Documentation Engineer: README, arc42, deployment/user docs, reports.
- Security/Sandbox reviewer: scripts, secrets, unsafe defaults.
- Git reviewers/operators: commit and push readiness only after D8 gates pass.

## Quality Gate Expectations

Use `QUALITY.md` as authority.

Minimum workflow-creation checks:

```bash
git diff --check
```

Required before implementation checkpoint push when practical:

```bash
python3 tools/quality_gate.py quality
```

Targeted gates are listed per slice. If `python3` or tooling is unavailable in
the current environment, record the exact failure and do not claim the gate
passed. A local fallback command can be recorded as supplemental evidence only.

## Documentation Synchronization Points

- `documentation/epics/system-unification.md`
- `documentation/workflow/workflow.md`
- `documentation/workflow/context-pack.md`
- `documentation/workflow/context-pack.json`
- `documentation/workflow/execution-report.md`
- `documentation/architecture/**`
- `documentation/arc42/**`
- `documentation/deployment/**`
- `documentation/system/**`
- `documentation/user_guide/**`
- `README.md`

## Commit And Push Plan

The user explicitly authorized push when the workflow is at least 90 percent
acceptable.

Workflow creation may be committed and pushed when:

1. The active branch is `codex/workflow-system-unification-20260524`.
2. `documentation/workflow/workflow.md` and context-pack files exist.
3. `git diff --check` passes.
4. Any skipped full quality gate is documented and justified.

Workflow execution checkpoint pushes must follow the workflow-executor rule:
one slice-scoped commit and push per completed slice after required quality
gates pass.

## Stop Conditions

Stop and report when:

- active branch is not `codex/workflow-system-unification-20260524`;
- working tree contains unrelated or unclear changes;
- workflow or context-pack branch names are stale;
- EPIC baseline cannot be created or contradicts the accepted architecture;
- live infrastructure execution would be required;
- ADR convention remains unresolved before new decisions;
- artifact/deployment ownership would require guessing;
- application code would import infrastructure;
- quality commands are missing and no documented limitation exists;
- a slice would weaken `.importlinter`, architecture tests, or `QUALITY.md`;
- Java, React/browser, Spring Boot, Kubernetes-first, or unrelated analytics
  concerns start driving the Python automation architecture.

## Definition Of Done

This workflow is complete when:

- the EPIC baseline exists;
- Platform, Artifacts, Deployment, Shared, and Console/status UI responsibilities
  are test-backed;
- platform verify-after-apply behavior is executable or deliberately blocked
  with tested reasons;
- artifact and deployment CLI workflows are explicit and test-backed;
- legacy live-operation surfaces are classified;
- README, architecture docs, arc42, user/deployment docs, workflow reports, and
  quality evidence are synchronized;
- `python3 tools/quality_gate.py quality` passes or any inability to run it is
  explicitly recorded as a blocker;
- final execution report answers what is complete, what remains blocked, and
  what the next slice or workflow must do.

## Handoff To Workflow Execute

Workflow execution is released with this entrypoint:

```text
workflow execute with subagents
```

Before executing, the executor must verify:

```bash
git status --short --branch
git branch --show-current
git show-ref --verify --quiet refs/heads/codex/workflow-system-unification-20260524
```

Execution may start only when the active branch is
`codex/workflow-system-unification-20260524`, the local branch ref exists, and
the working tree contains no unrelated or unclear changes.

## arc42 Check Status

arc42 was checked during workflow creation. No arc42 update is required for
workflow creation itself because this turn only regenerates workflow artifacts.
Execution slices must update arc42 when they change implemented status,
runtime behavior, architecture-decision convention, deployment wiring, or risk
classification.
