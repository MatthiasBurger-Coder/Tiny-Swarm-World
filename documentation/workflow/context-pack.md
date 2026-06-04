# Workflow Context Pack

Workflow: `fresh-install-reset-full-deploy-v1.1.0`

Branch: `feature/workflow-install-reset-reinstall-20260602`

Process strand: installation wrapper, platform reset, setup run, artifact
preparation, deployment apply/verify, service-access dashboard/index assets.

Execution profile: `FULL_PATH`

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
* `infra/prepare`
* `infra/platform`
* `infra/artifacts`
* `infra/deployment`
* `infra/shared`
* `documentation/user_guide`
* `documentation/system`
* `documentation/arc42`
* `documentation/workflow`

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
PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_node_provider_selection
PYTHONPATH=src python3 -m unittest tests.test_package_entrypoint
PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition
PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_ensure_portainer_admin_access
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_lxc_swarm_runtime
PYTHONPATH=src python3 -m unittest tests.domain.deployment.test_service_stack_contract
PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_service_stack_plan
PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_verify_swarm_service_readiness
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml
PYTHONPATH=src python3 -m unittest tests.architecture.test_legacy_surface_documentation tests.architecture.test_infra_responsibility_boundaries
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
c2ba662e79f871afdfed8af6fa7db45b67cfc6b8e3ccb706766bc710a00ff923  documentation/arc42/02_constraints.adoc
3edb9c8429def576e5cd24dc087b005da2df4bb1204ede2a238f92c6eb615098  documentation/arc42/06_runtime_view.adoc
665973954b8b3d674e9e3548cd5b1d58d401fa0933a6acc28af22f5151f7c733  documentation/arc42/12_glossary.adoc
863ca029e2e01a29f5b5d9854f9e2345eca1bcddbb3477319ecc295e19717302  documentation/system/live-operation-surfaces.adoc
54a5d73b1d83f2242ab8754813eb3b45f89f218359c390b58a16a593a62bbf11  documentation/user_guide/installation.adoc
28ee9f1fd5299739d4b67edd182f6d9785708841cc2c4f1d1bcfb9e53a35cfaa  documentation/workflow/workflow.md
de1b0c3dcbe199c96459dd10c806f4a967bf05a0590b39c75f0975b65a6a0733  install.sh
a51d95168d3c9737dadde9be387895ce4cef371e437c27064a18e4c752f561cd  src/tiny_swarm_world/application/services/platform/workflows.py
a648266b4c974fa940fd1a13ea4e91d0fe89348b965ac60005d2a0a9d4247533  src/tiny_swarm_world/application/services/platform/workflow_taxonomy.py
d3d3390ae5c523edbee712d945863a20d64769c840aac102d90c3e2e24a10c47  src/tiny_swarm_world/application/services/platform/node_provider_selection.py
fec693cf136a516b7755e196b832e28e6651cd9506c02cb63f102a8cd69eb03b  src/tiny_swarm_world/application/ports/node_provider/port_managed_node_teardown.py
e44317065f966d55a1f2ab566b8ad2b5768a52d7a70b57366904d95a73227ec6  src/tiny_swarm_world/application/ports/node_provider/__init__.py
8fb4615f130fcac45f1fc253fff3da829c98298e69e77ff7cdfa783f64696903  tests/application/services/platform/test_node_provider_selection.py
ca94e11fa58549d4281a8b69fed7789d45ca523173b8f2df61b49c6b11287318  tests/application/services/platform/test_platform_workflows.py
da82bfe359e14fc8626dc6baa3f1697fd75462ccfce8560a23236e46fe9248c4  src/tiny_swarm_world/__main__.py
a67ef61e5f3e706b3186d324ee87173462d95f72eee6b0ac0487f5d554e764ad  src/tiny_swarm_world/infrastructure/adapters/clients/lxc_node_provider.py
959c9faab307aa7d74d549b09a7060b7a34a1b68380d1ad7f0ef3eff6580066b  src/tiny_swarm_world/infrastructure/composition.py
8af47e83362c73a17143cdc390941ee269d9e962f5fb4234816b94eff13dbdfd  tests/infrastructure/adapters/clients/test_lxc_node_provider.py
c1bf2aa6c1307eb120e8288a34499e1a8026c98071df958b3ad96dff2e4c6c4d  tests/infrastructure/test_composition.py
2e1b5e74862c1c401cdca14c28197aae9a16f10fd28f6247f3e30d67d734aa32  documentation/workflow/execution-report.md
27c01d7dad639117968f65ced77b6715024ee299ab8cf104a9858e4dbf6c9be0  tests/test_install_script.py
b560b1902e911f2d572b005f22b48fa5baed5dcf170bdfd0b9b580a0891b9b3e  infra/prepare/README.md
d916dfc5e81b3da20366d13ae3c9e8f3f4c5dfb26fdc228eb3969410f93f637e  infra/prepare/portainer/README.md
1518eb2766df77b87a0687611e08582e237a64fa44a38029ad6b11fabd037719  infra/prepare/nexus/README.md
c2aadf9b97dd756fcf56eca54e6b8b0b970c73244ca73f15c23b858b9ec3674a  infra/platform/README.md
1eca831263b64349aaab0568f9829b5b14fd14fffbfc3813bb052514e000f3db  infra/artifacts/README.md
9a35165a1fbfbcde6f3e75ddc9180071e526984d53702f7ee0c63ba9a64d8719  infra/deployment/README.md
3524cd534d08daf196d4396faa86a563d27e3aedd79874a614e96afadd03e00b  infra/shared/README.md
```

This context pack is stale when any governing hash changes, when branch
verification fails, or when workflow execution changes destructive scope.
