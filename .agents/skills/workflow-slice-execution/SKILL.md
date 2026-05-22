---
name: workflow-slice-execution
description: "Use for current-project slice execution: read-only verification, minimal implementation, targeted tests, quality gate, and final summary."
---

# Slice Execution

## Purpose

Execute small, traceable implementation increments.

## Practices

1. Read-only verification.
2. Slice plan with affected files and quality checks.
3. Verify that the active branch belongs to the current workflow and is not `main`, `master`, `develop`, or another shared branch.
4. Minimal implementation.
5. Targeted tests.
6. Applicable quality gate from `QUALITY.md`.
7. Documentation update when public behavior changes.
8. Clear final summary with commands executed.

## Stop Conditions

- Required symbols, tasks, files or contracts cannot be verified.
- Documentation and source disagree in a behavior-relevant way.
- The active branch is not the expected workflow branch.
- The slice would modify files on `main`, `master`, `develop`, or another shared branch.
- Continuing would require fabricating evidence or guessing semantics.
