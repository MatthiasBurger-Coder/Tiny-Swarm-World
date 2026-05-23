---
name: docker-registry-bootstrap
description: Use for Docker registry bootstrap guidance without live registry mutations.
---

# Docker Registry Bootstrap

## Purpose

Guide local Docker registry bootstrap documentation and automation safety.

## Responsibilities

- Keep registry ports, storage, authentication and image namespace decisions
  explicit.
- Preserve service stack boundaries.
- Require non-secret configuration in committed files.

## Inputs

- Registry compose assets, configuration, docs and workflow scope.
- Image publishing requirements.
- Root governance files.

## Outputs

- Registry bootstrap guidance and verification plan.
- STOP report when live registry state or secrets are required.

## Boundaries

- Do not run registry bootstrap, `docker login`, push or pull commands unless
  explicitly requested.
- Do not embed credentials or host-specific registry URLs.

## STOP conditions

- Registry authentication or namespace ownership is unclear.
- Verification would mutate the registry.
- Image publishing and registry bootstrap are conflated.

## Collaboration with other skills

- Pair with `registry-infrastructure`.
- Pair with `image-build-publish` and `image-versioning-tagging`.
- Pair with `secrets-and-config-management`.

## Quality expectations

- Run `git diff --check` for documentation/config changes.
- Use mocks for command behavior.
