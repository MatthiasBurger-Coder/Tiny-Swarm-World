# Changed Files: #282 / CRED-04

## Production and product configuration

- `src/tiny_swarm_world/installer.py`
- `src/tiny_swarm_world/simple_installer.py`
- `src/tiny_swarm_world/application/services/deployment/secret_management.py`
- `src/tiny_swarm_world/application/services/deployment/infisical_silent_install.py`
- `src/tiny_swarm_world/application/services/deployment/__init__.py`
- `src/tiny_swarm_world/domain/configuration/credential_resolution.py`
- `src/tiny_swarm_world/domain/configuration/internal_test_credentials.py`
- `src/tiny_swarm_world/infrastructure/adapters/clients/infisical_cli_client.py`
- `src/tiny_swarm_world/infrastructure/composition_configuration.py`
- `src/tiny_swarm_world/infrastructure/composition_operator_configuration.py`
- `src/tiny_swarm_world/infrastructure/composition_deployment.py`
- `src/tiny_swarm_world/infrastructure/composition_runtime.py`
- `infra/config/secrets/infisical-secrets.yaml`
- `install.sh`
- `tools/coverage_diff.py`
- `.env.example`

## Tests and documentation

The changed test files cover the resolver conflict guard, catalog-backed sync,
Infisical bootstrap/client behavior, composition profile wiring, installer
options and output, simple-installer overrides, install-script behavior, and
secret-file removal. The affected operator contract, catalog, bootstrap,
Infisical, handbook, README, and console-output documentation was updated.
The post-merge audit also extends the resolver regression test and corrects the
security applicability wording in `documentation/security/statement-of-applicability.md`.

No generated runtime artifact, raw environment file, credential value, token,
authorization header, or private endpoint is part of this evidence package.
