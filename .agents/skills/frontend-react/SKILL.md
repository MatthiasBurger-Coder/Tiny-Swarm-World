---
name: frontend-react
description: Use for React frontend work only after verifying that the repository has a frontend module.
---

# React

## Purpose

Guide React implementation when a verified frontend module exists.

## Practices

- Follow the existing frontend framework, state and styling conventions.
- Keep API access behind adapters or hooks that are testable.
- Apply `.agents/skills/resilience-engineering/SKILL.md` for UI timeouts, bounded retries, cancellation, partial failure states, diagnostics and graceful degradation decisions.
- Preserve evidence categories and verification status in UI state.
- Build accessible controls with clear focus and keyboard behavior.
- Avoid marketing-style layouts for operational analysis tools.

## Verification

- Inspect package files before adding dependencies or scripts.
- Run the verified frontend test/build commands and the repository checks required by `QUALITY.md`.
