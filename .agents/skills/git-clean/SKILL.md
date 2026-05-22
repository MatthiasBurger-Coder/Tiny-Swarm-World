---
name: git-clean
description: Use when the user enters exactly `clean`, when `push auto` needs post-merge cleanup, or when Codex is asked to clean up after a GitHub pull request was merged in the repository. Verifies the PR merge, fetches and prunes origin, switches the worktree to main, fast-forwards main, deletes only local branches proven merged and unnecessary, and reports blockers without force deletion.
---

# Clean Skill

## Goal

Clean the local Git worktree after a pull request was merged, leaving the repository on an up-to-date `main` branch with only necessary branches kept.

This skill does not replace repository rules. This skill applies `AGENTS.md`, `QUALITY.md`, and the repository Git safety rules.

## Required References

Read these files before cleanup:

```text
AGENTS.md
QUALITY.md
```

When the cleanup follows a commit, PR, or `push auto` workflow, also read the active task context and the relevant git-commit-preparation output if present.

## Command Execution Environment

Follow the command execution environment defined by `AGENTS.md` and `QUALITY.md`:

- On Windows hosts, run repository commands through WSL from the repository's WSL-mounted worktree path.
- On Linux hosts, run repository commands through native shell access.
- If WSL Git reports broad unexpected line-ending-only changes, correct the local Git EOL configuration or stop and report before deleting branches.
- Stop and report if WSL is unavailable on Windows or if the worktree cannot be reached from WSL.

## Trigger

Use this skill when the user enters exactly:

```text
clean
```

Also use it when the user explicitly asks to clean up after a merged PR.

Also use it when `.agents/skills/git-commit-preparation/SKILL.md` invokes cleanup after a successful `push auto` merge.

Do not treat Gradle's `clean` task as this workflow unless the request is about Git or PR cleanup.

## Mandatory Behavior

You must:

- verify the current worktree and branch before changing branches,
- verify that the relevant pull request was merged before deleting its branch,
- use GitHub PR metadata when the PR number or branch can be identified and GitHub access is available,
- otherwise verify that the branch tip is an ancestor of `origin/main` or `main`,
- fetch and prune remote-tracking references before deciding branch status,
- switch the worktree to `main` and fast-forward it,
- delete only local branches proven merged and unnecessary,
- keep branches with unclear ownership, unmerged commits, active worktrees, or missing merge evidence,
- report every deleted, kept, and blocked branch.

Remote branch deletion is not part of this skill unless the user explicitly requests remote deletion in addition to `clean`. The `push auto` workflow may delete the merged pull request's remote head branch before invoking this skill.

## Required Commands

Inspect:

```bash
git status --short --branch
git branch --show-current
git branch -vv
git worktree list
git fetch --prune origin
git switch main
git pull --ff-only origin main
git branch --merged main
git branch --no-merged main
```

When a candidate branch is known, verify it before deletion:

```bash
git merge-base --is-ancestor <branch> main
git merge-base --is-ancestor <branch> origin/main
git branch -d <branch>
```

Use shell-safe branch names and avoid string-built destructive commands.

## Workflow

### Phase 0: Preconditions

Confirm that `AGENTS.md` and `QUALITY.md` are readable.

Run `git status --short --branch`. Stop if the worktree has uncommitted changes, staged changes, unresolved conflicts, or unclear local modifications.

### Phase 1: Identify Cleanup Context

Identify the current branch, the recently used PR branch, and the PR number when available from the conversation, recent commit workflow, GitHub metadata, or branch tracking information.

If no PR branch or PR can be identified, continue only with safe cleanup of local branches that are already proven merged into `main`.

### Phase 2: Refresh Repository State

Run `git fetch --prune origin`.

Inspect branch status with `git branch -vv` and `git worktree list`.

Do not rely only on a disappeared remote branch as proof that a PR merged.

### Phase 3: Verify PR Merge

Prefer GitHub PR metadata when available:

- PR state must be merged,
- PR base branch must be `main`,
- PR head branch must match the branch being cleaned, when known.

If GitHub metadata is unavailable, verify merge by ancestry:

- the branch tip must be an ancestor of `origin/main` or the updated local `main`,
- or the branch must appear in `git branch --merged main` after `main` is fast-forwarded.

If the PR merge or branch ancestry cannot be verified, do not delete the branch.

### Phase 4: Switch to Main

Switch to `main` before deleting task branches:

```bash
git switch main
git pull --ff-only origin main
```

Stop if `main` is missing, checkout fails, or the fast-forward pull fails.

### Phase 5: Delete Only Safe Local Branches

Delete local branches only when all are true:

- the branch is not `main`,
- the branch is not the current branch,
- the branch is not used by another worktree,
- the branch has no unmerged commits relative to `main` or `origin/main`,
- the branch belongs to the completed task or is otherwise clearly unnecessary,
- `git branch -d <branch>` succeeds.

Never use `git branch -D` as part of this skill.

Keep and report any branch that needs force deletion, has unclear ownership, has unmerged commits, is attached to another worktree, or cannot be matched to a completed PR.

### Phase 6: Final Verification

Run:

```bash
git status --short --branch
git branch -vv
```

The final branch should be `main`, and `main` should be up to date with `origin/main` unless the repository reports a blocker.

## Output Format

Return:

```text
Cleanup readiness: READY | NOT READY | BLOCKED

PR merge status:
- <verified merged / not merged / unknown with reason>

Branch cleanup:
- <branch>: <deleted / kept / blocked and reason>

Main status:
- <branch, commit, tracking status>

Verification:
- <commands executed and results>

Remaining blockers:
- <blockers or "None">
```

## Stop Conditions

Stop if:

- `AGENTS.md` cannot be read,
- `QUALITY.md` cannot be read,
- the worktree has uncommitted changes,
- the current branch or cleanup target is unclear and deletion would require guessing,
- GitHub PR merge status cannot be verified and branch ancestry does not prove the merge,
- `main` cannot be checked out,
- `main` cannot be fast-forwarded,
- a candidate branch is used by another worktree,
- deleting a branch would require `git branch -D`,
- remote branch deletion would be needed but was not explicitly requested,
- credentials, tokens, or unrelated local files appear during cleanup.

## Forbidden Actions

Do not:

- delete `main`,
- delete the current branch,
- force-delete branches,
- delete remote branches unless explicitly requested,
- remove worktrees,
- discard uncommitted changes,
- run `git reset --hard`,
- run `git clean`,
- infer that a PR merged only because a remote branch disappeared,
- hide kept branches or blockers from the final report.

## Final Rule

Cleanup is evidence-based. If PR merge status, branch ownership, or branch ancestry cannot be proven from GitHub metadata or Git state, keep the branch and report the blocker.
