---
name: registry-infrastructure
description: Use for local registry and artifact repository infrastructure guidance.
---

# Registry Infrastructure

## Purpose

Guide local registry infrastructure decisions for Tiny Swarm World without
running live bootstrap or deployment commands.

## Responsibilities

- Keep Docker registry, Nexus and Maven repository responsibilities distinct.
- Preserve credentials, ports, volumes and URLs as configurable values.
- Keep bootstrap scripts and compose assets within their documented boundaries.

## Inputs

- Registry-related docs, config, compose assets and workflow scope.
- Root governance files and required service behavior.
- Existing tests or mocks.

## Outputs

- Registry guidance, security notes and verification plan.
- STOP report when credentials or live state are required.

## Boundaries

- Do not run Nexus, Docker registry or Maven repository bootstrap scripts unless
  explicitly requested.
- Do not commit secrets or host-specific endpoints.

## STOP conditions

- Credential handling is unclear.
- Verification would mutate a registry service.
- Registry and image responsibilities are conflated.

## Collaboration with other skills

- Pair with `nexus-bootstrap`, `docker-registry-bootstrap` and
  `maven-repository-bootstrap`.
- Pair with `secrets-and-config-management`.
- Pair with `image-build-publish` for producer workflows.

## Quality expectations

- Run `git diff --check` for docs/config governance.
- Use mocked integration points for behavior changes.
