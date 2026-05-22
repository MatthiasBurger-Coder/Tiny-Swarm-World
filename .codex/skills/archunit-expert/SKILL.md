---
name: archunit-expert
description: Use when adding, reviewing, or fixing ArchUnit architecture rules for layered boundaries, forbidden dependencies, package ownership, adapter isolation, provider isolation, and architecture quality validation.
---

# ArchUnit Expert

Use this skill for architecture tests, forbidden dependencies, package-boundary checks, dependency direction, and quality-gate architecture validation in Java projects that use ArchUnit.

## Authoritative Sources

Read, when present:

- root `AGENTS.md`
- root `QUALITY.md`
- existing ArchUnit tests
- build files that define architecture-test dependencies and tasks
- project-specific architecture or quality skills under `.agents/`

## Rules

- Enforce the architecture boundaries documented by the project.
- Domain or core code must not depend on adapters, infrastructure, provider APIs, build-tool APIs, parser APIs, database clients, or UI frameworks unless the project explicitly allows it.
- Application or use-case code may depend on core/domain and ports, not concrete adapters, unless the project architecture says otherwise.
- Adapters may depend inward on application and domain contracts.
- Build-tool adapter APIs should stay inside build-tool adapter packages.
- Do not weaken ArchUnit rules to make a change pass.

## Verification

Locate existing ArchUnit tests before adding rules. Run affected architecture tests and the applicable quality gate from project documentation when architecture behavior changes.
