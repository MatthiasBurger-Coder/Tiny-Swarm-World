# Issue #183 Responsibility Map — After Local Implementation

Observed after workflow slices 02–07 and facade cleanup: 2026-08-09.

| Extracted area | Current responsibility | Compatibility surface | Verification |
| --- | --- | --- | --- |
| `lxc/command/manager_shell_gateway.py` | Incus/LXD manager and node shell execution, timeout, retry, failure mapping | `LxcSwarmRuntime._run_manager_shell` and `_run_node_shell` delegate dynamically | Slice 02 focused suite; full quality gate |
| `lxc/command/diagnostics.py` | Bounded/redacted output and transient child-PID detection | `_safe_log_text` and `_is_transient_manager_shell_failure` aliases | Redaction/retry tests |
| `lxc/swarm/swarm_stack_runtime.py` | Stack deployment, service status, secrets, lock recovery, host-port reconciliation | `LxcSwarmRuntime` Swarm-port facade | Slice 03 direct and legacy suites |
| `lxc/swarm/stack_asset_transfer.py` | Traefik, service-access, and Swagger remote asset transfer | `prepare_stack_assets` and `_transfer_stack_assets` seams | Asset and runtime tests |
| `lxc/swarm/stack_prerequisite_registry.py` | Ordered external-network, Traefik TLS, SonarQube kernel, and Swagger asset-only strategies | `_ensure_stack_prerequisites`, `_ensure_external_overlay_network`, `_ensure_traefik_tls_secrets` | Registry strategy tests |
| `lxc/docker/lxc_container_runtime.py` | Docker container lookup and file reads inside managed LXC nodes | Legacy `LxcContainerRuntime` import now resolves to extracted class | Direct Docker and regression tests |
| `lxc/services/lxc_portainer_admin_client.py` | Portainer bootstrap/admin HTTP behavior and manager address resolution | Legacy manager-IP-compatible facade | Direct service and regression tests |
| `lxc/services/lxc_portainer_http_client.py` | Portainer endpoint/stack/deployment behavior and overlay preparation | Legacy manager-IP-compatible facade | Direct service and regression tests |
| `lxc/services/lxc_nexus_http_client.py` | Nexus URL mapping and repository/user delegation | Legacy manager-IP-compatible facade | Direct service and regression tests |
| `lxc/services/common.py` | Shared LXC service address, scheme, timeout, and retry helpers | Resolver injection preserves old patch seam | Typecheck and service tests |
| `lxc/images/lxc_container_image_publisher.py` | Image build/pull/cache/context transfer/login/push behavior | Legacy image class alias | Direct image and regression tests |
| `lxc/images/errors.py` | Typed image errors, redacted diagnostics, operator actions | Legacy error aliases preserve identity | Image error tests |
| `lxc_swarm_runtime.py` | Swarm-port implementation plus approved public compatibility facades/aliases | Existing imports and patch targets remain stable | Boundary, composition, and full regression tests |
| `composition.py` | Concrete adapter construction and wiring root | Imports extracted Docker/service/image modules directly | Composition tests and boundary guard |

## Residual acceptance gaps

* The approved live Selenium suite passed all nine routed browser flows. The
  direct urllib route probe still records TLS/routing `URLError` results and
  should be diagnosed separately.
* SonarCloud PR #238 reports `OK` for commit `3a81bf0`, with 90.0% New Code
  coverage and zero unresolved new issues.
