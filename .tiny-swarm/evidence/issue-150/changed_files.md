# Issue #150 Changed Files

## Workflow and evidence

- `documentation/workflow/workflow.md`
- `documentation/workflow/issues/issue-150/workflow.md`
- `documentation/workflow/context-pack.md`
- `documentation/workflow/context-pack.json`
- `documentation/workflow/workflow.index.md`
- `.tiny-swarm/evidence/issue-150/**`

## Architecture and documentation

- `documentation/arc42/09_decisions/adr-traefik-https-ingress-existing-ca.adoc`
- `documentation/arc42/05_building_blocks.adoc`
- `documentation/arc42/06_runtime_view.adoc`
- `documentation/arc42/07_deployment_view.adoc`
- `documentation/arc42/08_configuration/operator-configuration-contract.md`
- `documentation/arc42/08_configuration/config-contract-inventory.md`
- `documentation/evidence/live-greenpath-evidence-contract.md`

## Product configuration and tests

- `.env.example`
- `infra/config/compose/traefik/docker-compose.yml`
- `infra/config/compose/traefik/dynamic/tls.yml`
- `infra/config/secrets/infisical-secrets.yaml`
- `src/tiny_swarm_world/domain/configuration/configuration_contract.py`
- `src/tiny_swarm_world/infrastructure/composition_configuration.py`
- `src/tiny_swarm_world/infrastructure/composition_runtime.py`
- `src/tiny_swarm_world/installer.py`
- `tests/application/services/deployment/test_secret_management.py`
- `tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py`
- `tests/infrastructure/test_composition.py`
- `tests/live/test_post_install_browser_live.py`
- `tests/test_install_script.py`
