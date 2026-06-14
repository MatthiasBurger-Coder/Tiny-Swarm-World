# Slice 83 Consolidation

Workflow id: `issue-83-ui-status-evidence-contract-20260614`
Slice id: `S01-S04`
Slice title: Define the status and evidence contract consumed by the console UI

Stream results:

- application contract: added `ConsoleStatusEvent` and `PortUI.update_status_event`.
- workflow progress: added optional safe `evidence_path`, `correlation_id`,
  and `trace_id` fields and mapped progress events into console status events.
- console UI: Linux terminal rendering now reads supplied recovery, evidence,
  and correlation fields from UI status state.
- tests: added Linux UI tests for event ingestion and event-only rendering.
- documentation: updated runtime view and README.

Accepted findings:

- The existing application UI port is the minimal contract location.
- The event must be additive so existing command-runner status updates remain
  compatible.
- `TerminalWorkflowProgress` should translate `WorkflowProgressEvent` into
  `ConsoleStatusEvent` so console adapters consume status/evidence state rather
  than workflow internals.

Rejected findings:

- No new browser, React, or standalone UI layer is needed.

Files changed per stream:

- application contract: `src/tiny_swarm_world/application/ports/ui/port_ui.py`,
  `src/tiny_swarm_world/application/ports/progress/port_workflow_progress.py`
- console UI: `src/tiny_swarm_world/infrastructure/adapters/ui/linux_ui.py`,
  `src/tiny_swarm_world/infrastructure/adapters/ui/progress_trace_ui.py`
- tests: `tests/application/ports/test_workflow_progress.py`,
  `tests/infrastructure/adapters/ui/test_progress_trace_ui.py`,
  `tests/infrastructure/adapters/ui/test_linux_ui.py`
- documentation: `documentation/arc42/06_runtime_view.adoc`, `README.md`
- evidence: `.codex/evidence/slice-83-distribution.md`,
  `.codex/evidence/slice-83-consolidation.md`

Conflicts found:

- None.

Tests executed:

- `PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.ui.test_linux_ui`:
  passed.
- `PYTHONPATH=src python3 -m unittest tests.application.ports.test_workflow_progress tests.infrastructure.adapters.ui.test_progress_trace_ui tests.infrastructure.adapters.ui.test_linux_ui`:
  passed.
- `python3 tools/quality_gate.py lint`: passed.
- `python3 tools/quality_gate.py quality`: passed. The full gate executed lint,
  arch-lint, arch-tests, typecheck, and 878 unit tests with 17 skipped.

SonarQube findings and fixes:

- Pending remote PR lifecycle.

Documentation updates:

- arc42 runtime view now describes `ConsoleStatusEvent` as the presentation
  boundary.
- README now identifies the UI event contract for status/evidence rendering.

Final integration decision:

- Accepted for PR lifecycle after required remote checks pass.
