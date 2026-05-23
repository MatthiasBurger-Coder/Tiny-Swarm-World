---
name: platform-layout-governance
description: Use for repository layout and documentation path governance in Tiny Swarm World.
---

# Platform Layout Governance

## Purpose

Keep Tiny Swarm World files in their documented repository locations and avoid
parallel legacy path structures.

## Responsibilities

- Preserve `documentation/` as the canonical docs root.
- Keep `infra/config`, `infra/compose`, `infra/prepare` and `infra/swarm`
  responsibilities distinct.
- Prevent host-specific paths, generated caches and local environment files from
  entering committed configuration.

## Inputs

- Repository map from root `AGENTS.md`.
- Current file paths, workflow scope and documentation references.
- Proposed new files or moved files.

## Outputs

- Layout decision, path mapping and stale-reference notes.
- STOP report when a proposed path conflicts with repository conventions.

## Boundaries

- Do not create a root `docs/` tree unless the workflow explicitly decides it.
- Do not move runtime wiring or adapters as part of documentation cleanup.

## STOP conditions

- A path decision would contradict root `AGENTS.md`.
- A moved file still has unresolved references.
- The active slice does not own the affected path.

## Collaboration with other skills

- Pair with `documentation-generation`.
- Pair with `workflow-orchestration` for workflow artifact paths.
- Escalate runtime layout changes to `tiny-swarm-world-system-architecture`.

## Quality expectations

- Run reference searches and `git diff --check`.
- Run full quality gate when executable files move.
