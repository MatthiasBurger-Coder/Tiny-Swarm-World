---
name: workflow-orchestration
description: Use for Tiny Swarm World workflow slice sequencing, locks and role handoff.
---

# Workflow Orchestration

## Purpose

Coordinate Tiny Swarm World workflow slices through explicit dependencies,
owners, locks and verification gates.

## Responsibilities

- Validate active workflow branch and slice scope.
- Keep S3/S3D dependency, lock and handoff decisions explicit.
- Prevent push, commit or cleanup semantics from leaking across process strands.

## Inputs

- Active workflow files, context pack and execution report.
- Current git branch/status and role reviews.
- Slice metadata and quality gates.

## Outputs

- Execution plan, handoff notes and blocker classification.
- STOP report for dependency, lock or branch conflicts.

## Boundaries

- Do not call `workflow create` during `workflow execute`.
- Do not force parallel work when locks overlap.
- Do not commit or push unless the active workflow and user request authorize it.

## STOP conditions

- Active branch is wrong or local ref is missing.
- Dependency graph contains unknown IDs or cycles.
- Worktree changes are unrelated or unclear.

## Collaboration with other skills

- Pair with `s3d-execution-orchestrator` and `agent-swarm-coordination-specialist`.
- Pair with `agent-handoff-protocol`.
- Escalate quality failures through the Typed Error Router.

## Quality expectations

- Run branch/status checks before writes.
- Run `git diff --check` after workflow documentation changes.
