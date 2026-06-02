# Workflow Context Pack

Workflow: `fresh-install-reset-full-deploy-v1.1.0`

Branch: `feature/workflow-install-reset-reinstall-20260602`

Process strand: installation wrapper, platform reset, setup run, artifact
preparation, deployment apply/verify, service-access dashboard/index assets.

Execution profile: `NORMAL_PATH`

## Affected Areas

* `install.sh`
* `src/tiny_swarm_world/application/services/platform`
* `src/tiny_swarm_world/application/ports`
* `src/tiny_swarm_world/infrastructure/adapters/clients`
* `src/tiny_swarm_world/infrastructure/composition.py`
* `src/tiny_swarm_world/__main__.py`
* `src/tiny_swarm_world/domain/artifacts`
* `src/tiny_swarm_world/domain/deployment`
* `infra/config/compose/service-access/docker-compose.yml`
* `infra/compose/service-access/dashboard/index.html`
* `infra/compose/service-access/dashboard/Dockerfile`
* `infra/compose/service-access/nginx/default.conf`
* `infra/compose/service-access/nginx/Dockerfile`
* `documentation/user_guide`
* `documentation/system`
* `documentation/arc42`

## Forbidden Areas

* Java, Maven, Spring Boot project structure
* Browser React or frontend build tooling
* Multipass provider restoration
* Kubernetes-first implementation
* Live infrastructure execution during tests
* External static-analysis CI additions

## Required Roles

* Senior Requirement Engineer
* Senior System Architect
* Senior Python Automation Developer
* Senior Tester

## Conditional Roles

* Senior DevOps Engineer
* Console/status UI skills
* Senior Documentation Engineer
* ADR Steward
* Quality Gate Orchestrator

## Quality Commands

Targeted:

```bash
bash -n install.sh
PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_platform_workflows
PYTHONPATH=src python3 -m unittest tests.test_package_entrypoint
PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition
PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_ensure_portainer_admin_access
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_lxc_swarm_runtime
PYTHONPATH=src python3 -m unittest tests.domain.deployment.test_service_stack_contract
PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_service_stack_plan
PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_verify_swarm_service_readiness
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml
git diff --check
```

Required:

```bash
python3 tools/quality_gate.py quality
```

## Governing File Hashes

```text
ecba0ffcfb5ae1d2db209cbecff34d77fd79a60593e866d881f7e31c40907964  AGENTS.md
458e5f4d8fbdedea1c413e1ff135ec91392a4bb5a5aea20300dcac8e209414b6  QUALITY.md
087658240296e3b1ec74205c60a96a9a4c67a17cf653f7867e6f316bd9afa94e  .agents/skills/workflow-authoring/SKILL.md
dae7115594172e159c051c3ece15c0b535f1570efbb28fc67440aef0bbadc9c9  documentation/process/workflow-create.md
3edb9c8429def576e5cd24dc087b005da2df4bb1204ede2a238f92c6eb615098  documentation/arc42/06_runtime_view.adoc
c891afea2de6d4f12178cb91eb97e924069da02f7fcd0c82aef616594308cee5  documentation/arc42/12_glossary.adoc
4a49673d13e7eeba00841f21f49dcf17637f7a03f7855368ec8639ff4eebf84a  install.sh
39195d58426caa93a581f83e9904157cdfb81411f91f5ffd9b54c188e91e9113  src/tiny_swarm_world/application/services/platform/workflows.py
6aea8f47ab064634649014573e546634dc9e66258f766c5a3128bd3321f23dba  src/tiny_swarm_world/application/services/platform/workflow_taxonomy.py
da82bfe359e14fc8626dc6baa3f1697fd75462ccfce8560a23236e46fe9248c4  src/tiny_swarm_world/__main__.py
```

This context pack is stale when any governing hash changes, when branch
verification fails, or when workflow execution changes destructive scope.
