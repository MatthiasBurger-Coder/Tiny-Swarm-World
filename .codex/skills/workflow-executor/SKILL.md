---
name: workflow-executor
description: Reusable entrypoint for executing repository workflows when the user writes workflow execute; routes slices through subagents or role reviews, quality gates, diff inspection, stop conditions, and commit restrictions.
---

# Workflow Executor

Use this skill only when the user writes `workflow execute` or explicitly asks to execute the active repository workflow.

## Resolution Rule

This file is the reusable base workflow-executor protocol.

When a repository provides a project-specific executor such as
`.agents/skills/workflow-executor/SKILL.md`, that project-specific executor is
the active execution protocol for that repository. Use this `.codex` file for
portable baseline context and conflict detection, not as a competing second
execution protocol.

## Authoritative Sources

Read, when present:

- root `AGENTS.md`
- root `QUALITY.md`
- `.codex/workflow/workflow-execution-rules.md`
- project workflow files such as `documentation/workflow/workflow.md`, `documentation/workflow/README.md`, or the newest relevant `documentation/workflow/*.md`
- project-specific workflow, routing, role, or skill files under `.agents/`

## Workflow

1. Locate the active workflow using project instructions when they exist.
2. Read the full workflow before implementation.
3. Verify required start artifacts from project instructions, such as a checked workflow file and architecture documentation.
4. Run the S3 safety preflight when project governance defines it: check working tree status, active execution branch, local branch ref and active workflow scope before classifying a slice. Project-defined S3 classification must include a default unclassified STOP and escalation path; unclassifiable slices must not execute automatically.
5. Identify slices, dependencies, write scopes, and verification commands.
6. Automatically analyze each slice for backend, frontend, tests, runtime,
   documentation, quality, architecture and security stream separation.
7. Route each slice to the smallest suitable set of subagents or role reviews.
   Use callable subagents where supported; if unavailable, perform explicit
   role-based fallback review and record it.
8. Execute one slice at a time unless project governance approves safe stream
   parallelization in isolated Git worktrees.
9. Run required targeted checks and quality gates after each slice.
10. Fix in-scope test, quality-gate and SonarQube findings without weakening gates.
11. Inspect `git diff` and `git diff --check`.
12. When the active project workflow permits slice checkpoint pushes, stage only current-slice files, run `git diff --cached --check`, create the slice-scoped checkpoint commit, push only the current workflow branch to `origin`, and record the commit SHA and push result.
13. Continue only when the slice is clean, the required checkpoint is recorded, or the workflow explicitly permits carrying a documented blocker.

Slice checkpoint push is separate from `push` and `push auto`; it does not create or merge a PR, run branch cleanup, force-push or push to `main`.
A later explicit `push auto` may publish any task-scoped repository change from
workflow execution only through the guarded commit, pull request, green
required-checks, SonarQube when configured, merge and cleanup lifecycle.

Parallel workflow execution requires one dedicated worktree, branch, working
directory, PR and quality lifecycle per workflow. Do not execute multiple
parallel workflows in the same worktree. Serialize overlapping workflows and
shared live infrastructure validation unless isolated infrastructure is
verified. Merge parallel workflow PRs one at a time after refreshing the
integration branch, updating the branch when required, rerunning affected tests
and rechecking CI plus SonarQube.

Parallel slice stream execution requires one dedicated stream branch and
worktree per stream. Branch names follow
`<workflow-branch>-slice-<number>-<stream>`. Stream workers may not merge
directly to the main workflow branch; Codex must consolidate accepted stream
results after stream tests, evidence and conflict review pass.

## Stop Conditions

Stop when a slice, symbol, module, API, build task, schema, command,
architecture rule, quality gate, start artifact, checkpoint target, service
boundary, active branch, working-tree status, local branch ref, workflow scope,
parallel worktree isolation, merge order, live infrastructure isolation, or
slice classification cannot be verified exactly.
