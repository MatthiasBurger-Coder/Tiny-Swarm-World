---
name: maven-repository-bootstrap
description: Use for Maven repository bootstrap guidance while keeping Java as deployment-example surface.
---

# Maven Repository Bootstrap

## Purpose

Guide Maven repository bootstrap in Nexus without making Maven or Java the
default Tiny Swarm World build authority.

## Responsibilities

- Keep Maven repository setup scoped to platform services and Java examples.
- Preserve credentials and repository URLs as configurable values.
- Separate repository bootstrap from Java build behavior.

## Inputs

- Nexus/Maven repository docs, prepare scripts and workflow scope.
- Root `AGENTS.md`, `QUALITY.md` and Java example boundary.
- Required repository behavior.

## Outputs

- Maven repository guidance, safety notes and verification plan.
- STOP report for Java/build authority drift.

## Boundaries

- Do not make Maven the default project quality gate.
- Do not run Nexus or Maven repository bootstrap scripts unless explicitly
  requested.

## STOP conditions

- Java example scope is confused with Python automation architecture.
- Repository credentials are unclear.
- Verification would mutate a live Nexus service.

## Collaboration with other skills

- Pair with `nexus-bootstrap`.
- Pair with `registry-infrastructure`.
- Escalate Java-example changes to `java-25-backend` only when explicitly in
  scope.

## Quality expectations

- Run `git diff --check` for docs/config changes.
- Use Python quality gates as project default unless Java example work is
  explicitly requested.
