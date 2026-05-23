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
2. Run S3 preflight:
   - `S3_STATUS`: inspect the worktree and classify any existing changes.
   - `S3_BRANCH`: verify the workflow branch is active and has a local ref.
   - `S3_SCOPE`: verify the requested work belongs to the active workflow.
   - `S3_CLASSIFY`: classify the next slice only after status, branch and
     scope are valid.
3. Run S3D orchestration before write-capable work:
   - extract slice metadata, dependencies, affected files, contracts, modules
     and quality gates;
   - build the dependency graph and reject unknown IDs or cycles;
   - verify file, contract, module and architecture locks;
   - choose serial execution when locks overlap.
4. Classify the next slice and route it to the smallest suitable role set.
5. Implement only the slice's allowed write scope.
6. Run targeted checks first, then required gates from `QUALITY.md`.
7. Classify failures through the Typed Error Router before retries.
8. Inspect `git diff` and `git diff --check`.
9. When the active workflow requires checkpoint pushes, stage only current-slice files, commit, push the workflow branch, and record the result.

## Stop Conditions

Stop when the branch, slice metadata, dependency graph, locks, ownership,
quality gate, write scope, failure route, or checkpoint target cannot be
verified.
