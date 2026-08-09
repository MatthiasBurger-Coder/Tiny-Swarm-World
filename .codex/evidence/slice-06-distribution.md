# Issue #188 — S06 Distribution Decision

- Workflow: `issue-188-20260809` / `issue-188-v1.0.0`
- Slice: `S06` — Migrate image-publisher process execution
- Execution mode: `sequential`
- Real subagents: not available; no parallel stream created
- Owner roles: Senior Python Automation Developer, Senior Security Sandbox
  Engineer, Senior System Architect, Senior Tester

## Scope

- Route host Docker inspection/cache transfer and manager text/byte operations
  through the shared runner.
- Preserve image cache/build/pull policy, typed rejection diagnostics,
  registry-rate-limit detection, operator actions, byte-stream behavior, and
  secret-safe logging.

## Safety and locks

- No live Docker, Incus/LXC, registry, or credential-backed command.
- No generic runner policy change and no application/domain port change.
- Shell wrappers remain explicit adapter command arguments; they are not
  interpreted by the runner as implicit shell mode.

## Verification plan

- Focused image-publisher unittest suite, including text and byte paths,
  typed failures, cache behavior, redaction, and transfer behavior.
- `python3 tools/quality_gate.py lint`.
- `python3 tools/quality_gate.py typecheck`.
- `git diff --check`.

The repository-wide quality gate retains the pre-existing Arc42 governing-hash
exception recorded in S02 until that independent governance artifact is
reconciled.
