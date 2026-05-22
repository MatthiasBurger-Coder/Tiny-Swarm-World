---
name: git-commit-message-preparation
description: Use when drafting, reviewing, or validating a current-project Git commit message from actual git status, diffs, changed-file classification, task scope, verification evidence, AGENTS.md, QUALITY.md, and git-commit-preparation output. Stops when message content would require guessing.
---

# Commit Message Preparation Skill

## Goal

Create a traceable commit message from repository evidence only.

This skill does not decide commit readiness by itself. Use it after, or together with, the git-commit-preparation skill and commit reviewer output.

## Authority

This skill specializes the message-writing part of `.agents/skills/git-commit-preparation/SKILL.md`.

`AGENTS.md` remains authoritative for agent behavior and architecture rules.

`QUALITY.md` remains authoritative for verification and quality gates.

## Required References

Read these files before drafting the final commit message:

```text
AGENTS.md
QUALITY.md
.agents/skills/git-commit-preparation/SKILL.md
active workflow.md or task-specific workflow if present
```

## Required Evidence

Use only:

- the actual staged diff,
- the actual unstaged diff when it affects commit readiness,
- the current task or issue context,
- changed-file classification,
- executed verification commands and their results,
- explicitly documented skip reasons,
- reviewer findings from the git-commit-preparation output when available.

Do not infer hidden reasons for changes.

## Command Execution Environment

Follow the command execution environment defined by `AGENTS.md` and `QUALITY.md` when inspecting Git state or verification evidence:

- On Windows hosts, run repository commands through WSL from the repository's WSL-mounted worktree path.
- On Linux hosts, run repository commands through native shell access.
- Stop and report if WSL is unavailable on Windows or if the worktree cannot be reached from WSL.

## Required Commands

Inspect:

```bash
git status --short --branch
git diff --stat
git diff
git diff --cached --stat
git diff --cached
```

For a message that will be used in a real commit, base the final message on the staged diff.

## Commit Message Template

Use this structure unless the task explicitly requires another format:

```text
<type>(<scope>): <short imperative summary>

Why:
- <reason for the change>

What:
- <main change 1>
- <main change 2>

How:
- <implementation approach>
- <important design or safety decision>

Verification:
- <command executed and result>
- <command executed and result>

Impact:
- <affected layer/component/API/schema/evidence behavior>
- <breaking changes or behavior-relevant changes, or "None">

Limitations:
- <known limitation, blocker, skipped optional check, or "None">
```

Allowed commit types:

```text
feat
fix
refactor
test
docs
build
ci
quality
agent
chore
```

## Message Rules

The title must:

- use an allowed type,
- include a concise scope,
- be imperative,
- describe the actual change.

The body must:

- explain why the change exists,
- summarize what changed,
- explain how the change was made,
- list verification commands with pass, fail, or not-executed status,
- state behavior, architecture, evidence, test, documentation, dependency, or workflow impact,
- state limitations or `None`.

Use `None` only when the diff and verification evidence support it.

For `workflow execute` slice checkpoint commits, the body must also include:

- exactly one `Slice-ID`,
- active `workflowVersion`,
- slice title,
- responsible agent or reviewed role,
- changed files,
- quality-gate commands and result,
- rollback reference,
- `arc42Updated`,
- `adrUpdated`.

Do not draft a checkpoint commit message that combines multiple slice IDs or
omits the workflow version.

## Output Format

Return:

```text
Commit message readiness: READY | NOT READY | BLOCKED

Message evidence:
- <diff, task, reviewer, or verification source used>

Missing evidence:
- <missing input or "None">

Proposed commit message:
<full commit message>
```

## Stop Conditions

Stop if:

- `AGENTS.md` cannot be read,
- `QUALITY.md` cannot be read,
- `.agents/skills/git-commit-preparation/SKILL.md` cannot be read,
- the final staged diff cannot be inspected for an actual commit,
- changed files cannot be classified,
- staged and unstaged changes conflict,
- verification evidence is missing and no explicit skip reason exists,
- sensitive data appears in the diff,
- generated artifacts appear unexpectedly,
- the type, scope, summary, impact, or limitations would require guessing.

## Forbidden Actions

Do not:

- invent verification results,
- claim tests passed without execution evidence,
- hide failed or skipped checks,
- write vague titles such as `fix stuff`, `cleanup`, `changes`, or `wip`,
- include unrelated files in the message,
- present uncertain evidence, replay, graph, LLM, or report impact as confirmed,
- stage files,
- create commits,
- push branches.

## Final Rule

The commit message must be a faithful summary of the reviewed diff and verification evidence. If the message cannot be written without guessing, return `BLOCKED`.
