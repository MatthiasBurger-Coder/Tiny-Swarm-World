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
   - belongs only to `skills-agents`;
   - runs a guarded PR lifecycle;
   - may merge the PR and clean up only after guard checks pass.

## Rules

- Do not push when required gates failed.
- Do not push when branch or remote target is unclear.
- Do not push unrelated local changes.
- Create PRs only when workflow or user request allows it.
- For slice checkpoint push, stage only current-slice files and push only to `origin/<workflow-branch>`.
- For `push auto`, stop unless the active process strand is `skills-agents`.
- `push auto` must not publish product implementation, services, contracts, Docker/runtime, build logic, frontend or analytics files.

## STOP Rules

Stop when:

- push target is unknown;
- required gate evidence is missing;
- secret or sensitive-data risk is unresolved;
- branch contains unrelated scope;
- workflow does not allow push.
- slice checkpoint push would include files outside the current slice;
- slice checkpoint push would push to `main`, create or merge a PR, run `push auto`, run branch cleanup or force-push;
- `push auto` is requested outside the `skills-agents` strand;
- `push auto` would publish backend, frontend, Docker/runtime, contracts, persistence, analysis engine, Joern, JavaParser, BTM generator or analytics implementation changes.
