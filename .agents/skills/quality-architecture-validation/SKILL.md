---
name: quality-architecture-validation
description: Use for the current project architecture validation, package-boundary checks, import-linter review, and module dependency verification.
---

# Architecture Validation

## Purpose

Validate package and module boundaries for architecture-sensitive changes.

## Practices

- Verify package ownership before changing dependencies.
- Keep domain and application free from adapters, infrastructure and provider APIs.
- Add import-linter contracts or architecture tests for new or changed architecture rules.
- Keep architecture docs synchronized with verified implementation.

## Verification

- Run affected architecture tests.
- Run the full gate from `QUALITY.md` when dependency direction or module boundaries change.
