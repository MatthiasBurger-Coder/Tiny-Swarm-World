# Slice 02 Distribution: Issue 65 Implementation

Workflow id: `issue-65-backend-resource-mapping-20260614`
Slice id: `S02`
Slice title: Scoped implementation inside the declared architecture boundary

## Affected Areas

- `infra/config/node-providers/provider_config.yaml`
- `src/tiny_swarm_world/infrastructure/adapters/repositories/node_provider_config_yaml_repository.py`
- `src/tiny_swarm_world/infrastructure/adapters/clients/lxc_node_provider.py`
- `tests/infrastructure/adapters/repositories/test_node_provider_config_yaml_repository.py`
- `tests/infrastructure/adapters/clients/test_lxc_node_provider.py`

## Execution Mode

Sequential implementation.

## Selected Streams

- backend
- tests
- architecture

## Subagents

Real read-only subagent review used after implementation.

## Worktrees

Main issue worktree:

```text
../Tiny-Swarm-World-worktrees/issue-65-backend-resource-mapping
```

## Conflict Risks

- Schema migration must fail closed and be documented in S04.
- Resource mapping must remain in infrastructure/configuration boundaries.
- Evidence must remain summary-only and avoid raw command-like remediation text.

## Quality Gates

- `git diff --check`
- `PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_node_provider_config_yaml_repository tests.infrastructure.adapters.clients.test_lxc_node_provider`
- `PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition tests.infrastructure.adapters.preflight.test_lxc_provider_preflight tests.application.services.platform.test_node_provider_selection`
- `python3 tools/quality_gate.py lint`
- `python3 tools/quality_gate.py typecheck`

## Consolidation Plan

Accept the backend-aware resource mapping implementation only if focused tests,
typecheck, lint, evidence safety, and subagent review pass.
