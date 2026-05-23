---
name: secrets-and-config-management
description: Use for secret handling and configuration governance in Tiny Swarm World.
---

# Secrets And Config Management

## Purpose

Protect Tiny Swarm World configuration from committed secrets, host-specific
values and unsafe credential handling.

## Responsibilities

- Keep secrets out of committed YAML, compose, docs and scripts.
- Prefer placeholders and documented environment-specific setup.
- Review config paths, permissions and redaction expectations.

## Inputs

- Configuration files, compose assets, docs, scripts and workflow scope.
- Credential or secret-handling requirements.
- Root safety and quality rules.

## Outputs

- Secret-handling guidance, risk notes and verification commands.
- STOP report for unsafe credential exposure.

## Boundaries

- Do not invent credentials, tokens or host-specific endpoints.
- Do not run bootstrap commands that create or rotate secrets unless explicitly
  requested.

## STOP conditions

- A proposed change would commit a secret or private endpoint.
- Required credential source is unclear.
- Redaction or rotation expectations are undefined.

## Collaboration with other skills

- Pair with registry and service bootstrap skills.
- Pair with `security-threat-modeling`.
- Pair with `observability-and-diagnostics` for log redaction.

## Quality expectations

- Run `git diff --check` and targeted secret/reference searches.
- Run broader gates when executable config-loading behavior changes.
