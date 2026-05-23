---
name: tiny-swarm-world-system-architecture
description: Use for Tiny Swarm World system architecture governance and project identity checks.
---

# Tiny Swarm World System Architecture

## Purpose

Preserve Tiny Swarm World's identity as a Linux/WSL-only Python automation
project for Multipass-backed Docker Swarm environments.

## Responsibilities

- Keep Python automation architecture distinct from Java deployment examples.
- Maintain Docker Swarm-first and Kubernetes-aware positioning.
- Align system decisions with arc42, root `AGENTS.md` and `QUALITY.md`.

## Inputs

- Root governance files, arc42 docs, README and active workflow scope.
- Architecture-sensitive changes or documentation.
- Current repository layout.

## Outputs

- System architecture review notes and required documentation updates.
- STOP report for project identity drift.

## Boundaries

- Do not reclassify the project as Spring Boot, React, forensic analytics or
  Kubernetes-first.
- Do not authorize product runtime changes from governance-only workflows.

## STOP conditions

- Architecture identity conflicts with root `AGENTS.md`.
- A change would make Java drive Python automation architecture.
- Required arc42 or quality authority is unclear.

## Collaboration with other skills

- Pair with `hexagonal-architecture-expert`.
- Pair with `platform-layout-governance` and `workflow-orchestration`.
- Escalate process governance changes to the Senior Workflow Architect.

## Quality expectations

- Run `git diff --check` for architecture documentation changes.
- Run architecture gates when Python module boundaries change.
