---
name: workflow-conflict-resolution
description: Use when repository work may overlap with local changes, user edits, generated files, or parallel agent ownership.
---

# Conflict Resolution

## Purpose

Resolve or report overlapping changes without losing user work.

## Practices

- Inspect git status before editing.
- Verify the active workflow branch before editing.
- Treat unexpected local changes as user-owned unless proven otherwise.
- Do not revert unrelated changes.
- Assign disjoint file ownership for parallel work.
- Do not switch branches while unrelated or unclear uncommitted changes exist.
- Stop and ask when a user-owned change makes the task impossible to complete safely.

## Verification

- Review diffs for touched files.
- Confirm edits stayed on the expected workflow branch.
- Confirm no broad line-ending-only changes were introduced on Windows-hosted WSL worktrees.
