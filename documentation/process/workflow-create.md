# Workflow Create Process

Use this process when the user requests `workflow create`.

## Required References

- `AGENTS.md`
- `QUALITY.md`
- `.agents/prompts/workflow-create.md`
- `.agents/skills/workflow-authoring/SKILL.md`
- `.agents/orchestrator/routing-rules.md`
- `documentation/process/branch-governance.md`

## Process

1. Clarify the requirement until it is ready for workflow authoring or clearly blocked.
2. Verify repository status and branch safety before creating workflow artifacts.
3. Create or verify the dedicated workflow branch.
4. Generate or regenerate `documentation/workflow`.
5. Define slices with owners, dependencies, allowed write scopes, stop conditions, and quality gates from `QUALITY.md`.
6. Add the required `## Parallel Execution` section to every executable workflow, including parallel eligibility, conflicting workflows, shared files, shared infrastructure, isolated worktree requirement, serialized live validation requirement, and merge-order constraints.
7. Add the required `## Automatic Work Distribution Policy` section to every
   executable workflow so `workflow execute` automatically analyzes each slice
   for backend, frontend, tests, runtime, documentation, quality, architecture
   and security streams, uses real subagents where supported, falls back to
   explicit role-based review where needed, and records distribution plus
   consolidation evidence.
8. Add the required `## Git Worktree Execution Rule` section to every
   executable workflow so parallel stream work uses isolated worktrees and
   branches named `<workflow-branch>-slice-<number>-<stream>`.
9. Commit the completed workflow-authoring artifacts and push only `HEAD` to
   `origin/<workflow-branch>` as guarded workflow-create publication.
10. Do not run `push auto` for workflow-create-only output. Stop before PR
    merge, remote branch deletion or local cleanup unless the user explicitly
    confirms a workflow-documentation-only PR merge after the workflow-create
    guard is reported.
11. Verify that `documentation/workflow/workflow.md` and relevant `documentation/arc42` updates exist before releasing `workflow execute`.

## Stop Conditions

Stop when requirement ownership, branch safety, architecture impact, quality commands, workflow artifact paths, or guarded workflow-create publication cannot be verified.
