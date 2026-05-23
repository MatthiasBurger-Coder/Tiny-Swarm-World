---
name: swarm-node-management
description: Use for Docker Swarm node management guidance in Tiny Swarm World.
---

# Swarm Node Management

## Purpose

Guide Swarm node lifecycle, labels and role management without live cluster
mutation during development.

## Responsibilities

- Keep node identity, manager/worker roles and labels explicit.
- Preserve safe command orchestration and result handling.
- Distinguish desired state, observed state and unresolved state.

## Inputs

- Swarm node docs, command templates, application services and tests.
- Workflow scope and root governance files.
- Node management requirement.

## Outputs

- Node management guidance, tests and risk notes.
- STOP report for ambiguous cluster state.

## Boundaries

- Do not run Docker node or Swarm commands unless explicitly requested.
- Do not infer live node health from documentation.

## STOP conditions

- Node state cannot be represented deterministically.
- Verification would mutate a Swarm cluster.
- Error handling or retry behavior is unclear.

## Collaboration with other skills

- Pair with `docker-swarm-initialization`.
- Pair with `platform-verification` for non-mutating checks.
- Pair with `resilience-engineering` for retry and timeout semantics.

## Quality expectations

- Add mocked command tests for node behavior.
- Run relevant Python quality-gate subcommands.
