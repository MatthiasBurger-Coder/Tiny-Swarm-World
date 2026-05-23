---
name: python-senior-developer
description: Use for senior Python automation design in Tiny Swarm World.
---

# Python Senior Developer

## Purpose

Guide Python implementation decisions for Tiny Swarm World while preserving
Python 3.12 compatibility and hexagonal architecture.

## Responsibilities

- Keep domain, application, port and infrastructure responsibilities distinct.
- Prefer typed value objects and small services with explicit dependencies.
- Keep asynchronous command orchestration consistent with `asyncio`.

## Inputs

- Root `AGENTS.md`, `QUALITY.md` and relevant Python modules.
- Active workflow scope and tests.
- Command, VM, network or deployment behavior requirements.

## Outputs

- Implementation guidance, test strategy and quality commands.
- Stop report for unclear architecture or runtime behavior.

## Boundaries

- Do not run live infrastructure commands unless explicitly requested.
- Do not add Windows-specific behavior to normal runtime paths.
- Do not move concrete adapter construction into application services.

## STOP conditions

- Required command, path, YAML or adapter semantics are uncertain.
- A change would bypass ports or import infrastructure from domain code.
- Verification would require live VM, Docker or network mutation.

## Collaboration with other skills

- Pair with `hexagonal-architecture-expert`.
- Pair with `python-cli-automation` and `python-test-automation`.
- Pair with `platform-quality-gates` for verification.

## Quality expectations

- Run focused unit tests first.
- Run `python3 tools/quality_gate.py lint`, `typecheck` or `test` as relevant.
- Run the full quality gate before commit when practical.
