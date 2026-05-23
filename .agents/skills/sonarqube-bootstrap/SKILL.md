---
name: sonarqube-bootstrap
description: Use for SonarQube bootstrap guidance without adding external static-analysis CI by default.
---

# SonarQube Bootstrap

## Purpose

Guide SonarQube service bootstrap documentation while keeping external analysis
optional unless explicitly adopted.

## Responsibilities

- Keep SonarQube service, credentials and quality-profile setup explicit.
- Prevent Sonar from replacing root `QUALITY.md`.
- Report optional external checks as skipped unless credentials and runtime are
  available and requested.

## Inputs

- SonarQube compose assets, bootstrap docs, scripts and workflow scope.
- Root `QUALITY.md` and service requirements.
- Credential and token handling rules.

## Outputs

- SonarQube bootstrap guidance and verification notes.
- STOP report for unsupported CI or secret handling.

## Boundaries

- Do not run SonarQube bootstrap, analysis or compose deployment commands unless
  explicitly requested.
- Do not introduce external static-analysis CI configuration by default.

## STOP conditions

- Token or credential handling is unclear.
- External analysis would be treated as required without workflow authority.
- Verification would mutate a SonarQube service.

## Collaboration with other skills

- Pair with `platform-quality-gates`.
- Pair with `secrets-and-config-management`.
- Pair with `sca-migration-expert` for analysis migration concerns.

## Quality expectations

- Run `git diff --check` for docs/config changes.
- Keep Python quality gate as the default repository gate.
