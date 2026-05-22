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
6. Verify that `documentation/workflow/workflow.md` and relevant `documentation/arc42` updates exist before releasing `workflow execute`.

## Stop Conditions

Stop when requirement ownership, branch safety, architecture impact, quality commands, or workflow artifact paths cannot be verified.
