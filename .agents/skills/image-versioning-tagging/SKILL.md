---
name: image-versioning-tagging
description: Use for container image version and tag governance in Tiny Swarm World.
---

# Image Versioning Tagging

## Purpose

Keep image tags and versions deterministic, traceable and safe for local Swarm
deployment workflows.

## Responsibilities

- Define tag inputs, naming rules and rollback references.
- Prevent implicit `latest`-only workflows where traceability is needed.
- Align image tags with registry and deployment documentation.

## Inputs

- Image build docs, registry docs, compose or stack references and workflow
  scope.
- Release or rollback requirement.
- Root governance files.

## Outputs

- Tagging decision, compatibility notes and verification plan.
- STOP report for ambiguous version ownership.

## Boundaries

- Do not publish or retag images unless explicitly requested.
- Do not embed environment-specific registry names in committed config.

## STOP conditions

- Version source or rollback semantics are unclear.
- A tag change would require live registry validation.
- Deployment references would become inconsistent.

## Collaboration with other skills

- Pair with `image-build-publish`.
- Pair with `image-verification`.
- Pair with `release-branch-governance` for release semantics.

## Quality expectations

- Run reference searches and `git diff --check`.
- Use tests for tag-construction code changes.
