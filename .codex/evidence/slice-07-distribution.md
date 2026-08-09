# Issue #188 — S07 Distribution Decision

- Workflow: `issue-188-20260809` / `issue-188-v1.0.0`
- Slice: `S07` — Migrate `HostPreflightProbe` Git probes
- Execution mode: `sequential`
- Real subagents: not available; no parallel stream created
- Owner roles: Senior Python Automation Developer, Senior System Architect,
  Senior Tester

## Scope

- Route `git check-ignore` and `git ls-files` through the shared runner.
- Preserve fail-soft behavior when Git is missing/unresponsive and preserve
  tracked-file filesystem fallback scanning.
- Do not introduce service-fingerprint strategy changes or live mutation.

## Safety and locks

- No live Git repository mutation, infrastructure command, or credential use.
- No application/domain port change.
- The runner remains an infrastructure dependency and does not own preflight
  policy.

## Verification plan

- Focused HostPreflightProbe tests, including Git unavailable and fallback
  behavior.
- `python3 tools/quality_gate.py lint`.
- `python3 tools/quality_gate.py typecheck`.
- `git diff --check`.

The final repository-wide quality gate is recorded in S08 and is green after
the Arc42 governing hash was synchronized.
