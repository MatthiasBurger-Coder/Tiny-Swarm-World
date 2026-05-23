---
name: documentation-generation
description: Use for generating and synchronizing Tiny Swarm World documentation.
---

# Documentation Generation

## Purpose

Create and synchronize Tiny Swarm World documentation while keeping product
behavior, verified evidence and recommendations distinct.

## Responsibilities

- Keep documentation aligned with Linux/WSL-only operation and POSIX paths.
- Update relevant `documentation/` files when behavior or process changes.
- Avoid stale references to missing skills, roles, workflows or directories.

## Inputs

- Root `AGENTS.md`, `QUALITY.md`, README and relevant documentation.
- Active workflow scope, changed files and verification evidence.
- Existing role, skill or process references.

## Outputs

- Documentation updates, reference checks and synchronization notes.
- STOP report for unresolved documentation/source conflicts.

## Boundaries

- Do not create root `docs/` unless explicitly authorized.
- Do not claim quality or live infrastructure checks passed when skipped.

## STOP conditions

- Documentation points to missing files or unsupported commands.
- Source and documentation disagree in a behavior-relevant way.
- Required evidence is missing.

## Collaboration with other skills

- Pair with `platform-layout-governance`.
- Pair with `llm-analysis-expert` for evidence-labeled summaries.
- Pair with `workflow-orchestration` for workflow reports.

## Quality expectations

- Run `git diff --check`.
- Run targeted reference searches for renamed skills and paths.
