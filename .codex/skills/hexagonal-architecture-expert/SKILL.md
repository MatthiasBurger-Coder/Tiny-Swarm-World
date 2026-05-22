---
name: hexagonal-architecture-expert
description: Use for architecture work that must preserve hexagonal boundaries, domain isolation, application use cases, ports/adapters separation, dependency direction, and explicit project-specific state semantics.
---

# Hexagonal Architecture Expert

Use this skill for architecture work involving domain, application, ports, adapters, infrastructure, dependency direction, or explicit state semantics.

## Authoritative Sources

Read, when present:

- root `AGENTS.md`
- root `QUALITY.md`
- project architecture documentation
- project-specific architecture roles or skills under `.agents/`
- existing architecture tests

## Rules

- Keep domain code independent from application orchestration, adapters, infrastructure, provider SDKs, filesystem adapters, database clients, parser APIs, and UI code.
- Keep application code depending on domain and ports, not concrete adapters.
- Keep adapters thin and dependent inward.
- Preserve provenance, uncertainty, and explicit missing-state semantics required by the project domain.
- Add or update architecture tests for boundary-sensitive changes when the project has architecture-test tooling.

## Verification

Inspect current packages, module dependencies, architecture tests, and affected quality tooling before changing architecture. Stop when a boundary or dependency cannot be verified.
