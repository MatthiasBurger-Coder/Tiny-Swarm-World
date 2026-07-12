# Changed Files

The implementation diff contains 43 task files before this evidence package.

## Windows service and preflight

- `tools/windows/tws-wsl-bridge.ps1`
- `tools/windows/tws-wsl-bridge-service.ps1`
- `tools/windows/tws-wsl-bridge.config.json`
- `tools/windows/optional/tws_dns_resolver.py`
- `src/tiny_swarm_world/application/ports/preflight/port_host_preflight_probe.py`
- `src/tiny_swarm_world/application/services/platform/preflight_service.py`
- `src/tiny_swarm_world/infrastructure/adapters/preflight/host_preflight_probe.py`
- `src/tiny_swarm_world/infrastructure/adapters/preflight/windows_wsl_bridge_state.py`
- `src/tiny_swarm_world/installer.py`
- corresponding Windows, preflight, composition, and installer tests

## Deployment and runtime recovery

- `infra/config/compose/traefik/docker-compose.yml`
- `infra/config/compose/pulsar/docker-compose.yml`
- `infra/config/inventory/desired_inventory.yaml`
- `infra/config/node-providers/provider_config.yaml`
- `src/tiny_swarm_world/application/services/deployment/secret_management.py`
- `src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py`
- `src/tiny_swarm_world/infrastructure/adapters/file_management/local_file_storage.py`
- `src/tiny_swarm_world/infrastructure/composition.py`
- corresponding deployment, repository, runtime, storage, and composition tests

## Browser verification

- `tests/live/browser_e2e_contract.py`
- `tests/live/test_browser_e2e_contract.py`
- `tests/live/test_post_install_browser_live.py`

## Documentation and governance

- `README.md`
- `documentation/arc42/09_architecture_decisions.adoc`
- `documentation/arc42/09_decisions/adr-windows-wsl-bridge-service-agent.adoc`
- `documentation/process/skills/audit/skill-registry.json`
- `documentation/system/network.adoc`
- `documentation/user-handbook.adoc`
- `documentation/user_guide/installation.adoc`
- `documentation/user_guide/troubleshooting.adoc`
- Windows bridge operator/workflow guides

No credential file, generated local runtime artifact, IDE state, cache, or historical Issue #157 evidence is included in Git status.
