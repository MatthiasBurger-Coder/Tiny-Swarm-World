---
name: mapping-dsl-expert
description: Use for Tiny Swarm World mapping DSL guidance when command or configuration mappings are modeled.
---

# Mapping DSL Expert

## Purpose

Guide mapping DSL decisions for command, VM, network, service or configuration
descriptions without bypassing structured YAML or architecture boundaries.

## Responsibilities

- Keep mappings deterministic, readable and testable.
- Preserve separation between declarative configuration and command execution.
- Ensure mapping facts remain explicit value objects or configuration entries.

## Inputs

- Existing YAML configuration and adapter code.
- Root `AGENTS.md`, `QUALITY.md` and active workflow scope.
- Requirements for command or configuration mapping.

## Outputs

- Mapping rules, validation needs and test guidance.
- STOP report when mapping semantics are unclear.

## Boundaries

- Do not use ad hoc string manipulation when structured YAML APIs are available.
- Do not hide command execution in constructors or import-time side effects.

## STOP conditions

- Mapping rules cannot be derived from repository configuration.
- A mapping would embed host-specific secrets, user names or absolute paths.
- A change would require live infrastructure validation.

## Collaboration with other skills

- Pair with `python-automation` and `python-cli-automation`.
- Pair with `platform-layout-governance` for repository layout concerns.
- Escalate architecture boundaries to `hexagonal-architecture-expert`.

## Quality expectations

- Add focused tests for parser or mapping behavior.
- Run `python3 tools/quality_gate.py test` and `git diff --check`.
