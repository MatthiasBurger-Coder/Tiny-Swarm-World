# Slice 02 Consolidation

Workflow id: `workflow-replace-rabbitmq-with-apache-pulsar`

Slice id: `S02`

Slice title: Add Apache Pulsar compose stack

Stream results:

- Runtime: added `infra/config/compose/pulsar/docker-compose.yml`.
- Tests: added focused coverage for the committed Pulsar compose file.
- Architecture: kept this slice limited to adding Pulsar; RabbitMQ contracts
  and RabbitMQ compose remain unchanged for later ordered slices.

Accepted findings:

- Existing compose files use Docker Swarm `deploy` sections and manager
  placement constraints.
- Host port mappings use structured mappings with `mode: host`.
- `service_access_link` is the existing external network used for service
  access to internal HTTP services.

Rejected findings:

- Direct `8080:8080` host mapping was rejected because Jenkins and other
  service-access surfaces already use or depend on host `8080`.
- RabbitMQ removal was rejected for this slice because the workflow reserves it
  for Slice 07 after inventory, contracts, service access, configuration, and
  documentation are updated.

Files changed per stream:

- runtime:
  - `infra/config/compose/pulsar/docker-compose.yml`
- tests:
  - `tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py`
- documentation/evidence:
  - `.codex/evidence/slice-02-distribution.md`
  - `.codex/evidence/slice-02-consolidation.md`

Conflicts found:

- None.

Conflicts resolved:

- Not applicable.

Tests executed:

- `wsl bash -lc 'cd /mnt/d/Projects/Tiny-Swarm-World && PATH="$PWD/.venv/bin:$PWD/venv/bin:$PWD/bin:$PATH" PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml'`
- `wsl bash -lc 'cd /mnt/d/Projects/Tiny-Swarm-World && PATH="$PWD/.venv/bin:$PWD/venv/bin:$PWD/bin:$PATH" python3 tools/quality_gate.py quality'`

Quality-gate result:

- Targeted compose repository test: passed, 33 tests.
- Full quality gate: passed, 886 tests with 17 skipped.

SonarQube findings and fixes:

- Not applicable for local Slice 02 execution.

Documentation updates:

- Slice execution evidence was created.

Final integration decision:

- Accepted. The Pulsar compose stack exists, includes a healthcheck, persists
  data/config volumes, exposes `6650` and `8087:8080`, avoids host `8080`, and
  remains scoped to Slice 02.
