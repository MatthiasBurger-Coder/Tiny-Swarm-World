# Workflow: Validate Docker Swarm stack definitions

```yaml
workflow_id: issue-4-swarm-stack-validation-20260614
workflow_version: 1.0.0
issue: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/4
issue_number: 4
authoring_branch: feature/workflow-index-open-issues-20260614
proposed_execution_branch: feature/workflow-issue-4-swarm-stack-validation-20260614
indexed_workflow: true
active_workflow: false
execution_profile: NORMAL_PATH
released_for_workflow_execute: false
created_utc: "2026-06-14T00:00:00Z"
decision: PROCEED_WITH_ACCEPTED_ASSUMPTIONS
confidence: 75
dependencies: []
```

## Executive Summary

Validate compose files as Docker Swarm stack definitions and fail when stack-only requirements such as deploy sections are missing.

This indexed workflow is authored for later promotion or explicit indexed
execution. It does not replace `documentation/workflow/workflow.md`.

## Requirement Clarification Gate

Original request:

- Create workflows for all open GitHub issues except Issue #5 and Issue #7.
- Use `workflow.index.md` so multiple `workflow.md` files do not overwrite
  each other.
- Use subagents for workflow creation analysis.

Interpreted intent:

- Create an executable workflow plan for Issue #4: Validate Docker Swarm stack definitions.
- Defer implementation until all indexed workflows are authored and the
  execution order is selected from `workflow.index.md`.

Change type:

- Workflow creation for future deployment configuration validation work.

Affected process strand:

- deployment configuration validation.
- Workflow execution with S3/S3D validation.
- Documentation and quality-gate synchronization.

Affected architecture area:

- `infra/config/compose/**`
- `src/tiny_swarm_world/domain/deployment/**`
- `src/tiny_swarm_world/application/services/deployment/**`
- `tests/**`
- `documentation/**`

Explicit requirements:

- Address the linked GitHub issue acceptance criteria.
- Preserve hexagonal architecture and Linux/WSL-only assumptions.
- Keep live infrastructure commands mocked or static unless explicitly
  approved.
- Add or update tests for changed product behavior.
- Update relevant documentation when behavior or operator workflow changes.

Implicit requirements:

- Keep domain independent from infrastructure adapters and side effects.
- Keep application services dependent on ports rather than concrete adapters.
- Keep concrete adapter construction in infrastructure composition.
- Preserve deterministic, redacted, host-neutral evidence.

Assumptions:

- Subagent analysis classified this issue as workflow-authoring-ready.
- Slice-local product decisions must be resolved from repository evidence
  before implementation.

Non-goals:

- No live LXD, Incus, LXC, Docker, Swarm, Portainer, Nexus, Jenkins,
  RabbitMQ, SonarQube, networking, or socat mutation during normal
  verification.
- No Java, Maven, Spring Boot, browser React, Kubernetes-first, Multipass,
  or Windows-native behavior.
- No committed secrets, host-specific absolute paths, local runtime env
  files, generated evidence, logs, caches, or IDE state.

Risks:

- Shared files may overlap with other indexed workflows; execution must use
  the dependency order and S3D lock checks from the index.
- Quality-gate failures block commit and push until classified and fixed
  inside the active workflow scope.

Open questions:

- Resolve slice-local design choices from repository evidence before code
  changes.

Blocking questions:

- None for workflow authoring. Any issue-specific decision is represented
  as an early executable decision slice when required.

Confidence level: 75 percent.

Decision: `PROCEED_WITH_ACCEPTED_ASSUMPTIONS`.

## Target Picture

Issue #4 has an executable, test-backed implementation path that
preserves Linux/WSL-only operation, Python 3.12 compatibility, hexagonal
boundaries, and guarded live-infrastructure safety.

## Verified Baseline

- Root `AGENTS.md`, `QUALITY.md`, and `.agents/skills/workflow-authoring/SKILL.md`
  were checked during indexed workflow authoring.
- The workflow is stored under `documentation/workflow/issues/issue-4/`.
- This workflow is not the active workflow until explicitly promoted or
  selected by an indexed executor.

## Scope

In scope:

- Files and modules listed in the affected architecture area.
- Tests and documentation needed to satisfy Issue #4.
- Quality gates from `QUALITY.md`.

Out of scope:

- Live infrastructure execution.
- Java, Maven, Spring Boot, browser React, Kubernetes-first, Multipass, or
  Windows-native behavior.
- Secret, local evidence, cache, or IDE-state commits.

## Architecture Constraints

- Domain code must not import infrastructure, YAML parsers, command runners,
  Docker/LXC clients, logging setup, file managers, or composition.
- Application services orchestrate ports and domain types only.
- Infrastructure adapters own filesystem, YAML, HTTP, shell, Docker, LXC,
  and composition details.
- `src/tiny_swarm_world/infrastructure/composition.py` remains the standard
  wiring boundary unless this issue explicitly and safely refactors its
  internal modules.

## Python Automation Assessment

This is Python automation work. Keep Python 3.12 compatibility, typed value
objects where useful, deterministic unit tests, and mocked external command
or network behavior.

## Frontend Assessment

No browser or React frontend work is authorized. Console/status UI work, if
any, remains terminal-oriented and routes through console/status UI skills.

## Test Strategy

- Run focused unit or architecture tests for changed files first.
- Run `python3 tools/quality_gate.py quality` before merge when practical.
- Do not execute live infrastructure commands in tests.
- Mock command execution, LXC/Incus/LXD, Docker, Swarm, Portainer, and
  network calls unless a later explicit live-validation approval exists.

## Resilience Requirements

- Fail closed before mutation when configuration, consent, runtime state, or
  ownership is ambiguous.
- Report blockers with target, expected state, observed state, and next
  action when applicable.
- Preserve deterministic, redacted evidence and diagnostics.

## Ordered Slices

### Slice 01: Requirement, repository baseline, and decision gate

Purpose:

- Requirement, repository baseline, and decision gate for Issue #4.

```yaml
slice_id: S01
profile: NORMAL_PATH
owner: Senior Requirement Engineer
secondary_reviewers:
  - Senior System Architect
  - Senior Tester
affected_files:
  - documentation/workflow/issues/issue-4/**
  - infra/config/compose/**
  - src/tiny_swarm_world/domain/deployment/**
affected_modules:
  - deployment configuration validation
affected_contracts:
  - issue_4_swarm_stack_validation
dependencies:
  []
parallel_group: issue-4-group-1
file_locks:
  - documentation/workflow/issues/issue-4/**
  - infra/config/compose/**
  - src/tiny_swarm_world/domain/deployment/**
contract_locks:
  - issue_4_swarm_stack_validation
architecture_locks:
  - hexagonal_architecture
  - linux_wsl_only_runtime
quality_gates:
  targeted:
- git diff --check
- python3 tools/quality_gate.py test
  required:
- python3 tools/quality_gate.py quality
documentation:
  arc42: checked-update-if-behavior-or-boundary-changes
  adr: checked-update-if-policy-or-architecture-decision-changes
stop_conditions:
  - Repository evidence contradicts the selected implementation direction.
  - A slice requires live infrastructure mutation without explicit approval.
  - The change would violate hexagonal architecture or Linux/WSL-only scope.
```

Done criteria:

- The slice is complete inside the declared file locks.
- Targeted checks cover the accepted behavior.
- No live infrastructure command is executed by default verification.

Verification commands:

```bash
git diff --check
python3 tools/quality_gate.py test
```

### Slice 02: Scoped implementation inside the declared architecture boundary

Purpose:

- Scoped implementation inside the declared architecture boundary for Issue #4.

```yaml
slice_id: S02
profile: NORMAL_PATH
owner: Senior Python Automation Developer
secondary_reviewers:
  - Senior System Architect
  - Senior Tester
affected_files:
  - infra/config/compose/**
  - src/tiny_swarm_world/domain/deployment/**
  - src/tiny_swarm_world/application/services/deployment/**
  - tests/**
  - documentation/**
affected_modules:
  - deployment configuration validation
affected_contracts:
  - issue_4_swarm_stack_validation
dependencies:
  - S01
parallel_group: issue-4-group-2
file_locks:
  - infra/config/compose/**
  - src/tiny_swarm_world/domain/deployment/**
  - src/tiny_swarm_world/application/services/deployment/**
  - tests/**
  - documentation/**
contract_locks:
  - issue_4_swarm_stack_validation
architecture_locks:
  - hexagonal_architecture
  - linux_wsl_only_runtime
quality_gates:
  targeted:
- git diff --check
- python3 tools/quality_gate.py test
  required:
- python3 tools/quality_gate.py quality
documentation:
  arc42: checked-update-if-behavior-or-boundary-changes
  adr: checked-update-if-policy-or-architecture-decision-changes
stop_conditions:
  - Repository evidence contradicts the selected implementation direction.
  - A slice requires live infrastructure mutation without explicit approval.
  - The change would violate hexagonal architecture or Linux/WSL-only scope.
```

Done criteria:

- The slice is complete inside the declared file locks.
- Targeted checks cover the accepted behavior.
- No live infrastructure command is executed by default verification.

Verification commands:

```bash
git diff --check
python3 tools/quality_gate.py test
```

### Slice 03: Focused regression and architecture tests

Purpose:

- Focused regression and architecture tests for Issue #4.

```yaml
slice_id: S03
profile: NORMAL_PATH
owner: Senior Tester
secondary_reviewers:
  - Senior System Architect
  - Senior Tester
affected_files:
  - tests/**
  - infra/config/compose/**
  - src/tiny_swarm_world/domain/deployment/**
affected_modules:
  - deployment configuration validation
affected_contracts:
  - issue_4_swarm_stack_validation
dependencies:
  - S02
parallel_group: issue-4-group-3
file_locks:
  - tests/**
  - infra/config/compose/**
  - src/tiny_swarm_world/domain/deployment/**
contract_locks:
  - issue_4_swarm_stack_validation
architecture_locks:
  - hexagonal_architecture
  - linux_wsl_only_runtime
quality_gates:
  targeted:
- git diff --check
- python3 tools/quality_gate.py test
  required:
- python3 tools/quality_gate.py quality
documentation:
  arc42: checked-update-if-behavior-or-boundary-changes
  adr: checked-update-if-policy-or-architecture-decision-changes
stop_conditions:
  - Repository evidence contradicts the selected implementation direction.
  - A slice requires live infrastructure mutation without explicit approval.
  - The change would violate hexagonal architecture or Linux/WSL-only scope.
```

Done criteria:

- The slice is complete inside the declared file locks.
- Targeted checks cover the accepted behavior.
- No live infrastructure command is executed by default verification.

Verification commands:

```bash
git diff --check
python3 tools/quality_gate.py test
```

### Slice 04: Documentation synchronization and final quality evidence

Purpose:

- Documentation synchronization and final quality evidence for Issue #4.

```yaml
slice_id: S04
profile: NORMAL_PATH
owner: Senior Documentation Engineer
secondary_reviewers:
  - Senior System Architect
  - Senior Tester
affected_files:
  - documentation/**
  - README.md
affected_modules:
  - deployment configuration validation
affected_contracts:
  - issue_4_swarm_stack_validation
dependencies:
  - S03
parallel_group: issue-4-group-4
file_locks:
  - documentation/**
  - README.md
contract_locks:
  - issue_4_swarm_stack_validation
architecture_locks:
  - hexagonal_architecture
  - linux_wsl_only_runtime
quality_gates:
  targeted:
- git diff --check
- python3 tools/quality_gate.py test
  required:
- python3 tools/quality_gate.py quality
documentation:
  arc42: checked-update-if-behavior-or-boundary-changes
  adr: checked-update-if-policy-or-architecture-decision-changes
stop_conditions:
  - Repository evidence contradicts the selected implementation direction.
  - A slice requires live infrastructure mutation without explicit approval.
  - The change would violate hexagonal architecture or Linux/WSL-only scope.
```

Done criteria:

- The slice is complete inside the declared file locks.
- Targeted checks cover the accepted behavior.
- No live infrastructure command is executed by default verification.

Verification commands:

```bash
git diff --check
python3 tools/quality_gate.py test
```

## Slice Dependency Graph

```text
S01 -> S02 -> S03 -> S04
```

Cross-workflow dependencies: none.

## Parallel Execution

- Can this workflow run in parallel? Only after S3D confirms disjoint file,
  contract, module, and architecture locks.
- Conflicting workflows: see `documentation/workflow/workflow.index.md`.
- Shared files: infra/config/compose/**, src/tiny_swarm_world/domain/deployment/**, src/tiny_swarm_world/application/services/deployment/**, tests/**, documentation/**.
- Shared infrastructure: none for default verification; live validation is
  serialized unless isolated infrastructure is explicitly provided.
- Requires isolated worktree: yes for workflow execution streams.
- Requires serialized live validation: yes.
- Merge-order constraints: honor cross-workflow dependencies and slice order.

## Automatic Work Distribution Policy

During `workflow execute`, Codex must inspect each slice for safe specialist
stream decomposition. Real Codex subagents should be used where supported;
otherwise explicit role-based fallback review must be recorded in evidence.
For every slice, create `.codex/evidence/slice-<number>-distribution.md`
before implementation and `.codex/evidence/slice-<number>-consolidation.md`
after implementation. Codex remains final integration owner.

Stream map: backend, frontend, tests, runtime, documentation, quality,
architecture, security. Do not split work when files overlap, architecture
is unclear, requirements contradict, ordering is mandatory, generated files
may conflict, secrets handling is unclear, or safety guards would be
weakened.

## Git Worktree Execution Rule

Parallel execution must use isolated Git worktrees. Stream branch names must
follow:

```text
<workflow-branch>-slice-<number>-<stream>
```

Subagents or stream workers must not merge directly to the integration
branch. Codex consolidates accepted changes after tests and evidence pass.

## Role And Ownership Map

- Senior Workflow Architect: dependency order and workflow handoff.
- Senior Requirement Engineer: issue acceptance traceability.
- Senior System Architect: hexagonal boundaries and architecture decisions.
- Senior Python Automation Developer: Python implementation slices.
- Senior React Frontend Developer: no-impact check for browser/React scope.
- Senior Tester: regression and quality evidence.
- Senior Documentation Engineer: documentation synchronization.

## Quality-Gate Expectations

Workflow authoring:

```bash
git diff --check
```

Workflow execution:

```bash
python3 tools/quality_gate.py test
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py quality
```

## Documentation Synchronization Points

- Update README or user guide when operator behavior changes.
- Update `documentation/arc42/**` when boundaries, runtime view, quality
  attributes, or building blocks change.
- Add or update ADRs only when a slice creates architecture-significant
  policy or ownership decisions.

## Stop Conditions

Stop and report when repository evidence contradicts this workflow, when
live infrastructure would be required without approval, when architecture
boundaries are unclear, when quality gates fail without a safe scoped fix,
or when acceptance criteria cannot be mapped to tests and documentation.

## Uncertainty Escalation Rules

- Architecture ambiguity: Root Architect and Senior System Architect.
- Requirement ambiguity: Senior Requirement Engineer.
- Quality failure: Senior Tester and Quality Gate Orchestrator.
- Security or secret handling: security and configuration owners.
- Documentation mismatch: Senior Documentation Engineer.

## Commit And Push Plan

Workflow authoring commit:

- Branch: `feature/workflow-index-open-issues-20260614`.
- Stage this issue workflow, its context pack, `workflow.index.md`, and the
  workflow-authoring skill update.
- Run `git diff --check`.
- Push the authoring branch after all indexed workflows are created.

Future workflow execution:

- Promote or explicitly select this indexed workflow.
- Use proposed execution branch `feature/workflow-issue-4-swarm-stack-validation-20260614` unless a later
  governance decision selects another branch.
- Commit each executable slice separately.

## Definition Of Done

Workflow authoring is done when this file, its context pack, and the index
entry exist and pass documentation checks.

Issue #4 implementation is done when acceptance criteria are satisfied
by scoped code, tests, documentation, quality evidence, and merge-ready
review.

## Handoff To Workflow Execute

Do not run unqualified `workflow execute` for this indexed workflow. First
promote it to `documentation/workflow/workflow.md` or extend the executor to
accept an explicit indexed workflow path.

## arc42 Check Status

- arc42 impact: checked during workflow authoring; update during execution
  if behavior, boundaries, runtime view, or quality requirements change.
- ADR impact: checked during workflow authoring; add or update ADR only for
  architecture-significant decisions.
