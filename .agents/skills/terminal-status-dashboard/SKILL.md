---
name: terminal-status-dashboard
description: Use for terminal dashboard and dense operational status views in Tiny Swarm World.
---

# Terminal Status Dashboard

## Purpose

Guide terminal dashboard views for repeated inspection of Tiny Swarm World
local platform state.

## Responsibilities

- Keep dashboards compact, readable and evidence-based.
- Preserve clear states for unknown, pending, failed and verified statuses.
- Avoid layout choices that hide errors or recovery steps.

## Inputs

- Status data models, CLI output, diagnostics and workflow scope.
- User workflow needs and test fixtures.
- Root `AGENTS.md` and `QUALITY.md`.

## Outputs

- Terminal dashboard guidance, state model notes and verification plan.
- STOP report for unclear evidence or scope drift.

## Boundaries

- Do not introduce browser UI, React or frontend build tooling.
- Do not poll or mutate live infrastructure unless explicitly requested.

## STOP conditions

- Dashboard data source cannot be verified.
- Unknown state would be displayed as healthy.
- Terminal behavior cannot be tested deterministically.

## Collaboration with other skills

- Pair with `console-status-ui-developer`.
- Pair with `observability-and-diagnostics`.
- Pair with `platform-verification`.

## Quality expectations

- Add deterministic rendering or formatting tests when behavior changes.
- Run `git diff --check` for documentation-only changes.
