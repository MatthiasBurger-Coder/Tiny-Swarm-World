---
name: image-build-publish
description: Use for container image build and publish workflow guidance without running Docker commands.
---

# Image Build Publish

## Purpose

Guide image build and publish workflows for Tiny Swarm World services while
keeping Docker operations explicit and optional.

## Responsibilities

- Keep image build inputs, tags, registries and publish steps deterministic.
- Separate documentation, command construction and live Docker execution.
- Preserve service stack ownership and registry boundaries.

## Inputs

- Dockerfiles, compose assets, image docs and workflow scope.
- Registry requirements and versioning rules.
- Root governance files.

## Outputs

- Image workflow guidance, tag plan and verification notes.
- STOP report for live build or registry blockers.

## Boundaries

- Do not run `docker build`, tag, push or pull commands unless explicitly
  requested.
- Do not add generated image artifacts to the repository.

## STOP conditions

- Image source, tag or registry ownership is unclear.
- Verification would build or publish images.
- A change crosses service boundaries without a workflow.

## Collaboration with other skills

- Pair with `image-versioning-tagging` and `image-verification`.
- Pair with `docker-registry-bootstrap`.
- Pair with `swarm-stack-deployment` for deployment references.

## Quality expectations

- Run `git diff --check` for docs/config changes.
- Use mocked command tests for automation behavior changes.
