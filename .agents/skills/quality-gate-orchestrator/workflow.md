# Workflow

## Phase 1 - Load Quality Authority

Read `QUALITY.md` and identify:

- minimum quality command;
- full local quality gate;
- domain-specific quality expectations;
- optional diagnostic commands;
- special gates for plugins, build logic, Docker or CI.

## Phase 2 - Classify Slice

Classify changed files:

- documentation only
- skill or role governance
- source code
- tests
- build logic
- dependency verification
- CI/CD
- security-sensitive configuration

## Phase 3 - Select Checks

Choose:

- narrow targeted checks first;
- `git diff --check` for documentation and Markdown slices;
- minimum Python gate before commit-ready claims;
- full local gate before commit or push when required by workflow or broad changes;
- specialized checks when affected files require them.

## Phase 4 - Execute Or Record Exception

For each required check, record:

- exact command;
- result;
- failure summary;
- owner;
- whether failure is related to current changes;
- next action.

Required checks that cannot run need an exception report and remain blocking for commit unless governance explicitly accepts a non-commit state.

## Phase 5 - Decide

Return:

- `PASS` when required checks are clean;
- `BLOCKED` when required checks fail or cannot be verified;
- `NOT_COMMIT_READY` when checks are deferred by documented execution scope;
- `NON_BLOCKING_NOTE` only for optional, unavailable or not-applicable checks.

Map required-check decisions to `D8`. A `BLOCKED` D8 result stops commit,
checkpoint push and release readiness.

Map asynchronous execution-report findings to `Q11`. A Q11 finding is
non-blocking by default and may not downgrade a failed required check to a
non-blocking note. Regulatory or compliance reporting may block only when the
active workflow explicitly declares it as part of D8.
