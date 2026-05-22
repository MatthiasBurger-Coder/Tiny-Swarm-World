---
name: testing-junit6
description: Use when writing or reviewing JUnit 6 tests, deterministic fixtures, and regression coverage.
---

# JUnit 6

## Purpose

Guide deterministic unit, integration and architecture tests using the repository test baseline.

## Practices

- Test observable behavior rather than implementation details.
- Use descriptive English test names.
- Keep fixtures small, explicit and clearly synthetic.
- Avoid shared mutable test state and execution-order dependencies.
- Use temporary directories for filesystem output.

## Verification

- Run the narrowest relevant test task first.
- Run `./gradlew test --dependency-verification strict --console=plain --stacktrace` when the change affects shared behavior.
- Run the full gate from `QUALITY.md` for commit readiness.
