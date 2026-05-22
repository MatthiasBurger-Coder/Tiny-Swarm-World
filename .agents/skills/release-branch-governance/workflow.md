# Workflow

## Phase 1 - Verify Branch

Check:

- current branch
- branch purpose
- upstream status when relevant
- whether branch name follows repository expectations
- whether worktree contains unrelated changes

## Phase 2 - Review Changes

Inspect:

- changed files
- staged files
- untracked files
- generated files
- line-ending risk on Windows-hosted WSL worktrees

## Phase 3 - Verify Quality

Require quality result evidence from Quality Gate Orchestrator or `QUALITY.md`.

Failed required gates block commit and push.

This phase is the `D8` readiness decision for workflow-execute commit, push and
release preparation. Q11 reporting notes are non-blocking by default and must
not override a failed D8 result.

## Phase 4 - Prepare Commit Readiness

Commit readiness requires:

- scoped changed files
- complete commit message
- quality evidence
- risk notes
- rollback notes when relevant

## Phase 5 - Prepare Push Readiness

Push readiness requires:

- committed changes
- clean or explicitly governed working tree
- required quality gates passed
- remote target known
- PR or release expectations known when applicable

## Phase 6 - Decision

Return `READY_TO_COMMIT`, `READY_TO_PUSH`, `NOT_READY` or `BLOCKED`.
