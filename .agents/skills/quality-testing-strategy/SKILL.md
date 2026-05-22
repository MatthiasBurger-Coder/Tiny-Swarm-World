---
name: quality-testing-strategy
description: Use for test planning, regression-first workflow, deterministic fixtures, and evidence-integrity coverage.
---

# Testing Strategy

## Purpose

Define test coverage for small slices without weakening repository quality rules.

## Practices

- Use regression-first workflow for bug fixes.
- Prefer narrow tests for small changes and broader tests for shared contracts.
- Keep integration tests deterministic and isolated from external services by default.
- Verify forensic semantics: provenance, ordering, explicit gaps and evidence categories.
- Use temporary directories and synthetic fixtures in tests.

## Verification

- Run targeted tests first.
- Run `python3 tools/quality_gate.py test` for shared behavior, and the full gate from `QUALITY.md` for broader readiness.
- Run the full gate from `QUALITY.md` for commit readiness.
