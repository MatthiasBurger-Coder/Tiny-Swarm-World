# Slice 80 Distribution

Workflow id: `issue-80-ui-execution-decoupling-20260614`
Slice id: `S01-S04`
Slice title: Decouple command execution from the console UI adapter

Affected areas:

- command workflow orchestration
- console UI adapters
- command-runner UI tests
- documentation

Chosen execution mode: sequential.

Selected streams:

- architecture/runtime: move command execution loops into `CommandWorkflow`.
- UI: keep async/sync command UI adapters as presentation-only sessions.
- tests: preserve command-runner failure and aggregate status semantics.
- documentation: update runtime boundary.

Real subagents used: no. Previous #82/#83 subagents informed the dependency
chain; this slice used main-thread role-based execution.

Fallback role-based review used: yes.

Git worktrees used: no. The same command/UI behavior is being split across
tightly coupled files.

Conflict risks:

- Existing tests assert command-runner aggregate status and redaction behavior.
- UI adapters must not call command execution services after the split.

Quality gates to run:

- `PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.ui.test_command_runner_ui_failure_semantics tests.architecture.test_hexagonal_imports`
- `python3 tools/quality_gate.py lint`
- `python3 tools/quality_gate.py quality`

Consolidation plan:

- Convert UI adapters to UI session helpers.
- Move async and sync command execution loops into `CommandWorkflow`.
- Keep redaction and aggregate terminal-state tests green.

Parallelization decision:

- Rejected because execution orchestration and UI status semantics must remain
  behaviorally identical.
