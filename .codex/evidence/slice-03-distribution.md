# Slice 03 Distribution Decision

Workflow id: `workflow-replace-rabbitmq-with-apache-pulsar`

Slice id: `S03`

Slice title: Replace RabbitMQ in desired inventory and setup manifest

Affected areas:

- backend
- runtime
- tests

Chosen execution mode: sequential

Selected streams:

- backend
- tests

Real subagents used: no

Fallback role-based review used: yes

Git worktrees used: no

Expected touched files/directories:

- `infra/config/inventory/desired_inventory.yaml`
- `src/tiny_swarm_world/domain/preflight/setup_manifest.py`
- `src/tiny_swarm_world/infrastructure/adapters/preflight/host_preflight_probe.py`
- `tests/domain/preflight/test_preflight_result.py`
- `tests/infrastructure/adapters/preflight/test_host_preflight_probe.py`
- `.codex/evidence/slice-03-distribution.md`
- `.codex/evidence/slice-03-consolidation.md`

Conflict risks:

- Inventory and setup manifest must agree on the active platform service name.
- Host preflight must not keep RabbitMQ port recognition as an active expected
  service path.
- RabbitMQ compose and deployment contract removal are intentionally later
  slices.

Quality gates to run:

- `PYTHONPATH=src python3 -m unittest tests.domain.preflight.test_preflight_result`
- `PYTHONPATH=src python3 -m unittest discover tests/infrastructure/adapters/preflight`
- `python3 tools/quality_gate.py quality`

Consolidation plan:

- Replace active inventory stack entries with `pulsar`.
- Replace setup manifest RabbitMQ service with Pulsar port checks.
- Add/adjust host preflight recognition for occupied Pulsar ports.
- Update preflight tests and run targeted gates before the full quality gate.

Parallelization decision:

- Rejected. Domain manifest, infrastructure recognition, and tests must move
  together to avoid a transient inconsistent preflight contract.
