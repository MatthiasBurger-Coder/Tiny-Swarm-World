---
name: idempotent-platform-automation
description: Use for idempotency, retry and safe re-run semantics in Tiny Swarm World automation.
---

# Idempotent Platform Automation

## Purpose

Ensure Tiny Swarm World automation can be safely reasoned about across repeated
runs, partial failures and recovery paths.

## Responsibilities

- Define desired state, observed state, retries and no-op behavior explicitly.
- Preserve command result provenance and failure classification.
- Avoid hidden side effects in constructors, imports or global lookups.

## Inputs

- Application services, command adapters, config, tests and workflow scope.
- Failure or retry requirement.
- Root governance files and resilience expectations.

## Outputs

- Idempotency design notes, tests and recovery guidance.
- STOP report for unsafe re-run behavior.

## Boundaries

- Do not run live platform commands during normal verification.
- Do not swallow command failures or erase retry evidence.

## STOP conditions

- Desired state or current state cannot be represented.
- Retrying would be destructive or non-deterministic.
- A command side effect cannot be mocked or verified safely.

## Collaboration with other skills

- Pair with `resilience-engineering`.
- Pair with `python-cli-automation`.
- Pair with `platform-reset-and-recovery`.

## Quality expectations

- Add tests for repeated runs and failure paths.
- Run focused tests and relevant quality-gate subcommands.
