---
name: nexus-bootstrap
description: Use for Nexus bootstrap guidance without executing Nexus setup scripts.
---

# Nexus Bootstrap

## Purpose

Guide Nexus setup documentation and automation boundaries for Tiny Swarm World.

## Responsibilities

- Keep Nexus repositories, credentials and endpoints explicit.
- Separate bootstrap planning from live service mutation.
- Preserve idempotency and rollback expectations.

## Inputs

- Nexus docs, compose assets, prepare scripts and workflow scope.
- Root `AGENTS.md`, `QUALITY.md` and registry decisions.
- Required Nexus repository behavior.

## Outputs

- Nexus bootstrap guidance, security notes and verification plan.
- STOP report for live-service or secret-handling blockers.

## Boundaries

- Do not run Nexus bootstrap scripts unless explicitly authorized.
- Do not commit credentials, tokens or host-specific endpoints.

## STOP conditions

- Repository ownership or credential handling is unclear.
- Verification would mutate a Nexus instance.
- Bootstrap behavior cannot be made idempotent.

## Collaboration with other skills

- Pair with `registry-infrastructure`.
- Pair with `maven-repository-bootstrap`.
- Pair with `secrets-and-config-management`.

## Quality expectations

- Use documentation checks and mocked command tests by default.
- Run `git diff --check`.
