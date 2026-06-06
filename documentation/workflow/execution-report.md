# Workflow Execution Report

```yaml
workflow_id: lxc-proxy-drift-reconciliation-v1.0.0
branch: fix/lxc-proxy-drift-reconciliation-20260606
status: completed
```

This workflow has been created and released for `workflow execute`.

## Command Evidence

### Slice 01

```text
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_node_provider_config_yaml_repository
result=passed
tests=19
```

```text
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_lxc_node_provider
result=passed
tests=24
```

```text
python3 tools/quality_gate.py quality
result=failed
failure=lint missing ruff in system Python
classification=BUILD_FAILURE
relation=environment tooling missing before project checks
```

```text
python3 -m pip install --user ruff mypy import-linter types-requests
result=failed
failure=externally-managed-environment
classification=BUILD_FAILURE
relation=environment tooling setup
```

```text
python3 -m venv .tiny-swarm-world/local/quality-venv && .tiny-swarm-world/local/quality-venv/bin/python -m pip install --upgrade pip && .tiny-swarm-world/local/quality-venv/bin/python -m pip install -r requirements.txt ruff mypy import-linter types-requests
result=passed
classification=tooling_bootstrap
```

```text
.tiny-swarm-world/local/quality-venv/bin/python tools/quality_gate.py quality
result=failed
failure=lint unused imports in Slice 02-owned files
classification=BUILD_FAILURE
relation=pre-existing lint surfaced by full gate, fixed in Slice 02
```

### Slice 02

```text
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_lxc_proxy_device_runtime
result=failed then passed
tests=6
failure=one test still passed NodeSpec after profile-name port change
classification=TEST_FAILURE
retry_count=1
```

```text
PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_lxc_service_exposure
result=passed
tests=5
```

```text
PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition
result=passed
tests=45
```

```text
.tiny-swarm-world/local/quality-venv/bin/python tools/quality_gate.py lint
result=passed
```

```text
git diff --check
result=passed
```

### Slice 03

```text
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_lxc_node_provider
result=passed
tests=27
```

```text
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_node_provider_config_yaml_repository
result=passed
tests=19
```

```text
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_lxc_proxy_device_runtime
result=passed
tests=6
```

```text
PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_lxc_service_exposure
result=passed
tests=5
```

```text
PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition
result=passed
tests=45
```

```text
.tiny-swarm-world/local/quality-venv/bin/python tools/quality_gate.py lint
result=passed
```

```text
git diff --check
result=passed
```

### Slice 04

```text
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_lxc_node_provider
result=passed
tests=27
```

```text
PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_platform_workflows
result=passed
tests=34
```

```text
PYTHONPATH=src python3 -m unittest tests.test_package_entrypoint tests.test_install_script
result=passed
tests=35
```

```text
.tiny-swarm-world/local/quality-venv/bin/python tools/quality_gate.py lint
result=passed
```

```text
git diff --check
result=passed
```

### Slice 05

```text
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_lxc_proxy_device_runtime
result=passed
tests=10
```

```text
PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_lxc_service_exposure
result=passed
tests=8
```

```text
PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_platform_workflows
result=passed
tests=34
```

```text
PYTHONPATH=src python3 -m unittest tests.test_package_entrypoint
result=passed
tests=29
```

```text
PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition
result=passed
tests=46
```

```text
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_lxc_node_provider
result=passed
tests=27
```

```text
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_node_provider_config_yaml_repository
result=passed
tests=19
```

```text
.tiny-swarm-world/local/quality-venv/bin/python tools/quality_gate.py lint
result=passed
```

```text
git diff --check
result=passed
```

### Slice 06

```text
python3 -m json.tool documentation/workflow/context-pack.json
result=passed
```

```text
rg 'platform expose (creates|configures|ensures).*LXC proxy devices on|created by `platform expose`|treated as project-owned reset state|manager-gateway proxy' README.md documentation -n
result=found historical workflow-creation report only
classification=not_active_operator_documentation
```

```text
git diff --check
result=passed
```

```text
.tiny-swarm-world/local/quality-venv/bin/python tools/quality_gate.py quality
result=failed
failure=mypy type narrowing in src/tiny_swarm_world/infrastructure/adapters/clients/portainer_http_client.py
classification=QUALITY_GATE_FAILURE
relation=unrelated existing typecheck issue surfaced by final full gate
resolution=local endpoint-id helper added without changing Portainer behavior
```

```text
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_portainer_http_client
result=passed
tests=17
```

```text
.tiny-swarm-world/local/quality-venv/bin/python tools/quality_gate.py quality
result=passed
tests=678
```

## Slice Status

* Slice 01: completed.
* Slice 02: completed.
* Slice 03: completed.
* Slice 04: completed.
* Slice 05: completed.
* Slice 06: completed.

## Notes

Do not record live infrastructure success here unless live validation is
explicitly requested and evidence is collected separately from the default
quality gate.

## Checkpoints

### Slice 01

```text
workflow_version=1.0.0
slice_id=01
slice_title=Desired Manager Profile Contract
responsible_agent=Senior Python Automation Developer
changed_files=infra/config/node-providers/provider_config.yaml,src/tiny_swarm_world/infrastructure/adapters/repositories/node_provider_config_yaml_repository.py,tests/infrastructure/adapters/repositories/test_node_provider_config_yaml_repository.py,documentation/workflow/execution-report.md
quality_gates=PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_node_provider_config_yaml_repository
quality_result=passed
arc42_update_status=pending Slice 06
adr_update_status=not required
rollback_reference=pending checkpoint commit
push_result=pending checkpoint push
```

### Slice 02

```text
workflow_version=1.0.0
slice_id=02
slice_title=Profile-Level Proxy Reconciliation
responsible_agent=Senior Python Automation Developer
changed_files=src/tiny_swarm_world/application/ports/node_provider/port_lxc_proxy_device_runtime.py,src/tiny_swarm_world/application/services/platform/lxc_service_exposure.py,src/tiny_swarm_world/infrastructure/adapters/clients/lxc_proxy_device_runtime.py,src/tiny_swarm_world/infrastructure/composition.py,tests/infrastructure/adapters/clients/test_lxc_proxy_device_runtime.py,tests/application/services/platform/test_lxc_service_exposure.py,tests/infrastructure/test_composition.py,documentation/workflow/execution-report.md
quality_gates=PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_lxc_proxy_device_runtime; PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_lxc_service_exposure; PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition; .tiny-swarm-world/local/quality-venv/bin/python tools/quality_gate.py lint; git diff --check
quality_result=passed after one test retry
arc42_update_status=pending Slice 06
adr_update_status=not required
rollback_reference=pending checkpoint commit
push_result=pending checkpoint push
```

### Slice 03

```text
workflow_version=1.0.0
slice_id=03
slice_title=Strict Node Drift And Profile Assignment
responsible_agent=Senior Python Automation Developer
changed_files=src/tiny_swarm_world/infrastructure/adapters/clients/lxc_node_provider.py,tests/infrastructure/adapters/clients/test_lxc_node_provider.py,documentation/workflow/execution-report.md
quality_gates=PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_lxc_node_provider; PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_node_provider_config_yaml_repository; PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_lxc_proxy_device_runtime; PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_lxc_service_exposure; PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition; .tiny-swarm-world/local/quality-venv/bin/python tools/quality_gate.py lint; git diff --check
quality_result=passed
arc42_update_status=pending Slice 06
adr_update_status=not required
rollback_reference=pending checkpoint commit
push_result=pending checkpoint push
```

### Slice 04

```text
workflow_version=1.0.0
slice_id=04
slice_title=Normal Flow Guidance Without Silent Repair
responsible_agent=Senior Python Automation Developer
changed_files=src/tiny_swarm_world/infrastructure/adapters/clients/lxc_node_provider.py,tests/infrastructure/adapters/clients/test_lxc_node_provider.py,documentation/workflow/execution-report.md
quality_gates=PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_lxc_node_provider; PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_platform_workflows; PYTHONPATH=src python3 -m unittest tests.test_package_entrypoint tests.test_install_script; .tiny-swarm-world/local/quality-venv/bin/python tools/quality_gate.py lint; git diff --check
quality_result=passed
arc42_update_status=pending Slice 06
adr_update_status=not required
rollback_reference=pending checkpoint commit
push_result=pending checkpoint push
```

### Slice 05

```text
workflow_version=1.0.0
slice_id=05
slice_title=Explicit Stale Proxy Repair Path
responsible_agent=Senior Python Automation Developer
changed_files=src/tiny_swarm_world/application/ports/node_provider/port_lxc_proxy_device_runtime.py,src/tiny_swarm_world/application/ports/node_provider/__init__.py,src/tiny_swarm_world/application/services/platform/lxc_service_exposure.py,src/tiny_swarm_world/application/services/platform/workflow_taxonomy.py,src/tiny_swarm_world/application/services/platform/workflows.py,src/tiny_swarm_world/application/services/platform/__init__.py,src/tiny_swarm_world/infrastructure/adapters/clients/lxc_proxy_device_runtime.py,src/tiny_swarm_world/infrastructure/composition.py,src/tiny_swarm_world/__main__.py,tests/infrastructure/adapters/clients/test_lxc_proxy_device_runtime.py,tests/application/services/platform/test_lxc_service_exposure.py,tests/application/services/platform/test_platform_workflows.py,tests/test_package_entrypoint.py,tests/infrastructure/test_composition.py,documentation/workflow/execution-report.md
quality_gates=PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_lxc_proxy_device_runtime; PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_lxc_service_exposure; PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_platform_workflows; PYTHONPATH=src python3 -m unittest tests.test_package_entrypoint; PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition; PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_lxc_node_provider; PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_node_provider_config_yaml_repository; .tiny-swarm-world/local/quality-venv/bin/python tools/quality_gate.py lint; git diff --check
quality_result=passed
arc42_update_status=pending Slice 06
adr_update_status=not required
rollback_reference=pending checkpoint commit
push_result=pending checkpoint push
```

### Slice 06

```text
workflow_version=1.0.0
slice_id=06
slice_title=Documentation And Final Quality Gate
responsible_agent=Senior Documentation Engineer
changed_files=README.md,documentation/deployment/system.adoc,documentation/system/live-operation-surfaces.adoc,documentation/system/network.adoc,documentation/system/lxc-native-setup.adoc,documentation/user_guide/installation.adoc,documentation/user_guide/troubleshooting.adoc,documentation/arc42/06_runtime_view.adoc,documentation/arc42/07_deployment_view.adoc,documentation/arc42/10_quality_requirements.adoc,documentation/arc42/11_risks_and_debt.adoc,documentation/workflow/workflow.md,documentation/workflow/context-pack.md,documentation/workflow/context-pack.json,documentation/workflow/execution-report.md,src/tiny_swarm_world/infrastructure/adapters/clients/portainer_http_client.py
quality_gates=python3 -m json.tool documentation/workflow/context-pack.json; git diff --check; PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_portainer_http_client; .tiny-swarm-world/local/quality-venv/bin/python tools/quality_gate.py quality
quality_result=passed after unrelated typecheck repair
arc42_update_status=completed
adr_update_status=not required
rollback_reference=pending final commit
push_result=pending final push
```
