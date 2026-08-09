# Issue #190 — S190-01 Distribution Decision

- Workflow: `issue-190-20260809` / `issue-190-v1.0.0`
- Slice: `S190-01` — Residual special-case inventory
- Execution branch: `feature/stack-prerequisite-strategies-solid`
- Profile: `FULL_PATH`
- Chosen execution mode: sequential
- Real subagents used: `no`; no callable project-subagent tool is exposed.
- Fallback role-based review: `yes`; requirement, architecture, Python, tester,
  security and orchestration perspectives are recorded in the main thread.
- Parallelization: rejected because the existing prerequisite and asset
  dispatch contracts must be reconciled as one residual inventory.
- Stop conditions checked: no duplicate extraction, unclassified special case
  or missing baseline test was found.

## Consolidation plan

Freeze the current #238 baseline, distinguish strategy-local stack policy from
generic runtime orchestration, and identify the residual gap: asset transfer
still uses a stack-name conditional chain. S190-02 may only complete that
dispatch boundary while preserving asset paths, command text and no-op default
behavior.
