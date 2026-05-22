# Branch Rules

## Rules

- Larger workflow execution should happen on a dedicated branch.
- New workflow creation must ensure a dedicated workflow branch exists, is checked out and is verified before any workflow artifact is created or modified: `workflow.md`, `documentation/workflow/**`, workplans, slice definitions, workflow-specific documentation changes, implementation tasks or write-capable agent assignments.
- Branch naming follows the matrix in `documentation/process/branch-governance.md`.
- `skills update` uses `docs/skills-<short-topic>-<yyyyMMdd>` for documentation and registry-only changes, or `architecture/agents-<short-topic>-<yyyyMMdd>` for role, routing or process structure changes.
- For `workflow create`, use `feature/workflow-<short-topic>-<yyyyMMdd>` by default, with `fix/`, `docs/` or `architecture/` only when the workflow scope clearly matches that category.
- For `workflow execute`, use the branch declared by the active checked workflow and stop on branch mismatch.
- For ad-hoc implementation outside exact process commands, use `feature/<short-topic>-<yyyyMMdd>` or `fix/<short-topic>-<yyyyMMdd>` unless the user requests another prefix.
- Commit preparation on `main` must create the branch required by the active strand and must not fall back to a generic `work/<task-slug>` branch when strand rules apply.
- Branch purpose must match workflow scope.
- Do not create or modify workflow artifacts on `main`, `master`, `develop` or another shared branch.
- Do not switch branches if doing so would endanger uncommitted user work.
- Before staging or committing on Windows-hosted WSL worktrees, check for broad line-ending-only noise.

## STOP Rules

Stop when:

- branch context is unclear;
- the current branch is detached or unclear;
- local or remote branch-name collisions cannot be resolved with a clear unique suffix;
- the workflow branch cannot be created, checked out or verified as active;
- branch switch would lose or hide uncommitted work;
- line-ending-only changes pollute unrelated files;
- workflow scope and branch purpose conflict.
