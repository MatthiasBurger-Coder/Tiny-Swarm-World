---
name: git-commit-preparation
description: Use when preparing, reviewing, validating, repairing, committing, pushing, creating a PR, running workflow-execute slice checkpoint pushes, or running `push auto` for task-scoped repository changes including Python product code. This skill is the commit-readiness workflow and enforces AGENTS.md, QUALITY.md, git diff inspection, task-scope validation, quality-gate verification, blocker routing, git-commit-message-preparation, PR creation on explicit `push`, and commit, PR, green required-checks, SonarQube when configured, merge plus branch cleanup on explicit `push auto`.
---

# Commit Preparation Skill

## Goal

Prepare, review, repair, commit, push, and open a pull request for the current project changes without weakening repository rules, mixing unrelated changes, or claiming unexecuted verification.

This `SKILL.md` is the single source for the git-commit-preparation workflow. The previous standalone workflow content is consolidated here.

This skill does not replace repository rules. This skill applies repository rules.

`AGENTS.md` remains the source of truth for agent behavior, architecture rules, safety rules, and documentation ownership.

`QUALITY.md` remains the source of truth for quality gates, verification commands, coverage, dependency verification, and failure policy.

## Role Split

Use this skill with these Codex roles:

- `git-commit-message-preparation`: reusable skill for drafting and validating the proposed commit message from diff and verification evidence.
- `git_commit_reviewer`: read-only reviewer that classifies changes, checks scope, verifies evidence, and returns `READY`, `NOT READY`, or `BLOCKED`.
- `git_commit_operator`: mutating operator that may stage explicit files, commit, push, create or complete a GitHub pull request, or run a workflow-execute slice checkpoint push only when the contract allows it. On exact `push auto` for a task-scoped change, it may also wait or retry until required checks are green including SonarQube when configured, merge the verified pull request, delete the merged pull request's remote head branch, and invoke the git-clean workflow.

The reviewer must not modify files. The operator must not bypass the reviewer result, required verification, branch rules, or the `push` command requirement.

## Required References

Read these files before deciding commit readiness:

```text
AGENTS.md
QUALITY.md
.agents/skills/git-commit-preparation/SKILL.md
.agents/skills/git-commit-message-preparation/SKILL.md
.codex/agents/git_commit_reviewer.toml
active workflow.md or task-specific workflow if present
```

When commit, push, or pull-request execution is requested, also read:

```text
.codex/agents/git_commit_operator.toml
```

When the user enters exactly `push auto`, also read:

```text
.agents/skills/git-clean/SKILL.md
```

If any required reference cannot be read, stop and report the missing file.

## Command Execution Environment

Follow the command execution environment defined by `AGENTS.md` and `QUALITY.md`:

- On Windows hosts, run repository commands through WSL from the repository's WSL-mounted worktree path.
- On Linux hosts, run repository commands through native shell access.
- Use the Linux-style Python quality commands documented in this skill and in `QUALITY.md`.
- If WSL Git reports broad unexpected line-ending-only changes, correct the local Git EOL configuration or stop and report before staging, committing, pushing, or reviewing commit readiness.
- If WSL is unavailable on a Windows host, or if the worktree cannot be reached from WSL, stop and report instead of silently using Windows-native commands.

## When to Use This Skill

Use this skill when:

- preparing a commit,
- reviewing staged or unstaged changes,
- validating commit readiness,
- writing a commit message,
- checking whether changed files belong to a task,
- documenting verification evidence before commit,
- acting on exact `push`,
- acting on exact `push auto`.
- running a workflow-execute slice checkpoint push.

When only drafting or validating the commit message, use `.agents/skills/git-commit-message-preparation/SKILL.md`.

## Branch Handling Rule

Always verify the current branch before staging, committing, pushing, creating a pull request, merging a pull request, deleting a remote branch, or running cleanup.

If the current branch is `main`, create the branch required by the active process strand before continuing with commit preparation or publication. This prevents `push` and `push auto` from stopping only because the work started on `main`, while keeping branch names aligned with repository governance.

The branch matrix rule is mandatory:

1. Inspect the current branch with `git status --short --branch` or `git branch --show-current`.
2. When the branch is exactly `main`, identify the active strand: `skills update`, `workflow create`, `workflow execute`, exact `push`, exact `push auto`, or ad-hoc implementation.
3. Create the non-`main` branch required by `documentation/process/branch-governance.md`.
4. If the branch name already exists, choose the next clear unique suffix after checking local and remote branch names.
5. Preserve existing unstaged or staged task changes when switching to the new branch.
6. Rerun `git status --short --branch` after branch creation and continue only from the new branch.

Do not create a generic `work/<task-slug>` branch when a process strand or active workflow branch rule applies.

Stop and report only when the required branch cannot be created, the branch state is detached or unclear, the branch name would collide with unrelated work, the active strand cannot be determined, or switching branches would risk losing local changes.

Never push directly to `main`.

## Workflow

### Phase 0: Preconditions

Verify the intended worktree, branch, task scope, repository rules, and local change ownership.

Apply the branch handling rule before any staging, commit, push, pull-request, merge, remote-branch deletion, or cleanup action.

Stop when the branch, worktree, task, or ownership of local changes is unclear.

Do not commit while detached.

Do not modify unrelated files.

Do not stage or commit generated output, local runtime data, credentials, tokens, or IDE metadata.

### Phase 1: Read Repository Rules

Read, in order:

```text
1. AGENTS.md
2. QUALITY.md
3. .agents/skills/git-commit-preparation/SKILL.md
4. .agents/skills/git-commit-message-preparation/SKILL.md
5. .codex/agents/git_commit_reviewer.toml
6. .codex/agents/git_commit_operator.toml when mutating execution is requested
7. .agents/skills/git-clean/SKILL.md when `push auto` is requested
```

Also read the active `workflow.md` or task-specific workflow if present.

Do not rely on remembered commands, package names, quality tasks, quality rules, or architecture boundaries.

### Phase 2: Inspect Git State

Inspect:

```bash
git status --short --branch
git diff --stat
git diff
git diff --cached --stat
git diff --cached
```

Inspect staged and unstaged changes separately.

### Phase 3: Classify Changed Files

Classify every changed file by purpose, ownership, and task relevance.

Unexpected, unrelated, sensitive, generated, or unclassified files block commit readiness.

### Phase 4: Scope Review

Verify why each file changed, which task requirement caused the change, and whether behavior, API, schema, evidence, graph, replay, LLM, report, test, dependency, documentation, or workflow semantics are affected.

### Phase 5: Run Commit Reviewer

Ask the `git_commit_reviewer` worker/subagent to perform a read-only commit-readiness review when subagents are explicitly authorized or the active workflow requires that role.

The reviewer must:

- read `AGENTS.md`, `QUALITY.md`, `.agents/skills/git-commit-preparation/SKILL.md`, and `.agents/skills/git-commit-message-preparation/SKILL.md`,
- inspect status and diffs,
- classify every changed file,
- check task scope,
- check verification evidence,
- check branch eligibility for `push` or `push auto` when requested,
- return the output contract defined in this skill.

The reviewer must not modify files, stage files, create commits, push branches, create pull requests, merge pull requests, or delete branches.

If subagents are not explicitly authorized, reproduce the same read-only review locally before mutating Git state.

### Phase 6: Review Findings And Route Blockers

Review the commit-readiness output.

If readiness is `BLOCKED`, stop and report the blocker.

If readiness is `NOT READY`, fix only clear, in-scope blockers or stop and report why the fixes cannot be made safely.

Do not continue while unrelated files, sensitive data, generated artifacts, or unclassified files remain.

When a blocker is clear and in scope, route it to the appropriate role:

- implementation defects: `implementation_worker`
- tests, coverage, dependency verification, or build failures: `quality_reviewer` or `quality_archunit_reviewer`
- documentation inconsistencies: `documentation_reviewer`
- architecture boundary risks: `architecture_reviewer`
- security, credentials, tokens, or sensitive data: `security_reviewer`
- static source-analysis risks: `source_analysis_reviewer`
- ingestion or handoff risks: `ingestion_handoff_reviewer`
- Joern semantic artifact risks: `joern_semantics_reviewer`
- persistence or deterministic artifact risks: `analytics_persistence_reviewer`
- replay, graph, reporting, or LLM evidence-package risks: `replay_graph_llm_reviewer`
- commit-message defects: `git-commit-message-preparation`

After repair, rerun the commit-readiness review.

Do not repair speculative, out-of-scope, or unclear blockers. Report those instead.

### Phase 7: Run Required Verification

Use `QUALITY.md` for exact commands.

Run the narrowest meaningful verification first when applicable, then the required quality gate when practical.

The current minimum Python quality command is:

```bash
python3 tools/quality_gate.py test
```

The current full local quality gate is:

```bash
python3 tools/quality_gate.py quality
```

For documentation-only and agent-instruction-only changes, run the minimum quality command when practical. If it is skipped, report the reason and do not claim it passed.

Do not claim a command passed unless it actually passed.

### Phase 8: Stage Explicit Files

Stage only exact task-related files after the final diff has been reviewed.

Do not stage:

- unrelated files,
- generated build output,
- `.gradle/`,
- `build/`,
- IDE workspace metadata,
- temporary logs,
- local databases,
- local trace dumps,
- credentials, tokens,
- private local configuration,
- generated reports unless explicitly required.

### Phase 9: Final Diff Review

After staging, inspect:

```bash
git diff --cached --stat
git diff --cached
```

Review the staged diff before committing.

### Phase 10: Prepare Commit Message

Use `.agents/skills/git-commit-message-preparation/SKILL.md`.

The final message must come from the staged diff, task scope, reviewer findings, and executed verification evidence.

Do not invent verification, affected components, risks, limitations, type, scope, or impact.

### Phase 11: Commit Decision

Create a commit only when:

- commit readiness is `READY`,
- required verification passed or has an acceptable documented skip reason,
- no unstaged changes remain,
- all staged files are in scope,
- the staged diff was reviewed,
- the commit message is traceable,
- the user or active workflow permits committing.

Do not push or create a pull request during this phase unless the user also entered exactly `push`, entered exactly `push auto`, the active workflow reached a workflow-execute slice checkpoint push, or the user explicitly requested publication.

### Workflow Execute Slice Checkpoint Push

When `workflow execute` reaches a successful slice checkpoint, treat it as permission to:

1. inspect the slice diff and staged diff,
2. stage only files changed by the current slice,
3. run `git diff --cached --check`,
4. create the slice-scoped checkpoint commit,
5. push `HEAD` only to `origin/<workflow-branch>`,
6. record the commit SHA and push result in the execution report.

The slice checkpoint push belongs to `workflow execute` and may run only after a slice quality gate passed, the staged diff contains only current-slice files, the commit is created on the workflow branch, and the push target is `origin/<workflow-branch>`.

It does not create or merge a PR, does not clean up branches and must not force-push.

Do not create a pull request, merge a pull request, delete remote branches, delete local branches, run git-clean, push to `main`, run `push auto`, or force-push.

The required commit-readiness decision is `D8` for workflow-execute checkpoint
commits. D8 blocks commit and push when build, tests, architecture validation,
required documentation, workflow version or a required quality gate fails or is
missing. Q11 execution-report notes are non-blocking by default and must not be
used to approve a failed D8 result.

For workflow-execute checkpoint commits:

- commit exactly one slice;
- include exactly one `sliceId` and the active `workflowVersion`;
- require a `CP_RECORD` with changed files, quality-gate commands,
  quality-gate result, rollback reference, arc42 update status and ADR update
  status;
- record the actual commit hash after `CP_COMMIT` succeeds;
- stop when staged files or the commit message would mix multiple slices.

### Phase 12: Push Command And GitHub Pull Request

When the user enters exactly `push`, treat it as explicit permission to:

1. rerun commit readiness,
2. apply the branch handling rule,
3. obtain or reproduce a `git_commit_reviewer` readiness result,
4. create the commit from the reviewed staged diff,
5. push the current non-`main` branch to `origin`,
6. create or complete a GitHub pull request from the current branch against `main`.

Before pushing, verify:

- the current branch is not `main`; if it is `main`, create a work branch first,
- the current branch and upstream state are clear,
- no unstaged changes exist,
- commit readiness is `READY`,
- required verification passed,
- `origin/main` exists after fetching from `origin`,
- GitHub access is available,
- no duplicate open pull request will be created for the same branch and base,
- `git_commit_operator` is the role performing the mutating Git and GitHub actions when a mutating subagent workflow is used.

The pull request must target `main`.

The pull request title must come from the final commit message title.

The pull request body must include:

- summary,
- changed files or areas,
- verification commands and results,
- impact,
- risks and limitations,
- explicit note that no push to `main` or merge was performed.

Do not treat `push` as permission to force-push, push to `main`, merge a pull request, enable auto-merge, skip verification, or create a pull request against another base branch.

If an open pull request already exists for the current branch against `main`, reuse it instead of creating a duplicate.

### Phase 13: Push Auto Check Loop, Merge, Branch Deletion, And Cleanup

When the user enters exactly `push auto`, treat it as explicit permission to run the normal `push` workflow and then automatically finish the GitHub pull request lifecycle for the active task-scoped change, including Python product code and Python product-behavior tests.

`push auto` must not publish unrelated changes, sensitive files, generated local artifacts, credentials, or files that cannot be classified as part of the active task.

Execute this order:

1. Rerun commit readiness and verification.
2. Apply the branch handling rule.
3. Create the commit from the reviewed staged diff.
4. Push the current non-`main` branch to `origin`.
5. Create or reuse a GitHub pull request from the current branch against `main`.
6. Verify that the pull request head branch matches the current branch and the base branch is `main`.
7. Wait, refresh, or retry the required PR checks until they are successful. This includes SonarQube or SonarCloud checks when configured for the pull request.
8. If checks fail because of an in-scope defect that can be safely fixed, repair the defect, commit the fix, push the branch, and repeat the required-check loop.
9. Stop if checks remain failed, pending indefinitely, missing, unknown, unverifiable, or require out-of-scope or unsafe changes.
10. Verify that GitHub reports the pull request as mergeable and that all required checks are successful, or that no required checks are configured.
11. Merge the pull request through GitHub.
12. Re-fetch the pull request and verify `merged: true` before any branch deletion.
13. Delete only the merged pull request's remote head branch.
14. Run `.agents/skills/git-clean/SKILL.md` to switch to `main`, fast-forward it, and delete the local merged branch.
15. Report the merge commit, required-check and SonarQube status, remote branch deletion result, clean result, and final `main` status.

For `push auto`, the pull request body must include the same content as the `push` workflow plus an explicit note that the workflow intends to wait or retry until required checks are green including SonarQube when configured, merge the PR, delete the merged PR head branch, and run clean after merge verification.

Do not treat `push auto` as permission to force-push, push directly to `main`, retarget the pull request, bypass failed or pending checks, merge an unrelated pull request, delete `main`, delete a branch before the pull request is verified as merged, or enable GitHub auto-merge.

If the diff contains unrelated, sensitive, generated local, unclassified, or out-of-task files, stop and report the exact blocker.

If GitHub mergeability, required-check status, SonarQube status when configured, merge result, remote branch deletion, or clean execution cannot be verified, stop and report the exact blocker.

## Required Commands

Run or inspect output from:

```bash
git status --short --branch
git diff --stat
git diff
git diff --cached --stat
git diff --cached
```

For `push` and `push auto`, also verify the current branch and `origin/main`.

For `push auto`, also verify the relevant GitHub pull request state and run the command required by the git-clean skill after the merge.

Use the minimum and full quality commands documented in `QUALITY.md` when verification is required and practical.

## Required Execution Order

```text
1. Read AGENTS.md
2. Read QUALITY.md
3. Read .agents/skills/git-commit-preparation/SKILL.md
4. Read .agents/skills/git-commit-message-preparation/SKILL.md
5. Read .codex/agents/git_commit_reviewer.toml
6. Read .codex/agents/git_commit_operator.toml when mutating execution is requested
7. Read .agents/skills/git-clean/SKILL.md when `push auto` is requested
8. Inspect branch, git status, and diffs
9. If the branch is main, create the branch required by the active strand before staging, committing, pushing, or running push auto
10. Ask git_commit_reviewer to review commit readiness, or reproduce the same read-only review locally when subagents are not explicitly authorized
11. Route only clear, in-scope blockers to the appropriate repair role
12. Rerun commit-readiness review after repairs
13. Run required verification from QUALITY.md
14. Inspect final staged diff
15. Prepare commit message with git-commit-message-preparation
16. Use git_commit_operator to commit only if all required gates pass and user/task permits committing
17. On a workflow-execute slice checkpoint, use git_commit_operator to stage only current-slice files, commit, push only to origin/<workflow-branch>, and record the SHA and push result
18. On `push`, use git_commit_operator to push the branch and create or complete a GitHub pull request against main
19. On `push auto`, use git_commit_operator for the task-scoped change to push, create or reuse the PR, wait or retry until required checks are green including SonarQube when configured, verify mergeability, merge the PR, verify merged state, delete the remote head branch, and run clean
```

## Commit Message Contract

Use `.agents/skills/git-commit-message-preparation/SKILL.md` to draft or validate the proposed commit message.

Do not invent verification, affected components, risks, limitations, type, scope, or impact.

## Output Format

Return exactly this structure:

```text
Commit readiness: READY | NOT READY | BLOCKED

Changed files:
- <file>: <reason for change>

Scope assessment:
- <in scope / out of scope findings>

Verification:
- <commands executed>
- <pass/fail/not executed with reason>

Risks:
- <behavior, architecture, evidence, test, documentation, or dependency risks>

Required fixes before commit:
- <fixes or "None">

Recommended remediation:
- <role or skill to address each blocker, or "None">

Proposed commit message:
<full commit message>
```

## Stop Conditions

Stop if:

- `AGENTS.md` cannot be read,
- `QUALITY.md` cannot be read,
- `.agents/skills/git-commit-message-preparation/SKILL.md` cannot be read when drafting the commit message,
- `.agents/skills/git-clean/SKILL.md` cannot be read when the user enters `push auto`,
- `.codex/agents/git_commit_operator.toml` cannot be read when commit, push, or pull-request execution is requested,
- branch or worktree is unclear,
- the worktree is detached,
- the current branch is `main` and a work branch cannot be created safely,
- staged and unstaged changes conflict,
- unexpected files exist,
- files cannot be classified,
- unrelated files are present,
- generated artifacts appear unexpectedly,
- sensitive data appears in the diff,
- required quality gates fail,
- quality gates were skipped without justification,
- the commit reviewer returns `NOT READY` or `BLOCKED`,
- the commit message would require guessing,
- the user requested `push` but GitHub pull request creation is unavailable or would require guessing,
- a workflow-execute slice checkpoint contains files outside the current slice or targets anything other than `origin/<workflow-branch>`,
- `push auto` would publish unrelated, sensitive, generated local, unclassified, or out-of-task files,
- the user requested `push auto` but mergeability, required-check status, SonarQube status when configured, merge result, remote branch deletion target, or clean execution cannot be verified.

## Forbidden Actions

Do not:

- modify files while acting as a commit reviewer,
- stage files without explicit git-commit-preparation authority,
- create commits unless the user or active workflow permits committing,
- push or create pull requests unless the user enters `push`, enters `push auto`, the active workflow reaches a workflow-execute slice checkpoint, or explicitly requests that action,
- push directly to `main`,
- merge pull requests unless the user enters exactly `push auto`, the diff is task-scoped, and all required checks including SonarQube when configured are green,
- delete remote branches unless the user enters exactly `push auto`, the diff is task-scoped, all required checks including SonarQube when configured are green, and the pull request was verified as merged,
- delete local branches directly instead of using the git-clean workflow after push auto,
- force-push,
- enable GitHub auto-merge,
- retarget the pull request away from `main`,
- commit unrelated files,
- commit generated build output,
- commit `.gradle/`,
- commit `build/`,
- commit IDE workspace metadata,
- commit temporary logs,
- commit local databases,
- commit local trace dumps,
- commit credentials or tokens,
- bypass failed verification,
- bypass failed, pending, or unknown required checks,
- claim tests passed without execution evidence,
- approve a commit when required quality gates fail.

## Final Rule

Commit readiness is evidence-based. If scope, verification, file ownership, branch safety, or commit-message content cannot be proven from repository state and executed commands, return `BLOCKED` or `NOT READY` instead of guessing.
