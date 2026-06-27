# Slice 03 Distribution

Workflow ID: `workflow-project-paths-di-20260627`
Workflow version: `workflow-project-paths-di-v1.0.0`
Slice ID: `03`
Slice title: `Wire ProjectPaths Through Composition And Adapters`

## Affected Areas

- backend: composition root and infrastructure adapters
- tests: composition, repository, local-state, and architecture checks
- architecture: dependency direction and adapter constructor boundaries

## Execution Mode

Sequential.

Parallel execution is rejected because multiple streams would touch the same
adapter constructors, composition wiring, and tests.

## Streams

- backend: Senior Python Automation Developer
- tests: Senior Tester
- architecture: Senior System Architect

Real subagents used: no.

Fallback role-based review used: yes.

Git worktrees used: no.

## Expected Touched Files

- `src/tiny_swarm_world/infrastructure/composition.py`
- `src/tiny_swarm_world/infrastructure/adapters/file_management/file_manager.py`
- `src/tiny_swarm_world/infrastructure/adapters/file_management/file_locator.py`
- `src/tiny_swarm_world/infrastructure/adapters/repositories/desired_inventory_yaml_repository.py`
- `src/tiny_swarm_world/infrastructure/adapters/repositories/node_provider_config_yaml_repository.py`
- `src/tiny_swarm_world/infrastructure/adapters/repositories/port_registry_yaml_repository.py`
- `src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py`
- `src/tiny_swarm_world/infrastructure/adapters/repositories/local_state_paths.py`
- `src/tiny_swarm_world/infrastructure/adapters/preflight/host_preflight_probe.py`
- `src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py`
- `src/tiny_swarm_world/infrastructure/logging/logger_factory.py`
- `tests/infrastructure/test_composition.py`
- `tests/infrastructure/adapters/repositories/test_command_repository_yaml_contract.py`
- `tests/architecture/test_local_state_storage.py`
- `.codex/evidence/workflow-project-paths-di-20260627/slice-03-consolidation.md`

## Conflict Risks

- Medium. Constructor changes can affect many tests.
- Mitigation: keep all new `ProjectPaths` parameters optional and preserve
  explicit path/root overrides.

## Quality Gates

- `PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition`
- `PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_command_repository_yaml_contract`
- `PYTHONPATH=src python3 -m unittest tests.architecture.test_local_state_storage`
- `python3 tools/quality_gate.py arch-tests`

## Consolidation Plan

Migrate targeted infrastructure consumers, run targeted gates, inspect import
boundaries, then commit and push only Slice 03 files.
