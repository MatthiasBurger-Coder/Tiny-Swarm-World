---
name: jenkins-bootstrap
description: Use for Jenkins bootstrap guidance without running Jenkins setup.
---

# Jenkins Bootstrap

## Purpose

Guide Jenkins service bootstrap documentation and configuration boundaries for
Tiny Swarm World.

## Responsibilities

- Keep Jenkins configuration, credentials and volumes explicit.
- Separate CI service bootstrap from local Python quality gates.
- Preserve service stack boundaries.

## Inputs

- Jenkins compose assets, bootstrap scripts, docs and workflow scope.
- Root `AGENTS.md`, `QUALITY.md` and service requirements.
- Security or credential constraints.

## Outputs

- Jenkins bootstrap guidance, risk notes and verification plan.
- STOP report for live-service or secret-handling blockers.

## Boundaries

- Do not run Jenkins bootstrap scripts or compose deployments unless explicitly
  requested.
- Do not make Jenkins required for the local quality gate.

## STOP conditions

- Credential or plugin setup is unclear.
- Verification would mutate a Jenkins instance.
- CI expectations conflict with root `QUALITY.md`.

## Collaboration with other skills

- Pair with `secrets-and-config-management`.
- Pair with `platform-quality-gates`.
- Pair with `swarm-stack-deployment` for service deployment boundaries.

## Quality expectations

- Run `git diff --check` for docs/config changes.
- Use mocked command tests for automation changes.
