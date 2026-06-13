# Push Rules

## Push Readiness

Push requires:

- committed changes;
- target branch known;
- required quality gates clean;
- no unresolved required failures;
- PR or release expectations known;
- no secrets or sensitive data in diff.

Push readiness is governed by `D8`. Failed build, tests, architecture
validation, required documentation, workflow version or required quality gates
block push readiness.

`Q11` execution reporting is non-blocking by default for normal push and PR
creation. Regulatory or compliance reporting blocks only when the active
workflow explicitly declares it as a D8 requirement.

## Publication Modes

There are three separate publication modes:

1. Slice checkpoint push
   - belongs to `workflow execute`;
   - runs after a successful slice quality gate;
   - creates a slice-scoped commit;
   - pushes the current workflow branch to `origin`;
   - does not create or merge a PR;
   - does not run branch cleanup;
   - is not `push auto`.
2. `push`
   - normal publication after explicit user approval;
   - pushes the branch and creates or updates a PR;
   - does not automatically merge.
3. `push auto`
   - applies to any task-scoped repository change, including Python product
     code and Python product-behavior tests;
   - runs a guarded commit, PR, check-loop, merge and cleanup lifecycle;
   - may merge the PR and clean up only after required checks are green,
     including SonarQube when configured.

## Parallel Workflow Publication

Parallel workflow publication handles one PR per workflow worktree. Each PR
must be tied to exactly one workflow branch, one isolated worktree and one
quality lifecycle. CI and SonarQube status are observed independently for each
PR.

Completed PRs must be merged one at a time. Before each merge, refresh the
integration branch state, check whether another workflow merged first, update
or rebase the workflow branch when repository policy requires it, rerun affected
tests, and re-check CI plus SonarQube. Do not batch-merge multiple PRs.

After a successful merge, delete only the merged PR head branch and remove a
workflow worktree only after the PR is verified merged, the integration branch
is updated locally, the worktree has no uncommitted changes, evidence is
documented, and workflow status is updated.

## Rules

- Do not push when required gates failed.
- Do not push when branch or remote target is unclear.
- Do not push unrelated local changes.
- Create PRs only when workflow or user request allows it.
- For slice checkpoint push, stage only current-slice files and push only to `origin/<workflow-branch>`.
- For `push auto`, stop unless the active change is task-scoped and free of
  unrelated, sensitive, generated local or unclassified files.
- `push auto` must create or reuse a pull request, wait or retry until required
  checks are green including SonarQube when configured, merge only after green
  checks, delete the merged remote head branch and run local cleanup.
- For parallel workflows, keep one branch, one worktree, one PR and one
  quality lifecycle per workflow.
- Re-check integration branch state and affected tests before merging each PR
  when another parallel workflow merged first.

## STOP Rules

Stop when:

- push target is unknown;
- required gate evidence is missing;
- secret or sensitive-data risk is unresolved;
- branch contains unrelated scope;
- workflow does not allow push.
- slice checkpoint push would include files outside the current slice;
- slice checkpoint push would push to `main`, create or merge a PR, run `push auto`, run branch cleanup or force-push;
- `push auto` would publish unrelated, sensitive, generated local,
  unclassified or out-of-task files;
- required checks, SonarQube status when configured, mergeability, merge
  result, remote branch deletion or local cleanup cannot be verified.
- a workflow worktree is dirty before publication or cleanup;
- a PR cannot be tied to exactly one workflow branch and worktree;
- merge order matters and cannot be determined safely;
- rebasing or updating after another parallel workflow merged creates
  conflicts or requires changes outside the workflow boundary.
