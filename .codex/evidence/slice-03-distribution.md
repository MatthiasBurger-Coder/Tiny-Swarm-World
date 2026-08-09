# Issue #188 — S03 Distribution Decision

- Workflow: `issue-188-20260809` / `issue-188-v1.0.0`
- Slice: `S03` — Migrate Docker runtime process calls
- Execution mode: `sequential`
- Real subagents: not available; no parallel stream created
- Owner roles: Senior Python Automation Developer, Senior Tester, Senior
  Security Sandbox Engineer

## Scope

- Migrate `DockerCliRuntime` to its injected `ProcessRunner`.
- Preserve argv execution, `shell=False`, timeout, result parsing, and
  adapter-owned sanitized error behavior.
- Update only the Docker runtime regression seam and focused evidence.

## Safety and locks

- No live Docker, Swarm, Incus, registry, or credential-backed command.
- No application port, domain rule, or composition contract change.
- The shared runner contract and composition wiring are locked by completed
  S02; this slice consumes that contract.

## Verification plan

- Docker runtime focused unittest suite.
- `python3 tools/quality_gate.py lint`.
- `python3 tools/quality_gate.py typecheck`.
- `git diff --check`.

The final repository-wide quality gate is recorded in S08 and is green after
the Arc42 governing hash was synchronized.
