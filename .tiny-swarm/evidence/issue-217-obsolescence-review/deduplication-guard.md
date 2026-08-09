# Duplicate-Work and Action Guard — Issue #217

## Stable action identity

Every final issue action must use this canonical key:

```text
issue-217-20260809:<issue-number>:<decision>:ecdc71d94a72530905ecb0a41d2845921ad6debb
```

The key is derived from the workflow, issue number, canonical decision and
review baseline. It is not derived from a commit message or a mutable issue
title.

## Compare-and-set protocol

Before writing an issue, the executor must re-read the issue and compare:

1. issue number and repository;
2. state, state reason, body and `updated_at` against the Slice 01 snapshot;
3. the routing comment and duplicate/supersession relationships;
4. the canonical decision and action key;
5. the absence of a prior comment or body change carrying the same action key.

If any precondition differs, the action is not retried blindly. The result is
`REMOTE_STATE_CONFLICT`, the issue is re-audited, and no close/rewrite action is
claimed. A successful mutation must be followed by a fresh read and recorded
with the returned state and timestamp.

## Current state

No action key has been used remotely in this execution. No candidate issue was
closed, reopened, relabeled or rewritten before this guard was recorded. The
closed duplicate relationship #159/#160 is preserved.

