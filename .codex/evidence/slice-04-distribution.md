# Slice 04 Distribution Decision

Workflow id: `workflow-replace-rabbitmq-with-apache-pulsar`

Slice id: `S04`

Slice title: Update service stack contract

Affected areas:

- backend
- tests
- documentation

Chosen execution mode: sequential

Selected streams:

- backend
- tests
- documentation

Real subagents used: no

Fallback role-based review used: yes

Git worktrees used: no

Expected touched files/directories:

- `src/tiny_swarm_world/domain/deployment/service_stack_contract.py`
- `tests/domain/deployment/test_service_stack_contract.py`
- `tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py`
- `tests/infrastructure/adapters/repositories/test_inventory_repositories.py`
- `documentation/workflow/issues/issue-4/swarm-stack-validation-baseline.md`
- `.codex/evidence/slice-04-distribution.md`
- `.codex/evidence/slice-04-consolidation.md`

Conflict risks:

- Deployment contracts must now align with the Slice 03 desired inventory.
- RabbitMQ compose still exists until Slice 07, so tests may still inspect it
  as a committed file but must not treat it as a default required stack.

Quality gates to run:

- `PYTHONPATH=src python3 -m unittest tests.domain.deployment.test_service_stack_contract`
- `python3 tools/quality_gate.py quality`

Consolidation plan:

- Replace the RabbitMQ service stack contract with Pulsar.
- Update deployment contract tests and downstream contract consumers.
- Remove the Slice 03 temporary inventory-test bridge.
- Update Issue 4 stack-validation baseline documentation.

Parallelization decision:

- Rejected. Contract, inventory consistency tests, and baseline documentation
  must change together.
