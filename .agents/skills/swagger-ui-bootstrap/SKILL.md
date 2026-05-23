---
name: swagger-ui-bootstrap
description: Use for Swagger UI service bootstrap guidance in Tiny Swarm World.
---

# Swagger UI Bootstrap

## Purpose

Guide Swagger UI service bootstrap and routing documentation without live
deployment.

## Responsibilities

- Keep OpenAPI/static asset source, service port and reverse proxy routing
  explicit.
- Preserve service stack and documentation boundaries.
- Avoid implying a broader REST API architecture without verified contracts.

## Inputs

- Swagger UI compose assets, docs, routing config and workflow scope.
- Root governance files and API documentation requirements.
- Existing contract artifacts if present.

## Outputs

- Bootstrap guidance, routing notes and verification plan.
- STOP report for missing contract or live deployment needs.

## Boundaries

- Do not run compose deployment or service bootstrap commands unless explicitly
  requested.
- Do not invent OpenAPI contracts.

## STOP conditions

- API contract source is missing or ambiguous.
- Routing would conflict with reverse proxy ownership.
- Verification would mutate live services.

## Collaboration with other skills

- Pair with `reverse-proxy-routing`.
- Pair with `contract-governance-expert` when API contracts change.
- Pair with `swarm-stack-deployment`.

## Quality expectations

- Run `git diff --check` for docs/config changes.
- Run contract or config tests only when tooling exists.
