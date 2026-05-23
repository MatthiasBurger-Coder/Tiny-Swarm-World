---
name: python-cli-automation
description: Use for Tiny Swarm World CLI automation, command orchestration and progress reporting.
---

# Python CLI Automation

## Purpose

Guide CLI automation changes while keeping entrypoints thin and command
execution behind ports and adapters.

## Responsibilities

- Keep `__main__` and CLI entrypoints focused on composition and invocation.
- Preserve explicit progress and error reporting.
- Keep shell details in infrastructure adapters.

## Inputs

- CLI modules, application services, ports and command runner adapters.
- Active workflow scope and tests.
- Root `AGENTS.md` and `QUALITY.md`.

## Outputs

- CLI implementation guidance, command contract notes and test plan.
- STOP report when command behavior is unclear.

## Boundaries

- Do not hide command execution in constructors or import-time side effects.
- Do not run live infrastructure commands during normal verification.

## STOP conditions

- CLI behavior cannot be verified with mocks.
- Application code would depend on concrete infrastructure.
- A workflow would require live VM, Docker or network mutation.

## Collaboration with other skills

- Pair with `python-senior-developer` and `python-test-automation`.
- Pair with `console-status-ui-developer` for status output.
- Escalate YAML or mapping questions to `mapping-dsl-expert`.

## Quality expectations

- Add focused CLI tests for new behavior.
- Run `python3 tools/quality_gate.py test` and `git diff --check`.
