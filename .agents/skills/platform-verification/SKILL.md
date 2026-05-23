---
name: platform-verification
description: Use for safe Tiny Swarm World platform verification planning and evidence reporting.
---

# Platform Verification

## Purpose

Define safe platform verification evidence without running live infrastructure
commands by default.

## Responsibilities

- Separate static repository checks, mocked tests and live platform checks.
- Record exact commands and whether they were executed or skipped.
- Keep required default gates aligned with root `QUALITY.md`.

## Inputs

- Active workflow, changed files, root quality contract and available command
  output.
- Platform behavior or documentation under review.
- Safety constraints from root `AGENTS.md`.

## Outputs

- Verification matrix, pass/fail/skipped summary and residual risk.
- STOP report for missing required evidence.

## Boundaries

- Do not run Multipass, Docker Swarm, compose, netplan, `socat` or service
  bootstrap commands unless explicitly requested.
- Do not claim live health without evidence.

## STOP conditions

- A required verification command is unsafe or unavailable.
- Evidence is inferred rather than observed.
- Quality gate failure cannot be classified.

## Collaboration with other skills

- Pair with `platform-quality-gates`.
- Pair with `image-verification` and service bootstrap skills.
- Pair with `observability-and-diagnostics` for diagnostic evidence.

## Quality expectations

- Run `git diff --check` for governance changes.
- Run full quality gate before commit or push when practical.
