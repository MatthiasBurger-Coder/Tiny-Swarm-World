---
name: docker-swarm-initialization
description: Use for Docker Swarm initialization guidance without running swarm mutations.
---

# Docker Swarm Initialization

## Purpose

Guide Docker Swarm initialization behavior and documentation while preserving
safe mocked verification by default.

## Responsibilities

- Keep manager initialization, join tokens and node facts explicit.
- Preserve idempotent command construction through application ports and
  infrastructure adapters.
- Avoid leaking secrets or tokens into committed files.

## Inputs

- Swarm setup scripts, command templates, docs and tests.
- Root `AGENTS.md`, `QUALITY.md` and workflow scope.
- Required initialization behavior.

## Outputs

- Initialization guidance, risk notes and verification commands.
- STOP report when live Swarm state is required.

## Boundaries

- Do not run `docker swarm init`, join, leave or update commands unless
  explicitly requested.
- Do not place Docker command details in domain code.

## STOP conditions

- Swarm state, token handling or rollback behavior is unclear.
- Verification would mutate Swarm state.
- A change would expose credentials or tokens.

## Collaboration with other skills

- Pair with `swarm-node-management`.
- Pair with `swarm-volume-network-governance`.
- Pair with `idempotent-platform-automation`.

## Quality expectations

- Use mocked command execution tests.
- Run focused tests and `git diff --check`.
