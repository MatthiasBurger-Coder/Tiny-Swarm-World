# Slice 01 Distribution: Issue 65 Backend Resource Mapping

Workflow id: `issue-65-backend-resource-mapping-20260614`
Slice id: `S01`
Slice title: Requirement, repository baseline, and decision gate

## Affected Areas

- `documentation/workflow/issues/issue-65/**`
- `infra/config/node-providers/**`
- `src/tiny_swarm_world/domain/node_provider/**`
- `src/tiny_swarm_world/infrastructure/adapters/**`
- `tests/**`

## Execution Mode

Sequential.

## Selected Streams

- requirements
- architecture
- tests

## Subagents

Real read-only subagent review used for repository baseline and implementation
risk assessment.

## Worktrees

Main issue worktree:

```text
../Tiny-Swarm-World-worktrees/issue-65-backend-resource-mapping
```

## Conflict Risks

- Backend-specific resource mapping must stay in configuration and
  infrastructure boundaries.
- Missing selected-backend mappings must fail before live mutation.
- Existing tests currently encode LXD-specific expectations for Incus paths.

## Quality Gates

- `git diff --check`
- `PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_node_provider_config_yaml_repository tests.infrastructure.adapters.clients.test_lxc_node_provider tests.infrastructure.test_composition`

## Consolidation Plan

Record repository baseline, classify requirements, and proceed to S02 only if
repository evidence shows a clear backend-aware configuration path without
architecture or live-infrastructure conflicts.
