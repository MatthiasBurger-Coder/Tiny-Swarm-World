---
name: swarm-stack-deployment
description: Use for Docker Swarm stack deployment guidance without live deployments.
---

# Swarm Stack Deployment

## Purpose

Guide stack deployment automation and documentation while preserving service
stack boundaries and mocked verification.

## Responsibilities

- Keep service stacks under `infra/config/compose` and `infra/compose`
  boundaries.
- Preserve deterministic command templates and deployment results.
- Separate planning, command construction and live deployment execution.

## Inputs

- Compose or stack configuration, deployment services, docs and tests.
- Root `AGENTS.md`, `QUALITY.md` and workflow scope.
- Required deployment behavior.

## Outputs

- Deployment guidance, test plan and safety notes.
- STOP report when live deployment is required.

## Boundaries

- Do not run compose or Swarm stack deployment commands unless explicitly
  requested.
- Do not change service boundaries opportunistically.

## STOP conditions

- Stack ownership or configuration path is unclear.
- Verification would deploy or mutate services.
- A change would embed secrets or host-specific values.

## Collaboration with other skills

- Pair with `swarm-volume-network-governance`.
- Pair with `image-build-publish` and `image-verification`.
- Pair with `platform-reset-and-recovery` for rollback guidance.

## Quality expectations

- Use structured YAML APIs and focused tests for behavior changes.
- Run `git diff --check` for docs and config-only changes.
