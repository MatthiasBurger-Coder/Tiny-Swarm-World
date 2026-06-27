---
name: workflow-authoring
description: Use for creating or regenerating the current project workflows with verified baselines, executable slices, dependency ordering, subagent ownership, architecture constraints, resilience requirements, quality gates, stop conditions, and full documentation/workflow lifecycle control.
---

# Skill: Workflow Authoring

## Purpose

Create executable, repository-specific workflows that preserve `AGENTS.md`, `QUALITY.md`, architecture governance, requirement traceability and verification integrity.

This skill governs workflow creation. It does not implement runtime business functionality.

## Requirement Clarification Gate

Before workflow authoring, run the `workflow create` requirement clarification loop.

Record:

- Original Request
- Interpreted Intent
- Change Type
- Affected Process Strand
- Affected Architecture Area
- Explicit Requirements
- Implicit Requirements
- Assumptions
- Non-Goals
- Risks
- Open Questions
- Blocking Questions
- Confidence Level
- Decision: `READY_FOR_WORKFLOW`, `PROCEED_WITH_ACCEPTED_ASSUMPTIONS` or `REQUIRES_REFINEMENT`

Confidence greater than or equal to 90 percent may be `READY_FOR_WORKFLOW` when no blocking questions remain. Confidence from 70 to 89 percent may be `PROCEED_WITH_ACCEPTED_ASSUMPTIONS` only when every assumption is non-blocking and documented. Confidence below 70 percent is `REQUIRES_REFINEMENT`.

Blocking questions prevent final workflow authoring and release for `workflow execute`.

Automatic clarification loops are capped at `maxRetries = 3`. After the third unresolved attempt, stop workflow authoring, keep the decision at `REQUIRES_REFINEMENT`, and escalate to the Root Architect with the unresolved blockers.

`workflow create` must use five mandatory roles:

- Senior Requirement Engineer
- Senior System Architect
- Senior Python Automation Developer
- Senior React Frontend Developer
- Senior Tester

Classic labels such as Requirement Analyst, Architecture Validator and Quality Validator are optional perspectives. They do not replace the five mandatory roles.

## Mandatory Branch-First Rule

Every workflow creation must start by ensuring a dedicated Git branch for that workflow exists and is active.

For a new workflow this means creating and checking out a workflow branch before mutating workflow artifacts. If the current branch already exactly matches the current workflow, verify it before continuing.

Read-only verification, requirement intake, routing-rule inspection, and role selection may occur before branch creation. Mutating workflow creation must not.

This rule applies before any workflow artifact is created or modified: `workflow.md`, `documentation/workflow/**`, workplans, slice definitions, workflow-specific documentation changes, implementation tasks, or write-capable agent assignments.

Required order:

1. Verify the Git repository context.
2. Check the working tree status.
3. Stop if the current branch is detached, unclear, or if unrelated or unclear uncommitted changes exist.
4. Create a dedicated workflow branch, unless the current branch already matches the current workflow.
5. Check local and remote branch-name collisions, choosing the next clear unique suffix when needed.
6. Checkout the workflow branch, or verify the existing matching workflow branch.
7. Verify that the local branch ref exists.
8. Verify the active branch.
9. Create or regenerate workflow artifacts only after successful branch verification.
10. Continue with slices, subagents, quality gates, commits, and optional push.

Default branch naming:

```text
feature/workflow-<short-topic>-<yyyyMMdd>
fix/workflow-<short-topic>-<yyyyMMdd>
docs/workflow-<short-topic>-<yyyyMMdd>
architecture/workflow-<short-topic>-<yyyyMMdd>
```

Never create or modify workflow artifacts on `main`, `master`, `develop`, or any shared branch. If branch creation, checkout or verification fails, stop and report the reason instead of continuing in the current branch.

Branch verification after creation or checkout must include both:

```bash
git show-ref --verify --quiet refs/heads/<workflow-branch>
git branch --show-current
```

Do not rely on generated workflow notes as proof that a branch exists.

## Workflow Authoring Publication Rule

`workflow create` is a planning and governance publication step, not an
implementation release step. When workflow authoring completes successfully,
the workflow branch must be committed and pushed to `origin/<workflow-branch>`
as the default publication action so other agents, worktrees and parallel
development streams can see the same workflow baseline.

The workflow authoring publication action must:

1. stage only workflow-authoring files and directly required governance
   synchronization files;
2. create a workflow-authoring commit after the reviewed diff and required
   governance checks pass;
3. push only `HEAD` to `origin/<workflow-branch>`;
4. record the branch name, commit SHA, push target and verification result in
   the workflow handoff;
5. stop if the branch is `main`, if unrelated files are present, if the remote
   target is unclear, or if the workflow branch cannot be pushed.

This default publication is equivalent to a guarded `push`, not `push auto`.
It must not create, merge or clean up a pull request, must not delete local or
remote branches, must not force-push and must not push to `main`.

After a completed `workflow create`, an immediate user request for `push auto`
against the same workflow-authoring branch must be treated as a request to keep
the workflow branch published only. The operator must run or reuse the normal
`push` publication path and must stop before PR merge, remote branch deletion
or branch cleanup unless a later task produces implementation changes through
`workflow execute` or the user explicitly requests a workflow-documentation PR
merge after acknowledging that `push auto` is blocked for workflow-authoring
only output.

## Required Inputs

Read before authoring or regenerating a workflow:

1. User request.
2. Root `AGENTS.md`.
3. Root `QUALITY.md`.
4. Existing `documentation/workflow` if present.
5. Relevant EPIC files under `documentation/epics` if present.
6. Relevant `documentation/arc42` and `documentation/adr` files.
7. Relevant `.agents/skills` and `.agents/roles` files.
8. Python tooling or CI files only when quality-gate behavior is affected.

## Workflow Regeneration Rule

Before creating a new workflow:

1. Verify the repository root and the absolute target path.
2. Verify that the dedicated workflow branch exists and is active.
3. Delete `documentation/workflow` completely, unless the user explicitly asks to preserve an existing workflow.
4. Recreate `documentation/workflow`.
5. Regenerate the full workflow structure.

Do not partially overwrite old slices. Do not keep stale workflow files unless the user explicitly asks to archive them outside the active workflow.

## Multi-Issue Workflow Index Rule

When a user explicitly asks to create workflows for multiple issues before
executing any of them, do not overwrite the single active workflow file for
each issue. Preserve `documentation/workflow/workflow.md` unless the user
explicitly asks to replace the active workflow.

Use this indexed layout:

```text
documentation/workflow/workflow.index.md
documentation/workflow/issues/issue-<number>/workflow.md
documentation/workflow/issues/issue-<number>/context-pack.md
documentation/workflow/issues/issue-<number>/context-pack.json
```

The index must list each included issue, workflow id, workflow path, branch,
status, dependencies, blockers, and execution order. It must also list excluded
issues with the reason they were excluded.

Each issue workflow remains executable only after it is promoted to the active
workflow location or the workflow executor is explicitly extended to accept an
indexed workflow path. Until then, `workflow execute` must not guess which
indexed workflow to run.

For multi-issue authoring:

1. Create one dedicated multi-workflow authoring branch unless the user
   explicitly requests one branch per issue.
2. Create or update `workflow.index.md` first.
3. Create one issue-local `workflow.md` per authoring-ready issue.
4. Keep issue-local context packs beside the issue-local workflow.
5. Do not execute slices until all requested issue workflows are authored and
   the execution order is confirmed from `workflow.index.md`.
6. Use Git worktrees for later parallel execution only when S3D confirms
   disjoint locks and the workflow index declares the workflows independent.

Issues that fail the requirement clarification gate must be listed in the
index as excluded or blocked instead of receiving executable workflow plans.

## Workflow Structure

Every workflow should include:

- Executive Summary
- Target Picture
- verified baseline
- target outcome
- Scope
- explicit non-goals
- architecture constraints
- Python Automation Assessment
- Frontend Assessment
- Test Strategy
- resilience requirements
- ordered slices
- slice dependency graph
- Parallel Execution
- Automatic Work Distribution Policy
- Git Worktree Execution Rule
- parallelization opportunities
- role or subagent ownership map
- quality-gate expectations from `QUALITY.md`
- documentation synchronization points
- stop conditions
- uncertainty escalation rules
- commit and push plan when requested
- Definition of Done
- Handoff to workflow execute
- arc42 Check Status

## Workflow Context Pack

When a workflow is created or regenerated, create or update:

- `documentation/workflow/context-pack.md`
- `documentation/workflow/context-pack.json`

The context pack is a workflow-local navigation aid. It must record the active
workflow version, branch, process strand, execution profile, affected areas,
forbidden areas, required roles, conditional roles, quality commands and hashes
for governing files used during creation.

The context pack must not replace root `AGENTS.md`, `QUALITY.md`, ADRs, arc42,
routing rules, active workflow files or skill files. It is stale when any
recorded hash changes, when the task touches governance files, or when a
conflict is detected.

Workflow creation is complete only when both of these artifacts have been checked:

1. complete checked `documentation/workflow/workflow.md`
2. checked or updated `documentation/arc42/**` documentation

## Slice Rules

Use stable two-digit slice numbers:

```text
Slice 01
Slice 02
Slice 03
```

For each slice define:

- purpose
- prerequisites
- machine-readable YAML metadata
- affected files
- affected modules
- affected contracts
- owner role
- allowed write scope
- dependencies
- parallel group
- parallel execution eligibility
- conflicting workflows
- shared files
- shared infrastructure
- isolated worktree requirement
- serialized live validation requirement
- merge-order constraints
- file, contract and architecture locks
- parallelization status
- done criteria
- verification commands
- stop conditions

Each slice must include a fenced `yaml` metadata block with these fields:

```yaml
slice_id:
profile:
owner:
secondary_reviewers: []
affected_files: []
affected_modules: []
affected_contracts: []
dependencies: []
parallel_group:
file_locks: []
contract_locks: []
architecture_locks: []
quality_gates:
  targeted: []
  required: []
documentation:
  arc42:
  adr:
stop_conditions: []
```

Use empty arrays for none. Dependencies must be concrete slice IDs, not ranges
or prose. Missing metadata blocks future `workflow execute` until the workflow
is corrected.

Every executable workflow must include this section:

```markdown
## Parallel Execution

- Can this workflow run in parallel?
- Conflicting workflows:
- Shared files:
- Shared infrastructure:
- Requires isolated worktree:
- Requires serialized live validation:
- Merge-order constraints:
```

Default policy:

- Every workflow requires its own Git worktree.
- Parallel execution is allowed only after Three Amigos confirms
  independence.
- Live validation is serialized unless isolated infrastructure is available.

Parallelize only when write scopes are disjoint, shared contracts are stable,
workflow templates, governance files, skill files, agent files, tests, package
structures and architecture decisions do not overlap, and verification can be
run independently. Conflicting workflows must be executed sequentially.

Every executable workflow must also include `## Automatic Work Distribution
Policy` and `## Git Worktree Execution Rule` sections that mirror the active
workflow executor policy. The workflow must state that `workflow execute`
automatically analyzes each slice for safe specialist stream decomposition,
uses real Codex subagents where supported, falls back to explicit role-based
review when subagents are unavailable, requires
`.codex/evidence/slice-<number>-distribution.md` before implementation,
requires `.codex/evidence/slice-<number>-consolidation.md` for implemented
slices, and keeps Codex as final integration owner.

The workflow must define the stream map for backend, frontend, tests, runtime,
documentation, quality, architecture and security. It must also define the
non-parallelization rules for overlapping files, unclear architecture,
contradictory requirements, mandatory ordering, shared migrations, strict
database/schema sequencing, generated-file conflicts, a Three Amigos
not-safely-parallelizable decision, unclear secrets handling and weakened
safety guards.

## Subagent Assignment

Assign roles by verified responsibility:

- workflow creation and dependency ordering: Senior Workflow Architect
- requirement and EPIC drift: Senior Requirement Engineer
- architecture boundaries and arc42: Senior System Architect or arc42 governance
- documentation consistency: Senior Documentation Engineer
- quality verification: Senior Tester or quality-gate skills
- branch, commit and push readiness: git commit preparation skills

During `workflow execute`, the command itself authorizes automatic distribution
analysis and safe stream execution. Use real Codex subagents where supported.
If callable subagents are unavailable or not visible, perform the same review
through explicit role-based fallback in the main execution thread and document
the fallback in evidence.

Subagents must verify that the active branch or stream worktree branch belongs
to the current workflow before modifying files. They must not implement on
`main`, `master`, `develop`, or any shared branch. Stream workers must not
merge directly to the main workflow branch; Codex consolidates accepted stream
results after evidence and tests pass.

## Quality Gates

Read `QUALITY.md` before documenting quality commands.

Do not invent Python quality commands, CI jobs or quality scripts. If a command cannot be verified, stop and report.

## Stop Conditions

Stop and report if:

- the Git repository context cannot be verified
- the current branch is detached or unclear
- unrelated or unclear uncommitted changes exist before workflow branch creation
- the branch name collides with an existing local or remote branch and no clear unique suffix can be chosen
- the dedicated workflow branch cannot be created, checked out, verified as a local ref, or verified as active
- the active branch is `main`, `master`, `develop`, or another shared branch when workflow files would be created
- `documentation/workflow` cannot be safely deleted and regenerated
- architecture conflicts are unclear
- EPIC contradicts implementation and the source of truth is unclear
- multiple active workflows conflict
- service ownership is ambiguous
- resilience expectations are unclear
- quality-gate authority is unclear
- planned file paths cannot be verified
- blocking requirement questions remain
- `documentation/workflow/workflow.md` cannot be validated
- arc42 documentation cannot be checked or updated
- continuing would require guessing governance decisions

## Expected Outputs

- fully regenerated `documentation/workflow`
- ordered slice plan
- dependency graph or dependency summary
- role ownership map
- verification plan
- documented assumptions and unresolved conflicts
