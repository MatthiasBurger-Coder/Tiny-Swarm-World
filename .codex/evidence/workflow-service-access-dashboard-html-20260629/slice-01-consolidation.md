# Slice 01 Consolidation Evidence

Workflow: workflow-service-access-dashboard-html-20260629
Slice: 01 - regression tests
Date: 2026-06-29

Changes:

- Added runtime regression coverage proving Service Access dashboard asset transfer must use generated dashboard HTML, not the committed static dashboard file.
- Added composition regression coverage proving `LxcSwarmRuntime` must receive the compose repository dashboard renderer without calling it during construction.
- Updated composition expectations so the apply workflow visibly exposes `deployment:service-access-stack-assets` as a pre-apply step.

RED verification:

- Command: `wsl bash -lc 'cd /mnt/d/Projects/Tiny-Swarm-World_2 && PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_lxc_swarm_runtime.TestLxcSwarmRuntime.test_prepare_stack_assets_transfers_generated_service_access_dashboard_to_remote_root'`
- Result: failed as expected.
- Evidence: transferred input text was `<html>stale-dashboard</html>` instead of the generated dashboard fixture.

- Command: `wsl bash -lc 'cd /mnt/d/Projects/Tiny-Swarm-World_2 && PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition.TestComposition.test_build_deployment_services_wires_stack_contracts_without_running_runtime tests.infrastructure.test_composition.TestComposition.test_build_deployment_services_wires_service_access_dashboard_renderer_to_swarm_runtime tests.infrastructure.test_composition.TestComposition.test_build_deployment_services_wires_service_access_infisical_environment'`
- Result: failed as expected.
- Evidence: `service_access_dashboard_renderer` was absent from `LxcSwarmRuntime` construction and the pre-apply target tuple lacked `deployment:service-access-stack-assets`.

Requirement coverage:

- REQ-001: RED test proves generated dashboard content is not currently transferred.
- REQ-002: RED test fixes the expected remote path `service-access/dashboard/index.html`.
- REQ-003: RED test proves stale committed dashboard content is currently a hidden deployment source.
- REQ-004: RED test proves the Service Access asset step is currently not visible in pre-apply workflow metadata.
- REQ-005: No secret file was read; tests use synthetic fixture strings.

Decision:

- Slice 01 is intentionally committed in RED state because the active workflow requires regression-first evidence before implementation slices.
