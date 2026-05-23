---
name: docker-engine-installation
description: Use for Docker engine installation guidance in Tiny Swarm World setup documentation.
---

# Docker Engine Installation

## Purpose

Guide Docker engine installation documentation and automation boundaries for
Tiny Swarm World hosts and VMs.

## Responsibilities

- Keep Docker installation steps explicit, idempotent and Linux/WSL-oriented.
- Separate installation documentation from live execution.
- Preserve command execution through infrastructure adapters.

## Inputs

- Docker setup docs, scripts, command templates and tests.
- Root `AGENTS.md`, `QUALITY.md` and active workflow scope.
- Installation requirement or failure report.

## Outputs

- Installation guidance, safety notes and verification plan.
- STOP report when live installation would be required.

## Boundaries

- Do not run Docker installation or package-manager commands unless explicitly
  requested.
- Do not make Docker checks part of default quality gates unless documented.

## STOP conditions

- Installation target or privileges are unclear.
- A change would run installation at import time or constructor time.
- Verification would mutate the host or VM.

## Collaboration with other skills

- Pair with `linux-host-preparation`.
- Pair with `docker-swarm-initialization`.
- Escalate command orchestration to `python-cli-automation`.

## Quality expectations

- Mock installation commands in tests.
- Run `git diff --check` for docs and focused tests for behavior changes.
