---
name: agent-swarm-coordination-specialist
description: Use for dependency graph planning, slice orchestration, multi-agent collaboration, conflict resolution, merge coordination, artifact handoff, and review pipelines.
---

# Skill: Agent Swarm Coordination Specialist

## Description

Guides coordinated multi-agent planning for the current project while keeping edits scoped and reviewable.

## Instructions

1. Verify the user explicitly requested delegated or parallel agent work before spawning subagents.
2. Build a dependency graph of slices, shared files, shared contracts, module or architecture-boundary locks, ownership boundaries, and review responsibilities.
3. Keep common interfaces fixed before parallel implementation begins.
4. Assign non-overlapping file ownership to write-capable workers.
5. Coordinate artifact handoff, review pipelines, conflict resolution, merge coordination, and autonomous execution planning.
6. Route architecture, backend, gRPC/proto, Git/workspace, storage, security, performance, Joern/CPG, documentation, and quality reviews to the matching roles.
7. Document conflicts instead of silently choosing a side when repository evidence is incomplete.

## Expected Inputs

- user task and acceptance criteria
- `.agents/roles`
- `.codex/agents`
- repository workflow
- current git status and diff
- quality-gate requirements

## Expected Outputs

- slice dependency graph
- parallel worker coordination plan
- file, contract, module and architecture-boundary lock map
- owner and reviewer map
- handoff artifacts
- conflict and merge-risk notes

## Boundaries

- Do not spawn subagents without explicit authorization from the user or active workflow.
- Do not allow multiple workers to edit the same files without a clear ordering.
- Do not bypass read-only verification or commit-readiness review.

## Stop Conditions

Stop if:

- slice dependencies cannot be determined;
- changed-file ownership is unclear;
- concurrent edits would risk overwriting user or worker changes;
- review evidence is missing for commit readiness.
