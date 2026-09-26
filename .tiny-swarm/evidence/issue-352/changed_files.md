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

## S352-05

- .codex/evidence/slice-05-distribution.md
- .tiny-swarm/evidence/issue-352/remaining_risks.md
- documentation/workflow/context-pack.json
- documentation/workflow/context-pack.md
- documentation/workflow/workflow.md
- src/tiny_swarm_world/application/services/configuration/configuration_validation_service.py
- src/tiny_swarm_world/application/services/deployment/ensure_service_stack.py
- src/tiny_swarm_world/application/services/deployment/ensure_swarm_stack.py
- src/tiny_swarm_world/application/services/deployment/workflows.py
- src/tiny_swarm_world/infrastructure/adapters/repositories/installer_configuration_repository.py
- src/tiny_swarm_world/infrastructure/composition_deployment.py
- src/tiny_swarm_world/infrastructure/composition_platform.py
- src/tiny_swarm_world/infrastructure/composition_runtime.py
- src/tiny_swarm_world/infrastructure/composition_setup.py
- src/tiny_swarm_world/installer.py
- tests/application/services/deployment/test_deployment_workflows.py
- tests/application/services/deployment/test_ensure_service_stack.py
- tests/application/services/deployment/test_ensure_swarm_stack.py
- tests/infrastructure/adapters/repositories/test_installer_configuration_repository.py
- tests/infrastructure/test_composition.py
- tests/test_install_script.py
- tests/test_installer.py

## S352-06

- .codex/evidence/slice-06-distribution.md
- .tiny-swarm/evidence/issue-352/acceptance_checklist.md
- .tiny-swarm/evidence/issue-352/implementation_summary.md
- .tiny-swarm/evidence/issue-352/remaining_risks.md
- .tiny-swarm/evidence/issue-352/requirement_matrix.md
- .tiny-swarm/evidence/issue-352/test_results.md
- documentation/arc42/05_analysis/arch-03-09-configuration-parsing-boundary.md
- documentation/arc42/05_building_blocks.adoc
- documentation/arc42/08_concepts.adoc
- documentation/arc42/08_configuration/config-contract-inventory.md
- documentation/arc42/08_configuration/operator-configuration-contract.md
- documentation/process/skills/audit/skill-registry.json
- documentation/workflow/context-pack.json
- documentation/workflow/requirement-matrix.md
- documentation/workflow/workflow.md
- tests/architecture/test_hexagonal_imports.py

S352-06 also refreshes all six issue-evidence files and its consolidation record. Separate unrelated Jenkins commit c6685c44 is excluded from issue attribution.

Final independent audit record: `.tiny-swarm/evidence/issue-352/completion_audit.md`.
