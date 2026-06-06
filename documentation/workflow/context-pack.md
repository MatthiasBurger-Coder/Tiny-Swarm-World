# Workflow Context Pack

## Active Workflow

```text
workflow_id=lxc-proxy-drift-reconciliation-v1.0.0
workflow_version=1.0.0
branch=fix/lxc-proxy-drift-reconciliation-20260606
execution_profile=FULL_PATH
decision=READY_FOR_WORKFLOW
```

## Navigation

Primary workflow:

* `documentation/workflow/workflow.md`

Role reports:

* `documentation/workflow/reports/01-requirement-agent-findings.md`
* `documentation/workflow/reports/02-architecture-agent-findings.md`
* `documentation/workflow/reports/03-python-automation-agent-findings.md`
* `documentation/workflow/reports/04-frontend-impact-agent-findings.md`
* `documentation/workflow/reports/05-test-agent-findings.md`

Primary source files:

* `infra/config/node-providers/provider_config.yaml`
* `src/tiny_swarm_world/application/ports/node_provider/port_lxc_proxy_device_runtime.py`
* `src/tiny_swarm_world/infrastructure/adapters/repositories/node_provider_config_yaml_repository.py`
* `src/tiny_swarm_world/infrastructure/adapters/clients/lxc_node_provider.py`
* `src/tiny_swarm_world/infrastructure/adapters/clients/lxc_proxy_device_runtime.py`
* `src/tiny_swarm_world/application/services/platform/lxc_service_exposure.py`
* `src/tiny_swarm_world/application/services/platform/workflow_taxonomy.py`
* `src/tiny_swarm_world/application/services/platform/workflows.py`
* `src/tiny_swarm_world/infrastructure/composition.py`
* `src/tiny_swarm_world/__main__.py`
* `install.sh`

Primary tests:

* `tests/infrastructure/adapters/repositories/test_node_provider_config_yaml_repository.py`
* `tests/infrastructure/adapters/clients/test_lxc_node_provider.py`
* `tests/infrastructure/adapters/clients/test_lxc_proxy_device_runtime.py`
* `tests/application/services/platform/test_lxc_service_exposure.py`
* `tests/application/services/platform/test_platform_workflows.py`
* `tests/test_package_entrypoint.py`
* `tests/test_install_script.py`
* `tests/infrastructure/test_composition.py`

Documentation sync targets:

* `README.md`
* `documentation/deployment/system.adoc`
* `documentation/system/live-operation-surfaces.adoc`
* `documentation/system/network.adoc`
* `documentation/system/lxc-native-setup.adoc`
* `documentation/user_guide/installation.adoc`
* `documentation/user_guide/troubleshooting.adoc`
* `documentation/arc42/06_runtime_view.adoc`
* `documentation/arc42/07_deployment_view.adoc`
* `documentation/arc42/10_quality_requirements.adoc`
* `documentation/arc42/11_risks_and_debt.adoc`

## Process Strand

LXC-native platform desired-state reconciliation and setup/install recovery.

## Affected Areas

* LXC-native provider config schema and committed provider configuration.
* Manager-specific LXC profile desired state.
* Platform expose proxy reconciliation.
* Node lifecycle drift detection.
* Explicit stale direct proxy repair.
* CLI/platform workflow taxonomy.
* Operator documentation and arc42 runtime/deployment views.

## Forbidden Areas

* Domain imports of LXC, Incus, Docker, command runners, YAML parsers, logging,
  HTTP clients, UI adapters, or dependency injection.
* Direct instance-level `tsw-proxy-*` devices as accepted normal state.
* Worker manager-proxy profile assignment.
* Silent repair inside install, reset, reinstall, init, reconcile, or expose.
* Ansible, Terraform, Kubernetes-first behavior, Multipass restoration, Java,
  Maven, Spring Boot, Gradle, JUnit, ArchUnit, browser React, or external
  static-analysis CI.
* Live infrastructure commands without explicit user approval.

## Required Roles

* Senior Requirement Engineer.
* Senior System Architect.
* Senior Python Automation Developer.
* Senior React Frontend Developer for no-impact review.
* Senior Tester.
* Senior Documentation Engineer for Slice 06.
* Senior DevOps Engineer for Slice 05 repair safety review.

## Conditional Roles

* ADR Steward if a later slice determines the provider profile model requires a
  new architecture decision.
* Quality Gate Orchestrator if `python3 tools/quality_gate.py quality` fails in
  a way that needs classification.

## Quality Commands

Targeted:

```bash
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_node_provider_config_yaml_repository
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_lxc_node_provider
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_lxc_proxy_device_runtime
PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_lxc_service_exposure tests.application.services.platform.test_platform_workflows
PYTHONPATH=src python3 -m unittest tests.test_package_entrypoint tests.test_install_script
PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition
git diff --check
```

Required before commit or push when practical:

```bash
python3 tools/quality_gate.py quality
```

## Governing File Hashes

```text
AGENTS.md ecba0ffcfb5ae1d2db209cbecff34d77fd79a60593e866d881f7e31c40907964
QUALITY.md 458e5f4d8fbdedea1c413e1ff135ec91392a4bb5a5aea20300dcac8e209414b6
.agents/skills/workflow-authoring/SKILL.md 087658240296e3b1ec74205c60a96a9a4c67a17cf653f7867e6f316bd9afa94e
.agents/skills/three-amigos-requirement-gatekeeper/SKILL.md 23de7d9aac9d2694eae26fac2765d65f369c101ac348dac24d5f3bbe9e2d3ba4
.agents/skills/execution-profile-router/SKILL.md b554ffd4c3c8de9b313b55d8a9c99deda8c3bf3910f559105000e338680263e9
.agents/skills/workflow-slice/SKILL.md bae552d4860614879871413918870df6940b95af185f6c1077a023caa88e3ddb
.agents/skills/quality-gate-governance/SKILL.md bf9e9b402d481a670b742ac9f3b9a9a41482ce3b523bf8edf876aae71d31d95d
documentation/epics/autonomous-runnable-setup.md fc7ec746446faa756306e459b54d700052eea0869c6dc2b1ef8a9e3b15be554a
documentation/arc42/06_runtime_view.adoc df8d4e3d1f9ecae07f614f4ab3b270b9ab4cf87294ac64f53fe04faedcca166f
documentation/arc42/07_deployment_view.adoc 5655f150367358d8800cba8b18b966fac7a603af1c9a2d8501e776f83b58a296
documentation/arc42/10_quality_requirements.adoc c7ee9f96bfb3b9942c80d8568172ba4751689b9b5b1b630b43e3241f3e11d19e
documentation/arc42/11_risks_and_debt.adoc 7b869951eca328d5e9b4ecddb1682415b31000bd619aab6d2bc585c256b851ed
documentation/deployment/system.adoc 9927e3b9fe35b0f68a3033e751faae2caea8ab61fbb228bcae4df8c799005313
documentation/system/live-operation-surfaces.adoc 7b4765e58b459c00f4c24db0fed252f4c1c856fdd44417e43e89e8b20fe23720
documentation/system/network.adoc ab270b8895c87e5f047440959be9e32f2160b3eeda07309f1847fcbf07a1044b
documentation/user_guide/installation.adoc 8023f230224e0f2633f6cbc02e1b0048c1ac449c081aa42a14620cd1a7a1c590
infra/config/node-providers/provider_config.yaml f7f19b0268f1a68c2e91e6ee09130334ceae9128ab22f5d7592e1df5614667f1
src/tiny_swarm_world/application/ports/node_provider/port_lxc_proxy_device_runtime.py 37f7b0eeffad8c425a19b096327231ff32a9acaf38347ee0b2384b86fb587176
src/tiny_swarm_world/application/services/platform/lxc_service_exposure.py d4938746a3601c4de6a8ba4cea168830c1c9a0c9493e7bca9737b150e41d7165
src/tiny_swarm_world/application/services/platform/workflow_taxonomy.py 11b145f7de2f4a2d3e58aa02f41171201fbc30e6fe9eb0b0a858eace953eab5d
src/tiny_swarm_world/application/services/platform/workflows.py f63b4c1bfea6cecb076abe674a642493316bafc3dd8396477585054698374ef6
src/tiny_swarm_world/infrastructure/adapters/clients/lxc_node_provider.py 850a31c3059764221f697188bd2b4dce932378cc9317c12a77cc180c85084ba5
src/tiny_swarm_world/infrastructure/adapters/clients/lxc_proxy_device_runtime.py f3c5434884ef81bea59da64a454cdfbf0bc21b65ae48253fa652c0f601f81f99
src/tiny_swarm_world/infrastructure/adapters/repositories/node_provider_config_yaml_repository.py 0d6bec789ba2fcb5610e533d04093fbc62ec5f108db837af61d574bd4ac949cc
src/tiny_swarm_world/infrastructure/composition.py ad2fe4d9035cf24dd16622f678d90931c900191dbdaf7c9220b976fffd27cf56
src/tiny_swarm_world/__main__.py 07a4e3126ea06e8bbb1faa295940d440580cb66175f71444d32b811b880cf15e
```

Context pack is stale when any hash above changes, when branch differs from
`fix/lxc-proxy-drift-reconciliation-20260606`, when slice locks conflict, or
when implementation changes the repair command name without updating this
pack.
