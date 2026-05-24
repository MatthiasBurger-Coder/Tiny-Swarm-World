---
name: java-25-backend
description: Retired for Tiny Swarm World; use only to stop unapproved Java/Maven/Spring Boot reintroduction.
---

# Retired Java Backend Scope

## Purpose

Tiny Swarm World no longer contains a Java/Maven project surface. This skill
exists only as a guard when a request would reintroduce Java, Maven, Gradle, or
Spring Boot structure without an explicit product-scope change.

## Practices

- Stop before adding Java source roots, Maven POMs, Gradle builds, or Spring
  Boot project structure.
- Route approved product-scope changes through root architecture governance
  before implementation.

## Verification

- Use the Python quality gate from root `QUALITY.md` for current Tiny Swarm
  World work.
