# Issue #188 — S05 Distribution Decision

- Workflow: `issue-188-20260809` / `issue-188-v1.0.0`
- Slice: `S05` — Migrate LXC Docker/container access
- Execution mode: `sequential`
- Real subagents: not available; no parallel stream created
- Owner roles: Senior Python Automation Developer, Senior System Architect,
  Senior Tester

## Scope

- Route `LxcContainerRuntime` Docker-inside-LXC calls through the injected
  shared runner.
- Preserve multi-node discovery, node-qualified references, command mapping,
  timeout behavior, exit-code behavior, and `PortContainerRuntime` semantics.

## Safety and locks

- No live Incus/LXC/Docker/Swarm command.
- No change to Issue #189 backend CLI mapping or application ports.
- The shared runner contract from S02 is consumed without modification.

## Verification plan

- Focused LXC container runtime tests, including node qualification and
  timeout/failure behavior.
- `python3 tools/quality_gate.py lint`.
- `python3 tools/quality_gate.py typecheck`.
- `git diff --check`.

The final repository-wide quality gate is recorded in S08 and is green after
the Arc42 governing hash was synchronized.
