# Issue #232 changed-file map

The workflow branch range starts at the workflow-create baseline and includes
the following product, test, documentation and evidence surfaces.

## Governance and workflow

- `documentation/workflow/workflow.md`
- `documentation/workflow/context-pack.json`
- `documentation/arc42/11_risks_and_debt.adoc`
- `.codex/evidence/issue-232/slice-01-distribution.md` through
  `slice-07-distribution.md`
- `.codex/evidence/issue-232/slice-01-consolidation.md` through
  `slice-06-consolidation.md`

## Application and domain

- `src/tiny_swarm_world/application/ports/file_management/port_local_file_storage.py`
- `src/tiny_swarm_world/application/ports/preflight/port_artifact_contract_inventory.py`
- `src/tiny_swarm_world/application/ports/preflight/port_live_readiness.py`
- `src/tiny_swarm_world/application/ports/preflight/__init__.py`
- `src/tiny_swarm_world/application/ports/repositories/port_compose_file_repository.py`
- `src/tiny_swarm_world/application/services/artifacts/__init__.py`
- `src/tiny_swarm_world/application/services/artifacts/workflows.py`
- `src/tiny_swarm_world/application/services/artifacts/static_contract_preflight.py`
- `src/tiny_swarm_world/application/services/artifacts/readiness_gate.py`
- `src/tiny_swarm_world/domain/artifacts/container_image_contract.py`
- `src/tiny_swarm_world/domain/artifacts/__init__.py`
- `src/tiny_swarm_world/domain/deployment/stack_definition.py`
- `src/tiny_swarm_world/domain/inventory/verification.py`
- `src/tiny_swarm_world/domain/inventory/__init__.py`
- `src/tiny_swarm_world/domain/preflight/readiness.py`
- `src/tiny_swarm_world/domain/preflight/__init__.py`
- `src/tiny_swarm_world/domain/preflight/installation_plan.py`

## Infrastructure and tests

- `src/tiny_swarm_world/infrastructure/adapters/file_management/local_file_storage.py`
- `src/tiny_swarm_world/infrastructure/adapters/preflight/artifact_readiness.py`
- `src/tiny_swarm_world/infrastructure/adapters/preflight/__init__.py`
- `src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py`
- `src/tiny_swarm_world/infrastructure/composition.py`
- `tests/application/services/artifacts/**`
- `tests/application/services/setup/test_setup_workflow.py`
- `tests/domain/artifacts/**`
- `tests/domain/inventory/test_inventory_model.py`
- `tests/domain/preflight/test_preflight_result.py`
- `tests/domain/preflight/test_readiness.py`
- `tests/infrastructure/adapters/file_management/test_file_manager.py`
- `tests/infrastructure/adapters/preflight/test_artifact_readiness.py`
- `tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py`
- `tests/infrastructure/test_composition.py`

## Issue evidence

- `.tiny-swarm/evidence/issue-232/requirement_matrix.md`
- `.tiny-swarm/evidence/issue-232/implementation_summary.md`
- `.tiny-swarm/evidence/issue-232/changed_files.md`
- `.tiny-swarm/evidence/issue-232/test_results.md`
- `.tiny-swarm/evidence/issue-232/remaining_risks.md`
- `.tiny-swarm/evidence/issue-232/acceptance_checklist.md`
