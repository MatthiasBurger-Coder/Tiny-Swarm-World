# Issue #218 — Read-only verify evidence

Date: 2026-08-04

## Commands

The following were run as separate commands with their own exit codes:

- `deployment verify`: exit `0`
- `platform verify`: exit `0`
- `host verify`: exit `0`

`host verify` collected bounded, read-only records for process table,
`pgrep`, Docker services/tasks/stacks/log tails, Incus containers, cgroup
memory files and network state. The diagnostic path has no provider,
deployment, firewall, portproxy, DNS or hosts-file mutation operation.

## Strict elevated before/after comparison

The Windows bridge service was stopped before the snapshot so its heartbeat
could not rewrite volatile metadata during the Verify calls. It was restarted
automatically in the `finally` path after the comparison.

- `deployment verify`: exit `0`
- `platform verify`: exit `0`
- `portproxy`: equal before/after, including managed and foreign tuples
- managed Firewall rules: equal before/after
- managed Windows hosts block: equal before/after
- protected `bridge-state.json` SHA-256: equal before/after
- Incus container and Docker stack/service/config/secret metadata: equal

Strict result: **PASS** (`stable_snapshot_equal=True`).

## Earlier comparison

- WSL snapshot before/after separate deployment/platform verify: equal.
- Incus/Docker service topology, stack list, config metadata and secret metadata:
  unchanged by the verify commands.
- Windows stable snapshot: no portproxy, managed-firewall or managed-hosts
  difference; bridge discovery remained ready with no drift.
- An earlier raw whole-file comparison changed because the independently
  running service heartbeat rewrote volatile `generatedAt` and `action`
  fields. The strict quiesced comparison above removes that race.

## Decision

The tested Verify paths are **PASS** for all compared managed state. No Verify
call mutated the Windows bridge, Incus state or Docker metadata.
