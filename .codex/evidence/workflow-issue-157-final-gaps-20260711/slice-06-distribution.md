# Slice 06 Distribution Decision

Workflow ID: `workflow-issue-157-final-gaps-20260711`

Workflow version: `workflow-issue-157-final-gaps-v1.0.0`

Slice ID: `06`

Title: `Guarded Publication, PR Checks And Review Fixing Loop`

## Dependency And Branch Gate

- Slice 05 checkpoint: `f7db32ea59b00d3fdc6158abb56d00c6ec65831e`.
- Remote workflow branch resolves to the same commit.
- Slice 05 pre-publication audit: `PASS`.
- All requested local gates: `PASS`; final test/quality result is 1,361 run,
  1,333 passed, and 28 skipped.
- Integration worktree is clean and remains on
  `fix/issue-157-final-gaps-20260711`.
- GitHub CLI authentication and SSH publication are available.
- No existing open PR from this branch to `main` was found before execution.

Decision: `EXECUTION_PLAN`.

## Execution And Ownership

- Execution mode: serialized `G4` external publication.
- Mutating owner: Root Codex acting under Git Commit Operator governance.
- Independent read-only owners: Git Commit Reviewer, Senior Tester, and final
  Issue Completion Auditor.
- Real subagents are used; no role-based fallback is required.

## Locks And Safety

Only the seven Slice 06 workflow-evidence files may change. Product, tests,
configuration, workflow definition, arc42, ADRs, CI, and live environment files
are read-only unless a concrete in-scope CI or review defect requires the
original owning slice lock to be reacquired.

Contract locks:

- push only the workflow branch; never push or commit directly to `main`;
- no force-push, automatic merge, branch deletion, or cleanup;
- create or reuse one PR targeting `main`;
- inspect every PR check, the configured `Python Quality And SonarCloud` job,
  mergeability, and thread-aware review state;
- route any concrete failure through the Typed Error Router and rerun local
  quality after an in-scope repair;
- keep Live Selenium `NOT_RUN` without current consent and approved
  prerequisites;
- never record pending, unknown, or stale external state as successful.

## Execution Plan

1. Create the PR from the already-pushed workflow branch to `main`.
2. Inspect the PR metadata, mergeability, required checks, SonarCloud step, and
   review threads on the current head.
3. Repair only concrete in-scope failures in their original slice locks.
4. Update the allowed Slice 06 evidence with observed PR/check/review state.
5. Run `git diff --check` and the required local `quality` gate.
6. Obtain commit readiness, create one Slice 06 evidence checkpoint, and push
   the workflow branch.
7. Reinspect the final PR head until checks are green and actionable review
   comments are resolved; record final external verification in the handoff.

The committed evidence records only observations available before its own
checkpoint. Final-head GitHub checks remain externally authoritative because
the evidence commit itself triggers a new CI run.
