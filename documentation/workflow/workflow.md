# Workflow: Remove Legacy Netplan Repository

Version: `workflow-remove-netplan-repository-v1.0.0`
Workflow ID: `workflow-remove-netplan-repository-20260627`
Created: `2026-06-27`
Branch: `feature/workflow-remove-netplan-repository-20260627`
Status: `CREATED_READY_FOR_EXECUTION`
Evidence Root: `.codex/evidence/workflow-remove-netplan-repository-20260627/`

## Executive Summary

Remove the unused legacy Netplan YAML repository adapter and its dedicated tests
from the current product path. The repository no longer supports committed
Netplan helper templates as product behavior; current networking is LXC-native
through LXD or Incus with Docker Swarm. The workflow must remove only the
obsolete adapter surface and synchronized references, while preserving safety
guards that still mention `netplan` as a live infrastructure command.

## Requirement Clarification Gate

Original Request:

- Create a branch.
- Run `workflow create`.
- Cleanly remove `netplant_repository` / `netplan_repository.py`.

Interpreted Intent:

- Author an executable workflow that removes
  `src/tiny_swarm_world/infrastructure/adapters/repositories/netplan_repository.py`,
  deletes tests that exist only for that adapter, and updates documentation that
  lists the adapter or generated Netplan file as an active owned surface.

Change Type:

- Product code cleanup, test cleanup, and documentation synchronization.

Affected Process Strand:

- `workflow create`, followed by a later `workflow execute`.

Affected Architecture Area:

- Infrastructure repository adapters.
- Platform provisioning legacy networking surface.
- Documentation references to removed Netplan repository behavior.

Explicit Requirements:

- Use a dedicated workflow branch.
- Preserve Tiny Swarm World Linux/WSL-only, LXC-native, Docker Swarm-first
  operating model.
- Do not run live Netplan, LXD, Incus, LXC, Docker Swarm, compose, socat, or
  service bootstrap commands.
- Remove the adapter cleanly rather than leaving unused tests or active
  documentation claims.

Implicit Requirements:

- Preserve hexagonal architecture boundaries.
- Do not remove safety references that treat `netplan` as a dangerous live
  command.
- Do not remove unrelated domain concepts that sanitize or model command text.
- Do not reintroduce Multipass, Java, Maven, Spring Boot, Kubernetes-first
  assumptions, or React frontend scope.

Assumptions:

- The adapter is unused because repository search found no production
  instantiation or composition registration for `PortNetplanRepositoryYaml`.
- Dedicated tests for the adapter can be deleted with the adapter.
- Historical or safety documentation can keep generic `netplan` mentions when
  they describe prohibited live operations rather than supported repository
  behavior.

Non-Goals:

- No live infrastructure changes.
- No provider networking migration.
- No removal of general `netplan` safety guards from sanitizers, inventory
  tests, readiness docs, ADRs, or AGENTS instructions.
- No push, pull request, merge, or branch cleanup unless requested separately.

Risks:

- Documentation may still list the removed adapter as an owned surface.
- Broad text removal of `netplan` could weaken live-command safety controls.
- Existing uncommitted changes in the adapter and adapter tests must not be
  overwritten accidentally during execution.

Open Questions:

- None blocking for workflow creation.

Blocking Questions:

- None.

Confidence Level:

- 92 percent.

Decision:

- `READY_FOR_WORKFLOW`

## Five-Role Review

Senior Requirement Engineer:

- The requirement is bounded to removing an unused legacy repository adapter and
  its adapter-specific test coverage.

Senior System Architect:

- The removal aligns with the documented LXC-native product direction and the
  statement that Netplan helper templates are outside the supported product
  path. Safety references to live `netplan` commands must remain.

Senior Python Automation Developer:

- No replacement adapter is needed unless `workflow execute` discovers an active
  production import. Removal should prefer direct file deletion and import
  cleanup over deprecation scaffolding.

Senior React Frontend Developer:

- No browser or React frontend surface exists for this workflow.

Senior Tester:

- Verification must prove there are no remaining imports of the deleted adapter
  and that the Python test suite still passes without adapter-specific tests.

## Target Picture

Verified baseline:

- Active branch:
  `feature/workflow-remove-netplan-repository-20260627`.
- Current search shows `PortNetplanRepositoryYaml` referenced only by
  `tests/infrastructure/adapters/repositories/test_netplan_repository.py` and
  the adapter file itself.
- `documentation/system/network.adoc` states that Netplan helper templates for
  legacy VM networking have been removed from the supported product path.

Target outcome:

- `netplan_repository.py` is removed.
- `test_netplan_repository.py` is removed.
- Active ownership documentation no longer lists the removed adapter or
  generated Netplan repository file as current product surfaces.
- General live-operation safety references to `netplan` remain intact.
- Quality gates pass or failures are classified with evidence.

## Scope

In scope:

- `src/tiny_swarm_world/infrastructure/adapters/repositories/netplan_repository.py`
- `tests/infrastructure/adapters/repositories/test_netplan_repository.py`
- `documentation/architecture/responsibility-separation-analysis.md`
- `documentation/configuration/config-contract-inventory.md`
- `documentation/workflow/workflow.md`
- `documentation/workflow/context-pack.md`
- `documentation/workflow/context-pack.json`
- `.codex/evidence/workflow-remove-netplan-repository-20260627/**`

Out of scope:

- Domain sanitizers and tests that mention `netplan` as unsafe command text.
- AGENTS, ADR, arc42, EPIC, README, and user-guide references that describe
  live-command safety or historical architecture unless they falsely claim the
  adapter remains active.
- Any live infrastructure command.
- Push, PR creation, merge, or branch cleanup.

Architecture constraints:

- Preserve hexagonal dependency direction.
- Do not move infrastructure construction into application services.
- Do not add new provider abstractions for removed Netplan behavior.
- Keep documentation aligned with Linux/WSL-only, LXC-native, Docker Swarm-first
  product scope.

## Python Automation Assessment

The change removes an unused infrastructure adapter and adapter-only tests.
`workflow execute` must first run a fresh reference search. If an active
production import appears, execution must stop and reassess ownership instead of
blindly deleting the file.

## Frontend Assessment

No frontend or console UI behavior changes are expected. Console/status UI
skills are not needed unless execution discovers user-facing command output tied
to this adapter.

## Test Strategy

Targeted verification:

- `rg -n "PortNetplanRepositoryYaml|netplan_repository|GENERATED_NETPLAN_PATH|DEFAULT_NAMESERVERS" src tests documentation infra README.md AGENTS.md QUALITY.md -g '!**/__pycache__/**'`
- `python3 tools/quality_gate.py test`
- `git diff --check`

Required final verification:

- `python3 tools/quality_gate.py quality`

If the full quality gate is impractical, `workflow execute` must record the
reason and at least run `test`, `arch-tests`, and `git diff --check`.

## Resilience Requirements

- Deletion must be idempotent when rerun after partial cleanup.
- Verification must not execute live provider, networking, Docker Swarm, compose,
  socat, or service bootstrap commands.
- If stale references remain, classify them as active, historical, or safety
  references before editing.

## Ordered Slices

### Slice 01 - Reference Audit And Execution Evidence

Purpose:

- Reconfirm that the Netplan repository adapter has no active product consumers
  before deletion and record distribution evidence.

Prerequisites:

- Active branch is `feature/workflow-remove-netplan-repository-20260627`.
- Working tree changes are understood and task-scoped.

```yaml
slice_id: "01"
profile: "NORMAL_PATH"
owner: "Senior System Architect"
secondary_reviewers:
  - "Senior Python Automation Developer"
  - "Senior Tester"
affected_files:
  - ".codex/evidence/workflow-remove-netplan-repository-20260627/slice-01-distribution.md"
  - ".codex/evidence/workflow-remove-netplan-repository-20260627/slice-01-consolidation.md"
affected_modules:
  - "tiny_swarm_world.infrastructure.adapters.repositories"
affected_contracts:
  - "legacy Netplan repository ownership"
dependencies: []
parallel_group: "serial-cleanup"
file_locks:
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/netplan_repository.py"
  - "tests/infrastructure/adapters/repositories/test_netplan_repository.py"
  - "documentation/**"
  - ".codex/evidence/workflow-remove-netplan-repository-20260627/**"
contract_locks:
  - "No supported Netplan repository product path"
architecture_locks:
  - "Infrastructure adapter removal only; no domain/application dependency changes"
quality_gates:
  targeted:
    - "rg -n \"PortNetplanRepositoryYaml|netplan_repository|GENERATED_NETPLAN_PATH|DEFAULT_NAMESERVERS\" src tests documentation infra README.md AGENTS.md QUALITY.md -g '!**/__pycache__/**'"
  required: []
documentation:
  arc42: "Checked; no arc42 change expected unless active architecture text claims the adapter is current."
  adr: "Checked; no ADR change expected because accepted ADRs already treat netplan as live-command safety surface."
stop_conditions:
  - "Stop if production code imports or instantiates PortNetplanRepositoryYaml."
  - "Stop if deletion would remove a safety guard for live netplan commands."
  - "Stop if uncommitted unrelated changes appear."
```

Done criteria:

- Reference audit classifies remaining `netplan` mentions.
- Evidence explains why deletion is safe or why execution stopped.

### Slice 02 - Remove Adapter And Adapter Tests

Purpose:

- Delete the unused Netplan repository adapter and tests that exist only to
  exercise that adapter.

Prerequisites:

- Slice 01 completed without active production consumers.

```yaml
slice_id: "02"
profile: "NORMAL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Tester"
  - "Senior System Architect"
affected_files:
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/netplan_repository.py"
  - "tests/infrastructure/adapters/repositories/test_netplan_repository.py"
  - ".codex/evidence/workflow-remove-netplan-repository-20260627/slice-02-distribution.md"
  - ".codex/evidence/workflow-remove-netplan-repository-20260627/slice-02-consolidation.md"
affected_modules:
  - "tiny_swarm_world.infrastructure.adapters.repositories"
  - "tests.infrastructure.adapters.repositories"
affected_contracts:
  - "infrastructure repository adapter inventory"
dependencies:
  - "01"
parallel_group: "serial-cleanup"
file_locks:
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/netplan_repository.py"
  - "tests/infrastructure/adapters/repositories/test_netplan_repository.py"
contract_locks:
  - "Adapter removal must not change live-operation safety rules"
architecture_locks:
  - "No replacement infrastructure adapter unless active consumer is found"
quality_gates:
  targeted:
    - "python3 tools/quality_gate.py test"
  required: []
documentation:
  arc42: "No direct arc42 update expected."
  adr: "No ADR required unless execution discovers a supported behavior change."
stop_conditions:
  - "Stop if imports fail because another product path depends on the removed adapter."
  - "Stop if tests reveal hidden behavior dependency on generated Netplan YAML."
  - "Stop if deletion requires live infrastructure validation."
```

Done criteria:

- Adapter file is deleted.
- Adapter-only test file is deleted.
- Test gate either passes or failure is classified with exact output.

### Slice 03 - Documentation Sync And Quality Gate

Purpose:

- Remove active documentation references to the deleted adapter and run final
  verification.

Prerequisites:

- Slice 02 completed or stopped with a documented reason.

```yaml
slice_id: "03"
profile: "NORMAL_PATH"
owner: "Senior Documentation Engineer"
secondary_reviewers:
  - "Senior Tester"
  - "Senior System Architect"
affected_files:
  - "documentation/architecture/responsibility-separation-analysis.md"
  - "documentation/configuration/config-contract-inventory.md"
  - "documentation/workflow/workflow.md"
  - "documentation/workflow/context-pack.md"
  - "documentation/workflow/context-pack.json"
  - ".codex/evidence/workflow-remove-netplan-repository-20260627/slice-03-distribution.md"
  - ".codex/evidence/workflow-remove-netplan-repository-20260627/slice-03-consolidation.md"
affected_modules:
  - "documentation"
affected_contracts:
  - "architecture documentation active surface inventory"
dependencies:
  - "02"
parallel_group: "serial-cleanup"
file_locks:
  - "documentation/architecture/responsibility-separation-analysis.md"
  - "documentation/configuration/config-contract-inventory.md"
  - "documentation/workflow/**"
  - ".codex/evidence/workflow-remove-netplan-repository-20260627/**"
contract_locks:
  - "Documentation must distinguish removed active behavior from retained safety references"
architecture_locks:
  - "No architecture decision change unless a supported behavior change is discovered"
quality_gates:
  targeted:
    - "rg -n \"PortNetplanRepositoryYaml|netplan_repository|GENERATED_NETPLAN_PATH|DEFAULT_NAMESERVERS\" src tests documentation infra README.md AGENTS.md QUALITY.md -g '!**/__pycache__/**'"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "Checked during workflow creation; update only if execution discovers stale current-behavior claims."
  adr: "No ADR expected; removal follows existing product direction."
stop_conditions:
  - "Stop if documentation conflict requires a new ADR."
  - "Stop if quality-gate authority is unclear."
  - "Stop if full quality gate fails for reasons outside this workflow."
```

Done criteria:

- Active docs no longer list the deleted adapter as current product surface.
- Safety references to `netplan` remain where they prevent live operations.
- Final verification evidence is recorded.

## Slice Dependency Graph

```text
01 Reference Audit
  -> 02 Remove Adapter And Tests
    -> 03 Documentation Sync And Quality Gate
```

## Parallel Execution

- Can this workflow run in parallel? No write-capable parallel execution.
- Conflicting workflows: any workflow touching repository adapters,
  `documentation/workflow/**`, or platform provisioning documentation.
- Shared files: `documentation/workflow/**`,
  `documentation/architecture/responsibility-separation-analysis.md`, and
  `documentation/configuration/config-contract-inventory.md`.
- Shared infrastructure: none; no live infrastructure may be used.
- Requires isolated worktree: yes for any concurrent workflow execution.
- Requires serialized live validation: live validation is forbidden.
- Merge-order constraints: execute slices in order 01, 02, 03.

## Automatic Work Distribution Policy

`workflow execute` must automatically inspect each slice for safe specialist
stream decomposition. Real Codex subagents may be used where supported. If
subagents are unavailable, execute the same checks through explicit role-based
fallback in the main thread and record that fallback in evidence.

Required evidence before implementation:

- `.codex/evidence/workflow-remove-netplan-repository-20260627/slice-<number>-distribution.md`

Required evidence after implemented slices:

- `.codex/evidence/workflow-remove-netplan-repository-20260627/slice-<number>-consolidation.md`

Stream map:

- Backend/Python: Slice 02.
- Frontend/React: not applicable.
- Tests: Slices 02 and 03.
- Runtime/DevOps: safety review only; no live commands.
- Documentation: Slice 03.
- Quality: Slice 03.
- Architecture: Slices 01 and 03.
- Security: ensure safety command sanitizers are not weakened.

Non-parallelization rules:

- Do not parallelize overlapping file edits.
- Do not parallelize unclear architecture ownership.
- Do not parallelize contradictory requirements.
- Do not parallelize mandatory ordered deletion and documentation sync.
- Do not parallelize generated-file conflict resolution.
- Do not parallelize if Three Amigos marks the slice not safely
  parallelizable.
- Do not proceed with unclear secrets handling or weakened safety guards.

Codex remains the final integration owner for consolidation, tests, evidence,
PR readiness, and merge readiness.

## Git Worktree Execution Rule

Execute this workflow only from branch
`feature/workflow-remove-netplan-repository-20260627` or from an isolated
worktree branch explicitly derived for this workflow. Subagents or stream
workers must verify the active branch before writing files and must not merge
directly. Codex consolidates accepted changes after evidence and tests pass.

## Role Ownership Map

- Senior Workflow Architect: workflow structure, dependency ordering, execution
  policy.
- Senior Requirement Engineer: requirement drift and non-goal enforcement.
- Senior System Architect: architecture and ADR/arc42 consistency.
- Senior Python Automation Developer: adapter deletion and import cleanup.
- Senior Documentation Engineer: documentation synchronization.
- Senior Tester: targeted and final verification.
- Senior React Frontend Developer: confirms no frontend scope.
- Senior DevOps Engineer: confirms no live infrastructure execution.

## Quality-Gate Expectations

From `QUALITY.md`:

- Preferred full gate: `python3 tools/quality_gate.py quality`
- Targeted gates during development:
  - `python3 tools/quality_gate.py test`
  - `git diff --check`

The full gate is required for final readiness because the workflow changes
Python source, tests, repository adapters, and documentation.

## Documentation Synchronization Points

- Update active adapter ownership references after deletion.
- Keep historical ADR and safety references unless they claim supported Netplan
  repository behavior.
- Do not update `documentation/system/network.adoc` unless execution discovers a
  stale current-behavior claim; it already states Netplan helper templates are
  outside the supported product path.

## Stop Conditions

Stop and report if:

- Git repository context or active branch cannot be verified.
- Unrelated uncommitted changes appear.
- Production code imports the adapter.
- Removing documentation would weaken live-command safety guidance.
- An ADR is needed before removing supported behavior.
- A quality gate fails for an unrelated reason that cannot be isolated.
- Any step would require live LXD, Incus, LXC, Docker Swarm, compose, netplan,
  socat, or service bootstrap commands.

## Uncertainty Escalation Rules

- If a remaining reference is ambiguous, classify it with Senior System
  Architect and Senior Requirement Engineer perspectives before editing.
- If documentation says Netplan behavior is both removed and current, stop for
  Root Architect decision.
- If test failures suggest hidden runtime behavior, stop and reassess deletion
  scope.

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
- Removal scope, non-goals, safety controls, quality gates, and stop conditions
  are explicit.
- arc42 status is checked and documented.
- Handoff to `workflow execute` is clear.

## Handoff To Workflow Execute

Run `workflow execute` only after confirming:

- active branch:
  `feature/workflow-remove-netplan-repository-20260627`
- workflow status: `CREATED_READY_FOR_EXECUTION`
- context pack hashes are current
- existing adapter/test modifications are still task-scoped and understood

## arc42 Check Status

- `documentation/arc42/**` was checked for Netplan references during workflow
  creation.
- No immediate arc42 edit is required because current arc42 references describe
  live-command safety, historical architecture decisions, or broad context.
- `workflow execute` must update arc42 only if it finds current-behavior text
  that claims the removed adapter remains supported.
