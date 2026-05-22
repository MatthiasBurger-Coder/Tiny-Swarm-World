# Workflow

## Phase 1 - Identify Observability Scope

Check whether the slice affects:

- external requests
- service-to-service calls
- workers
- analysis runs
- runtime sessions
- incident replay
- logging
- metrics
- stored diagnostics

## Phase 2 - Verify Context Fields

Require relevant fields from `trace-context-rules.md`.

Missing fields must be explicit as not applicable, unavailable or unresolved. Do not fabricate identifiers.

## Phase 3 - Review Logging

Verify:

- structured fields;
- safe redaction;
- no secrets;
- no unnecessary source or trace payloads;
- error logs include correlation context.

## Phase 4 - Review Metrics

Verify:

- service or worker health signals;
- queue or job lifecycle signals when applicable;
- failure counters;
- latency or duration metrics;
- cardinality controls.

## Phase 5 - Decide

Return `APPROVED`, `CHANGES_REQUESTED` or `BLOCKED`.

Unresolved correlation, sensitive logging or runtime identity issues are blocking.
