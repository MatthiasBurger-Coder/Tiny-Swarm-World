---
name: workflow-executor
description: Use when the user writes workflow execute or asks to execute the active project workflow through the configured subagent workflow with slice sequencing, specialist reviews, quality gates, git diff review, and commit restrictions.
---

# Workflow Executor Skill

## Purpose

Execute repository workflows through the configured subagent-based workflow while preserving `AGENTS.md`, `QUALITY.md`, architecture boundaries, evidence integrity, and commit restrictions.

## Resolution Rule

This file is the active workflow executor for Tiny Swarm World.

- `.agents/skills/workflow-executor/SKILL.md` is the project-specific execution protocol.
- `.codex/skills/workflow-executor/SKILL.md` is the reusable base protocol.
- During Tiny Swarm World `workflow execute`, use this `.agents` file as the active executor.
- Read the `.codex` base only for reusable baseline context or conflict detection, not as a second full execution protocol.
- If this rule conflicts with root `AGENTS.md`, root `AGENTS.md` wins and the conflict must be reported.

## Trigger

Use this skill whenever the user writes:

```text
workflow execute
```

or otherwise asks Codex to execute the active workflow through the configured subagent workflow.

## Required Inputs

Read these files before implementation:

1. Root `AGENTS.md`.
2. Root `QUALITY.md`.
3. Active workflow under `documentation/workflow`.
4. `.agents/orchestrator/routing-rules.md`.
5. `.agents/orchestrator/swarm-orchestrator.md`.
6. Relevant `.agents/roles` files for the slice.
7. Relevant `.agents/skills` files for the slice.

When `documentation/workflow/context-pack.md` or
`documentation/workflow/context-pack.json` exists, read it first for orientation and
hash provenance. Reopen the authoritative files above when a recorded hash
changed, the slice touches governance files, or any conflict is detected.

## Active Workflow Discovery

Locate the active workflow in this order:

1. `documentation/workflow/workflow.md`, when present.
2. The active workflow described by `documentation/workflow/README.md`, when present.
3. The most recent `documentation/workflow/*.md`.

Stop if multiple workflows appear active and the execution target cannot be verified.

## Start Conditions

`workflow execute` may start only when both are present and checked:

1. complete checked `documentation/workflow/workflow.md`
2. checked or updated `documentation/arc42/**` documentation

Stop when either artifact is missing or contradicts `AGENTS.md`, `QUALITY.md`, ADRs or verified repository state.

## Branch Verification

Before implementation, run the S3 safety preflight:

1. `S3_STATUS`: check the working tree. Dirty or unclear status stops and reports only.
2. `S3_BRANCH`: verify the active workflow branch and local branch ref. Wrong branch stops and reports only.
3. `S3_SCOPE`: verify that the requested slice belongs to the checked active workflow scope. Scope conflict stops and escalates.
4. `S3_CLASSIFY`: classify the slice only after status, branch and scope are valid.

`S3_CLASSIFY` must route only verified slice classes:

- backend
- frontend
- runtime, DevOps or contract governance
- documentation, governance or metadata when the active workflow explicitly declares that scope

When none of those classes matches, route to `S3_UNCLASSIFIED`, stop execution
and escalate to the Root Architect. An unclassifiable slice must not execute
automatically.

Verify the workflow branch from the active workflow with:

```bash
git branch --show-current
git show-ref --verify --quiet refs/heads/<workflow-branch>
git status --short --branch
```

Continue only when the active branch matches the workflow branch and the local
branch ref exists. If the branch is missing or inactive, stop before file
changes. Create or restore the branch only when the user explicitly approves
that remediation, then rerun the active-branch and local-ref checks before
continuing.

Do not rely on workflow notes or execution summaries as proof that the branch
exists.

## S3D Execution Orchestrator

After `S3_CLASSIFY` and before write-capable slice execution, run S3D as the
workflow-execute Execution Orchestrator. S3D is not a fourth strand.

S3D must extract these fields from the checked active workflow:

- `slice_id`
- slice goal or purpose
- `profile`
- `owner`
- `secondary_reviewers`
- `affected_files`
- `affected_modules`
- `affected_contracts`
- `dependencies`
- `parallel_group`
- `file_locks`
- `contract_locks`
- `architecture_locks`
- `quality_gates.targeted`
- `quality_gates.required`
- `documentation.arc42`
- `documentation.adr`
- `stop_conditions`

Use explicit `none` or `not applicable` values when a field has no content.
Missing fields, dependency ranges that are not concrete slice IDs, unknown
slice IDs and dependency cycles stop execution before implementation.

S3D builds a directed dependency graph, runs topological sort, forms
independent parallelization groups and acquires file, contract, module and
architecture-boundary locks before any write-capable worker starts. Parallel
execution is allowed only when locks are disjoint and quality gates can be
attributed independently.

## Automatic Work Distribution Policy

During `workflow execute`, Codex must automatically inspect every executable
slice and determine whether it can be split into specialist execution streams.
The user does not need to say "with subagents" for this analysis.

Codex must prefer automatic work distribution when a slice contains clearly
separable concerns, while preserving Three Amigos, S3/S3D, branch, evidence,
quality-gate, SonarQube and merge protections. Codex must use real Codex
subagents where the current environment supports them. If real subagents are
unavailable or not visible, Codex must perform an explicit role-based fallback
review in the main execution thread and record the fallback in distribution
and consolidation evidence.

For every slice, determine affected areas from this stream map:

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

Codex must not split work when:

- the slice modifies the same files across multiple streams;
- the architectural boundary is unclear;
- the workflow contains contradictory requirements;
- implementation order is mandatory;
- a shared migration step must happen first;
- database or schema changes require strict sequencing;
- generated files would create merge conflicts;
- the Three Amigos gate marks the slice as not safely parallelizable;
- secrets or credentials handling is unclear;
- safety guards would be weakened.

Codex remains responsible for final consolidation, tests, evidence, PR
readiness and merge readiness. Subagents or stream workers may advise or
produce stream changes, but they must not directly merge to the main workflow
branch without consolidation.

For every slice, create `.codex/evidence/slice-<number>-distribution.md`
before implementation. The file must contain:

- workflow id;
- slice id;
- slice title;
- affected areas;
- chosen execution mode: sequential or parallel;
- selected streams;
- whether real subagents were used;
- whether fallback role-based review was used;
- whether Git worktrees were used;
- expected touched files/directories;
- conflict risks;
- quality gates to run;
- consolidation plan;
- reason why parallelization was accepted or rejected.

For every implemented slice, create or update
`.codex/evidence/slice-<number>-consolidation.md`. The file must contain:

- stream results;
- accepted findings;
- rejected findings with reason;
- files changed per stream;
- conflicts found;
- conflicts resolved;
- tests executed;
- SonarQube findings and fixes;
- documentation updates;
- final integration decision.

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

Stream branches may only be merged back after:

- stream-specific tests pass;
- file ownership conflicts are resolved;
- evidence is written;
- consolidation review accepts the changes.

## Parallel Worktree Execution

Parallel workflow execution is supported only for workflows that S3D and Three
Amigos confirm as independent. Independence requires disjoint changed files,
tests, package structures, governance files, workflow templates, skill files,
agent files, architecture decisions, and live infrastructure state.

Each parallel workflow must run in its own Git worktree, branch, working
directory, pull request and quality-gate lifecycle. Never execute multiple
parallel workflows inside the same worktree. Use the preferred worktree parent
`../Tiny-Swarm-World-worktrees/` and create each worktree from the current
integration branch defined by repository governance.

For every parallel workflow worktree:

1. Create a dedicated worktree and branch before write-capable work.
2. Run Three Amigos Gate inside that worktree.
3. Execute exactly one workflow.
4. Run validation, commit, push, PR, CI, SonarQube remediation, and merge
   lifecycle independently for that worktree.
5. Merge completed PRs one at a time after checking the latest integration
   branch, rebasing or updating when policy requires it, and rerunning affected
   tests.
6. Remove the worktree only after the PR is verified merged, the integration
   branch is updated locally, the worktree is clean, evidence is documented,
   and workflow status is updated.

Serialize workflows when file locks, tests, package structures, architecture
decisions, governance artifacts, skill files, agent files, or live
infrastructure state overlap. Live LXD, LXC, Docker, Docker Swarm, networking,
firewall, Portainer, Jenkins, SonarQube, Nexus, secrets-management, install,
reset or reinstall validation must be serialized unless the workflow proves an
isolated live environment.

Route lock conflicts as `LOCK_CONFLICT` through the Typed Error Router. S3D may
stop, report, escalate or recommend manual workflow refinement, but it must not
call `workflow create`, rewrite the active workflow from S3 or expand scope
automatically.

## Context Pack Validation

Before the first write-capable slice and whenever a slice depends on cached
governance context, verify `documentation/workflow/context-pack.json` against the
current files it hashes. A stale context pack is not a failure when the active
slice is responsible for refreshing it; otherwise it is a S3/S3D blocker and
the executor must reread the authoritative files directly.

## Process Performance Metrics

When `.agents/skills/process-performance-profiler/SKILL.md` exists, use it to
record workflow-process diagnostics under `documentation/workflow/metrics/**` when the
active workflow requests metrics. Metrics may include phase timing, role count,
file-read count, quality command count, repeated governance reads, retry count,
blocker count, longest critical path and unused parallelization opportunities.

Metrics are diagnostic only. They must not record secrets, prompt content or
raw infrastructure payloads, and they must not delay, skip, downgrade or
replace S3/S3D checks, D8 quality decisions, required role reviews,
checkpoint commits or `QUALITY.md` commands.

## Core Rule

Never implement a workflow slice directly before the relevant subagent or role has reviewed the slice.

The `workflow execute` command authorizes the configured subagent workflow for that workflow only. Keep unrelated tasks under the normal repository subagent authorization rules.

## Required Default Roles

Use at least these roles when relevant to the slice:

- Agent Workflow Orchestrator or Senior Swarm Orchestrator
- Senior System Architect
- Senior Python Automation Developer
- Senior Tester
- Senior DevOps Engineer

Route additional specialist concerns through `.agents/orchestrator/routing-rules.md`.
For service-boundary work, route through Senior System Architect plus the
dedicated service-boundary skills named in `.agents/orchestrator/routing-rules.md`.

## Execution Strands

Keep these strands separate while executing workflow slices:

- Python Automation Strand
- Frontend Strand
- Docker / Runtime Strand
- S3_DOC documentation path inside workflow execute

Python automation work routes through Senior Python Automation Developer, Senior System Architect, `architecture-hexagonal`, `quality-testing-strategy`, and Senior DevOps with `devops-docker` when container readiness is affected.

Java/Maven/Spring Boot project structure is retired; requests to reintroduce it
stop for explicit scope confirmation.

Current Tiny Swarm World UI work routes through `frontend-developer`,
`console-status-ui-developer`, and `terminal-status-dashboard` as
console/status UI. Browser React, frontend state, API client integration or UI
component work stops unless a separate frontend workflow verifies a frontend
module, package tooling and quality gates; only then route through Senior React
Frontend Developer, Senior UX Designer, and Senior DevOps with `devops-docker`
when container readiness is affected.

## Typed Error Router

When a slice quality gate or validation step fails, classify the failure before
starting any retry or targeted fix:

| Error type | Route to |
|---|---|
| `ARCH_VIOLATION` | Root Architect, Senior System Architect, `architecture-hexagonal` |
| `BUILD_FAILURE` | responsible Python automation or Frontend Agent, Senior DevOps, `quality-gate` for Python quality-gate failures |
| `TEST_FAILURE` | Senior Tester and responsible Slice Agent |
| `DOC_GOVERNANCE_FAILURE` | Senior Documentation Engineer, Requirement Engineer |
| `LOCK_CONFLICT` | Senior Execution Orchestrator, Senior Swarm Orchestrator, Workflow Executor, Root Architect |
| `UNKNOWN_FAILURE` | Root Architect escalation |

Every failure report must include the error type, owner, retry count, next
action and rerun command. Automatic retry or targeted-fix attempts are capped at
`maxRetries = 3`; after retry exhaustion, stop and escalate to the Root
Architect.

Targeted fixes remain inside `workflow execute` and inside the current workflow
scope. The router must not call `workflow create`, expand the workflow, merge
slices or commit unresolved failures.

## Execution Protocol

For each slice:

1. Read `documentation/workflow/workflow.md`.
2. Read root `AGENTS.md` and relevant skill definitions.
3. Run the Three Amigos or specialist review gate for the slice.
4. Run S3D dependency, topological-order and conflict-lock checks.
5. Create `.codex/evidence/slice-<number>-distribution.md` with the automatic
   work distribution decision.
6. Select sequential or parallel execution.
7. If parallel, create isolated Git worktrees per selected stream, execute
   stream-specific work, collect stream evidence, and consolidate into the main
   workflow branch only after the Git Worktree Execution Rule is satisfied.
8. If sequential, document why sequential execution was chosen and execute the
   slice in the main workflow branch.
9. Apply only the changes authorized by the slice.
10. Run targeted tests first.
11. Run the required quality checks from `QUALITY.md` or the workflow.
12. Fix quality-gate, test and SonarQube findings that are inside the active
   workflow branch and slice scope. Stop only when the fix would be unsafe,
   out of scope, unverifiable or would weaken gates.
13. Treat the required quality decision as `D8`. Failed build, failed tests,
   architecture violation, missing required documentation, missing workflow
   version or failed required quality gate blocks commit, checkpoint push and
   release readiness.
14. Inspect `git diff` and `git diff --check`.
15. Create or update `.codex/evidence/slice-<number>-consolidation.md` with
    stream results, accepted and rejected findings, conflicts, tests,
    SonarQube fixes, documentation updates and final integration decision.
16. Document the result in the workflow quality log or the workflow-designated location.
17. When the slice quality gate passed, stage only files changed by the current slice.
18. Run `git diff --cached --check`.
19. Create the slice-scoped checkpoint commit. Each commit must represent
    exactly one slice; multi-slice commits are forbidden.
20. Push the current workflow branch to `origin`.
21. Create or update the pull request when the workflow or publication command
    requires it. Merge only after required gates pass, including SonarQube when
    configured.
22. Record the workflow version, slice ID, slice title, responsible agent,
    changed files, quality-gate commands, quality-gate result, commit SHA,
    rollback reference, arc42 update status, ADR update status and push result
    in the execution report.
23. Route asynchronous execution-report notes through `Q11`; Q11 is
    non-blocking by default unless the active workflow explicitly declares a
    regulatory or compliance report as a D8 requirement.
24. Continue with the next slice or next workflow issue only when the current
    slice is clean, the checkpoint push or required PR lifecycle succeeded, or
    the workflow explicitly permits carrying a documented blocker without a
    commit.

Slice checkpoint push is not `push auto`. It must not create or merge a PR, run branch cleanup, force-push or push to `main`.
A later explicit `push auto` may publish any task-scoped repository change
produced by workflow execution only through the guarded commit, pull request,
green required-checks, SonarQube when configured, merge and cleanup lifecycle.

Each workflow-execute checkpoint commit must represent exactly one slice. Do
not combine multiple slice IDs, opportunistic documentation edits or unrelated
fixes in one checkpoint commit. If the slice record cannot identify the active
workflow version or rollback reference, stop and route the blocker through
Documentation Governance or Root Architect escalation.

`workflow execute` must never call `workflow create` backwards. If the active
workflow is missing mandatory distribution metadata, evidence requirements or
execution-safety fields, stop and report the workflow governance blocker
instead of rewriting the workflow during execution.

## Stop Conditions

Stop and report if:

- architecture is unclear
- a class, module, API, quality command, schema, or command assumption is uncertain
- tests fail and cannot be fixed safely inside the slice
- the workflow conflicts with `AGENTS.md` or `QUALITY.md`
- multiple active workflows conflict
- `S3_STATUS` finds a dirty or unclear working tree
- `S3_BRANCH` finds the wrong branch or a missing local branch ref
- `S3_SCOPE` finds that the requested work is outside the checked active workflow
- `S3_CLASSIFY` cannot classify the slice and routes to `S3_UNCLASSIFIED`
- S3D cannot verify required slice metadata, a dependency graph, topological order or disjoint locks
- S3D detects a file, contract, module or architecture-boundary lock conflict
- the distribution decision evidence cannot be created before implementation
- parallel workflow worktrees cannot be created or are dirty before execution
- two parallel workflows unexpectedly modify the same file, test, governance
  artifact, skill file, agent file, package structure or architecture decision
- a stream worker or subagent would merge directly to the main workflow branch
- a slice would need a multi-slice commit
- a slice requires hidden or undocumented behavior
- shared live infrastructure would be modified concurrently
- merge order matters and cannot be determined safely
- a rebase or merge conflict occurs after another parallel workflow merged
- a quality or validation failure cannot be classified except as `UNKNOWN_FAILURE`
- the typed error owner cannot be mapped to a verified role, skill or documented interim owner
- typed-router retries exceed `maxRetries = 3`
- checked `documentation/workflow/workflow.md` is missing
- checked or updated arc42 documentation is missing
- the workflow branch is missing, inactive, or cannot be verified as a local ref
- a change would introduce shared Java code modules between microservices
- subagent or role execution is required and neither a real subagent nor an
  explicit fallback role-based review can be performed
- commit or push is requested but not explicitly allowed by the workflow
- checkpoint push would include files outside the current slice
- checkpoint push would push to `main`, create or merge a PR, run `push auto`, run branch cleanup or force-push
- `push auto` is requested but commit, pull request, green required-checks,
  SonarQube when configured, merge or cleanup verification cannot be completed
