# Issue #183 Responsibility Map — Before

Source: `src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py`
Observed baseline: 2026-08-08; approximately 1,437 lines.

| Current class/helper area | Current responsibilities | Target responsibility |
| --- | --- | --- |
| `LxcSwarmRuntime` | Manager/node shell execution, stack deployment, service listing, secrets, lock recovery, networks, ports, asset transfer, dashboard rendering | `lxc.command`, `lxc.swarm.swarm_stack_runtime`, `lxc.swarm.stack_asset_transfer`, `lxc.swarm.stack_prerequisite_registry` |
| `_run_manager_shell`, `_run_node_shell`, quoting and bounded diagnostics | Backend CLI selection, subprocess execution, retry, timeout, logging and failure mapping | `lxc.command.manager_shell_gateway` and diagnostics |
| `LxcContainerRuntime` | Manager-side Docker container lookup and file reads | `lxc.docker.lxc_container_runtime` |
| `LxcPortainerAdminClient` | Portainer bootstrap/admin HTTP behavior and manager address discovery | `lxc.services.lxc_portainer_admin_client` |
| `LxcPortainerHttpClient` | Portainer endpoint/stack operations, deployment gateway behavior, overlay-network preparation | `lxc.services.lxc_portainer_http_client` plus shared gateway delegation |
| `LxcNexusHttpClient` | Nexus availability, authentication, user/repository configuration and manager URL mapping | `lxc.services.lxc_nexus_http_client` |
| `LxcContainerImagePublisher` | Build/public image availability, context transfer, registry login, build/push/load and diagnostics | `lxc.images.lxc_container_image_publisher` |
| `PublicImagePullRejected`, `ImagePublisherOperationRejected` | Image-operation error identity and operator action | `lxc.images.errors` |
| Module-level parsers and helpers | Replica, port, environment, network, HTTP scheme, URL, LXC address, and shell formatting rules | Small responsibility-owned helpers with compatibility re-exports only where required |

## Stable surfaces to protect

* `PortSwarmStackRuntime`
* `PortContainerRuntime`
* `PortContainerImagePublisher`
* `PortPortainerAdminClient`
* `PortPortainerClient`
* `PortDeploymentGateway`
* `PortNexusClient`
* legacy imports and test patch locations that are explicitly retained by the
  issue workflow.
