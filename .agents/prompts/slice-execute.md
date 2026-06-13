# Slice Execute Prompt

Use for executing one workflow slice at a time.

## Required Flow

1. Read the slice scope, prerequisites, dependencies and allowed write scope.
2. Verify the active workflow branch and local branch ref before editing:

```bash
git branch --show-current
git show-ref --verify --quiet refs/heads/<workflow-branch>
```

3. Verify required files, symbols, tasks, contracts and commands before editing.
4. Run the Three Amigos or specialist review gate for the slice.
5. Create `.codex/evidence/slice-<number>-distribution.md` with affected
   areas, selected execution mode, selected streams, subagent or fallback
   status, worktree status, risks, quality gates and consolidation plan.
6. Route to required subagents or role reviews.
7. If parallel, use isolated Git worktrees and stream branches named
   `<workflow-branch>-slice-<number>-<stream>`.
8. Apply the smallest verified change.
9. Run targeted checks first.
10. Run required quality gates from `QUALITY.md` or the workflow.
11. Fix in-scope test, quality-gate and SonarQube findings without weakening gates.
12. Treat the required quality decision as `D8`; D8 blocks commit and checkpoint
   push on failed build, failed tests, architecture violation, missing required
   documentation, missing workflow version or failed required quality gate.
13. Inspect `git diff` and `git diff --check`.
14. Create or update `.codex/evidence/slice-<number>-consolidation.md`.
15. When the slice quality gate passed, prepare the `CP_RECORD` with workflow
   version, slice ID, slice title, responsible agent, changed files,
   quality-gate commands, quality-gate result, rollback reference,
   `arc42Updated` and `adrUpdated`.
16. Stage only current-slice files.
17. Run `git diff --cached --check`.
18. Create the slice-scoped checkpoint commit.
19. Push the current workflow branch to `origin`.
20. Record commit SHA, push result, blockers and handoff state.
21. Route asynchronous execution-report notes through `Q11`; Q11 is
   non-blocking by default unless a regulatory or compliance report is
   explicitly declared as a D8 requirement.

The slice checkpoint push is not `push auto`. It must not create or merge a PR, clean up branches, force-push or push to `main`.
A later explicit `push auto` may publish any task-scoped repository change
from a slice only through the guarded commit, pull request, green
required-checks, SonarQube when configured, merge and cleanup lifecycle.
Each checkpoint commit must contain exactly one slice.

## Stop Conditions

Stop when:

- write scope is unclear;
- active workflow branch is missing, inactive, or has no local ref;
- required role review is missing;
- distribution or consolidation evidence is missing;
- exact repository artifact cannot be verified;
- tests or required gates fail;
- D8 fails or cannot be verified;
- the staged diff contains files from another slice;
- the staged diff or commit message would combine multiple slices;
- the active workflow version cannot be recorded;
- the checkpoint push target is not `origin/<workflow-branch>`;
- continuing would require guessing.
