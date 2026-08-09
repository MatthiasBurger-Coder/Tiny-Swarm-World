# Issue #188 — S04 Distribution Decision

- Workflow: `issue-188-20260809` / `issue-188-v1.0.0`
- Slice: `S04` — Migrate the existing LXC manager shell gateway
- Execution mode: `sequential`
- Real subagents: not available; no parallel stream created
- Owner roles: Senior Python Automation Developer, Senior System Architect,
  Senior Tester, Senior Security Sandbox Engineer

## Scope

- Use the injected shared runner when the gateway is composed normally.
- Preserve the verified operation-time callback as a direct-test compatibility
  seam.
- Preserve Incus/LXD command composition, manager/node selection, retry policy,
  timeout mapping, safe logging, and gateway-owned error wording.

## Safety and locks

- No live Incus, LXC, Docker, Swarm, or credential-backed command.
- No second gateway and no application/domain port change.
- S02 runner contract and `LxcSwarmRuntime` delegation seam are prerequisites.

## Verification plan

- Focused manager gateway unittest suite, including default injection and
  legacy callback compatibility.
- `python3 tools/quality_gate.py lint`.
- `python3 tools/quality_gate.py typecheck`.
- `git diff --check`.

The final repository-wide quality gate is recorded in S08 and is green after
the Arc42 governing hash was synchronized.
