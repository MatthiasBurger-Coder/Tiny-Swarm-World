# Workflow Create Process

Use this process when the user requests `workflow create`.

## Required References

- `AGENTS.md`
- `QUALITY.md`
- `documentation/process/issue-completion-discipline.md`
- `.agents/prompts/workflow-create.md`
- `.agents/skills/workflow-authoring/SKILL.md`
- `.agents/orchestrator/routing-rules.md`
- `documentation/process/branch-governance.md`

## Process

1. Clarify the requirement until it is ready for workflow authoring or clearly blocked.
2. Verify repository status and branch safety before creating workflow artifacts.
3. Create or verify the dedicated workflow branch.
4. Create a requirement matrix for issue-driven workflows before defining
   executable slices.
5. Generate or regenerate `documentation/workflow`.
6. Define slices with owners, dependencies, allowed write scopes, stop conditions, quality gates from `QUALITY.md`, and required issue-completion evidence.
7. Add the required `## Parallel Execution` section to every executable workflow, including parallel eligibility, conflicting workflows, shared files, shared infrastructure, isolated worktree requirement, serialized live validation requirement, and merge-order constraints.
8. Add the required `## Automatic Work Distribution Policy` section to every
   executable workflow so `workflow execute` automatically analyzes each slice
   for backend, frontend, tests, runtime, documentation, quality, architecture
   and security streams, uses real subagents where supported, falls back to
   explicit role-based review where needed, and records distribution plus
   consolidation evidence.
9. Add the required `## Git Worktree Execution Rule` section to every
   executable workflow so parallel stream work uses isolated worktrees and
   branches named `<workflow-branch>-slice-<number>-<stream>`.
10. Add the required `## Issue Completion Discipline` section to every
    issue-driven executable workflow so `DONE` is blocked until all
    requirements are implemented, verified and evidenced.
11. Commit the completed workflow-authoring artifacts and push only `HEAD` to
   `origin/<workflow-branch>` as guarded workflow-create publication.
12. Do not run `push auto` for workflow-create-only output. Stop before PR
    merge, remote branch deletion or local cleanup unless the user explicitly
    confirms a workflow-documentation-only PR merge after the workflow-create
    guard is reported.
13. Verify that `documentation/workflow/workflow.md`, relevant
    `documentation/arc42` updates and requirement-matrix expectations exist
    before releasing `workflow execute`.

## Stop Conditions

Stop when requirement ownership, requirement-matrix completeness, branch
safety, architecture impact, quality commands, workflow artifact paths,
completion evidence expectations, or guarded workflow-create publication cannot
be verified.
