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
* `src/tiny_swarm_world/infrastructure/adapters/repositories/node_provider_config_yaml_repository.py`
* `src/tiny_swarm_world/infrastructure/adapters/clients/lxc_node_provider.py`
* `src/tiny_swarm_world/infrastructure/adapters/clients/lxc_proxy_device_runtime.py`
* `src/tiny_swarm_world/application/services/platform/lxc_service_exposure.py`
* `src/tiny_swarm_world/application/services/platform/workflow_taxonomy.py`
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

* `documentation/deployment/system.adoc`
* `documentation/system/live-operation-surfaces.adoc`
* `documentation/system/network.adoc`
* `documentation/user_guide/installation.adoc`
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
documentation/arc42/06_runtime_view.adoc 91e423c4cbadd835d915573d972377bf3381eb888627525c3c1d7fc07d8c12ba
documentation/arc42/07_deployment_view.adoc de2ad20fd6fb0c6907fe09508fe9846bb6168f95248ff1fcf3238293092b02a6
documentation/deployment/system.adoc 0a8b440e9bd080ba96a1d09e006df1548ddd8a788cede0b7f1d302ecdf12f1ff
infra/config/node-providers/provider_config.yaml c17ee2562b31e23a51ffcd1524f2806c08204bfc0930f27c9e143cf5e7d890fc
src/tiny_swarm_world/infrastructure/adapters/clients/lxc_node_provider.py 593a7d0a7f8f0f9e54c96e39ed46e69f92f196b2b125b8c8d67ec18b325ea5f6
src/tiny_swarm_world/infrastructure/adapters/clients/lxc_proxy_device_runtime.py b9507fb94eb6f49f67d885f11bb3435aa8d24bc6b96de888bfb9f2e612cdc0bb
src/tiny_swarm_world/application/services/platform/lxc_service_exposure.py 7946777d914b1d3ea66111ffdfa1cd3d074cf2e09695d4f1db26678c79896fe4
src/tiny_swarm_world/infrastructure/adapters/repositories/node_provider_config_yaml_repository.py 58459f048a82da8fff5104a8ed379c120339767923ed7ba54805bbf6093ef872
```

Context pack is stale when any hash above changes, when branch differs from
`fix/lxc-proxy-drift-reconciliation-20260606`, when slice locks conflict, or
when implementation changes the repair command name without updating this
pack.
