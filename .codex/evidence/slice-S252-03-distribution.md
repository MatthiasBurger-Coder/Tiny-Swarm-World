# Issue #252 — S252-03 Distribution Decision

- Workflow ID: `issue-252-classic-public-beta-rc1-20260814`
- Slice ID: `S252-03`
- Slice title: Deterministic lifecycle, fail-closed and recovery coverage
- Execution mode: `sequential`
- Dependency: `S252-02` checkpoint `fef42fe7`; canonical Classic suite is
  discoverable and opt-in.
- Owner stream: Senior Tester / quality implementation.
- Review streams: real Quality Reviewer subagent, Senior Python Automation
  Developer, Senior System Architect and Live Evidence Validation Expert.
- Real subagent: assigned as review-only before implementation; no live
  commands or write access.
- Parallelization: rejected. All affected test/support/evidence contracts
  overlap and the lifecycle assertions must be integrated in one deterministic
  suite.
- Git worktrees: no parallel implementation worktree.
- Expected touched paths: `tests/e2e/classic/`, `tests/live/` only if a
  compatibility contract is required, `tests/integration/`, `tests/support/`
  and `documentation/evidence/`.
- File locks: `tests/e2e/classic/`, `tests/integration/`, `tests/support/`,
  `documentation/evidence/`.
- Contract locks: `scenario-record-schema`, `evidence-redaction-schema`,
  `lifecycle-state-classification`, `default-tests-no-live-mutation`.
- Architecture locks: `observed-vs-static-evidence`,
  `tests-no-live-mutation-by-default`.
- Safety rule: fixtures must use synthetic values and temporary paths; no
  Incus, Docker, Swarm, compose, browser, service bootstrap or PowerShell
  operation is allowed.
- Targeted gates: focused lifecycle unittest, `python3 tools/quality_gate.py
  test`, `python3 tools/quality_gate.py arch-tests` and `git diff --check`.
- Required gate: `python3 tools/quality_gate.py quality`.
- Handoff condition: representative missing prerequisites, partial/ambiguous
  state, duplicate/destructive reconcile, update preservation, restart,
  redaction and exact RC1 state rules are executable and deterministic.
