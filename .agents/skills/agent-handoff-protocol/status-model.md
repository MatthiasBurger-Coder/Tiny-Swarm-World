# Status Model

## Allowed Statuses

```text
NOT_STARTED
READY
IN_PROGRESS
BLOCKED
READY_FOR_REVIEW
CHANGES_REQUESTED
APPROVED
DONE
```

## Status Meanings

| Status | Meaning |
| --- | --- |
| `NOT_STARTED` | Slice or handoff exists but no owner has begun work. |
| `READY` | Inputs, owner and expected outputs are verified. |
| `IN_PROGRESS` | Owner is actively working within the agreed scope. |
| `BLOCKED` | Work cannot continue without input, decision, fix or architecture decision. |
| `READY_FOR_REVIEW` | Output artifacts exist and are ready for required reviewers. |
| `CHANGES_REQUESTED` | Review found issues requiring changes. |
| `APPROVED` | Required reviewers approved or documented no blockers. |
| `DONE` | Output artifacts are complete and required validation is clean or explicitly not applicable. |

## Blocker Classes

```text
REQUIRES_INPUT
REQUIRES_DECISION
REQUIRES_FIX
REQUIRES_ARCHITECTURE_DECISION
```

## Transition Rules

- `NOT_STARTED` -> `READY` only after inputs and owner are verified.
- `READY` -> `IN_PROGRESS` only when write ownership is clear.
- Any status -> `BLOCKED` when a stop condition is found.
- `IN_PROGRESS` -> `READY_FOR_REVIEW` only after output artifacts exist.
- `READY_FOR_REVIEW` -> `APPROVED` only after required review evidence exists.
- `CHANGES_REQUESTED` -> `IN_PROGRESS` only when the owner accepts a concrete fix scope.
- `APPROVED` -> `DONE` only after required validation evidence exists.
