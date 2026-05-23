---
name: python-test-automation
description: Use for Python unittest fixtures, mocks and deterministic Tiny Swarm World test automation.
---

# Python Test Automation

## Purpose

Design deterministic Python tests for Tiny Swarm World without external service
dependencies.

## Responsibilities

- Use mocks for command execution, network calls, VM operations and Docker
  operations.
- Use temporary directories for filesystem tests.
- Keep test imports aligned with package style and `PYTHONPATH=src`.

## Inputs

- Existing tests, target modules and behavior requirements.
- Root `QUALITY.md` and active workflow scope.
- Failure output or regression report.

## Outputs

- Test fixtures, targeted test commands and failure triage notes.
- STOP report when deterministic testing is not possible.

## Boundaries

- Do not require live infrastructure for unit tests.
- Do not weaken assertions, architecture checks or import-linter contracts.

## STOP conditions

- The required behavior cannot be isolated from external systems.
- Test setup would write outside controlled temporary paths.
- The active workflow forbids the source files needed for the fix.

## Collaboration with other skills

- Pair with `tdd-expert`.
- Pair with `platform-quality-gates` and `quality-gate`.
- Escalate architecture-sensitive imports to `hexagonal-architecture-expert`.

## Quality expectations

- Run the nearest focused unittest command first.
- Run `python3 tools/quality_gate.py test` for broader regression coverage.
