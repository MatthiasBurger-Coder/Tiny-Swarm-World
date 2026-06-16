# Slice 03 Consolidation

Workflow id: `workflow-replace-rabbitmq-with-apache-pulsar`

Slice id: `S03`

Slice title: Replace RabbitMQ in desired inventory and setup manifest

Stream results:

- Backend/domain: replaced RabbitMQ with Pulsar in the setup manifest.
- Runtime/configuration: replaced `rabbitmq` with `pulsar` in desired inventory.
- Infrastructure: replaced RabbitMQ occupied-port recognition with Pulsar
  broker/Admin API recognition.
- Tests: updated preflight and inventory expectations.

Accepted findings:

- Desired inventory now lists `pulsar` as the active platform messaging stack.
- Default setup manifest now lists `Pulsar` and checks ports `6650` and `8087`
  outside centralized ingress.
- Setup manifest no longer requires `TSW_RABBITMQ_PASSWORD`.
- Host preflight recognizes an existing Pulsar Admin API on
  `/admin/v2/clusters` and the Pulsar broker TCP port.

Rejected findings:

- RabbitMQ deployment contract updates were not included because the workflow
  reserves service stack contract changes for Slice 04.
- RabbitMQ compose deletion was not included because deletion is reserved for
  Slice 07.

Files changed per stream:

- runtime/configuration:
  - `infra/config/inventory/desired_inventory.yaml`
- backend/domain:
  - `src/tiny_swarm_world/domain/preflight/setup_manifest.py`
- infrastructure:
  - `src/tiny_swarm_world/infrastructure/adapters/preflight/host_preflight_probe.py`
- tests:
  - `tests/domain/preflight/test_preflight_result.py`
  - `tests/infrastructure/adapters/preflight/test_host_preflight_probe.py`
  - `tests/infrastructure/adapters/repositories/test_inventory_repositories.py`
- documentation/evidence:
  - `.codex/evidence/slice-03-distribution.md`
  - `.codex/evidence/slice-03-consolidation.md`

Conflicts found:

- Full quality initially failed because inventory repository tests still
  expected `rabbitmq`.
- One inventory test compared inventory directly against deployment service
  stack contracts, which are intentionally migrated in Slice 04.

Conflicts resolved:

- Updated committed inventory expectations to `pulsar`.
- Added a narrow in-flight bridge in the inventory-to-contract comparison so
  Slice 03 can be green before Slice 04 moves the deployment contract.

Tests executed:

- `wsl bash -lc 'cd /mnt/d/Projects/Tiny-Swarm-World && PATH="$PWD/.venv/bin:$PWD/venv/bin:$PWD/bin:$PATH" PYTHONPATH=src python3 -m unittest tests.domain.preflight.test_preflight_result'`
- `wsl bash -lc 'cd /mnt/d/Projects/Tiny-Swarm-World && PATH="$PWD/.venv/bin:$PWD/venv/bin:$PWD/bin:$PATH" PYTHONPATH=src python3 -m unittest discover tests/infrastructure/adapters/preflight'`
- `wsl bash -lc 'cd /mnt/d/Projects/Tiny-Swarm-World && PATH="$PWD/.venv/bin:$PWD/venv/bin:$PWD/bin:$PATH" PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_inventory_repositories'`
- `wsl bash -lc 'cd /mnt/d/Projects/Tiny-Swarm-World && PATH="$PWD/.venv/bin:$PWD/venv/bin:$PWD/bin:$PATH" python3 tools/quality_gate.py quality'`

Quality-gate result:

- Domain preflight tests: passed, 15 tests.
- Infrastructure preflight tests: passed, 47 tests.
- Inventory repository tests: passed, 17 tests.
- Full quality gate: passed, 888 tests with 17 skipped.

SonarQube findings and fixes:

- Not applicable for local Slice 03 execution.

Documentation updates:

- Slice execution evidence was created.

Final integration decision:

- Accepted. RabbitMQ is no longer active desired inventory or setup/preflight
  state. Pulsar is active in both, and tests pass.
