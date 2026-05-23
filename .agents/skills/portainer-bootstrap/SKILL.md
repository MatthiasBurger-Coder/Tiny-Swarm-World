---
name: portainer-bootstrap
description: Use for Portainer bootstrap guidance without live service mutation.
---

# Portainer Bootstrap

## Purpose

Guide Portainer setup documentation and service boundaries for Tiny Swarm
World.

## Responsibilities

- Keep Portainer deployment, credentials, volumes and endpoint access explicit.
- Preserve Docker Swarm service stack ownership.
- Separate documented bootstrap steps from live execution.

## Inputs

- Portainer compose assets, scripts, docs and workflow scope.
- Root governance files and service requirements.
- Security and access constraints.

## Outputs

- Portainer bootstrap guidance, risk notes and verification plan.
- STOP report when live service mutation is required.

## Boundaries

- Do not deploy Portainer or run bootstrap commands unless explicitly requested.
- Do not commit credentials or host-specific endpoints.

## STOP conditions

- Endpoint, credential or volume ownership is unclear.
- Verification would mutate Portainer or Swarm state.
- Service boundary conflicts with other stacks.

## Collaboration with other skills

- Pair with `swarm-stack-deployment`.
- Pair with `secrets-and-config-management`.
- Pair with `platform-verification`.

## Quality expectations

- Run `git diff --check` for docs/config changes.
- Use mocks for automation behavior.
