---
name: maven-repository-bootstrap
description: Use for Nexus Maven repository bootstrap guidance without reintroducing Java/Maven build authority.
---

# Maven Repository Bootstrap

## Purpose

Guide Maven repository bootstrap in Nexus without making Maven or Java a Tiny
Swarm World build authority.

## Responsibilities

- Keep Maven repository setup scoped to Nexus artifact-repository behavior.
- Preserve credentials and repository URLs as configurable values.
- Separate repository bootstrap from Java build behavior.

## Inputs

- Nexus/Maven repository docs and workflow scope.
- Root `AGENTS.md` and `QUALITY.md`.
- Required repository behavior.

## Outputs

- Maven repository guidance, safety notes and verification plan.
- STOP report for Java/build authority drift.

## Boundaries

- Do not make Maven the default project quality gate.
- Do not run Nexus or Maven repository bootstrap scripts unless explicitly
  requested.

## STOP conditions

- Maven repository scope is confused with Python automation architecture or
  Java/Maven project structure.
- Repository credentials are unclear.
- Verification would mutate a live Nexus service.

## Collaboration with other skills

- Pair with `nexus-bootstrap`.
- Pair with `registry-infrastructure`.
- Stop if a change would reintroduce Java/Maven project structure without an
  explicit scope decision.

## Quality expectations

- Run `git diff --check` for docs/config changes.
- Use Python quality gates as the project default.
