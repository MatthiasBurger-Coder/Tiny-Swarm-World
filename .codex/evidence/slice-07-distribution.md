# Slice 07 Distribution Decision

Workflow id: `workflow-replace-rabbitmq-with-apache-pulsar`

Slice id: `S07`

Slice title: Remove RabbitMQ compose stack

Affected areas:

- infrastructure compose configuration
- tests
- documentation baseline

Chosen execution mode: sequential

Selected streams:

- runtime
- tests
- documentation

Real subagents used: no

Fallback role-based review used: yes

Git worktrees used: no

Expected touched files/directories:

- `infra/config/compose/rabbitmq/docker-compose.yml`
- `tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py`
- `documentation/workflow/issues/issue-4/swarm-stack-validation-baseline.md`
- `.codex/evidence/slice-07-distribution.md`
- `.codex/evidence/slice-07-consolidation.md`

Conflict risks:

- Compose repository tests still enumerated RabbitMQ while the file remained present.
- Historical documentation references must be distinguished from active stack references.

Quality gates to run:

- `PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml tests.domain.deployment.test_service_stack_contract`
- `python3 tools/quality_gate.py quality`

Consolidation plan:

- Remove the RabbitMQ compose file.
- Remove RabbitMQ compose assertions from active repository tests.
- Remove RabbitMQ from the current compose baseline list.

Parallelization decision:

- Rejected. File deletion and tests must be changed together to avoid a broken intermediate state.
