---
name: release-branch-governance
description: Use for branch, commit, push, rollback and release-readiness governance tied to workflow slices, quality gates and git commit preparation rules.
---

# Skill: Release And Branch Governance

## Mission

Keep branch, commit, push and rollback decisions traceable to workflow scope, changed files, quality evidence and repository git governance.

This skill governs release readiness. It does not stage, commit, push or merge by itself.

## Responsibilities

- Verify workflow branch context before workflow creation, commit or push.
- Require commit messages to explain summary, why, what changed, validation and risks.
- Require successful required quality gates before commit and push.
- Keep workflow slices commit-sized and rollback-aware.
- Distinguish commit readiness from push readiness.
- Route commit operations through git governance skills.
- Prevent unrelated dirty-worktree changes from being included silently.

## Authority

Release & Branch Governance may block workflow branch readiness, commit, push or release readiness when branch context, changed-file ownership, quality evidence or commit message content is incomplete.

## D8 And Q11 Boundary

`D8` is the synchronous gate for commit, push and release readiness. Failed
builds, failed tests, architecture violations, missing required documentation,
missing workflow version and failed required quality gates block readiness.

`Q11` is the asynchronous execution report path. Q11 does not block commit,
push, PR creation or release preparation by default. Regulatory or compliance
reporting blocks only when the active workflow explicitly declares that report
as a D8 requirement.

## Forbidden

- Do not commit without required quality gate evidence.
- Do not push with unresolved required failures.
- Do not stage unrelated user-owned changes.
- Do not use vague commit messages.
- Do not create rollback claims without a clear rollback point.
- Do not force-push or rewrite history unless explicitly requested and governed.

## Inputs

- active workflow
- `git status --short`
- relevant diffs
- quality result reports
- git governance skills
- branch naming rules
- commit message draft
- PR or release readiness requirements when applicable

## Outputs

- branch readiness report
- workflow branch readiness report
- commit readiness report
- push readiness report
- rollback notes
- release readiness template output

## Collaboration Rules

- Use `git-branch-strategy` for branch isolation and staged-file review.
- Use `git-commit-preparation` for commit readiness and staging.
- Use `git-commit-message-preparation` for commit messages.
- Use `quality-gate-orchestrator` before commit or push.
- Use `workflow-conflict-resolution` when local changes overlap.
- Use Senior DevOps for CI, release or deployment concerns.

## STOP Rules

Stop and report when:

- branch context is unclear;
- required quality gates have not passed;
- commit message is incomplete;
- unrelated changes would be staged;
- push is planned despite unresolved failures;
- rollback point is unclear for risky changes;
- continuing would require guessing changed-file ownership.
