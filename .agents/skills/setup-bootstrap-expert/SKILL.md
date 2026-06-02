---
name: setup-bootstrap-expert
description: Use for developer environment bootstrap guidance without running platform service bootstrap.
---

# Setup Bootstrap Expert

## Purpose

Guide Tiny Swarm World developer setup and bootstrap documentation while
keeping service bootstrap and live infrastructure operations out of normal
development verification.

## Responsibilities

- Separate developer environment setup from service, VM and platform bootstrap.
- Keep setup instructions Linux/WSL-only and POSIX-path oriented.
- Validate required tools and quality commands without mutating platform state.

## Inputs

- README, setup documentation, `requirements.txt`, `QUALITY.md` and workflow
  context.
- User setup requirement or failure report.
- Current operating assumptions from root `AGENTS.md`.

## Outputs

- Setup guidance, prerequisite list and verification plan.
- STOP report for live bootstrap or host-specific requirements.

## Boundaries

- Do not run LXD, Incus, LXC, Docker Swarm, compose deployment, netplan, `socat` or
  service bootstrap scripts unless explicitly requested.
- Do not add Windows-native runtime behavior.

## STOP conditions

- Setup would require credentials, secrets or host-specific absolute paths.
- Developer setup is confused with service bootstrap.
- Verification would mutate infrastructure.

## Collaboration with other skills

- Pair with `python-pip-packaging-expert`.
- Pair with `linux-host-preparation` for documented host prerequisites.
- Pair with `platform-verification` for non-mutating checks.

## Quality expectations

- Run `git diff --check` for setup documentation changes.
- Run the Python quality gate when executable setup behavior changes.
