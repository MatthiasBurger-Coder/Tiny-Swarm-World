# Slice 04 Report: Command Catalog, Inventory, And Evidence Foundation

## Status

```text
COMPLETED
```

## Changes

- Added command evidence policy metadata and propagated it from typed YAML
  command entities to executable command entities.
- Made credential-output commands fail closed unless they are classified as
  `credential_mutation` and explicitly forbid raw output storage.
- Made `runtime_change` commands fail closed when classified as `safe_read`.
- Reclassified the Docker Swarm join-token command as credential-sensitive and
  added a redacted evidence policy.
- Reclassified the Multipass restart command as `safe_mutation` with manual
  verification metadata.
- Added a host-neutral desired inventory baseline at
  `infra/config/inventory/desired_inventory.yaml`.
- Made desired inventory parsing reject unknown fields so host-specific IPs,
  gateways, users, tokens, passwords, and secrets cannot be silently ignored.
- Validated verification messages with the same summary-only redaction
  contract used for persisted evidence values.
- Updated arc42 concepts, quality requirements, building blocks, and risk debt
  to match the new command, inventory, and evidence behavior.

## Review Notes

- Manual command verification remains metadata only. It is not treated as
  passed evidence.
- Command-backed verification is represented by the domain type, but no
  product command YAML uses `verify.type: command` yet.
- End-to-end credential logging in application services remains outside Slice
  04 locks and must not be reported as fully solved by this slice.
- Existing legacy command YAML still contains live-operation/default-looking
  values that should be cleaned in a later scoped slice instead of copied into
  desired inventory.

## Verification

```text
PYTHONPATH=src python3 -m unittest tests.domain.command.test_command_spec
PASS, 14 tests
```

```text
PYTHONPATH=src python3 -m unittest tests.domain.inventory.test_inventory_model
PASS, 11 tests
```

```text
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_inventory_repositories
PASS, 14 tests
```

```text
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_command_repository_yaml_contract
PASS, 10 tests
```

```text
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.command_runner.test_command_workflow_configuration
PASS, 5 tests
```

```text
python3 tools/quality_gate.py arch-tests
PASS, 14 tests
```

```text
python3 tools/quality_gate.py test
PASS, 230 tests, 1 skipped
```

```text
/tmp/tsw-quality-venv/bin/python tools/quality_gate.py quality
PASS
```

```text
python3 -m json.tool documentation/workflow/context-pack.json
PASS
```

```text
git diff --check
PASS
```

Gate result details:

```text
lint: PASS
arch-lint: PASS, 3 contracts kept and 0 broken
arch-tests: PASS
typecheck: PASS, no issues found in 245 source files
test: PASS, 230 tests run, 1 skipped
```

## CP_RECORD

```yaml
Slice-ID: "04"
workflowVersion: "system-unification-v1.0.0"
sliceTitle: "Command Catalog, Inventory, And Evidence Foundation"
responsibleRole: "senior_python_automation_developer"
reviewedRoles:
  - "senior_python_automation_developer"
  - "senior_system_architect"
changedFiles:
  - "src/tiny_swarm_world/domain/command/command_entity.py"
  - "src/tiny_swarm_world/domain/inventory/desired_inventory.py"
  - "src/tiny_swarm_world/domain/inventory/verification.py"
  - "src/tiny_swarm_world/application/ports/commands/executable_command.py"
  - "src/tiny_swarm_world/application/services/commands/command_builder/vm_parameter/strategies/manager_strategy.py"
  - "src/tiny_swarm_world/application/services/commands/command_builder/vm_parameter/strategies/worker_strategy.py"
  - "src/tiny_swarm_world/application/services/commands/command_builder/vm_parameter/strategies/none_strategy.py"
  - "infra/config/docker/command_multipass_docker_swarm_manager_join_token.yaml"
  - "infra/config/multipass/command_multipass_restart_repository_yaml.yaml"
  - "infra/config/inventory/desired_inventory.yaml"
  - "tests/domain/command/test_command_spec.py"
  - "tests/domain/inventory/test_inventory_model.py"
  - "tests/infrastructure/adapters/command_runner/test_command_workflow_configuration.py"
  - "tests/infrastructure/adapters/repositories/test_command_repository_yaml_contract.py"
  - "tests/infrastructure/adapters/repositories/test_inventory_repositories.py"
  - "documentation/arc42/05_building_blocks.adoc"
  - "documentation/arc42/08_concepts.adoc"
  - "documentation/arc42/10_quality_requirements.adoc"
  - "documentation/arc42/11_risks_and_debt.adoc"
  - "documentation/workflow/context-pack.md"
  - "documentation/workflow/context-pack.json"
  - "documentation/workflow/reports/04-command-inventory-evidence-foundation.md"
  - "documentation/workflow/execution-report.md"
qualityGates:
  - command: "PYTHONPATH=src python3 -m unittest tests.domain.command.test_command_spec"
    result: "PASS"
  - command: "PYTHONPATH=src python3 -m unittest tests.domain.inventory.test_inventory_model"
    result: "PASS"
  - command: "PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_inventory_repositories"
    result: "PASS"
  - command: "PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_command_repository_yaml_contract"
    result: "PASS"
  - command: "PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.command_runner.test_command_workflow_configuration"
    result: "PASS"
  - command: "python3 tools/quality_gate.py arch-tests"
    result: "PASS"
  - command: "python3 tools/quality_gate.py test"
    result: "PASS"
  - command: "/tmp/tsw-quality-venv/bin/python tools/quality_gate.py quality"
    result: "PASS"
  - command: "python3 -m json.tool documentation/workflow/context-pack.json"
    result: "PASS"
  - command: "git diff --check"
    result: "PASS"
rollbackReference: "revert this Slice 04 checkpoint commit on codex/workflow-system-unification-20260524"
arc42Updated: true
adrUpdated: false
```

## Slice 04 Decision

```text
READY_FOR_NEXT_SLICE
```

Slice 05 may proceed to platform verify-after-apply contracts. It must not
claim end-to-end credential redaction until application-service logging is
addressed within an authorized lock.
