# Changed Files: #281 / CRED-03

## Production code

- `src/tiny_swarm_world/domain/configuration/credential_resolution.py` — pure precedence and lifecycle policy.
- `src/tiny_swarm_world/application/services/credential_resolution.py` — application resolution snapshots and safe metadata transport.
- `src/tiny_swarm_world/application/services/deployment/secret_management.py` — post-bootstrap sync, external references, and source evidence.
- `src/tiny_swarm_world/application/ports/clients/port_infisical_cli.py` — provider secret-read contract.
- `src/tiny_swarm_world/infrastructure/adapters/clients/infisical_cli_client.py` — redacted HTTP status handling and instance-scoped bootstrap token.
- `src/tiny_swarm_world/infrastructure/composition_configuration.py` — provider mode and local endpoint validation.
- `src/tiny_swarm_world/infrastructure/composition_runtime.py` — local self-hosted bootstrap wiring.
- `src/tiny_swarm_world/simple_installer.py` — normal install-path resolution and secure override loading.
- `src/tiny_swarm_world/installer.py` — compatibility-path routing and redacted install context.
- `src/tiny_swarm_world/domain/configuration/__init__.py` and `src/tiny_swarm_world/application/services/deployment/__init__.py` — public package exports.

## Product configuration and documentation

- `infra/config/services.yml` — explicit resolved-bootstrap input declaration.
- `documentation/arc42/08_configuration/credential-source-precedence.md` — canonical precedence and lifecycle sequence.
- `documentation/arc42/08_configuration/operator-configuration-contract.md` — operator/file/provider contract.
- `documentation/arc42/08_configuration/config-contract-inventory.md` — bootstrap compatibility mapping.
- `documentation/arc42/08_deployment_configuration/infisical-silent-setup.adoc` — bootstrap and external-provider behavior.

## Verification

- `tests/domain/configuration/test_credential_resolution.py`
- `tests/application/services/deployment/test_secret_management.py`
- `tests/infrastructure/adapters/clients/test_infisical_cli_client.py`
- `tests/infrastructure/test_composition_configuration.py`
- `tests/test_simple_installer.py`
- `tests/test_installer.py`
- `tests/test_install_script.py`
