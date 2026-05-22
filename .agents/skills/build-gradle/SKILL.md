---
name: build-gradle
description: Use for Gradle build logic, tasks, dependency verification, toolchains, and quality-gate alignment.
---

# Gradle

## Purpose

Guide build changes while preserving dependency verification, toolchains and task correctness.

## Practices

- Use the Gradle wrapper through WSL on Windows hosts.
- Verify task names in build files before referencing them.
- Keep task inputs and outputs explicit.
- Avoid resolving files eagerly during configuration.
- Do not weaken dependency verification or coverage thresholds.

## Verification

- Run targeted Gradle tasks first.
- Run the authoritative full local gate from `QUALITY.md` before commit readiness.
- Run `validatePlugins` only when plugin metadata or Gradle plugin implementation changes require it.
