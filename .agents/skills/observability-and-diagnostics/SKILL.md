---
name: observability-and-diagnostics
description: Use for logging, diagnostics and evidence reporting in Tiny Swarm World.
---

# Observability And Diagnostics

## Purpose

Guide observability and diagnostics decisions while preserving safe evidence
handling and redaction.

## Responsibilities

- Keep logs, metrics, status output and diagnostic evidence scoped and explicit.
- Preserve redaction of secrets, tokens and host-specific sensitive data.
- Distinguish runtime evidence from documentation or inferred state.

## Inputs

- Logging configuration, status output, diagnostics docs and workflow scope.
- Command output or failure evidence when provided.
- Root governance files.

## Outputs

- Diagnostic plan, redaction notes and evidence summary.
- STOP report for unsafe evidence handling.

## Boundaries

- Do not run live infrastructure diagnostics unless explicitly requested.
- Do not commit logs, secrets or local runtime artifacts.

## STOP conditions

- Evidence contains secrets that cannot be safely redacted.
- Diagnostic source or timestamp is unclear.
- The workflow would claim health without verified evidence.

## Collaboration with other skills

- Pair with `console-status-ui-developer`.
- Pair with `platform-verification`.
- Pair with `security-threat-modeling` or security roles for sensitive data.

## Quality expectations

- Run `git diff --check` for docs and governance changes.
- Add tests when diagnostics behavior changes.
