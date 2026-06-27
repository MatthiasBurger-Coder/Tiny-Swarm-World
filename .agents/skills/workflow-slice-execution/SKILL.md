---
name: workflow-slice-execution
description: "Use for current-project slice execution: read-only verification, minimal implementation, targeted tests, quality gate, and final summary."
---

# Slice Execution

## Purpose

Execute small, traceable implementation increments.

## Practices

1. Read-only verification.
2. Read `documentation/process/issue-completion-discipline.md` for
   issue-driven slices.
3. Create or verify the requirement matrix before implementation.
4. Slice plan with affected files and quality checks.
5. Verify that the active branch belongs to the current workflow and is not `main`, `master`, `develop`, or another shared branch.
6. Minimal complete implementation for every mapped requirement.
7. Targeted tests.
8. Applicable quality gate from `QUALITY.md`.
9. Documentation update when public behavior changes.
10. Required evidence under `.tiny-swarm/evidence/<workflow-or-issue-id>/`
    for issue-driven work.
11. `issue-completion-auditor` review before any `DONE` claim.
12. Clear final summary with commands executed, requirement status, evidence
    paths and open risks.

## Definition of Done

Use `DONE` only when every requirement from the slice or issue has
implementation evidence, verification evidence, local validation and required
evidence files. If any requirement is open or unverified, report `INCOMPLETE`
or `BLOCKED`.

## No Silent Scope Reduction

Do not implement only the easy parts, replace behavior with TODOs, claim
scaffolding as completion, skip evidence, or change unrelated behavior to make
checks pass.

## Stop Conditions

- Required symbols, tasks, files or contracts cannot be verified.
- The requirement matrix is missing or incomplete before implementation.
- Documentation and source disagree in a behavior-relevant way.
- The active branch is not the expected workflow branch.
- The slice would modify files on `main`, `master`, `develop`, or another shared branch.
- Required evidence or `issue-completion-auditor` review is missing before a
  `DONE` claim.
- Continuing would require fabricating evidence or guessing semantics.
