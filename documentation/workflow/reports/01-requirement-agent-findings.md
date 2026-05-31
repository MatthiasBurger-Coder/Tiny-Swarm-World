# Requirement Agent Findings

EPIC check: partially implemented.

The EPIC requires actionable terminal progress and recovery guidance, but the
clarified observability requirement is stricter than phase-level status. The
installation runtime path needs gapless method-flow tracing for every covered
method, including exception paths.

Requirement classification:

- functional requirement: complete installation progress reporting
- functional requirement: method entry, normal exit, and exception exit tracing
  for every covered installation runtime method
- UX requirement: console GUI response for task, step, result, and recovery
- observability requirement: safe centralized logging
- observability requirement: correlation data sufficient to reconstruct
  program flow
- architecture constraint: terminal-only in-process UI
- architecture constraint: logging is a Shared cross-cutting module governed by
  ADR
- security requirement: redaction for commands, stdout, stderr, tokens,
  passwords, environment payloads, host paths, and local IPs
- quality requirement: mocked default gates and no live infrastructure

Primary gaps:

- `CommandExecuter` has the requested `PortUI` and class logger pattern.
- `setup run` does not use `CommandExecuter` as its canonical execution path.
- `SetupWorkflow` prints progress directly.
- Platform workflows return verification results but do not update `PortUI`.
- Logging style is inconsistent between direct class loggers and
  `LoggerFactory`.
- The previous workflow interpretation reduced "continuous" to setup phase and
  platform step progress. That is not sufficient for the clarified method-level
  trace requirement.

Required setup progress transitions:

- refused;
- blocked;
- phase start;
- phase completed;
- phase failed;
- stopped;
- downstream `not_run`;
- final completed.

Required platform progress transitions:

- pre-apply guard;
- mutating step start;
- apply result;
- direct verification;
- verify step;
- blocked state;
- failed apply;
- failed verify;
- completion.

Corrected workflow decision:

- Keep the narrow progress port for high-level setup/platform status.
- Add ADR-governed cross-cutting method trace logging for method entry,
  returned, and raised lifecycle events.
- Do not inject concrete UI concerns across all application services.
- Treat current behavior as partial until later slices implement both
  method-level trace coverage and infrastructure adapters: command-runner UI
  already uses `PortUI`, setup/platform now emit workflow progress events, but
  method-flow tracing remains incomplete.

Corrected method-trace acceptance criteria:

- Document the installation method-trace scope, including setup run, setup
  phases, platform workflows, command execution, progress adapters, composition
  wiring, and related exception paths.
- Every in-scope method emits `entered`, `returned`, and `raised` events, or
  has an explicit tested exemption.
- Failed events are emitted for caught and propagated exceptions before the
  exception is re-raised or converted to a workflow result.
- Trace events include only safe metadata: run ID, correlation ID, parent span
  ID, method identity, component or layer, status, duration, safe summary, and
  recovery hint when applicable.
- UI output receives trace state through approved progress or trace ports and
  infrastructure adapters, not direct `PortUI` injection into application or
  domain services.
- Central logging records the same trace lifecycle after redaction.
- Domain code remains free of concrete UI, logging setup, command runner, YAML,
  HTTP, Docker, curses, and composition imports.
- Tests or static checks fail when an in-scope method lacks entry, returned, or
  raised trace coverage.

Slice 01 verification evidence:

- branch checked: `feature/workflow-install-observability-20260529`;
- read-only role reviews completed before documentation edits;
- required quality gate: `git diff --check`;
- no live infrastructure commands run.
