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
