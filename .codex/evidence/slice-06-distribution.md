# Slice 06 Distribution Decision

Workflow id: `workflow-replace-rabbitmq-with-apache-pulsar`

Slice id: `S06`

Slice title: Update secrets and environment contract

Affected areas:

- configuration
- secrets
- runtime wiring
- tests
- documentation

Chosen execution mode: sequential

Selected streams:

- configuration
- tests
- documentation

Real subagents used: no

Fallback role-based review used: yes

Git worktrees used: no

Expected touched files/directories:

- `.env.example`
- `infra/config/secrets/infisical-secrets.yaml`
- `documentation/configuration/operator-configuration-contract.md`
- `documentation/configuration/config-contract-inventory.md`
- `src/tiny_swarm_world/domain/configuration/configuration_contract.py`
- `src/tiny_swarm_world/infrastructure/composition.py`
- `tests`
- `.codex/evidence/slice-06-distribution.md`
- `.codex/evidence/slice-06-consolidation.md`

Conflict risks:

- Pulsar standalone is unauthenticated, so introducing a fake password would create misleading operator obligations.
- Existing Infisical seed wiring still referenced RabbitMQ and must be removed with the contract update.
- `.env.example` is expected to match the default configuration contract exactly.

Quality gates to run:

- `PYTHONPATH=src python3 -m unittest tests.domain.configuration.test_configuration_contract tests.architecture.test_repository_hygiene tests.infrastructure.test_composition tests.live.test_post_install_browser_live tests.test_install_script`
- `python3 tools/quality_gate.py quality`

Consolidation plan:

- Remove RabbitMQ credential requirements from environment examples, secret manifests, config contracts, and Infisical seed wiring.
- Add optional Pulsar URL configuration only, with no Pulsar credential.
- Document unauthenticated local standalone mode explicitly.

Parallelization decision:

- Rejected. The environment template, configuration contract, runtime wiring, and hygiene tests must remain synchronized.
