# Failure Handling

## Required Failure Report

Every failed gate report must include:

- command executed
- failing task or test
- typed router error type
- failure summary
- related changed files
- whether the failure appears related to current changes
- owner
- retry count
- next action
- rerun command

## Typed Router Classification

Workflow-execute quality and validation failures must be classified into one of
these router types before retry or escalation:

| Error type | Owner |
|---|---|
| `ARCH_VIOLATION` | Root Architect, Senior System Architect, `architecture-hexagonal` |
| `BUILD_FAILURE` | responsible Python automation, Java example or Frontend Agent, Senior DevOps, `quality-gate` for Python quality-gate failures |
| `TEST_FAILURE` | Senior Tester, responsible Slice Agent |
| `DOC_GOVERNANCE_FAILURE` | Senior Documentation Engineer, Requirement Engineer |
| `LOCK_CONFLICT` | Senior Execution Orchestrator, Senior Swarm Orchestrator, Root Architect |
| `UNKNOWN_FAILURE` | Root Architect |

`UNKNOWN_FAILURE` is a valid classification only when the cause cannot be
verified with the inspected evidence. It escalates instead of starting an
automatic fix loop.

## Failure Classification

The following classes describe causality evidence for the failure report. They
do not replace the Typed Error Router category:

- `CURRENT_CHANGE_FAILURE`: caused by the current slice.
- `PRE_EXISTING_FAILURE`: visible before or outside current slice.
- `ENVIRONMENT_FAILURE`: missing tool, lock, network or local setup issue.
- `UNKNOWN_FAILURE`: cause cannot be determined without more evidence.

## Rules

- Fix current-change failures inside the slice when safe.
- Do not hide pre-existing failures; document them and keep commit readiness blocked unless repository governance explicitly accepts the state.
- Do not downgrade required failures to warnings.
- Rerun the affected gate after fixes.
- Limit automatic targeted-fix retries to `maxRetries = 3`; then escalate.
- Do not jump from `workflow execute` back to `workflow create`.
- Stop when fixing a failure would require unrelated refactoring or guessing.
