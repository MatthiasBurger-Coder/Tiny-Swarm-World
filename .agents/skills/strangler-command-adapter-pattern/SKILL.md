---
name: strangler-command-adapter-pattern
description: Use for safely replacing legacy command adapters in Tiny Swarm World.
---

# Strangler Command Adapter Pattern

## Purpose

Guide incremental replacement of legacy command adapters while preserving
observable automation behavior.

## Responsibilities

- Identify the current adapter contract and replacement path.
- Keep old and new command paths testable during transition.
- Preserve command result, error and progress semantics.

## Inputs

- Existing ports, adapters, command templates and tests.
- Root `AGENTS.md`, `QUALITY.md` and workflow slice scope.
- Replacement requirement and rollback needs.

## Outputs

- Incremental adapter migration plan.
- Tests, compatibility notes and rollback guidance.

## Boundaries

- Do not execute live infrastructure commands during development verification.
- Do not move low-level shell concerns into domain or application services.

## STOP conditions

- The legacy command contract cannot be identified.
- The replacement would change runtime behavior without acceptance coverage.
- Rollback or compatibility expectations are unclear.

## Collaboration with other skills

- Pair with `python-cli-automation` and `python-test-automation`.
- Pair with `idempotent-platform-automation` for repeated execution semantics.
- Escalate architecture concerns to `hexagonal-architecture-expert`.

## Quality expectations

- Add regression tests before changing adapter behavior.
- Run focused tests, then the relevant quality-gate subcommands.
