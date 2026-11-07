# Performance Evidence Contract

Issue #152 defines the shared evidence format for performance-related work in
#144, #146, #147, #148 and #145. The contract is intentionally small and local:
it records measurements, but it does not run benchmarks or contact external
services.

## Record shape

Each record contains:

- `issue_id`, `workflow_id`, `segment_id` and a human-readable `segment`;
- `measurement_scope`, `target_kind` and sorted stable `target_ids`;
- a redacted `environment_summary`;
- optional timezone-aware `started_at`, `finished_at` and non-negative
  `duration_seconds`;
- optional non-negative `counters`;
- optional comparable `baseline` and `new_values` mappings; and
- explicit `limitations`.

The domain value object validates identifiers, timestamps, finite numeric
values and evidence text. It rejects raw paths, IP addresses, commands,
credentials and other unsafe evidence. Domain construction never reads the
clock or filesystem.

## Local files

`PerformanceEvidenceLocalRepository` writes one deterministic pair below the
governed ignored evidence root:

```text
.tiny-swarm/evidence/<issue-id>/<workflow-id>--<segment-id>.json
.tiny-swarm/evidence/<issue-id>/<workflow-id>--<segment-id>.md
```

The JSON projection uses sorted keys. The Markdown projection is intended for
human review and includes counters, baseline/new values and limitations. A
caller can supply a temporary or repository-specific root for tests.

## Consumer segments

| Issue | Segment | Typical measurements |
|---|---|---|
| #144 | `install-readiness-wait` | wait duration, attempts, waits, progress callbacks |
| #146 | `lxc-node-install` | per-node duration and outcome counters |
| #147 | `stack-apply-registration` | API and registration lookup counts |
| #148 | `installer-bootstrap` | file reads, subprocess probes and bootstrap duration |
| #145 | `setup-phase-group` | phase-group duration, phase count and max concurrency |

## Interpretation limits

Baseline/new values must compare like-for-like scopes. Local or mocked timing
is comparative evidence for the recorded environment; it is not a globally
absolute benchmark and is not live installation evidence. The contract does
not require Docker, Incus, LXC, Swarm, browser automation or external services.
