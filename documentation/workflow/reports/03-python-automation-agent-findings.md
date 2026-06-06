# Senior Python Automation Developer Findings

## Summary

The current code already contains the failure shape requested by the workflow:
proxy mutation is direct-instance based, while node lifecycle drift checks have
a project-proxy allowance that conflicts with the new desired behavior.

## Relevant Evidence

* `src/tiny_swarm_world/infrastructure/adapters/clients/lxc_proxy_device_runtime.py`
  uses `config device get/add/set <instance>`.
* `src/tiny_swarm_world/application/services/platform/lxc_service_exposure.py`
  applies proxy plans to `swarm-manager`.
* `src/tiny_swarm_world/infrastructure/adapters/clients/lxc_node_provider.py`
  uses `allow_project_proxy_devices=True` in normal mismatch detection.
* `infra/config/node-providers/provider_config.yaml` assigns one shared
  `docker-swarm` profile to manager and workers.

## Implementation Guidance

* Add a minimal config model for ordered profile assignment.
* Add profile-level proxy device reconciliation through ports.
* Remove normal-flow allowance for direct project proxy devices.
* Add explicit repair with equivalence checks and summary-only evidence.
* Keep `install.sh` thin.

## Decision

`READY_FOR_WORKFLOW`.
