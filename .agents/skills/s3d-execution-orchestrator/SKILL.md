---
name: s3d-execution-orchestrator
description: Builds workflow-execute dependency graphs, validates slice metadata, creates topological execution groups, checks file/contract/module/architecture locks, and returns EXECUTION_PLAN, LOCK_CONFLICT, or ORCHESTRATION_BLOCKER before write-capable work starts.
---

# Skill: S3D Execution Orchestrator

## Mission

Plan safe workflow slice execution before write-capable work starts.

S3D belongs to the `workflow execute` strand. It is not a fourth process
strand and must not rewrite workflow-create artifacts.

## Required Inputs

- Checked active `documentation/workflow/workflow.md`.
- Slice YAML metadata.
- Dependency map.
- Current branch and workflow branch.
- Current git status.
- File, contract, module and architecture-boundary locks.

## Validation Steps

1. Verify every slice has machine-readable metadata.
2. Verify every dependency is a concrete existing slice ID.
3. Build a directed dependency graph.
4. Reject cycles before implementation.
5. Build topological execution groups.
6. Validate file locks, contract locks, module locks and architecture locks.
7. Decide whether execution is serial or parallel.
8. Return a structured result.

## Result Contract

Return one of:

```text
EXECUTION_PLAN
```

with:

- ordered slice IDs;
- topological groups;
- serial or parallel decision;
- lock sets;
- required owners and reviewers;
- quality gates.

```text
LOCK_CONFLICT
```

with:

- conflicting slice IDs;
- conflicting locks;
- owning roles;
- recommended escalation route.

```text
ORCHESTRATION_BLOCKER
```

with:

- missing metadata, unknown dependency, dependency cycle or unverifiable scope;
- inspected files;
- reason continuing would be unsafe.

## Forbidden

- Do not implement slice changes.
- Do not mutate workflow files during S3D.
- Do not call `workflow create`.
- Do not infer missing slice IDs, locks, modules, contracts or owners.
- Do not allow parallel work when locks overlap.
- Do not mark a quality gate passed or optional.

## STOP Rules

Stop before implementation when:

- metadata is missing;
- dependencies use ranges or prose instead of concrete slice IDs;
- a dependency references an unknown slice;
- the dependency graph contains a cycle;
- file, contract, module or architecture locks overlap;
- owner or reviewer cannot be verified;
- the active branch or worktree status is unsafe.
