---
name: architecture-hexagonal
description: Use for architecture work that must preserve hexagonal boundaries, domain isolation, ports/adapters separation, and explicit state semantics.
---

# Hexagonal Architecture

## Purpose

Protect the current project core from technical frameworks, storage clients, runtime infrastructure, UI decisions and provider-specific SDKs.

## Practices

- Keep domain models and domain services independent from adapters and infrastructure.
- Keep application services focused on use cases and ports.
- Put CLI, filesystem, command-runner, Docker, network, YAML parser, UI and external-service integrations in adapter or infrastructure modules.
- Express cross-boundary behavior through explicit request, result and port types.
- Keep runtime state, command results and incomplete external-system facts explicit across layer boundaries.

## Verification

- Inspect package dependencies before changes.
- Add or update architecture tests for boundary-sensitive work.
- Run targeted tests first, then the applicable gate from `QUALITY.md`.
