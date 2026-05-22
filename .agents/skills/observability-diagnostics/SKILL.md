---
name: observability-diagnostics
description: Use for logging, metrics, diagnostics, redaction, and trace/correlation observability work.
---

# Observability

## Purpose

Guide logging, metrics and diagnostics without compromising sensitive forensic data.

## Practices

- Do not log secrets, credentials, personal data or unnecessary source content.
- Preserve trace and correlation identifiers when they are explicitly available.
- Keep diagnostic output separate from verified evidence.
- Avoid adding concrete logging providers unless explicitly required.
- Make sampling, retention and redaction behavior explicit.
- Apply `.agents/skills/resilience-engineering/SKILL.md` for retry provenance, failure diagnostics, health-check visibility, degraded-mode observability and secret-safe reporting.

## Verification

- Add tests for redaction or diagnostic formatting when behavior changes.
- Review logs and reports for sensitive-data exposure.
