# Changed files — S352-01

- documentation/workflow/configuration-surface-inventory.md: verified inputs, consumers, compatibility, mutation timing and scope.
- .codex/evidence/slice-01-{distribution,consolidation}.md: S3/S3D, reviews and decisions.
- .tiny-swarm/evidence/issue-352/: initial six-file issue evidence package, all implementation requirements OPEN.
- documentation/workflow/{workflow.md,context-pack.json}: execution progress/context refresh.

## S352-02

- .codex/evidence/slice-02-distribution.md
- src/tiny_swarm_world/application/ports/file_management/port_local_file_storage.py
- src/tiny_swarm_world/application/ports/repositories/port_secret_manifest_repository.py
- src/tiny_swarm_world/application/services/deployment/secret_management.py
- src/tiny_swarm_world/domain/configuration/secret_manifest.py
- src/tiny_swarm_world/infrastructure/adapters/file_management/local_file_storage.py
- src/tiny_swarm_world/infrastructure/adapters/repositories/secret_manifest_yaml_repository.py
- src/tiny_swarm_world/infrastructure/composition_deployment.py
- src/tiny_swarm_world/infrastructure/composition_runtime.py
- src/tiny_swarm_world/installer.py
- tests/application/services/deployment/test_secret_management.py
- tests/domain/configuration/test_secret_manifest.py
- tests/infrastructure/adapters/repositories/test_secret_manifest_yaml_repository.py
- tests/test_installer.py

## S352-03

- .codex/evidence/slice-03-distribution.md
- src/tiny_swarm_world/domain/inventory/desired_inventory.py
- src/tiny_swarm_world/infrastructure/adapters/configuration/configuration_sources.py
- src/tiny_swarm_world/infrastructure/adapters/repositories/command_repository_yaml.py
- src/tiny_swarm_world/infrastructure/adapters/repositories/desired_inventory_yaml_repository.py
- src/tiny_swarm_world/infrastructure/adapters/repositories/node_provider_config_yaml_repository.py
- src/tiny_swarm_world/infrastructure/adapters/repositories/port_registry_yaml_repository.py
- src/tiny_swarm_world/installer.py
- tests/domain/inventory/test_inventory_model.py
- tests/infrastructure/adapters/configuration/test_configuration_sources.py
- tests/infrastructure/adapters/repositories/test_command_repository_yaml_contract.py
- tests/infrastructure/adapters/repositories/test_inventory_repositories.py
- tests/infrastructure/adapters/repositories/test_node_provider_config_yaml_repository.py
- tests/infrastructure/adapters/repositories/test_port_registry_yaml_repository.py
- tests/test_installer.py

## S352-04

- .codex/evidence/slice-04-distribution.md
- src/tiny_swarm_world/application/ports/repositories/port_compose_file_repository.py
- src/tiny_swarm_world/domain/deployment/stack_definition.py
- src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py
- tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py
