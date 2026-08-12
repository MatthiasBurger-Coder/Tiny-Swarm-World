# Workflow: Issue #249 — Complete composition-root decomposition

Workflow id: `issue-249-composition-root-refactor-20260811`

Authoring branch: `architecture/workflow-composition-root-refactor-20260811`

Issue: [#249](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/249)

Status: `COMPLETED`

## Executive Summary

`infrastructure/composition.py` remains a high-risk shared wiring block. This
workflow preserves the public module facade while moving operator configuration,
boundary-specific runtime construction, deployment assembly, endpoint readiness,
and host/registry probing into focused infrastructure modules. The change is a
compatibility-preserving refactor; it does not create a service boundary or run
live infrastructure.

## Requirement Clarification Gate

### Original request

`workflow create: Der größte verbliebene technische Block ist jetzt eindeutig
composition.py ... Erstelle zusätzlich ein issue in github und löse das problem.`

### Interpreted intent

Create a governed issue workflow, create a new GitHub issue, and implement the
remaining composition-root decomposition in the current Python codebase. The
public `tiny_swarm_world.infrastructure.composition` import remains stable.

### Change type

Issue-driven architecture and Python infrastructure refactor with local tests,
documentation synchronization, and compatibility evidence.

### Affected process strand

`issue -> requirement matrix -> workflow authoring -> implementation -> local
quality gate -> issue completion audit`

### Affected architecture area

Infrastructure composition, configuration adapters, readiness/probe adapters,
platform/artifact/deployment/setup wiring, and arc42 runtime/building-block
documentation. Domain and application dependency direction remain unchanged.

### Explicit requirements

1. Create a new GitHub issue for the remaining composition-root problem.
2. Keep `tiny_swarm_world.infrastructure.composition` as the public facade.
3. Move operator environment parsing/validation out of the facade.
4. Move detailed platform, artifact, deployment, and setup wiring into focused
   infrastructure composition modules.
5. Move synchronous endpoint readiness and direct host/registry probing out of
   the facade; preserve async workflow behavior and fail-closed behavior.
6. Preserve public builder names, defaults, validation errors, secret
   placeholder semantics, provider selection, live-consent guards, deployment
   order, service-access behavior, and evidence semantics.
7. Add focused regression tests and run the applicable local quality gates.
8. Keep the Linux/WSL-only model and do not run live infrastructure by default.

### Implicit requirements

- No application or domain module may import concrete infrastructure adapters.
- Service construction must remain side-effect free with respect to live systems.
- Existing tests that import compatibility names from `composition` must remain
  valid unless the name is explicitly private and the test is moved to its new
  focused module.
- Configuration and readiness evidence must remain redacted and deterministic.
- No new Windows-specific behavior, Kubernetes-first behavior, Java, Maven, or
  Spring Boot structure may be introduced.

### Assumptions

- GitHub issue #249 is the authoritative issue scope for this implementation.
- Existing issues #195, #196, #198, and #199 are related context, not separate
  execution inputs for this workflow.
- The current clean `main` baseline at authoring was `d56df8d`.
- Local mocked/static verification is sufficient; live Docker, Swarm, LXC,
  Incus, networking, browser, and SonarQube checks are not required for this
  refactor unless explicitly authorized later.
- No new ADR is needed because the public facade and existing infrastructure
  ownership decision remain unchanged.

### Non-goals

- No new independently deployable service or microservice boundary.
- No deployment policy redesign beyond relocating existing assembly logic.
- No live mutation or bootstrap of Incus, Docker, Swarm, Portainer, Nexus,
  Jenkins, Pulsar, SonarQube, or networking.
- No unrelated cleanup or broad test rewrite.

### Risks

- Large existing composition tests import compatibility symbols directly.
- Moving code can change patch targets used by tests if compatibility aliases
  are removed too early.
- Deployment/readiness ordering is safety-sensitive even when construction is
  read-only.
- Environment defaults and sentinel secret behavior are easy to change by
  accident.

### Open questions

- None blocking. The exact module names may be selected during implementation
  within the allowed infrastructure scope, provided responsibilities and
  public compatibility are preserved.

### Blocking questions

- None.

### Confidence and decision

Confidence: 94%.

Decision: `READY_FOR_WORKFLOW`.

## Target Picture

```text
__main__.py
    |
    v
composition.py  (small public facade; no parsing/probing/large wiring)
    |
    +--> composition_configuration.py  (typed operator values and defaults)
    +--> composition_probes.py         (host/registry/readiness probes)
    +--> composition_platform.py       (platform service construction)
    +--> composition_artifacts.py      (artifact service construction)
    +--> composition_deployment.py     (deployment construction and ordering)
    +--> composition_setup.py          (setup orchestration construction)
    +--> composition_models.py / existing adapters
```

The exact split may use a package instead of flat modules if that is needed to
avoid import cycles. The public facade remains the caller-facing compatibility
surface, and all concrete construction stays in infrastructure.

## Verified Baseline

- Repository: `D:/Projects/Tiny-Swarm-World`
- Branch at authoring start: `main`
- Authoring branch: `architecture/workflow-composition-root-refactor-20260811`
- Baseline commit: `d56df8d856529a65d6a8cf2de0ad02eb026993e5`
- `composition.py`: approximately 2,860 lines and 108 KB at baseline.
- Existing focused tests: `tests/infrastructure/test_composition.py` and
  `tests/infrastructure/process/test_composition_wiring.py`.
- Existing architecture tests cover explicit composition bindings, import
  direction, process-spawn boundaries, and LXC runtime boundaries.
- Existing composition helper modules: `composition_models.py`,
  `composition_blocked_workflows.py`, and `composition_lxc_runtimes.py`.

## Scope

### In scope

- New focused infrastructure modules for configuration, probes/readiness, and
  boundary construction where verified responsibilities warrant extraction.
- A compatibility facade in `composition.py` exposing existing public builders
  and compatibility imports.
- Tests for delegation, extracted configuration semantics, readiness behavior,
  fail-closed host/registry probing, and unchanged workflow ordering.
- Arc42 building-block/runtime-view wording synchronized to the implemented
  structure.
- Required issue evidence under `.tiny-swarm/evidence/issue-249/` and workflow
  evidence under `.codex/evidence/`.

### Explicit non-goals

- No change to domain models, application ports, service contracts, or external
  deployment behavior unless required only to preserve imports.
- No live validation claim.
- No frontend/browser work; React/browser skills are not applicable.

## Python Automation Assessment

This is Python infrastructure work. It must use package imports, Python 3.12
compatibility, typed signatures, deterministic mocks, and the repository's
`tools/quality_gate.py` commands. No Windows-native Python command is allowed
for verification; from this Windows host, execute checks through WSL.

## Frontend Assessment

Not applicable. This is terminal/infrastructure composition work and does not
touch a browser React module or terminal presentation behavior.

## Architecture Constraints

- Preserve hexagonal dependency direction.
- Keep `composition.py` in infrastructure and keep concrete adapter creation
  out of application services.
- Keep domain independent of infrastructure and parsing/probing technology.
- Do not hide external command execution in constructors or import-time code.
- Keep explicit dependency wiring; do not introduce a service locator/global
  container.
- Preserve `LiveConsent` fail-closed behavior and typed verification states.
- Keep artifacts/deployment as in-process boundaries, not microservices.

## Resilience Requirements

- Existing numeric configuration bounds and validation errors remain stable.
- Readiness remains bounded by attempts, wait, and request timeouts.
- Missing host tools/files/interfaces continue to return safe unavailable values
  or blocked evidence rather than raising unexpected infrastructure errors.
- No service construction may initiate a live mutation.
- Secret values must never be logged or included in evidence.

## Ordered Slices

### Slice 01 — Baseline, matrix, and architecture contracts

Purpose: establish the issue requirement matrix, capture the public compatibility
surface, and record the three-amigos decision before product edits.

```yaml
slice_id: S249-01
profile: FULL_PATH
owner: Senior Requirement Engineer
secondary_reviewers: [Senior System Architect, Senior Python Automation Developer, Senior Tester]
affected_files: [.tiny-swarm/evidence/issue-249/requirement_matrix.md, .codex/evidence/slice-01-distribution.md, .codex/evidence/slice-01-consolidation.md]
affected_modules: [composition facade, issue evidence]
affected_contracts: [public composition imports, issue requirement matrix]
dependencies: []
parallel_group: SERIAL-BASELINE
file_locks: [.tiny-swarm/evidence/issue-249/requirement_matrix.md]
contract_locks: [composition-public-facade]
architecture_locks: [hexagonal-infrastructure-boundary]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: checked; update after implementation if verified structure changes
  adr: no new ADR expected; review existing separate-platform-artifacts-deployment decision
stop_conditions: [missing issue body, unclear public compatibility, dirty/unrelated branch changes]
```

Done criteria: the matrix contains every issue requirement and maps each row to
implementation and verification evidence; the three perspectives and scope
decision are recorded.

### Slice 02 — Extract operator configuration

Purpose: move environment constants, defaults, typed parsing, secret access,
registry/image configuration, and related validation behind a focused
infrastructure configuration module.

```yaml
slice_id: S249-02
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior System Architect, Senior Requirement Engineer, Senior Tester]
affected_files: [src/tiny_swarm_world/infrastructure/composition.py, src/tiny_swarm_world/infrastructure/composition_configuration.py, tests/infrastructure/test_composition_configuration.py, tests/infrastructure/test_composition.py]
affected_modules: [infrastructure configuration, composition facade]
affected_contracts: [operator defaults, validation errors, secret placeholders]
dependencies: [S249-01]
parallel_group: SERIAL-COMPOSITION
file_locks: [src/tiny_swarm_world/infrastructure/composition.py, src/tiny_swarm_world/infrastructure/composition_configuration.py, tests/infrastructure/test_composition_configuration.py]
contract_locks: [operator-configuration-contract]
architecture_locks: [infrastructure-only-configuration]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition tests.infrastructure.test_composition_configuration]
  required: []
documentation:
  arc42: building blocks/configuration ownership if wording changes
  adr: none unless ownership conflicts are discovered
stop_conditions: [default/validation drift, secret exposure, import cycle, live command during construction]
```

Done criteria: environment reads and related validation no longer live in the
facade; compatibility imports or explicit test migrations preserve callers;
positive, invalid, and secret-placeholder cases are tested.

### Slice 03 — Extract readiness and host/registry probes

Purpose: move endpoint readiness, HTTP status interpretation, host/kernel/file
inspection, interface IP lookup, and registry autodetection into focused probe
modules while preserving async workflow usage and fail-closed results.

```yaml
slice_id: S249-03
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior System Architect, Senior Tester, Senior Requirement Engineer]
affected_files: [src/tiny_swarm_world/infrastructure/composition.py, src/tiny_swarm_world/infrastructure/composition_probes.py, tests/infrastructure/test_composition_probes.py, tests/infrastructure/test_composition.py, tests/architecture/test_process_spawn_boundaries.py]
affected_modules: [readiness probes, host/registry probes, composition facade]
affected_contracts: [EndpointReadinessCheck, fail-closed probing, verification evidence]
dependencies: [S249-02]
parallel_group: SERIAL-COMPOSITION
file_locks: [src/tiny_swarm_world/infrastructure/composition.py, src/tiny_swarm_world/infrastructure/composition_probes.py, tests/infrastructure/test_composition_probes.py]
contract_locks: [readiness-contract, host-probe-contract]
architecture_locks: [no-direct-probing-in-facade]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition tests.infrastructure.test_composition_probes tests.architecture.test_process_spawn_boundaries]
  required: []
documentation:
  arc42: runtime readiness and building-block ownership
  adr: review WSL/platform boundary ADR; no new ADR expected
stop_conditions: [synchronous readiness remains in facade, changed status semantics, unbounded wait, live probe in tests]
```

Done criteria: `composition.py` contains no direct host/kernel/subprocess probe
implementation or synchronous readiness loop; async readiness and evidence are
covered with fake sessions and missing-tool/file cases.

### Slice 04 — Extract boundary-specific runtime wiring

Purpose: move platform, artifact, deployment, and setup service construction
into focused infrastructure composition modules. Preserve explicit builders and
the existing service bundle models.

```yaml
slice_id: S249-04
profile: FULL_PATH
owner: Senior System Architect
secondary_reviewers: [Senior Python Automation Developer, Senior Requirement Engineer, Senior Tester]
affected_files: [src/tiny_swarm_world/infrastructure/composition.py, src/tiny_swarm_world/infrastructure/composition_platform.py, src/tiny_swarm_world/infrastructure/composition_artifacts.py, src/tiny_swarm_world/infrastructure/composition_deployment.py, src/tiny_swarm_world/infrastructure/composition_setup.py, tests/infrastructure/test_composition.py, tests/infrastructure/process/test_composition_wiring.py]
affected_modules: [platform/artifact/deployment/setup composition]
affected_contracts: [public builder functions, service bundle types, explicit wiring]
dependencies: [S249-03]
parallel_group: SERIAL-COMPOSITION
file_locks: [src/tiny_swarm_world/infrastructure/composition.py, src/tiny_swarm_world/infrastructure/composition_platform.py, src/tiny_swarm_world/infrastructure/composition_artifacts.py, src/tiny_swarm_world/infrastructure/composition_deployment.py, src/tiny_swarm_world/infrastructure/composition_setup.py]
contract_locks: [boundary-builder-contract, service-bundle-contract]
architecture_locks: [composition-root-ownership, no-application-adapter-imports]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition tests.infrastructure.process.test_composition_wiring tests.architecture.test_explicit_composition_bindings]
  required: []
documentation:
  arc42: building blocks and runtime view must describe the implemented facade/delegates
  adr: existing separate-platform-artifacts-deployment decision only
stop_conditions: [public builder breakage, import cycle, concrete wiring in application, changed live-consent semantics]
```

Done criteria: the facade delegates to boundary modules; concrete runtime
construction is not duplicated; platform/artifact/deployment/setup behavior and
existing mocked wiring tests remain stable.

### Slice 05 — Extract deployment ordering and integrate facade

Purpose: isolate deployment stack ordering, readiness insertion, Infisical
sequencing, secret evidence steps, and final facade compatibility. This slice
is serialized after the prior shared-file changes.

```yaml
slice_id: S249-05
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior System Architect, Senior Tester, Senior Requirement Engineer]
affected_files: [src/tiny_swarm_world/infrastructure/composition.py, src/tiny_swarm_world/infrastructure/composition_deployment.py, tests/infrastructure/test_composition.py, tests/infrastructure/test_composition_deployment.py]
affected_modules: [deployment composition/planning, public facade]
affected_contracts: [stack order, service-access profile, secret/readiness sequencing]
dependencies: [S249-04]
parallel_group: SERIAL-COMPOSITION
file_locks: [src/tiny_swarm_world/infrastructure/composition.py, src/tiny_swarm_world/infrastructure/composition_deployment.py, tests/infrastructure/test_composition_deployment.py]
contract_locks: [deployment-order-contract, secret-evidence-order]
architecture_locks: [deployment-boundary-ownership]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition tests.infrastructure.test_composition_deployment]
  required: []
documentation:
  arc42: deployment building blocks/runtime view
  adr: no new ADR unless sequence ownership changes
stop_conditions: [stack order drift, readiness before required stack, secret evidence regression, facade exceeds agreed boundary]
```

Done criteria: stack and profile order is tested as an explicit planning
responsibility, and the facade contains only public delegation and compatibility
exports.

### Slice 06 — Verification, documentation, evidence, and audit

Purpose: run targeted tests and the full local quality gate, synchronize arc42,
write required issue evidence, and obtain the independent completion audit.

```yaml
slice_id: S249-06
profile: FULL_PATH
owner: Senior Tester
secondary_reviewers: [Senior System Architect, Senior Requirement Engineer, Senior Documentation Engineer]
affected_files: [documentation/arc42/05_building_blocks.adoc, documentation/arc42/06_runtime_view.adoc, .tiny-swarm/evidence/issue-249/*, .codex/evidence/slice-06-distribution.md, .codex/evidence/slice-06-consolidation.md]
affected_modules: [quality/evidence/documentation]
affected_contracts: [issue completion discipline, verification-state classification]
dependencies: [S249-05]
parallel_group: SERIAL-FINAL
file_locks: [documentation/arc42/05_building_blocks.adoc, documentation/arc42/06_runtime_view.adoc, .tiny-swarm/evidence/issue-249/]
contract_locks: [issue-249-evidence-package]
architecture_locks: [arc42-composition-ownership]
quality_gates:
  targeted: [git diff --check, PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition tests.infrastructure.process.test_composition_wiring]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: required; no planned behavior may be written as implemented
  adr: record reviewed/no-new-ADR status
stop_conditions: [open requirement, missing evidence file, failed quality gate, unavailable external gate must not be called success]
```

Done criteria: all required issue evidence files exist, the requirement matrix
has no open rows, local quality is reported exactly, arc42 matches verified
behavior, and the Issue Completion Auditor returns `PASS` before any `DONE`
claim.

## Slice Dependency Graph

```text
S249-01 -> S249-02 -> S249-03 -> S249-04 -> S249-05 -> S249-06
```

All implementation slices are serialized because they share `composition.py`,
public compatibility imports, and architecture locks. No unsafe parallel stream
is allowed.

## Parallel Execution

- Can this workflow run in parallel? No for implementation; all slices share the
  composition facade and contracts. Read-only role reviews may run in parallel.
- Conflicting workflows: #195, #196, #198, #199 or any workflow changing
  composition, provider wiring, deployment order, readiness, or related tests.
- Shared files: `composition.py`, composition tests, architecture tests,
  arc42 building blocks/runtime view, issue evidence.
- Shared infrastructure: local Python environment and repository working tree;
  no live infrastructure is permitted.
- Requires isolated worktree: yes for executable workflow slices.
- Requires serialized live validation: not applicable by default; any approved
  live validation must be serialized and separately evidenced.
- Merge-order constraints: strict S249-01 through S249-06 order.

## Automatic Work Distribution Policy

`workflow execute` must analyze each slice for safe decomposition across backend,
frontend, tests, runtime, documentation, quality, architecture, and security.
It must use real Codex subagents where supported and otherwise perform an
explicit role-based fallback review in the main thread. Before implementation it
must create `.codex/evidence/slice-<number>-distribution.md`; after each
implemented slice it must create `.codex/evidence/slice-<number>-consolidation.md`.
Codex remains final integration owner.

Stream map:

- backend: Python infrastructure extraction by Senior Python Automation Developer;
- frontend: not applicable;
- tests: focused unittest and architecture checks by Senior Tester;
- runtime: read-only runtime/provider safety review by Senior DevOps when needed;
- documentation: arc42 and evidence synchronization by Senior Documentation Engineer;
- quality: `QUALITY.md` gates and verification-state classification;
- architecture: facade/dependency-direction review by Senior System Architect;
- security: secret redaction and no-live-mutation review when configuration or
  external-action behavior is touched.

Do not parallelize overlapping files, unclear architecture, contradictory
requirements, mandatory ordering, shared migrations, generated-file conflicts,
Three-Amigos rejection, unclear secrets handling, or weakened safety guards.

## Git Worktree Execution Rule

Every executable slice requires an isolated worktree. Stream branches, if a
read-only stream is approved, use:

`architecture/workflow-composition-root-refactor-20260811-slice-<number>-<stream>`

Workers must verify the workflow branch and locks before writing, remain within
their scope, and never merge directly. Codex consolidates accepted changes and
owns final tests, evidence, and publication.

## Role and Ownership Map

| Responsibility | Owner |
|---|---|
| Workflow creation and dependency ordering | Senior Workflow Architect |
| Requirement extraction and issue traceability | Senior Requirement Engineer |
| Facade/module boundaries and arc42 fit | Senior System Architect |
| Configuration/probe/wiring implementation | Senior Python Automation Developer |
| Focused tests and quality evidence | Senior Tester |
| Arc42 and evidence synchronization | Senior Documentation Engineer |
| Final completion decision | Issue Completion Auditor |

Mandatory roles used for this workflow: Senior Requirement Engineer, Senior
System Architect, Senior Python Automation Developer, and Senior Tester.

## Issue Completion Discipline

- Requirement matrix path: `.tiny-swarm/evidence/issue-249/requirement_matrix.md`.
- Required evidence path: `.tiny-swarm/evidence/issue-249/`.
- Required evidence files: `requirement_matrix.md`, `implementation_summary.md`,
  `changed_files.md`, `test_results.md`, `remaining_risks.md`, and
  `acceptance_checklist.md`.
- Requirement Lead review: S249-01 and S249-06.
- System Architect Reviewer review: S249-03 through S249-06.
- Test / Evidence Reviewer review: S249-02 through S249-06.
- Issue Completion Auditor review: required after S249-06 and before `DONE`.
- DONE blocking rule: any open, guessed, conflicting, or unverified requirement
  forces `INCOMPLETE`, `BLOCKED`, or `FAILED`; local quality does not imply live
  or external success.

## Quality-Gate Expectations

Authoritative commands come from `QUALITY.md`:

```bash
PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition tests.infrastructure.process.test_composition_wiring
python3 tools/quality_gate.py quality
git diff --check
```

From the current Windows host, execute Python and quality commands inside WSL.
The full gate is local evidence only. Live and external states must use
`LIVE_NOT_APPLICABLE`/`LIVE_CONSENT_MISSING` and
`EXTERNAL_GATE_UNAVAILABLE` as applicable; never claim live or Sonar success
without executed evidence.

## Documentation Synchronization

The relevant arc42 building-block and runtime-view sections were reviewed.
After implementation, update only verified module ownership and keep the public
facade/runtime behavior statements accurate. Existing ADR
`adr-separate-platform-artifacts-deployment.adoc` remains the architecture
authority; this refactor is an internal organization change and does not need a
new ADR unless verified ownership changes.

## Stop Conditions and Uncertainty Escalation

Stop if the branch is detached/dirty with unrelated changes, the issue or
baseline cannot be read, a public compatibility contract is unclear, the
composition split would require an application/domain dependency violation, a
live command is needed without consent, the quality-gate authority is unclear,
or an ADR/design decision is required but absent. Escalate requirements to the
Requirement Engineer, architecture to the System Architect, and test failures
to the Senior Tester. Do not silently reduce scope.

## Definition of Done

- #249 requirements are all captured in the matrix.
- `composition.py` is a verified public facade with focused delegates.
- Configuration, probing/readiness, boundary wiring, and deployment ordering are
  in focused infrastructure modules.
- Compatibility and fail-closed behavior are tested.
- Arc42 matches the implemented structure.
- Required local evidence exists and the full local quality gate passes, or an
  exact documented blocker is recorded.
- Issue Completion Auditor returns `PASS`.

## Handoff to workflow execute

`workflow execute` may begin only after S3/S3D validates this workflow, the
requirement matrix, locks, and the dedicated worktree. Execute slices strictly
in order. The executor must not infer a public compatibility break, run live
infrastructure, or claim issue completion without the required evidence and
independent audit.

## Arc42 Check Status

Arc42 building-blocks, runtime-view, configuration, and existing composition
decision sections were read. No new ADR is required for the planned internal
module split. The final implementation must update `05_building_blocks.adoc`
and `06_runtime_view.adoc` if their verified ownership wording changes; planned
behavior is not treated as implemented behavior.
