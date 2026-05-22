---
name: devops-ci-cd
description: Use for CI/CD workflow changes, local CI equivalents, and quality-command alignment.
---

# CI/CD

## Purpose

Guide continuous integration and delivery changes.

## Practices

- Verify existing workflow files before changing CI behavior.
- Keep CI commands aligned with `QUALITY.md`.
- Do not require external credentials for default local verification.
- Treat optional external checks as additive and report skipped credentials.
- Keep artifacts deterministic and avoid committing generated analysis output.
- Apply `.agents/skills/resilience-engineering/SKILL.md` for CI retry policy, timeout, dependency-health, artifact cleanup, diagnostic redaction and quality-gate degradation decisions.

## Verification

- Run local equivalents of changed CI commands where feasible.
- Report any CI command that cannot be validated locally.
