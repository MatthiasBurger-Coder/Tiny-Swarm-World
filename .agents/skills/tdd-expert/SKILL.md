---
name: tdd-expert
description: Use for Tiny Swarm World test-first Python automation changes and regression design.
---

# TDD Expert

## Purpose

Guide test-first changes for Tiny Swarm World while preserving the Linux/WSL
automation model and Python hexagonal architecture.

## Responsibilities

- Identify the smallest behavior that needs a regression test.
- Prefer unit tests with mocked command, VM, Docker and network operations.
- Keep tests aligned with domain, application, port and infrastructure adapter
  boundaries.

## Inputs

- Root `AGENTS.md` and `QUALITY.md`.
- The changed behavior or bug report.
- Existing tests under `tests/`.

## Outputs

- Focused test plan or regression test guidance.
- Verification commands and residual risk notes.

## Boundaries

- Do not run live LXD, Incus, LXC, Docker Swarm, compose, netplan, `socat` or service
  bootstrap commands.
- Do not weaken architecture tests or import-linter contracts.

## STOP conditions

- Required behavior cannot be verified from repository files.
- A test would need live infrastructure instead of a mock or fixture.
- The change would touch forbidden runtime scope for the active workflow.

## Collaboration with other skills

- Pair with `python-test-automation` for fixtures and test mechanics.
- Pair with `quality-testing-strategy` and `quality-gate` for gate selection.
- Escalate architecture uncertainty to `hexagonal-architecture-expert`.

## Quality expectations

- Run the nearest focused test first.
- Run `python3 tools/quality_gate.py test` for Python behavior changes.
- Run `git diff --check` for documentation or governance-only changes.
