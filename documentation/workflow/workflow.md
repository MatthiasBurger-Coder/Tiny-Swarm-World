# Workflow: Issue #218 FR-2 WSL Project Filesystem Policy

Version: `workflow-issue-218-fr02-v1.0.0`
Workflow ID: `workflow-issue-218-fr02-filesystem-policy-20260712`
Created: `2026-07-12`
Issue: `#218 Treat WSL2 as a Dedicated Host Platform and Decouple Installation from Native Linux Assumptions`
Baseline Branch: `main`
Baseline Commit: `81ca7efab062347a87c32e5305427236b048d741`
Branch: `feature/workflow-issue-218-fr02-filesystem-policy-20260712`
Status: `DONE / PR #221 MERGED / MAIN GREEN / CLEANED`
Execution Profile: `FULL_PATH`

## Executive Summary

Implement only FR-2 of Issue #218. Under WSL2, the normalized resolved
repository path is inspected against `/proc/self/mountinfo`. Windows-mounted
filesystems block live installation by default; the exact
`--allow-wsl-windows-filesystem` override permits only that decision and must
be recorded in a protected local document. Native Linux and WSL-native paths
remain supported. No repository move/copy or live infrastructure operation is
allowed.

FR-1 completed through PR #220. GitHub Python 3.12 quality, coverage, and
SonarCloud passed, the PR merged as `81ca7ef`, the feature branch/worktree were
removed, and the full local gate passed again on merged `main` with 1,456 tests
and 28 expected skips.

## Target Picture

- A typed domain assessment distinguishes native Linux, WSL-native,
  Windows-mounted, and unknown project filesystems.
- A focused infrastructure inspector reads injected mountinfo without shell or
  Windows commands and resolves symlinked repository roots.
- WSL2 Windows mounts are `BLOCKED` unless the explicit override yields
  `ALLOWED_BY_OVERRIDE`; unknown WSL mount data fails closed.
- Native Linux is allowed without constructing or invoking Windows behavior.
- The existing global `--preflight` command is the governed CLI-002 equivalent
  and exposes a path-free `HOST-FILESYSTEM` check immediately after `HOST`.
- Installer order becomes host detection, filesystem authorization, Python
  bootstrap, then all later file/process/live work.
- An applied override is atomically recorded with owner-only permissions below
  `${XDG_STATE_HOME:-$HOME/.local/state}/tiny-swarm-world/installation/`.
- The resolved XDG evidence target must itself be a verified WSL-native/Linux
  filesystem. An operator-selected DrvFS/Windows-mounted XDG root blocks the
  override even when chmod appears to succeed.
- Only the protected document contains the exact resolved `project_path`.

## Verified Baseline

- Clean `main` and `origin/main` both resolve to
  `81ca7efab062347a87c32e5305427236b048d741`.
- PR #220 is merged; its Python quality and SonarCloud checks succeeded.
- The merged-main full WSL gate passed: Ruff, 3 import contracts over 300
  files/687 dependencies, 18 architecture tests, Mypy over 488 files, and
  1,456 tests with 28 skips.
- FR-2 characterization passed 281 existing installer, install-script, CLI,
  preflight, composition, project-path, and simulated host-path tests.
- Expected RED: the exact override is currently rejected by argparse, no
  filesystem policy exists, and a WSL2 checkout under `/mnt/d` reaches Python
  dependency bootstrap instead of blocking.
- Actual read-only mount evidence classifies the checkout as WSL `9p`/`v9fs`
  with a `drvfs` characteristic. No live command was run.

## Requirement Clarification Gate

- Original request: implement Issue #218 with each FR treated as an individual
  `workflow create` and `workflow execute`, preserving a runnable system.
- This workflow releases: `FR-002`, the project-path portion of `AC-002`,
  `AC-003`, `UT-006` through `UT-009`, `CLI-002`, `SEQ-002`, `DOC-005`,
  `DOD-003`, `FORBID-002`, and `GOV-006`.
- Cross-cutting obligations: `PROC-001`, `OUT-001`, `NFR-004` through
  `NFR-006`, relevant documentation requirements, `DOD-012` and
  `DOD-014` through `DOD-017`, applicable forbidden rules, `GOV-003`,
  `GOV-010`, `GOV-013`, and `GOV-014`.
- Revalidate without closing later scope: `FR-001`, `AC-001`, `IT-001`,
  `IT-002`, `RT-001`, `SEQ-001`, `GOV-004`, `DOD-002`, and `FORBID-008`.
- Downstream contracts remain open: resources, path cleanup, final evidence,
  and later setup sequencing in FR-3, FR-8, and FR-15.
- Blocking questions: none.
- Confidence: 96 percent.
- Decision: `READY_FOR_WORKFLOW`.

## Four-Role Three Amigos Gate

- Senior Requirement Engineer: `READY_FOR_WORKFLOW`; a Windows mount without
  override is a blocker, not a warning, and the override cannot bypass any
  other host, consent, resource, network, or live-safety gate.
- Senior System Architect: `PASS`; use pure domain policy, an inspector port,
  separate evaluate/authorize services, a protected-evidence repository port,
  focused adapters, and composition-root wiring. The accepted WSL2 and setup
  safety ADRs already decide the boundary; no new ADR is required.
- Senior Python Automation Developer: preserve the installer `python -S`
  standard-library bootstrap closure and stop before dependency bootstrap,
  secret generation, general evidence, subprocesses, or setup phases.
- Senior Tester: `PASS_FOR_WORKFLOW_CREATE`; require generic drive/mount
  detection, `/mnt/data` false-positive protection, symlink resolution,
  fail-closed mount errors, path-free general evidence, private atomic override
  evidence, and direct setup/installer stop-order tests.
- Security/evidence view: exact project path is forbidden from preflight JSON,
  logs, progress, committed evidence, and general installation context. The
  protected allowlist document is the sole exception.
- Dependency validation: FR-1 is merged and green. FR-2 is serial and must
  merge green before FR-3 workflow creation.

Gate evidence:
`.codex/evidence/workflow-issue-218-fr02-filesystem-policy-20260712/three-amigos-gate.md`.

## Scope

In scope:

- typed project-filesystem inspection and assessment;
- mountinfo parsing for native filesystems, `drvfs`, and WSL `9p`/`v9fs`;
- inspector and protected-evidence ports plus evaluate/authorize services;
- owner-only atomic local override evidence;
- `HOST-FILESYSTEM` preflight ordering and fail-fast behavior;
- installer flag, ordering, propagation, and standard-library bootstrap safety;
- direct setup and platform-init guard propagation through composition;
- FR-2 tests, architecture constraints, docs, and issue evidence.

Non-goals:

- automatic repository move, copy, clone, or repair;
- resource inspection/profile/Incus limits/memory pressure (FR-3 to FR-6);
- Windows/WSL network preparation or command cleanup (FR-7/FR-8);
- workflow observability/timeouts/diagnostics (FR-9 to FR-13);
- final native isolation or complete installation evidence (FR-14/FR-15);
- live Incus, Docker, Swarm, compose, network, Windows, or service execution.

## Architecture Constraints

- Domain policy is pure and imports no application/infrastructure modules.
- Application services depend on inspector/evidence ports, not adapters.
- Path resolution, mountinfo reads, atomic files, permissions, and XDG path
  resolution stay in infrastructure.
- `composition.py` constructs normal-runtime adapters; the installer may use
  the same standard-library-safe boundary before third-party bootstrap.
- Evaluation and authorization remain separate responsibilities.
- Native Linux must not load or execute WSL/Windows command behavior.
- The override applies only to a confirmed WSL2 Windows-mounted filesystem.
- An evidence write or permission-verification failure blocks an override.
- A protected-evidence target on DrvFS/Windows-mounted or unknown storage is a
  blocker; operator-controlled `XDG_STATE_HOME` cannot weaken this rule.
- No exact project path enters safe/public serializers or general evidence.

## Python Automation Assessment

FR-2 is architecture-sensitive Python automation. Use immutable typed domain
objects, injected ports, two small application services, focused POSIX
adapters, and explicit composition. The installer import path remains usable
with `python -S`; no constructor or import-time read, write, or command is
allowed. `asyncio` behavior outside the preflight boundary is unchanged.

## Frontend Assessment

No browser/React frontend exists or is affected. Console/status UI review is
required because the existing human and JSON preflight summaries gain one
ordered check and remediation. A terminal dashboard is not applicable to one
immediate preflight result. Output must remain accessible, deterministic, and
free of the resolved absolute project path.

## Resilience Requirements

- Missing, unreadable, ambiguous, or contradictory WSL mount facts fail closed.
- A blocked decision short-circuits all later checks and workflow phases.
- Override evidence is atomic and idempotently replaced; a partial prior file
  remains intact after write failure.
- Permission verification failure is a blocker, not a warning.
- The protected XDG target is independently classified as Linux-native before
  writing; Windows-mounted or unknown targets fail closed.
- Evaluation runs no retry, sleep, shell, network, or external process.
- Native Linux and WSL-native decisions do not depend on Windows interop.
- Repeated authorized evaluation produces the same safe decision and evidence
  schema without duplicate entries.

## ADR Decision

No new ADR is required. Implement the already accepted decisions in:

- `adr-dedicated-wsl2-host-platform-boundary.adoc`;
- `adr-autonomous-setup-safety.adoc`.

Update their implementation status only. Stop for a new ADR if implementation
would auto-move/copy the repository, widen path disclosure, weaken private
evidence, change read-only preflight semantics, or broaden override authority.

## Test Strategy

Regression-first implementation is mandatory. Add the FR-2 tests before
production code and persist the expected RED checkpoint.

Targeted modules:

```bash
PYTHONPATH=src python3 -m unittest \
  tests.domain.preflight.test_project_filesystem \
  tests.application.services.platform.host.test_evaluate_project_filesystem \
  tests.application.services.platform.host.test_authorize_project_filesystem \
  tests.application.services.platform.test_preflight_service \
  tests.application.services.platform.test_platform_workflows \
  tests.application.services.setup.test_setup_workflow \
  tests.infrastructure.adapters.host.test_project_filesystem_inspector \
  tests.infrastructure.adapters.repositories.test_project_filesystem_evidence_local_repository \
  tests.infrastructure.test_project_paths \
  tests.infrastructure.test_composition \
  tests.integration.test_host_platform_paths \
  tests.architecture.test_host_detection_boundaries \
  tests.test_installer \
  tests.test_install_script \
  tests.test_package_entrypoint
```

Run the focused command normally and with `CI=1`, then:

```bash
python3 tools/quality_gate.py lint
python3 tools/quality_gate.py arch-lint
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py typecheck
python3 tools/quality_gate.py test
python3 tools/quality_gate.py quality
git diff --check
```

Required cases include `/mnt/c`, `/mnt/d`, `/mnt/e`, another drive, a
mountinfo-detected DrvFS outside the standard automount root, `/mnt/data`, WSL
`/home`, native Linux, symlink-to-DrvFS, nested/escaped mountpoints, unreadable
or contradictory mountinfo, irrelevant overrides, evidence write/permission
failure, no path leakage, and no later action after `BLOCKED`.

## Ordered Slices

### Slice 01: WSL project filesystem gate

Purpose: implement the complete FR-2 contract as one independently revertible
slice without live infrastructure.

Prerequisites: guarded workflow-create commits are present on the dedicated
branch and exact remote head; `main@81ca7ef` is the recorded merged-green
baseline; S3/S3D metadata and locks validate; no unrelated worktree change is
present; the RED checkpoint is persisted before production writes.

```yaml
slice_id: "01"
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers:
  - Senior Requirement Engineer
  - Senior System Architect
  - Senior Tester
  - Senior Security/Evidence Reviewer
  - Senior Documentation Engineer
  - Console/status UI Developer
  - Issue Completion Auditor
affected_files:
  - documentation/workflow/workflow.md
  - documentation/workflow/context-pack.md
  - documentation/workflow/context-pack.json
  - documentation/workflow/publication-handoff.md
  - .codex/evidence/issue-218/requirement-matrix.md
  - .codex/evidence/issue-218/workflow-ledger.md
  - .codex/evidence/slice-01-distribution.md
  - .codex/evidence/slice-01-consolidation.md
  - .codex/evidence/workflow-issue-218-fr02-filesystem-policy-20260712/**
  - .tiny-swarm/evidence/issue-218-fr02/**
  - README.md
  - documentation/user_guide/installation.adoc
  - documentation/user_guide/usage.adoc
  - documentation/arc42/05_building_blocks.adoc
  - documentation/arc42/06_runtime_view.adoc
  - documentation/arc42/07_deployment_view.adoc
  - documentation/arc42/09_decisions/adr-autonomous-setup-safety.adoc
  - documentation/arc42/09_decisions/adr-dedicated-wsl2-host-platform-boundary.adoc
  - documentation/arc42/10_quality_requirements.adoc
  - src/tiny_swarm_world/__main__.py
  - src/tiny_swarm_world/installer.py
  - src/tiny_swarm_world/domain/project_filesystem.py
  - src/tiny_swarm_world/domain/preflight/preflight_check.py
  - src/tiny_swarm_world/application/ports/host/__init__.py
  - src/tiny_swarm_world/application/ports/host/port_project_filesystem_inspector.py
  - src/tiny_swarm_world/application/ports/repositories/port_project_filesystem_evidence_repository.py
  - src/tiny_swarm_world/application/services/platform/host/__init__.py
  - src/tiny_swarm_world/application/services/platform/host/evaluate_project_filesystem.py
  - src/tiny_swarm_world/application/services/platform/host/authorize_project_filesystem.py
  - src/tiny_swarm_world/application/services/platform/preflight_service.py
  - src/tiny_swarm_world/infrastructure/adapters/host/__init__.py
  - src/tiny_swarm_world/infrastructure/adapters/host/project_filesystem_inspector.py
  - src/tiny_swarm_world/infrastructure/adapters/repositories/project_filesystem_evidence_local_repository.py
  - src/tiny_swarm_world/infrastructure/composition.py
  - tests/domain/preflight/test_project_filesystem.py
  - tests/application/services/platform/host/test_evaluate_project_filesystem.py
  - tests/application/services/platform/host/test_authorize_project_filesystem.py
  - tests/application/services/platform/test_preflight_service.py
  - tests/application/services/platform/test_platform_workflows.py
  - tests/application/services/setup/test_setup_workflow.py
  - tests/infrastructure/adapters/host/test_project_filesystem_inspector.py
  - tests/infrastructure/adapters/repositories/test_project_filesystem_evidence_local_repository.py
  - tests/infrastructure/test_project_paths.py
  - tests/infrastructure/test_composition.py
  - tests/integration/test_host_platform_paths.py
  - tests/architecture/test_host_detection_boundaries.py
  - tests/test_installer.py
  - tests/test_install_script.py
  - tests/test_package_entrypoint.py
affected_modules:
  - tiny_swarm_world.domain.project_filesystem
  - tiny_swarm_world.application.ports.host
  - tiny_swarm_world.application.ports.repositories
  - tiny_swarm_world.application.services.platform.host
  - tiny_swarm_world.application.services.platform.preflight_service
  - tiny_swarm_world.infrastructure.adapters.host
  - tiny_swarm_world.infrastructure.adapters.repositories
  - tiny_swarm_world.infrastructure.composition
  - tiny_swarm_world.installer
  - tiny_swarm_world.__main__
affected_contracts:
  - ProjectFilesystemKind/Inspection/Assessment/Decision
  - PortProjectFilesystemInspector
  - PortProjectFilesystemEvidenceRepository
  - HOST-FILESYSTEM preflight check
  - --allow-wsl-windows-filesystem
  - protected project-filesystem evidence schema v1
  - installer standard-library bootstrap import closure
dependencies: []
parallel_group: serial-01
file_locks:
  - documentation/workflow/**
  - .codex/evidence/issue-218/**
  - .codex/evidence/workflow-issue-218-fr02-filesystem-policy-20260712/**
  - .codex/evidence/slice-01-*.md
  - .tiny-swarm/evidence/issue-218-fr02/**
  - README.md
  - documentation/user_guide/{installation,usage}.adoc
  - documentation/arc42/{05_building_blocks,06_runtime_view,07_deployment_view,10_quality_requirements}.adoc
  - documentation/arc42/09_decisions/{adr-autonomous-setup-safety,adr-dedicated-wsl2-host-platform-boundary}.adoc
  - src/tiny_swarm_world/{__main__,installer}.py
  - src/tiny_swarm_world/domain/{project_filesystem,preflight/preflight_check}.py
  - src/tiny_swarm_world/application/ports/host/**
  - src/tiny_swarm_world/application/ports/repositories/port_project_filesystem_evidence_repository.py
  - src/tiny_swarm_world/application/services/platform/{preflight_service,host/**}.py
  - src/tiny_swarm_world/infrastructure/adapters/host/**
  - src/tiny_swarm_world/infrastructure/adapters/repositories/project_filesystem_evidence_local_repository.py
  - src/tiny_swarm_world/infrastructure/composition.py
  - tests/domain/preflight/test_project_filesystem.py
  - tests/application/services/platform/{test_preflight_service,test_platform_workflows,host/**}.py
  - tests/application/services/setup/test_setup_workflow.py
  - tests/infrastructure/adapters/host/test_project_filesystem_inspector.py
  - tests/infrastructure/adapters/repositories/test_project_filesystem_evidence_local_repository.py
  - tests/infrastructure/{test_project_paths,test_composition}.py
  - tests/integration/test_host_platform_paths.py
  - tests/architecture/test_host_detection_boundaries.py
  - tests/test_{installer,install_script,package_entrypoint}.py
contract_locks:
  - host classification precedes filesystem authorization
  - HOST-FILESYSTEM immediately follows HOST and short-circuits on BLOCKED
  - safe serializers contain no resolved project path
  - protected schema is the sole exact-path evidence surface
  - protected XDG target must be verified Linux-native and owner-only
  - override applies only to confirmed WSL2 Windows mounts
  - python -S installer import loads no third-party dependency
architecture_locks:
  - domain remains independent of application and infrastructure
  - application depends only on inspector/evidence ports
  - mountinfo/path/atomic-file/permission I/O remains infrastructure
  - concrete normal-runtime construction remains in composition.py
  - evaluate and authorize responsibilities remain separate
  - no WSL mega-utility and no Windows command execution
quality_gates:
  targeted:
    - focused FR-2 unittest modules
    - focused FR-2 unittest modules with CI=1
    - python -S installer bootstrap guard
    - python3 tools/quality_gate.py lint
    - python3 tools/quality_gate.py arch-lint
    - python3 tools/quality_gate.py arch-tests
    - python3 tools/quality_gate.py typecheck
    - git diff --check
  required:
    - python3 tools/quality_gate.py test
    - python3 tools/quality_gate.py quality
    - GitHub Python 3.12 quality and SonarCloud
    - full quality gate on merged main
documentation:
  arc42: update building-block, runtime, deployment, and quality views
  adr: update implementation status only; no new ADR
stop_conditions:
  - unknown WSL mount facts would be allowed
  - private atomic evidence or permission verification cannot be enforced
  - protected XDG target is Windows-mounted or cannot be classified
  - exact project path escapes the protected local document
  - a live path bypasses the common filesystem guard
  - any later check or phase runs after BLOCKED
  - implementation requires automatic move/copy or live infrastructure
  - bootstrap imports a third-party dependency
  - scope, requirement, architecture, quality, CI, or merge evidence is red or unverifiable
acceptance:
  - all directly owned FR-2 IDs are VERIFIED with implementation and test evidence
  - WSL2 Windows mounts block before later work unless the exact override is applied
  - applied override is privately and atomically evidenced without general path leakage
  - native Linux and WSL-native paths remain green
  - focused, architecture, type, full quality, CI, Sonar, merge, cleanup, and merged-main gates pass
rollback: git revert <slice-commit>
```

Allowed write scope is exactly `affected_files`/`file_locks`; every other path
is read-only. Slice dependencies are empty because FR-1 is a merged baseline,
not a slice in this workflow. Parallel eligibility is `false`; conflicting
workflows are FR-3 through FR-15 and any workflow touching preflight,
installer, CLI, composition, host ports/adapters, or the protected schema.
Shared infrastructure is `none` because live validation is forbidden. An
isolated worktree is mandatory, live validation stays serialized and
`NOT_RUN`, and this slice must merge before FR-3 is authored.

### Slice 01 Requirement-To-Verification Mapping

| ID | Implementation target | Verification |
|---|---|---|
| FR-002 | typed policy, mount inspector, override authorization and protected evidence | domain/adapter/installer/setup/CLI tests plus completion audit |
| AC-002 | add the project-path assessment portion without claiming resources/network | simulated WSL2 preflight/integration JSON review |
| AC-003 | default block, Linux-home remediation and recorded applied override | `/mnt/d` blocker/override/evidence tests |
| UT-006 | generic Windows-drive inspection | named `/mnt/c` unit case |
| UT-007 | generic Windows-drive inspection | named `/mnt/d` unit case |
| UT-008 | generic Windows-drive inspection | named `/mnt/e` unit case |
| UT-009 | native filesystem assessment | named native Linux/WSL-home unit cases |
| CLI-002 | existing global `--preflight` emits ordered `HOST-FILESYSTEM` | human/JSON/exit/path-redaction CLI tests |
| SEQ-002 | common authorization immediately after host detection | installer stop-before-bootstrap and setup/platform-init guard tests |
| DOC-005 | Linux-home recommendation and exact override docs | README/installation/usage independent review |
| DOD-003 | complete Windows-mount evaluation contract | acceptance checklist and independent auditor |
| FORBID-002 | mountinfo plus generic drive logic; no `/mnt/d` special case | other-drive, `/mnt/data`, nested mount and static-diff tests |
| GOV-006 | report only; never move/copy/clone automatically | process/file mutation sentinels and diff audit |
| PROC-001 | isolated serialized FR-2 lifecycle | ledger, commits, PR, checks, merge, cleanup evidence |
| OUT-001 | keep filesystem handling outside shared Incus/Swarm/deployment core | architecture/static dependency revalidation; status not owned by FR-2 |
| NFR-004 | separate policy, inspector, evaluator, authorizer and evidence writer | architecture review and class-responsibility tests |
| NFR-005 | no shell decisions; mount/file I/O only in adapters | import contracts, architecture tests, subprocess sentinels |
| NFR-006 | immutable machine-readable inspection/assessment and safe dict | schema, Mypy and JSON tests |
| DOC-001 | update installation behavior affected by FR-2 | installation documentation review |
| DOC-002 | document WSL path prerequisite separately | WSL subsection review |
| DOC-003 | state native Linux remains separately allowed | native prerequisite review |
| DOD-012 | new unit/adapter/integration/regression tests remain green | focused, `CI=1`, test and full quality gates |
| DOD-014 | synchronize all FR-2 docs and ADR status | independent documentation/architecture review |
| DOD-015 | initial and completion Three Amigos reviews | gate and completion evidence |
| DOD-016 | required Python 3.12 and SonarCloud checks pass | exact-head GitHub check rollup |
| DOD-017 | PR merges only after successful gates | mergeability, merge, branch/worktree cleanup evidence |
| FORBID-001 | make no resource-limit-only change | affected-file/diff audit |
| FORBID-006 | no combined WSL utility | architecture boundary review |
| FORBID-009 | retain native Linux tests | native unit/integration/full regression gates |
| FORBID-010 | Windows/unknown WSL mounts are mandatory blockers | status/severity/short-circuit tests |
| FORBID-011 | make no live WSL readiness claim | `NOT_RUN` evidence and auditor review |
| FORBID-012 | no production TODO as completion | TODO/diff and completion audit |
| GOV-003 | preserve baseline and expected RED before implementation | characterization and TDD-red evidence |
| GOV-010 | execute every repository quality command | quality result evidence and CI |
| GOV-013 | synchronize named documentation | changed-file inventory and doc review |
| GOV-014 | isolated branch/worktree, commits, PR, merge and cleanup | Git/remote evidence |
| FR-001 | reuse the typed host result before filesystem policy | host detector regressions |
| AC-001 | native preflight remains independent of Windows behavior | native integration and no-Windows sentinels |
| DOD-002 | preserve separate native Linux handling | domain/preflight/integration regression |
| IT-001 | preserve deterministic native path | `test_host_platform_paths` native case |
| IT-002 | extend deterministic simulated WSL2 path | `test_host_platform_paths` WSL2 filesystem cases |
| RT-001 | preserve native preflight | focused and full regression suites |
| SEQ-001 | host detection remains first | installer/preflight order assertions |
| GOV-004 | host model remains established before filesystem/network work | architecture dependency audit |
| FORBID-008 | WSL never collapses into native Linux | host/filesystem classifier integration tests |

Verification commands are the exact focused/`CI=1` commands in Test Strategy,
the `quality_gates` metadata, GitHub exact-head checks, and the merged-main full
gate. Required issue evidence is `.tiny-swarm/evidence/issue-218-fr02/`.

## Slice Dependency Graph

```text
FR-1 merged green main
        |
        v
Slice 01 domain contract -> ports/services -> adapters/evidence
        -> preflight/installer/CLI/composition -> tests/docs/audits
        |
        v
PR/CI/Sonar -> merge -> green main -> FR-3 workflow create
```

## S3/S3D Preflight And Locks

- Baseline/branch/worktree: verified and isolated.
- Slice metadata: one executable slice with complete owner, scope, acceptance,
  rollback, and quality fields.
- Dependency group: serial group 1 only.
- Governance lock: workflow/context, matrix/ledger, FR-2 evidence, slice
  distribution/consolidation.
- Product lock: domain contract, host ports/services/adapters, protected
  evidence repository, preflight, installer, CLI, composition.
- Documentation lock: README, installation/usage, affected arc42/ADR status.
- Test lock: all targeted FR-2 and named regression modules.
- Contract lock: `HOST-FILESYSTEM`, safe serializer, protected evidence schema,
  exact CLI flag, bootstrap import closure.
- Live-mutation lock: all Incus/Docker/Swarm/network/service commands forbidden.

No parallel write streams are safe because the domain assessment, preflight
ordering, bootstrap closure, CLI propagation, and evidence schema are one
coupled contract. Independent read-only reviews may run in parallel.

## Parallel Execution

- Can this workflow run in parallel? `No`; Slice 01 is one serial group.
- Conflicting workflows: FR-3 through FR-15 and any active workflow changing
  host/preflight/installer/CLI/composition/evidence contracts.
- Shared files: active workflow/context, Issue #218 matrix/ledger, preflight,
  installer, entrypoint, composition, host packages, tests, and arc42.
- Shared infrastructure: none is authorized; all live infrastructure is locked.
- Requires isolated worktree: `Yes`, the declared FR-2 worktree only.
- Requires serialized live validation: `Yes`; this slice records `NOT_RUN`.
- Merge-order constraints: FR-1 green baseline -> FR-2 publication -> Slice 01
  -> local gates/audits -> PR checks/Sonar -> merge/cleanup/green main -> FR-3.

Parallelization opportunities are limited to read-only requirement,
architecture, test, security/evidence, console, documentation, and completion
reviews. They may not edit or merge. Overlapping files, unclear architecture,
contradictory requirements, mandatory ordering, schema changes, generated-file
conflicts, unclear secrets/evidence handling, or weakened guards force serial
execution.

## Automatic Work Distribution Policy

Before implementation, `workflow execute` automatically records
`.codex/evidence/slice-01-distribution.md` with a safety decision and stream
map. After implementation it records
`.codex/evidence/slice-01-consolidation.md`. Real Codex subagents are used for
safe read-only specialist reviews; if unavailable, the integration owner
performs and records explicit role-based fallback reviews.

Stream map:

- backend/product: one sequential Python implementation owner;
- frontend/browser: forbidden/not applicable;
- console/status UI: read-only output and accessibility reviewer;
- tests: regression-first reviewer, no concurrent writes;
- runtime/adapters: part of the same sequential product stream;
- documentation: read-only synchronization review; integration owner writes;
- quality: independent command/evidence review after consolidation;
- architecture: read-only hexagonal/ADR reviewer;
- security/evidence: read-only path-disclosure and private-write reviewer.

Codex remains final integration owner for accepted findings, code, tests,
evidence, commits, PR state, merge readiness, cleanup, and green-main proof.
Subagents/stream workers never merge directly. No stream may write when branch,
scope, lock, schema, dependency order, secrets handling, or safety is unclear.

## Git Worktree Execution Rule

- All Slice-01 work occurs in the isolated FR-2 worktree and branch.
- Before any write, verify the local branch ref, active branch name, baseline,
  clean/understood status, remote publication head, and declared locks.
- Never implement on `main`, `master`, `develop`, or another shared branch.
- A write-capable stream would require its own isolated worktree/branch, but no
  such parallel stream is approved for this slice.
- Workers may advise or produce isolated changes only within assigned locks;
  they do not merge into the workflow branch. Codex consolidates sequentially.
- Cleanup occurs only after PR merge, remote branch deletion, ignored-evidence
  preservation, local `main` fast-forward, and full merged-main gate success.

## Documentation Synchronization

Slice 01 updates README, installation and usage guides, arc42 building-block,
runtime, deployment and quality views, plus implementation status in the two
accepted ADRs. Documentation must distinguish implemented FR-2 behavior from
still-open FR-3 through FR-15 behavior and must not claim a live install.

## Issue Completion Discipline

- Requirement matrix path:
  `.codex/evidence/issue-218/requirement-matrix.md` (141 stable IDs).
- Required evidence path: `.tiny-swarm/evidence/issue-218-fr02/`.
- Required evidence files: `requirement_matrix.md`,
  `implementation_summary.md`, `changed_files.md`, `test_results.md`,
  `remaining_risks.md`, and `acceptance_checklist.md`.
- Requirement Lead review: required after implementation and final evidence.
- System Architect Reviewer review: required for boundaries, ADR status, safe
  serializer, common guard, and no later-FR drift.
- Test / Evidence Reviewer review: required for RED/green, stop order,
  path-redaction, private atomic evidence, regressions, and quality commands.
- Issue Completion Auditor review: independent publication decision required;
  the implementer is not sole DONE authority.
- DONE blocking rule: any open, unmapped, or unverified requirement, missing
  evidence file, red/unverifiable quality or external check, unknown merge or
  cleanup state forces `INCOMPLETE`, `BLOCKED`, or `FAILED`; it cannot be DONE.

During execution, update but never delete/renumber matrix rows. FR-2 is not
`DONE` until CI/Sonar, merge, cleanup, and green merged `main` pass.

## Stop Conditions

Stop and report if:

- mount facts under WSL2 cannot be classified safely and code would fail open;
- owner-only atomic evidence cannot be enforced;
- an absolute project path would escape the protected local document;
- any live setup path bypasses the common filesystem guard;
- any later action runs after a filesystem `BLOCKED` result;
- implementation requires automatic repository move/copy;
- a new architecture decision is required;
- `python -S` imports third-party dependencies;
- work exceeds affected files/locks or overlaps unrelated user changes;
- live infrastructure would be required;
- a requirement, test, quality, CI, Sonar, merge, or cleanup gate is red or
  unverifiable.

## Commit, Push, PR, And Rollback Plan

1. Publish workflow creation as guarded documentation/governance commits and
   push the branch without opening or merging a PR.
2. Execute Slice 01 regression-first in the same isolated branch/worktree.
3. Create exactly one Slice-01 implementation commit. Typed CI remediation may
   use a separate focused repair commit without rewriting pushed history.
4. Push, create/reuse the FR-2 PR, wait for Python 3.12 and SonarCloud, and
   merge only with exact-head success and clean mergeability.
5. Fast-forward local `main`, rerun the full gate, preserve ignored issue
   evidence, delete remote/local branch and worktree, then begin FR-3.
6. Roll back with a normal revert; never force-push or reset destructively.

## Definition of Done

- FR-2-owned matrix rows are VERIFIED and no mapped requirement is open.
- `HOST-FILESYSTEM` is typed, ordered second, path-free in general evidence,
  and fail-closed for unknown/Windows-mounted WSL paths.
- Override use is explicit, narrow, privately evidenced, and cannot bypass
  other safety gates.
- Native Linux/WSL-native regressions pass; no live mutation ran.
- Documentation and accepted ADR implementation status are synchronized.
- Independent architecture, test/evidence, security/evidence, console, final
  Three Amigos, and completion-auditor reviews pass.
- Targeted and full local gates, GitHub Python 3.12, SonarCloud, mergeability,
  merge, cleanup, and merged-main full gate pass.

## Handoff to workflow execute

After the guarded workflow-create publication is verified, exact
`workflow execute` resumes this workflow at Slice 01. It must not call
`workflow create` backwards. Product writes remain prohibited until the
publication commit and remote ref are verified.

## Execution Checkpoint

- Current phase: completed.
- Product implementation: merged through PR #221 as
  `2ce2202929e1d10ccdd648cf20d027d941ed8007`.
- GitHub Python Quality and SonarCloud: `PASS`.
- Merged-main full quality gate: `PASS`, 1,495 tests with 28 expected skips.
- Remote and local workflow branches plus the isolated worktree: removed.
- Ignored FR-2 issue evidence: preserved in the primary worktree.
- Live infrastructure: `NOT_RUN` and forbidden.
- Next allowed action: begin FR-3 only through its separate workflow.

## arc42 Check Status

- Existing WSL2 host boundary and autonomous setup safety ADRs cover FR-2.
- Building-block, runtime, deployment, quality, installation, usage, and README
  updates are required in Slice 01.
- No documentation claims FR-2 implemented before the slice verifies it.
