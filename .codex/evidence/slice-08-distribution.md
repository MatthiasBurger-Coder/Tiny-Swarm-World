# Issue #188 — S08 Distribution Decision

- Workflow: `issue-188-20260809` / `issue-188-v1.0.0`
- Slice: `S08` — Architecture enforcement, after-inventory, documentation,
  and audit handoff
- Execution mode: `serial-audit`
- Real subagents: not available; role-based fallback sign-offs recorded
- Owner roles: Senior System Architect, Senior Tester, Senior Requirement
  Engineer, Senior Documentation Engineer, Issue Completion Auditor

## Scope

- Add a scope-aware AST guard for direct process APIs and explicit allowlist
  boundaries.
- Record the final after-inventory and update every requirement/evidence file.
- Synchronize Arc42 planned/implemented language from verified local evidence.
- Obtain Requirement Lead, System Architect, and Test/Evidence sign-offs before
  the independent completion audit.

## Safety and locks

- No live infrastructure or browser command.
- No quality gate weakening and no allowlist entry without a documented
  boundary rationale.
- The governing hash for the final Arc42 content is synchronized before
  consolidation and is covered by the full quality gate.

## Verification plan

- `PYTHONPATH=src python3 -m unittest tests.architecture.test_process_spawn_boundaries`.
- `python3 tools/quality_gate.py arch-lint`.
- `python3 tools/quality_gate.py arch-tests`.
- `python3 tools/quality_gate.py test`.
- `git diff --check`.
- Independent issue-completion audit after all evidence/sign-offs exist.
