# S352-05 distribution

Workflow: issue-352-configuration-parsing-boundary; workflowVersion 1.0.
Predecessor checkpoint: 273c2951; declared dependencies: ['S352-04'].
S3_STATUS: clean before slice execution; earlier unrelated Jenkins edits were separately committed as c6685c44. No overlapping changes permitted. S3_BRANCH: architecture/workflow-352-config-parsing-20260925 verified.
S3_SCOPE: exact affected files below; S3_CLASSIFY backend/tests (06 architecture/docs).
S3D: serial acyclic dependency chain; shared contracts/composition/evidence.
Execution mode: sequential; single backend/test writer, root consolidation.
Real subagents: Python implementer and read-only architecture/test reviewers.
Fallback: none. New worktrees: none; user requests branches in existing checkout.
Expected areas: ['configuration', 'deployment', 'platform', 'setup']. Frontend/live runtime changes: none.
File locks/allowed product and test writes:
- src/tiny_swarm_world/infrastructure/adapters/repositories/installer_configuration_repository.py
- tests/infrastructure/adapters/repositories/test_installer_configuration_repository.py
- src/tiny_swarm_world/application/services/deployment/workflows.py
- src/tiny_swarm_world/application/services/deployment/ensure_swarm_stack.py
- src/tiny_swarm_world/application/services/deployment/ensure_service_stack.py
- src/tiny_swarm_world/application/services/setup/workflow.py
- src/tiny_swarm_world/application/services/platform/preflight_service.py
- src/tiny_swarm_world/application/services/configuration/configuration_validation_service.py
- src/tiny_swarm_world/infrastructure/composition.py
- src/tiny_swarm_world/infrastructure/composition_deployment.py
- src/tiny_swarm_world/infrastructure/composition_setup.py
- src/tiny_swarm_world/infrastructure/composition_platform.py
- src/tiny_swarm_world/infrastructure/composition_runtime.py
- src/tiny_swarm_world/installer.py
- src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py
- tests/application/services/deployment/test_deployment_workflows.py
- tests/application/services/deployment/test_ensure_swarm_stack.py
- tests/application/services/deployment/test_ensure_service_stack.py
- tests/application/services/setup/test_setup_workflow.py
- tests/application/services/platform/test_preflight_service.py
- tests/infrastructure/test_composition.py
- tests/test_installer.py

Contract locks: ['configuration-validation-contract']; architecture locks: ['configuration-to-core-boundary'].
Parallel writing rejected due to overlapping files and dependent contracts.
Root owns issue/workflow evidence. Existing unrelated files stay untouched.
Required quality: targeted commands below, then full quality and diff check.
- `PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_deployment_workflows tests.application.services.deployment.test_ensure_swarm_stack tests.application.services.deployment.test_ensure_service_stack tests.application.services.setup.test_setup_workflow tests.application.services.platform.test_preflight_service tests.infrastructure.test_composition tests.test_installer tests.infrastructure.adapters.repositories.test_installer_configuration_repository`
- `git diff --check`
- `python3 tools/quality_gate.py quality`

Consolidation: accept only scope-verified implementation, tests and independent review; record evidence and one slice commit/push. No PR, merge, live infrastructure or cleanup.

Reviewed verification-scope correction before repair: `tests/test_install_script.py` is included in file locks/allowed writes after full-gate fixture failure; Architect and Test/Evidence accept complete-input fixture repair while preserving mocked subprocess boundaries. No additional product scope.
