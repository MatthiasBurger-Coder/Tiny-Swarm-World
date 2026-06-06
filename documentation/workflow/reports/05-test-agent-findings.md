# Senior Tester Findings

## Summary

The requested behavior is testable with fake runners and unit tests. No live
LXC, Incus, LXD, Docker Swarm, compose, or service bootstrap commands are
needed for the default quality gate.

## Required Coverage

* Clean manager-specific profile containing expected `tsw-proxy-*` devices is
  accepted.
* Direct instance-level `tsw-proxy-*` devices on `swarm-manager` are detected
  as `unsafe_instance_devices`.
* Workers do not receive manager proxy devices.
* install/reset/reinstall does not reintroduce direct instance-level proxy
  devices.
* Repair removes stale direct `tsw-proxy-*` devices only when equivalent
  profile-level devices exist.
* Repair refuses removal when expected profile representation is missing.
* Existing safety behavior for unrelated unexpected instance devices remains
  unchanged.

## Targeted Commands

```bash
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_node_provider_config_yaml_repository
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_lxc_node_provider
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_lxc_proxy_device_runtime
PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_lxc_service_exposure tests.application.services.platform.test_platform_workflows
PYTHONPATH=src python3 -m unittest tests.test_package_entrypoint tests.test_install_script
git diff --check
```

## Required Gate

```bash
python3 tools/quality_gate.py quality
```

## Decision

`READY_FOR_WORKFLOW`.
