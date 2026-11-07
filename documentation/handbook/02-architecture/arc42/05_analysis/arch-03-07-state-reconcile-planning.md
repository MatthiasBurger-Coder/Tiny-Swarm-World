# ARCH-03.07 — Desired State, Current State and Reconcile Planning

Status: implemented 2026-09-13

Issue: #350

## Decision

Reconciliation now has explicit domain values for `DesiredState` and
`CurrentState`. They project the existing desired and observed inventory
models into the resource categories currently used by platform reconciliation:
VMs, stacks, and artifact registries.

`ReconcilePlanner` compares those values without I/O and returns an immutable
`ReconcilePlan` containing explainable `NOOP`, `CREATE`, `UPDATE`, or `REMOVE`
actions. Ordering is stable by resource type, resource name, and action kind.
`ReconcileResult` is execution data only; plan generation does not execute or
authorize mutations.

## Compatibility

The existing Classic/platform reconcile workflow remains responsible for
execution and is unchanged in this slice. The planner is additive and can be
introduced to execution workflows in a later, separately verified change.
