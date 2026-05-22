---
name: architecture-modular-monorepo
description: Use for module-boundary, Gradle project dependency, and monorepo responsibility changes.
---

# Modular Monorepo

## Purpose

Keep repository modules cohesive while allowing small, independently verifiable slices.

## Practices

- Verify module names in `settings.gradle.kts` before referencing them.
- Put shared domain concepts in domain modules, orchestration in application modules and technical integrations in adapter or infrastructure modules.
- Avoid cross-module shortcuts that bypass ports.
- Keep optional runtime infrastructure out of default unit-test requirements.
- Document module responsibility changes in architecture docs when public behavior changes.

## Verification

- Inspect Gradle project dependencies for new edges.
- Run targeted module tests for affected modules.
- Use the full local gate from `QUALITY.md` for commit readiness.
