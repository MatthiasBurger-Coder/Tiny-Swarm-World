# Workflow: Issue #218 FR-1 Dedicated Host Detection

Version: `workflow-issue-218-fr01-v1.0.0`
Workflow ID: `workflow-issue-218-fr01-host-detection-20260712`
Created: `2026-07-12`
Issue: `#218 Treat WSL2 as a Dedicated Host Platform and Decouple Installation from Native Linux Assumptions`
Baseline Branch: `main`
Baseline Commit: `d778fce69bd8f87195ad9b975a1036e3cd1a8819`
Branch: `feature/workflow-issue-218-fr01-host-detection-20260712`
Status: `AUTHORING_PUBLISHED_EXECUTION_PENDING`
Execution Profile: `FULL_PATH`

## Executive Summary

Implement only FR-1 of Issue #218: one structured host classification path
for native Linux, WSL1, WSL2, and unsupported systems. The workflow records
the architecture decision that WSL2 is a dedicated host platform, exposes the
read-only `host detect` CLI result, removes divergent FR-1 detector behavior
from the active installer path, and adds deterministic native/WSL simulations.
It performs no host, Windows, Incus, Docker, network, or service mutation.

This workflow replaces the stale Issue #157 active workflow on clean `main`.
Issue #157 is closed and its merged work remains in the baseline; no locks or
scope carry into Issue #218.

## Target Picture

- One typed result contains host type, distribution, kernel release, Windows
  interop availability, support/setup path, remediation, and sanitized signals.
- Detection evaluates `/proc/sys/kernel/osrelease`, `/proc/version`,
  `WSL_INTEROP`, and `WSL_DISTRO_NAME` rather than Linux family alone.
- WSL1 is explicitly unsupported; ambiguous WSL signals fail closed.
- Native Linux does not resolve or execute Windows preparation.
- `tiny_swarm_world host detect` is read-only and machine-readable with
  `--json`, while normal output remains human readable.
- The accepted host-boundary ADR governs later FR-2 through FR-15 work without
  presenting those later behaviors as implemented in this slice.

## Verified Baseline

- `main` and `origin/main` both resolve to
  `d778fce69bd8f87195ad9b975a1036e3cd1a8819`.
- The source worktree was clean before the isolated worktree was created.
- Baseline full gate passed in WSL with `.venv/bin/python`:
  Ruff passed; 3 Import Linter contracts were kept; 18 architecture tests
  passed; Mypy reported no issues in 472 files; 1,410 unit tests passed with
  28 skipped.
- Existing `HostEnvironmentReport` and `HostPreflightProbe` already cover part
  of FR-1, but `installer.py`, `os_types.py`, and network probing contain
  divergent classifiers and can treat WSL1 or incomplete WSL signals as WSL2.
- No `documentation/epics/` directory exists. Issue #218 and the user's
  explicit one-FR-per-workflow instruction are the requirement authority.

## Requirement Clarification Gate

- Original Request: implement Issue #218 and treat every FR as an individual
  `workflow create` plus `workflow execute`, retaining a runnable green system.
- Interpreted Intent: run 15 serialized, independently reviewable lifecycles;
  this workflow covers only FR-1 and its attached architecture/test evidence.
- Change Type: architecture decision, Python domain/application/port/adapter
  changes, composition/CLI wiring, tests, and directly affected arc42 docs.
- Affected Process Strand: `workflow create -> workflow execute -> PR/CI/Sonar -> merge`.
- Affected Architecture Area: host boundary, preflight, composition, CLI, arc42.
- Explicit Requirements: FR-1, attached NFR-4/5/6, AC-1 detection portion,
  AC-2 detection portion, mandatory detection and simulated-path tests.
- Implicit Requirements: preserve legacy callers where safe, keep the entry
  point thin, avoid import-time commands, redact raw host-specific evidence.
- Assumptions: Issue #218 replaces the stale workflow; the new ADR narrowly
  amends setup evidence policy and complements the Windows Service Agent ADR.
- Non-Goals: filesystem policy, resource inspection, network mutation,
  timeouts/heartbeats, installation evidence finalization, live validation.
- Risks: divergent detector drift, WSL1 false support, container/CI false host
  classification, or documentation claiming later FRs are implemented.
- Open Questions: none blocking.
- Blocking Questions: none.
- Confidence: 97 percent.
- Decision: `READY_FOR_WORKFLOW`.

## Four-Role Three Amigos Gate

- Senior Requirement Engineer: every Issue #218 requirement is retained in
  `.codex/evidence/issue-218/requirement-matrix.md`; FR-1 is the only OPEN item
  released for implementation here.
- Senior System Architect: introduce a focused detector port and native/WSL
  adapters, keep classification in typed core logic, and accept
  `adr-dedicated-wsl2-host-platform-boundary.adoc` before production code.
- Senior Python Automation Developer: inject signal readers/detectors through
  composition; no shell or filesystem reads in domain/application decisions.
- Senior Tester: characterize all current detector entry points; cover native
  Linux, WSL1, WSL2, missing `/proc`, missing interop, unsupported systems,
  CLI structure, and native/WSL simulated integration.
- Console/status UI Developer: keep the immediate human result scannable and
  the JSON result deterministic; do not claim live readiness or render raw
  host-specific signal values as evidence.
- Dependency validator: FR-1 is the root of the 15-FR DAG. The slice is serial
  because the ADR and typed result must stabilize before ports, adapters,
  composition, CLI, tests, and docs can be reviewed together.

Gate evidence:
`.codex/evidence/workflow-issue-218-fr01-host-detection-20260712/three-amigos-gate.md`.

## Scope

In scope:

- dedicated host-platform ADR and arc42 references;
- typed host detection result and signal classification;
- host environment detector port;
- native Linux and WSL detector adapters;
- integration with preflight, installer, legacy OS/runtime consumers,
  composition, and `host detect` CLI;
- FR-1 unit, adapter, CLI, architecture, and simulated integration tests;
- FR-1 documentation and committed execution evidence.

Non-goals:

- any live infrastructure command;
- Windows Firewall, portproxy, hosts-file, or service-agent mutation;
- project filesystem blocking or override implementation (FR-2);
- host resource, Incus limit, or memory pressure behavior (FR-3 to FR-6);
- network preparation (FR-7), hard-coded path cleanup (FR-8), or runner
  observability/timeouts/diagnostics (FR-9 to FR-13);
- final native isolation proof (FR-14) or final evidence package (FR-15).

## Architecture Constraints

- Domain stays independent of application and infrastructure.
- Application services depend on the detector port, not concrete adapters.
- Environment variables and `/proc` reads belong to infrastructure adapters.
- `composition.py` remains the concrete wiring root; `__main__.py` stays thin.
- WSL2 is dedicated but Linux/WSL-only; Windows-native execution remains unsupported.
- The Windows Service Agent remains the sole owner of Windows bridge mutation.
- The ADR may allow normalized `project_path` only in later ignored local
  installation evidence; generic evidence/logging remains path-free.
- No default CPU or memory overcommit is permitted in later resource workflows.

## Python Automation Assessment

This is architecture-sensitive Python product work. Use small immutable domain
types, an application detector port, focused signal adapters, explicit
composition, and deterministic fakes. Do not add a multi-purpose WSL utility.

## Frontend Assessment

No browser or React frontend exists or is affected. The Console/status UI
reviewer is required for `host detect`: human output must show classification,
support decision, setup path, and remediation in a scannable line-oriented
form, while `--json` remains deterministic and machine-readable. It must not
claim live readiness or expose raw host-specific evidence. A terminal dashboard
is not applicable because this is one immediate read-only result, not a dense
or evolving status view.

## Test Strategy

Regression-first characterization precedes detector consolidation. Tests use
temporary `/proc` roots and environment mappings; they do not depend on the
actual WSL host or execute Windows/Incus/Docker commands.

Targeted commands:

```bash
PYTHONPATH=src python3 -m unittest \
  tests.domain.preflight.test_host_environment \
  tests.application.services.platform.host.test_detect_host_environment \
  tests.infrastructure.adapters.host.test_host_environment_detector \
  tests.infrastructure.adapters.preflight.test_host_preflight_probe \
  tests.infrastructure.adapters.network.test_host_network_probe \
  tests.infrastructure.test_os_types \
  tests.infrastructure.test_composition \
  tests.integration.test_host_platform_paths \
  tests.test_installer \
  tests.test_package_entrypoint
python3 tools/quality_gate.py arch-lint
python3 tools/quality_gate.py arch-tests
git diff --check
```

Required D8 gate:

```bash
python3 tools/quality_gate.py quality
```

## Resilience Requirements

- Missing or contradictory signals fail closed; no silent native/WSL fallback.
- WSL1 never becomes live-ready.
- Detector I/O errors become structured unsupported/sandbox facts.
- No retry, sleep, mutation, or external-service dependency is introduced.

## Ordered Slices

### Slice 01: Dedicated host detection boundary

Purpose: accept the host-boundary ADR and implement all FR-1 behavior, tests,
documentation, and evidence as one independently revertible product slice.

```yaml
slice_id: "01"
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers:
  - Senior Requirement Engineer
  - Senior System Architect
  - Senior Tester
  - Senior DevOps Engineer
  - Senior Documentation Engineer
  - Console/status UI Developer
affected_files:
  - documentation/workflow/workflow.md
  - documentation/workflow/context-pack.md
  - documentation/workflow/context-pack.json
  - documentation/workflow/publication-handoff.md
  - documentation/arc42/09_decisions/adr-dedicated-wsl2-host-platform-boundary.adoc
  - documentation/arc42/09_architecture_decisions.adoc
  - documentation/arc42/02_constraints.adoc
  - documentation/arc42/05_building_blocks.adoc
  - documentation/arc42/06_runtime_view.adoc
  - documentation/arc42/07_deployment_view.adoc
  - documentation/arc42/10_quality_requirements.adoc
  - documentation/user_guide/usage.adoc
  - src/tiny_swarm_world/domain/preflight/host_environment.py
  - src/tiny_swarm_world/application/ports/host/**
  - src/tiny_swarm_world/application/services/platform/host/**
  - src/tiny_swarm_world/infrastructure/adapters/host/**
  - src/tiny_swarm_world/infrastructure/adapters/preflight/host_preflight_probe.py
  - src/tiny_swarm_world/infrastructure/adapters/network/host_network_probe.py
  - src/tiny_swarm_world/infrastructure/os_types.py
  - src/tiny_swarm_world/infrastructure/composition.py
  - src/tiny_swarm_world/installer.py
  - src/tiny_swarm_world/__main__.py
  - tests/domain/preflight/**
  - tests/application/services/platform/host/**
  - tests/infrastructure/adapters/host/**
  - tests/infrastructure/adapters/preflight/test_host_preflight_probe.py
  - tests/infrastructure/adapters/network/test_host_network_probe.py
  - tests/infrastructure/test_os_types.py
  - tests/infrastructure/test_composition.py
  - tests/architecture/**
  - tests/integration/test_host_platform_paths.py
  - tests/test_installer.py
  - tests/test_package_entrypoint.py
  - .codex/evidence/issue-218/**
  - .codex/evidence/workflow-issue-218-fr01-host-detection-20260712/**
  - .codex/evidence/slice-01-distribution.md
  - .codex/evidence/slice-01-consolidation.md
  - .tiny-swarm/evidence/issue-218-fr01/**
affected_modules:
  - domain.preflight
  - application.ports.host
  - application.services.platform.host
  - infrastructure.adapters.host
  - infrastructure.composition
  - package-entrypoint
affected_contracts:
  - HostEnvironmentReport
  - PortHostEnvironmentDetector
  - host-detect-cli
dependencies: []
parallel_group: serial-fr01
file_locks:
  - documentation/arc42/09_decisions
  - src/tiny_swarm_world/domain/preflight/host_environment.py
  - src/tiny_swarm_world/infrastructure/composition.py
  - src/tiny_swarm_world/__main__.py
contract_locks:
  - host-environment-classification
  - host-detect-cli
architecture_locks:
  - hexagonal-host-boundary
  - dedicated-wsl2-platform
quality_gates:
  targeted:
    - PYTHONPATH=src python3 -m unittest tests.domain.preflight.test_host_environment tests.application.services.platform.host.test_detect_host_environment tests.infrastructure.adapters.host.test_host_environment_detector tests.infrastructure.adapters.preflight.test_host_preflight_probe tests.infrastructure.adapters.network.test_host_network_probe tests.infrastructure.test_os_types tests.infrastructure.test_composition tests.integration.test_host_platform_paths tests.test_installer tests.test_package_entrypoint
    - python3 tools/quality_gate.py arch-lint
    - python3 tools/quality_gate.py arch-tests
    - git diff --check
  required:
    - python3 tools/quality_gate.py quality
documentation:
  arc42: update host boundary, runtime, deployment, quality, ADR index, and CLI usage
  adr: add accepted dedicated WSL2 host-platform boundary ADR
stop_conditions:
  - host signal semantics cannot be reconciled without guessing
  - native Linux or WSL1 behavior regresses
  - concrete adapter imports cross into domain or application services
  - required targeted or full quality gate fails
```

Done criteria:

- FR-1, its attached AC/NFR/test rows, and CLI detection are implemented.
- The ADR is accepted and arc42 describes only verified FR-1 behavior.
- Distribution and consolidation evidence exist.
- Targeted tests and full quality gate pass.
- Issue-level matrix and FR-1 evidence are consistent.
- Independent review reports no open FR-1 requirement.
- Exactly one Slice-01 checkpoint commit is pushed and its PR is green/merged.

Prerequisites:

- the workflow-authoring commit is published on the declared branch;
- S3 status, branch, scope, and classification checks pass;
- every context-pack hash matches or the authoritative source is reopened;
- `.tiny-swarm/evidence/issue-218-fr01/requirement_matrix.md` and
  `.codex/evidence/slice-01-distribution.md` exist before product writes;
- the dedicated host-boundary ADR text is accepted before production code is
  changed in this slice.

Allowed write scope is exactly the `affected_files` list above. A newly
discovered file requires a stop-and-review scope amendment before it is edited.
The slice is not parallel-write eligible: host result, ADR, composition, CLI,
and tests form one shared contract. There is no shared live infrastructure;
live validation remains serialized and `NOT_RUN`. Merge order is FR-1 before
FR-2.

Requirement-to-verification mapping:

| Requirements | Implementation evidence | Verification |
|---|---|---|
| FR-001, DOD-001, FORBID-008 | typed classifier, detector port/adapters, preflight integration | native/WSL1/WSL2/ambiguous unit and adapter tests |
| NFR-004, NFR-005 | focused domain/port/adapter boundary | `arch-lint`, `arch-tests`, static import review |
| NFR-006, CLI-001 | structured report and `host detect --json` | CLI JSON/schema and human-output tests |
| AC-001 detection portion, DOD-002 | native detector path with no Windows dependency | native simulated integration and sentinel regression |
| AC-002 detection portion, IT-002 | WSL2 detector path with distro/kernel/interop facts | WSL2 simulated integration |
| UT-001 through UT-005, IT-001, RT-001 | deterministic fixtures and compatibility wiring | focused test command plus full quality gate |
| DOC-008 detection portion | accepted ADR, synchronized arc42 text, and `documentation/user_guide/usage.adoc` CLI example | documentation diff and completion review |

## Slice Dependency Graph

```text
Slice 01
```

No cycle, unknown dependency, or parallel execution group exists.

## Parallel Execution

- Can this workflow run in parallel? No.
- Conflicting workflows: FR-2 through FR-15 depend on this contract.
- Shared files: host result, composition, CLI, arc42 index, issue matrix.
- Shared infrastructure: none; live validation is forbidden.
- Requires isolated worktree: yes, already provisioned for this workflow.
- Requires serialized live validation: yes; not applicable/not run here.
- Merge-order constraints: merge FR-1 to green `main` before authoring FR-2.

## Automatic Work Distribution Policy

Before Slice 01 implementation, create
`.codex/evidence/slice-01-distribution.md`.
Analyze every stream in this map:

| Stream | FR-1 decision |
|---|---|
| backend | domain result/classifier, application port/service, infrastructure adapters |
| frontend | no browser/React; Console/status UI review of human and JSON CLI output |
| tests | unit, adapter, CLI, architecture, and simulated integration coverage |
| runtime | installer and network-runtime consumer compatibility; no live execution |
| documentation | ADR, arc42, CLI usage, workflow and evidence |
| quality | targeted commands, architecture gates, full D8 gate, PR/Sonar evidence |
| architecture | hexagonal dependency direction and dedicated host boundary |
| security | signal/evidence redaction and prohibition of Windows/live mutation |

Use real Codex subagents for read-only specialist review.
Implementation remains sequential because the ADR and host result contract are
shared by all streams and regression-first code/test iteration overlaps those
locks. Record the reason, expected files, reviewers, gates, and consolidation
plan. After implementation, create
`.codex/evidence/slice-01-consolidation.md` with accepted
and rejected findings, changed files, tests, documentation, and integration
decision. Codex remains final integration owner.

Unsafe parallelization includes overlapping files, unclear or unstable
architecture/contracts, contradictory requirements, mandatory ordering,
shared migrations, strict database/schema sequencing, generated-file merge
conflicts, a Three Amigos not-safely-parallelizable decision, unclear secrets
handling, or weakened safety guards.

## Git Worktree Execution Rule

This workflow executes only in the verified worktree for
`feature/workflow-issue-218-fr01-host-detection-20260712`. Parallel stream
branches would use `<workflow-branch>-slice-01-<stream>`, but none are selected.
Subagents are read-only reviewers and may not switch branches, merge, or push.

## Issue Completion Discipline

- Requirement matrix path: `.codex/evidence/issue-218/requirement-matrix.md`
  plus ignored `.tiny-swarm/evidence/issue-218-fr01/requirement_matrix.md`.
- Required evidence path: `.tiny-swarm/evidence/issue-218-fr01/` and
  `.codex/evidence/workflow-issue-218-fr01-host-detection-20260712/`.
- Required evidence files: `requirement_matrix.md`, `implementation_summary.md`,
  `changed_files.md`, `test_results.md`, `remaining_risks.md`,
  `acceptance_checklist.md`, distribution, consolidation, and audit record.
- Requirement Lead review: required before completion.
- System Architect Reviewer review: required before completion.
- Test / Evidence Reviewer review: required before completion.
- Issue Completion Auditor review: required for FR-1 completion and again for
  full Issue #218 in FR-15.
- DONE blocking rule: any open/unverified FR-1 requirement forces
  `INCOMPLETE`, `BLOCKED`, or `FAILED`; full Issue #218 remains `IN_PROGRESS`.

## Documentation Synchronization

Update the dedicated host ADR, arc42 constraints/building blocks/runtime/
deployment/quality sections, and any FR-1 CLI documentation actually changed.
Do not document FR-2 through FR-15 as implemented.

## Stop Conditions

- Branch/ref/worktree does not match this workflow.
- Requirement matrix, distribution evidence, metadata, or locks are missing.
- ADR scope contradicts the existing Windows Service Agent ownership.
- A detector needs shell execution outside infrastructure.
- WSL1 or ambiguous WSL is accepted as WSL2.
- Native Linux depends on Windows commands.
- Targeted or required gates fail after at most three classified repair attempts.
- A commit would mix another FR or unrelated changes.
- PR checks or Sonar status are failed, pending indefinitely, or unverifiable.

## Commit, Push, PR, And Rollback Plan

- Workflow authoring commit: workflow/context/evidence files only, guarded push
  to `origin/feature/workflow-issue-218-fr01-host-detection-20260712`; no PR merge.
- Slice commit: exactly Slice 01, with workflow version and rollback reference.
- Execution push: current branch only; no force push or direct main push.
- PR: ready-for-review against `main` after D8 passes; include `Issue #218 / FR-1`.
- Merge: only after required CI and Sonar checks are green and mergeability is verified.
- Rollback: revert the Slice-01 implementation commit and its authoring commit;
  no live state cleanup is required because live commands are forbidden.

## Definition of Done

- Slice 01 done criteria pass.
- `python3 tools/quality_gate.py quality` passes in the FR-1 worktree.
- FR-1 completion audit is PASS; Issue #218 remains IN_PROGRESS.
- PR is merged and `main` is revalidated before FR-2 authoring.
- Real WSL live validation is `NOT_RUN`; no live success claim is made.

## Handoff to workflow execute

Run S3 status/branch/scope/classification, S3D metadata and lock validation,
context hash validation, requirement-matrix verification, specialist review,
distribution evidence, sequential Slice 01 implementation, targeted tests,
D8 full gate, consolidation/evidence/audit, slice commit/push, PR checks, merge,
and clean worktree handoff. The ownership map is: Codex as execution and
integration owner; Senior Python Automation Developer as implementation owner;
Requirement Engineer, System Architect, Tester/DevOps, Documentation Engineer,
and Issue Completion Auditor as independent read-only reviewers. `workflow
execute` must not regenerate this plan.

## arc42 Check Status

Reviewed: constraints, strategy, context, building blocks, runtime, deployment,
cross-cutting concepts, quality requirements, risks, the Windows Service Agent
ADR, installer reporting ADR, command-runner decision, and setup-safety ADR.
The implementation slice must add the dedicated host-boundary ADR and update
the listed active arc42 consequences before completion.
