# Requirement Matrix — Issue #152

Source: [GitHub Issue #152](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/152)

Status at workflow authoring: `PLANNED`.

| ID | Requirement | Type | Planned implementation area | Slice | Verification/evidence | Status |
|---|---|---|---|---|---|---|
| REQ-152-01 | A documented performance evidence contract exists. | governance | performance evidence documentation | S152-01/S152-05 | contract review | PLANNED |
| REQ-152-02 | Issues #144–#148 can use one evidence location and schema. | traceability | shared evidence path/schema | S152-02/S152-04 | cross-workflow contract checks | PLANNED |
| REQ-152-03 | Schema records workflow/issue ID, segment, environment summary, timestamps or duration, counters, baseline/new values and limitations. | observability | typed value object/schema | S152-02 | serialization tests | PLANNED |
| REQ-152-04 | A small helper or clear template records measurements without heavyweight benchmarking. | functional | helper/adapter/template | S152-03 | helper tests and diff review | PLANNED |
| REQ-152-05 | Contract supports single-computer and future multi-node/worker flows. | scalability | schema dimensions | S152-02/S152-03 | fixture coverage | PLANNED |
| REQ-152-06 | Measurements do not require external services and state environment limitations. | safety/evidence | docs and local writer | S152-03/S152-05 | static documentation check | PLANNED |
| REQ-152-07 | Tests cover stable serialization/template rendering and missing optional values. | quality gate | unit tests | S152-05 | targeted unittest | PLANNED |
| REQ-152-08 | Documentation explains baseline/new comparison without treating local timing as globally absolute. | documentation | performance evidence guide | S152-05 | doc review | PLANNED |
| REQ-152-09 | The issue does not implement the #144–#148 optimizations itself. | non-goal | workflow scope | S152-01/S152-06 | changed-files audit | PLANNED |

## Shared performance evidence schema v1

The implementation slices use one small, local and Git-friendly schema. Every
record carries `issue_id`, `workflow_id`, `segment_id`, `segment`,
`measurement_scope`, `target_kind`, sorted `target_ids`, a redacted
`environment_summary`, optional caller-supplied `started_at`/`finished_at`,
optional finite non-negative `duration_seconds`, optional sorted `counters`,
optional sorted `baseline` and `new_values`, and explicit `limitations`.

The schema supports a single computer through one target ID and future
multi-node/worker or phase-group measurements through multiple stable target
IDs. It does not read the clock, execute commands, call external services or
store raw host identity, paths, IP addresses, credentials or command output.
Local and mocked timings are comparative evidence only and are never treated
as globally absolute benchmarks.

Consumer segment mapping:

| Consumer | Segment | Measurement focus |
|---|---|---|
| #144 | `install-readiness-wait` | wait duration, attempts, waits, progress callbacks |
| #146 | `lxc-node-install` | per-node duration, outcomes and stable target IDs |
| #147 | `stack-apply-registration` | API/registration lookup counts and baseline/new values |
| #148 | `installer-bootstrap` | file reads, subprocess probes and bootstrap duration |
| #145 | `setup-phase-group` | phase-group duration, phase count and max concurrency |
