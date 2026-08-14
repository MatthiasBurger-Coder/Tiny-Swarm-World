# Issue #252 — S252-02 Distribution Decision

- Workflow ID: `issue-252-classic-public-beta-rc1-20260814`
- Slice ID: `S252-02`
- Slice title: Canonical test layout and tool/test separation
- Execution mode: `sequential`
- Dependency: `S252-01` checkpoint `e8603ec4`; matrix, inventory and gate are
  present.
- Planned review streams: Senior Python Automation Developer (integration
  owner), Senior Tester (real review stream), Senior System Architect and
  Senior Documentation Engineer.
- Real subagent used: `yes`; one isolated review-only Senior Tester stream was
  assigned before implementation. It was not authorized to edit or commit.
- Codex integration owner: yes; the shared test roots have overlapping locks,
  so no parallel write stream was started.
- Fallback role review: retained for the non-subagent perspectives in the
  main execution thread.
- Git worktrees: no parallel implementation worktree; serial integration on
  the active workflow branch.
- Expected touched paths: `tests/e2e/classic/`, the migrated
  `tests/live/test_post_install_browser_live.py`, the retired duplicate
  integration runner, and issue execution evidence.
- File locks: `tests/live/`, `tests/integration/`, `tests/e2e/classic/`,
  `tests/support/`.
- Contract locks: `canonical-classic-test-layout`,
  `existing-live-suite-reuse`, `tests-no-live-mutation-by-default`.
- Architecture locks: `tools-not-test-assertions`,
  `tests-no-live-mutation-by-default`.
- Conflict risks: moving the 1,825-line assertion suite can change discovery
  and module paths; keeping the Playwright integration runner would retain a
  duplicate browser framework. The old module path is therefore removed only
  after canonical discovery tests pass.
- Live safety: no live browser, Incus, Docker, Swarm, service or PowerShell
  operation is allowed or executed.
- Targeted gates: focused canonical-suite unittest, `python3
  tools/quality_gate.py lint`, `python3 tools/quality_gate.py test`,
  `python3 tools/quality_gate.py arch-tests`, and `git diff --check`.
- Required gate: `python3 tools/quality_gate.py quality`.
- Handoff condition: canonical suite is discoverable, opt-in, redacted and
  free of a second Playwright runner; S252-03 adds deterministic lifecycle and
  fail-closed assertions.
