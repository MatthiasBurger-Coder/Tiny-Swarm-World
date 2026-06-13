# Branch Governance

## Purpose

Define branch names used by agent, workflow, commit, and push procedures for
Tiny Swarm World.

## Rules

- Never push directly to `main`.
- Create a dedicated branch before committing or pushing work that starts on
  `main`.
- Preserve existing user changes when switching branches.
- Check local and remote branch-name collisions before creating a branch.
- Prefer clear, task-specific branch names over generic work branches.
- `push auto` may automatically merge any task-scoped repository change,
  including product feature or bug-fix branches, Python product code, and
  Python product-behavior tests.
- `push auto` must create or reuse a pull request, wait or retry until required
  checks are green including SonarQube when configured, merge only after green
  checks, delete the merged remote head branch, and clean up the local branch.

## Branch Matrix

| Strand | Branch pattern |
|---|---|
| Skills or agent registry documentation only | `docs/skills-<short-topic>-<yyyyMMdd>` |
| Agent roles, routing, process structure or workflow governance | `architecture/agents-<short-topic>-<yyyyMMdd>` |
| Workflow creation | `feature/workflow-<short-topic>-<yyyyMMdd>` |
| Workflow execution | Use the branch declared by the active checked workflow |
| Product feature work | `feature/<short-topic>-<yyyyMMdd>` |
| Product bug fix | `fix/<short-topic>-<yyyyMMdd>` |
| Documentation-only work | `docs/<short-topic>-<yyyyMMdd>` |

## Verification

Before staging, committing, or pushing, inspect:

```bash
git status --short --branch
git branch --show-current
```

On Windows-hosted WSL worktrees, also check that unrelated line-ending-only
changes are absent before staging.
