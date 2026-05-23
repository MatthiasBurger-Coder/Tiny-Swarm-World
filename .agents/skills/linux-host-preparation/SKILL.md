---
name: linux-host-preparation
description: Use for Linux or WSL host prerequisite guidance for Tiny Swarm World.
---

# Linux Host Preparation

## Purpose

Document and validate host preparation expectations for Linux/WSL users without
adding Windows-native runtime behavior.

## Responsibilities

- Keep prerequisite instructions POSIX-path and Linux/WSL-oriented.
- Separate host preparation from service bootstrap.
- Identify safe non-mutating checks where possible.

## Inputs

- README, setup docs, host prerequisite notes and workflow scope.
- Root operating assumptions.
- User setup requirement or failure report.

## Outputs

- Host prerequisite guidance and verification notes.
- STOP report for unsupported host mutations.

## Boundaries

- Do not add PowerShell or backslash-path examples unless legacy cleanup asks
  for them.
- Do not run netplan, Docker, Multipass or service bootstrap commands.

## STOP conditions

- Host change would be destructive or environment-specific.
- Required privilege, credential or secret handling is unclear.
- Documentation would contradict the Linux/WSL-only model.

## Collaboration with other skills

- Pair with `setup-bootstrap-expert`.
- Pair with `network-topology-design` for documented networking prerequisites.
- Pair with `platform-verification` for safe checks.

## Quality expectations

- Run `git diff --check` for documentation changes.
- Run full quality gate when executable setup logic changes.
