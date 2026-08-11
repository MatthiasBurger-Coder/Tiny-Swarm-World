# I152-S01 Distribution

Workflow: `issue-152-20260809`
Slice: `I152-S01`
Dependency: `I197-S06` / `ae97bc2`

## Execution decision

- Execution mode: serial, per the user-requested issue order.
- Primary role: Senior Requirement Engineer.
- Fallback reviewers: Senior System Architect, Senior Python Automation
  Developer and Senior Tester; real subagent tools were not available in this
  session.
- Parallelization decision: not split. The shared schema and all consumer
  mappings are one contract lock.

## Frozen schema fields

- Identity: issue ID, workflow ID and segment ID/name.
- Scope: measurement scope, target kind and stable target IDs for single or
  future multi-node/worker contexts.
- Safe context: redacted environment/runtime summary only.
- Timing: optional ISO timestamps and non-negative duration seconds.
- Measurements: optional non-negative counters and explicit baseline/new
  value mappings.
- Limitations: explicit tuple of measurement limitations.

## Consumer lock

- #144 records readiness wait duration, attempts, waits and progress events.
- #146 records per-node duration, node outcome counters and ordered target IDs.
- #147 records stack-application duration and registration/API lookup counts.
- #148 records bootstrap duration, file reads and probe counters.
- #145 records phase-group duration, phase count and bounded concurrency.

No downstream optimization implementation is included in S01.
