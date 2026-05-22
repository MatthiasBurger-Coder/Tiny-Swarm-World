# Workflow Execute Process

Use this process when the user requests `workflow execute`.

## Required References

- `AGENTS.md`
- `QUALITY.md`
- `.agents/prompts/workflow-execute.md`
- `.agents/skills/workflow-executor/SKILL.md`
- `.agents/orchestrator/routing-rules.md`
- active workflow under `documentation/workflow`

## Process

1. Verify the active workflow and branch.
2. Classify the next slice and route it to the smallest suitable role set.
3. Implement only the slice's allowed write scope.
4. Run targeted checks first, then required gates from `QUALITY.md`.
5. Inspect `git diff` and `git diff --check`.
6. When the active workflow requires checkpoint pushes, stage only current-slice files, commit, push the workflow branch, and record the result.

## Stop Conditions

Stop when the branch, slice metadata, ownership, quality gate, write scope, or checkpoint target cannot be verified.
