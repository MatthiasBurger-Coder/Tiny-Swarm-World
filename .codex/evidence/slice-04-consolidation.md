# Slice 04 Consolidation

Workflow id: `workflow-replace-rabbitmq-with-apache-pulsar`

Slice id: `S04`

Slice title: Update service stack contract

Stream results:

- Backend/domain: replaced the RabbitMQ service stack contract with Pulsar.
- Tests: updated deployment contract tests and contract consumers.
- Documentation: updated Issue 4 stack-validation baseline to include Pulsar.

Accepted findings:

- Default service stack contracts now include `pulsar` instead of `rabbitmq`.
- Pulsar service readiness target is `deployment:pulsar-service-readiness`.
- Pulsar stack target is `deployment:pulsar-stack`.
- Pulsar localhost endpoint is `http://localhost:8087`.
- Desired inventory now matches the default service stack profile directly; the
  Slice 03 temporary inventory-test bridge was removed.

Rejected findings:

- RabbitMQ compose stack deletion was not included because Slice 07 owns
  deletion after service access, configuration, docs, and residue checks are
  updated.
- RabbitMQ secrets/config cleanup was not included because Slice 06 owns the
  configuration contract.

Files changed per stream:

- backend/domain:
  - `src/tiny_swarm_world/domain/deployment/service_stack_contract.py`
- tests:
  - `tests/domain/deployment/test_service_stack_contract.py`
  - `tests/application/services/deployment/test_service_stack_plan.py`
  - `tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py`
  - `tests/infrastructure/adapters/repositories/test_inventory_repositories.py`
  - `tests/infrastructure/test_composition.py`
- documentation:
  - `documentation/workflow/issues/issue-4/swarm-stack-validation-baseline.md`
- documentation/evidence:
  - `.codex/evidence/slice-04-distribution.md`
  - `.codex/evidence/slice-04-consolidation.md`

Conflicts found:

- Full quality initially found deployment planning and composition tests still
  expecting RabbitMQ stack target IDs.

Conflicts resolved:

- Updated contract-consumer expectations to Pulsar target IDs and stack names.

Tests executed:

- `wsl bash -lc 'cd /mnt/d/Projects/Tiny-Swarm-World && PATH="$PWD/.venv/bin:$PWD/venv/bin:$PWD/bin:$PATH" PYTHONPATH=src python3 -m unittest tests.domain.deployment.test_service_stack_contract'`
- `wsl bash -lc 'cd /mnt/d/Projects/Tiny-Swarm-World && PATH="$PWD/.venv/bin:$PWD/venv/bin:$PWD/bin:$PATH" PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml tests.infrastructure.adapters.repositories.test_inventory_repositories'`
- `wsl bash -lc 'cd /mnt/d/Projects/Tiny-Swarm-World && PATH="$PWD/.venv/bin:$PWD/venv/bin:$PWD/bin:$PATH" PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_service_stack_plan tests.domain.deployment.test_service_stack_contract'`
- `wsl bash -lc 'cd /mnt/d/Projects/Tiny-Swarm-World && PATH="$PWD/.venv/bin:$PWD/venv/bin:$PWD/bin:$PATH" PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition'`
- `wsl bash -lc 'cd /mnt/d/Projects/Tiny-Swarm-World && PATH="$PWD/.venv/bin:$PWD/venv/bin:$PWD/bin:$PATH" python3 tools/quality_gate.py quality'`

Quality-gate result:

- Deployment contract tests: passed, 15 tests.
- Compose and inventory repository tests: passed, 50 tests.
- Deployment planning and contract tests: passed, 21 tests.
- Composition tests: passed, 70 tests.
- Full quality gate: passed, 888 tests with 17 skipped.

SonarQube findings and fixes:

- Not applicable for local Slice 04 execution.

Documentation updates:

- Issue 4 stack-validation baseline now lists the Pulsar compose stack.

Final integration decision:

- Accepted. Service stack contracts no longer require RabbitMQ and now require
  Pulsar, with downstream tests and composition wiring aligned.
