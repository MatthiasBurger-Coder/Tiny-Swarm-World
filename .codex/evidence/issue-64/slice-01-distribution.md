# Slice 01 Distribution: Issue 64 Backend Selection Order

Workflow id: `issue-64-backend-selection-order-20260614`
Slice id: `S01`
Slice title: Requirement, repository baseline, and decision gate

## Affected Areas

- `documentation/workflow/issues/issue-64/**`
- `infra/config/node-providers/**`
- `src/tiny_swarm_world/domain/node_provider/**`

## Execution Mode

Sequential baseline analysis.

## Subagents

Real subagent review requested from the Senior Requirement Engineer and Senior
System Architect stream.

## Selected Streams

- requirements
- architecture
- tests

## Worktrees

Main issue worktree:

```text
../Tiny-Swarm-World-worktrees/issue-64-backend-selection-order
```

## Conflict Risks

- Backend selection spans configuration, application ports, infrastructure
  preflight adapters, and tests.
- Config reading must remain in infrastructure; application services must not
  depend on concrete YAML repositories.

## Quality Gates

- `PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.preflight.test_lxc_provider_preflight tests.infrastructure.adapters.repositories.test_node_provider_config_yaml_repository tests.application.services.platform.test_node_provider_selection`
- `git diff --check`

## Consolidation Plan

Record issue requirements, repository baseline, and S02 implementation target
files before write-capable backend selection changes.
