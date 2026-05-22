---
name: quality-gate-governance
description: Use for quality-gate selection, command reporting, dependency verification, coverage, and optional external checks.
---

# Quality Gates

## Purpose

Use the repository quality contract without replacing or weakening it.

## Authoritative Commands

`QUALITY.md` is the source of truth. The default minimum Python test command is:

```bash
python3 tools/quality_gate.py test
```

The full local gate is:

```bash
python3 tools/quality_gate.py quality
```

## Practices

- Do not claim a command passed unless it was executed.
- Report exact failing tasks and suspected relation to the current change.
- Skip optional external checks only when credentials or services are unavailable, and report the skip.
- Apply `.agents/skills/resilience-engineering/SKILL.md` for quality-gate timeout, retry, health-check, diagnostics, cleanup and degraded-verification decisions.
