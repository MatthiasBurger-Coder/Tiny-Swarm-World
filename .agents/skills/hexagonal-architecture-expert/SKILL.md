---
name: hexagonal-architecture-expert
description: Use for Tiny Swarm World hexagonal boundary decisions and dependency-direction review.
---

# Hexagonal Architecture Expert

## Purpose

Protect Tiny Swarm World's Python automation architecture from dependency
direction drift and technology leakage.

## Responsibilities

- Keep domain code independent from application and infrastructure concerns.
- Keep application services dependent on ports and domain objects.
- Keep command runners, YAML, Docker, filesystem, UI and external clients in
  infrastructure adapters.

## Inputs

- Root `AGENTS.md`, architecture docs and relevant Python modules.
- Current diff, import graph and tests.
- Active workflow scope.

## Outputs

- Boundary review, required refactor notes and verification commands.
- Architecture blockers when dependency direction is unclear.

## Boundaries

- Do not drive architecture from Java/Maven/Spring Boot project structure.
- Do not introduce browser React, Spring Boot or Kubernetes-first assumptions.

## STOP conditions

- A domain module would import infrastructure, YAML, logging or command runner
  code.
- Runtime wiring would move out of `infrastructure/composition.py` without an
  explicit architecture decision.
- Required architecture checks cannot run or are failing.

## Collaboration with other skills

- Pair with `python-senior-developer` for implementation guidance.
- Pair with `architecture-hexagonal` and `quality-architecture-validation`.
- Escalate cross-service contract concerns to contract governance skills.

## Quality expectations

- Run `python3 tools/quality_gate.py arch-lint` and `arch-tests` for boundary
  sensitive changes.
- Run the full quality gate before commit when practical.
