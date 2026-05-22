---
name: git-branch-strategy
description: Use for branch isolation, commit preparation boundaries, staged-file review, and line-ending checks.
---

# Branch Strategy

## Purpose

Keep slices isolated and reviewable.

## Practices

- Use the branch matrix in `documentation/process/branch-governance.md` before creating branches for process-governance or implementation work.
- For `skills update`, use `docs/skills-<short-topic>-<yyyyMMdd>` for documentation and registry-only changes, or `architecture/agents-<short-topic>-<yyyyMMdd>` when role, routing or process structure changes.
- For `workflow create`, follow the workflow-specific branch naming requested by repository governance: `feature/workflow-<short-topic>-<yyyyMMdd>` by default, with `fix/`, `docs/`, or `architecture/` when the workflow scope clearly matches that category.
- For `workflow execute`, use only the branch declared by the active checked workflow. Do not create a replacement branch during execution.
- For ad-hoc implementation outside the exact process commands, use `feature/<short-topic>-<yyyyMMdd>` or `fix/<short-topic>-<yyyyMMdd>` unless the user requests another branch strategy.
- Create and checkout the workflow branch before creating or modifying workflow artifacts: `workflow.md`, `documentation/workflow/**`, workplans, slice definitions, workflow-specific documentation changes, implementation tasks, or write-capable agent assignments.
- Stop if unrelated or unclear uncommitted changes exist before branch creation.
- Stop if the current branch is detached or unclear.
- Check local and remote branch-name collisions; choose the next clear unique suffix when needed.
- Keep commits scoped to the requested task.
- Do not commit or push unless the user explicitly asks for that step.
- Verify that broad line-ending changes are absent before staging or committing.
- Prefer non-interactive git commands.

## Verification

- Run `git status --short` before and after changes.
- Verify the active branch with `git branch --show-current` after workflow branch creation.
- Verify active-strand branch eligibility against `documentation/process/branch-governance.md` before commit preparation on `main`.
- Review staged files before commit preparation.
