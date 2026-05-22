---
name: architecture-archunit-hexagonal
description: Use when adding, reviewing, or fixing ArchUnit rules for hexagonal architecture and forbidden dependencies.
---

# ArchUnit Hexagonal Rules

## Purpose

Use architecture tests to keep dependency direction and module boundaries visible and enforceable.

## Practices

- Domain code must not depend on application, adapters, infrastructure or provider APIs.
- Application code may depend on domain and ports, not concrete adapters.
- Inbound and outbound adapters may depend inward on application and domain contracts.
- Build-tool adapters must keep Gradle and Maven APIs inside their own adapter packages.
- LLM, graph and parser provider APIs must stay outside domain and application.

## Verification

- Locate existing ArchUnit tests before adding new rules.
- Do not weaken a rule without a dedicated, documented justification.
- Run affected architecture tests and the quality gate from `QUALITY.md` when architecture changes.
