# Slice 82 Distribution

Workflow id: `issue-82-ui-presentation-arch-tests-20260614`
Slice id: `S01-S04`
Slice title: Add architecture tests that keep the console UI presentation-only

Affected areas:

- architecture tests
- console UI adapters
- command workflow wiring
- documentation

Chosen execution mode: sequential.

Selected streams:

- architecture: add deterministic UI presentation-only import guardrail.
- implementation: remove direct `CommandExecuter` construction from UI
  adapters by injecting an executor factory.
- tests: preserve async/sync command UI failure semantics.
- documentation: record the guardrail.

Real subagents used: no. Agent spawning was blocked by the active thread limit.

Fallback role-based review used: yes. The main thread performed Senior System
Architect and Senior Tester review against the current UI adapter imports.

Git worktrees used: no. The slice touches tightly coupled UI adapters and
architecture tests.

Conflict risks:

- Existing command UI failure tests expect `runner_ui.command_execute`.
- The guardrail must allow UI/progress/status ports while forbidding execution
  and live infrastructure concerns.

Quality gates to run:

- `PYTHONPATH=src python3 -m unittest tests.architecture.test_hexagonal_imports tests.infrastructure.adapters.ui.test_command_runner_ui_failure_semantics`
- `python3 tools/quality_gate.py lint`
- `python3 tools/quality_gate.py quality`

Consolidation plan:

- Add the failing architecture guardrail.
- Move concrete command executor construction out of UI adapters into
  `CommandWorkflow`.
- Preserve UI status semantics through targeted tests.

Parallelization decision:

- Rejected because the guardrail and UI adapter repair must be integrated
  together.
