# Issue #218 — Changed-file scope

The following issue-scoped changes were merged by PR #233 into `main` at
`4e8eff8f41c3f28dda240003f4fb24317d834a42`. This list is descriptive and
excludes local secrets, caches and generated installation state.

## Domain and application

- `src/tiny_swarm_world/domain/preflight/artifact_sources.py`
- `src/tiny_swarm_world/domain/configuration/configuration_contract.py`
- `src/tiny_swarm_world/domain/preflight/host_preparation.py`
- `src/tiny_swarm_world/domain/preflight/hang_diagnostics.py`
- `src/tiny_swarm_world/domain/preflight/resources.py`
- `src/tiny_swarm_world/domain/install/install_event.py`
- `src/tiny_swarm_world/domain/install/install_status.py`
- `src/tiny_swarm_world/application/ports/host/port_host_preparation.py`
- `src/tiny_swarm_world/application/ports/host/port_windows_command_runner.py`
- `src/tiny_swarm_world/application/ports/preflight/port_artifact_source_readiness.py`
- `src/tiny_swarm_world/application/services/platform/host/prepare_host.py`
- `src/tiny_swarm_world/application/services/platform/preflight_service.py`
- `src/tiny_swarm_world/application/services/setup/workflow.py`
- `src/tiny_swarm_world/application/services/deployment/workflows.py`

## Infrastructure and entry points

- `src/tiny_swarm_world/infrastructure/adapters/host/native_linux_host_preparation.py`
- `src/tiny_swarm_world/infrastructure/adapters/host/wsl_host_preparation.py`
- `src/tiny_swarm_world/infrastructure/adapters/host/windows_command_runner.py`
- `src/tiny_swarm_world/infrastructure/adapters/host/hang_diagnostics.py`
- `src/tiny_swarm_world/infrastructure/adapters/host/wsl_resource_inspector.py`
- `src/tiny_swarm_world/infrastructure/adapters/network/host_network_repair.py`
- `src/tiny_swarm_world/infrastructure/adapters/preflight/artifact_source_readiness.py`
- `src/tiny_swarm_world/infrastructure/adapters/clients/lxc_container_docker_runtime.py`
- `src/tiny_swarm_world/infrastructure/composition.py`
- `src/tiny_swarm_world/installer.py`
- `src/tiny_swarm_world/__main__.py`
- `tools/windows/tws-wsl-bridge.ps1`

## Tests and documentation

- Host, resource, preflight, timeout, network and installer tests under
  `tests/`.
- `tests/windows/tws-wsl-bridge.Tests.ps1`.
- `tests/application/services/deployment/test_deployment_workflows.py`.
- `tests/live/browser_e2e_contract.py` was inspected and its opt-in live run
  recorded the missing Selenium prerequisite; no source edit was needed there.
- `.env.example` and `documentation/arc42/08_configuration/operator-configuration-contract.md`
  document the deployment-verify timeout.
- `documentation/user_guide/usage.adoc` documents the distinct `host prepare`
  boundary.
- Workflow/context and `.codex/evidence/` slice records for Slice 04–16.

No secrets, local environment files, Python caches or generated installation
credentials are included in this evidence list.
