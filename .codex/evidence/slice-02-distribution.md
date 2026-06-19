# Slice 02 Distribution Decision

Workflow id: `workflow-replace-rabbitmq-with-apache-pulsar`

Slice id: `S02`

Slice title: Add Apache Pulsar compose stack

Affected areas:

- runtime
- tests
- architecture

Chosen execution mode: sequential

Selected streams:

- runtime
- tests

Real subagents used: no

Fallback role-based review used: yes

Git worktrees used: no

Expected touched files/directories:

- `infra/config/compose/pulsar/docker-compose.yml`
- `tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py`
- `.codex/evidence/slice-02-distribution.md`
- `.codex/evidence/slice-02-consolidation.md`

Conflict risks:

- Compose conventions must remain compatible with Docker Swarm stack
  deployment.
- Slice 02 must not remove or retarget RabbitMQ contracts yet.
- Host port `8080` must not be exposed directly.

Quality gates to run:

- `PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml`
- `python3 tools/quality_gate.py quality`

Consolidation plan:

- Add the Pulsar compose file.
- Add focused compose repository test coverage for the committed Pulsar file.
- Run the targeted compose repository test under WSL.
- Run the full quality gate under WSL before checkpoint commit.

Parallelization decision:

- Rejected. The compose file and its focused test are tightly coupled, and the
  workflow requires RabbitMQ to remain untouched in this slice.
