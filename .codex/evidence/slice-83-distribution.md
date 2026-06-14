# Slice 83 Distribution

Workflow id: `issue-83-ui-status-evidence-contract-20260614`
Slice id: `S01-S04`
Slice title: Define the status and evidence contract consumed by the console UI

Affected areas:

- application UI port
- terminal console adapter
- UI adapter tests
- architecture documentation

Chosen execution mode: sequential.

Selected streams:

- application contract: introduce a status/evidence event on the UI port.
- console UI: render supplied evidence and trace fields from the event state.
- tests: prove rendering from the supplied event only.
- documentation: record the presentation-only boundary.

Real subagents used: yes. Avicenna provided read-only planning.

Fallback role-based review used: no.

Git worktrees used: no. The changed files are tightly coupled and share one UI
port contract.

Conflict risks:

- Existing `update_status` callers must remain backward compatible.
- Console UI must not own workflow lifecycle decisions.
- Evidence and correlation fields must be optional so existing command-runner
  flows keep working.

Quality gates to run:

- `PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.ui.test_linux_ui`
- `python3 tools/quality_gate.py lint`
- `python3 tools/quality_gate.py quality`

Consolidation plan:

- Keep the existing `PortUI.update_status` API stable.
- Add an event-based method that maps to the same UI state plus optional
  recovery, evidence, and trace metadata.
- Run targeted UI tests first, then full quality before PR.

Parallelization decision:

- Rejected because the UI port, renderer, and tests define one small contract
  and should change together.
