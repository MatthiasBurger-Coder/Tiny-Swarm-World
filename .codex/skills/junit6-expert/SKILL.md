---
name: junit6-expert
description: Use when writing or reviewing JUnit 6 tests, deterministic fixtures, regression-first bug fixes, integration tests, filesystem test isolation, and project quality-gate verification.
---

# JUnit 6 Expert

Use this skill for unit tests, integration tests, regression-first fixes, deterministic fixtures, and test placement in Java projects that use JUnit 6.

## Authoritative Sources

Read, when present:

- root `AGENTS.md`
- root `QUALITY.md`
- build files that define the Java and JUnit versions
- existing tests near the affected code
- project-specific testing or quality skills under `.agents/`

## Rules

- Test observable behavior, not implementation details.
- Write or update a failing regression test before fixing a verified bug when practical.
- Keep fixtures small, explicit, deterministic, and clearly synthetic.
- Use temporary directories for filesystem output.
- Avoid shared mutable state, order-dependent tests, and external services by default.
- Use the repository's documented language for test names and comments.

## Verification

Run the narrowest relevant test first. Use project quality documentation for the applicable broader quality gate.
