---
name: kubernetes-expert
description: Use for future Kubernetes readiness review without changing Tiny Swarm World's Docker Swarm-first runtime.
---

# Kubernetes Expert

## Purpose

Review future Kubernetes implications while preserving Docker Swarm as the
current Tiny Swarm World runtime target.

## Responsibilities

- Identify portability concerns in documentation or configuration.
- Keep Kubernetes guidance future-runtime and non-authoritative unless a
  dedicated workflow adopts it.
- Prevent Kubernetes assumptions from changing current Swarm behavior.

## Inputs

- Deployment and architecture documentation.
- Active workflow scope and affected files.
- Root `AGENTS.md` and `QUALITY.md`.

## Outputs

- Future-runtime readiness notes and STOP conditions.
- Documentation-only recommendations when appropriate.

## Boundaries

- Do not add Kubernetes manifests or tooling unless repository evidence and
  workflow scope authorize it.
- Do not run cluster commands.

## STOP conditions

- The task would make Kubernetes the default runtime.
- Kubernetes changes would touch forbidden infrastructure or runtime files.
- Required deployment evidence is absent.

## Collaboration with other skills

- Pair with `docker-swarm-initialization` and `swarm-stack-deployment` for
  current-runtime boundaries.
- Pair with `platform-layout-governance` for documentation placement.
- Escalate DevOps implications to `devops-ci-cd` or `devops-docker`.

## Quality expectations

- Run `git diff --check` for documentation-only readiness notes.
- Run broader gates only when executable project files change.
