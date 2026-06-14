# Slice 01 Consolidation: Issue 65 Baseline

Workflow id: `issue-65-backend-resource-mapping-20260614`
Slice id: `S01`
Slice title: Requirement, repository baseline, and decision gate

## Requirement Classification

- Functional: resolve network and storage resources per selected managed LXC
  backend.
- Architecture: keep backend-specific mapping in configuration and
  infrastructure adapters, not domain logic or application services.
- Resilience: missing selected-backend mappings must block before mutation.
- Documentation: operator override examples must describe backend-specific
  resource mappings.
- Quality: tests must cover Incus, LXD, and missing mapping failure.

## Repository Baseline

- `infra/config/node-providers/provider_config.yaml` currently supports Incus
  and LXD backend candidates but has a single global
  `provider_resource_resolution` mapping: `control: lxdbr0`, storage pool
  `default`.
- `NodeProviderConfigYamlRepository` currently accepts only
  `network_mappings` and `storage_pool` directly under
  `provider_resource_resolution`.
- `ProviderResourceResolution` is currently a single global value object.
- `LxcNodeProvider.ensure_node()` already verifies provider resources before
  profile reconciliation, node lookup, launch, or mutation.
- Resource verification and launch commands use the selected backend CLI, but
  read network and storage names from the global mapping.
- Existing tests include resource-resolution coverage, but some assertions use
  LXD-specific `lxdbr0` expectations for Incus selections.

## Subagent Findings

- Real subagent review completed read-only.
- Accepted finding: proceed to S02 with backend-specific resource-resolution
  configuration.
- Accepted finding: do not put CLI names, bridge names, YAML structure, or
  adapter details into domain logic.
- Accepted finding: selected backend without mapping must block before live
  mutation.

## Rejected Findings

- None.

## Tests Executed

- `git diff --check`
- `PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_node_provider_config_yaml_repository tests.infrastructure.adapters.clients.test_lxc_node_provider tests.infrastructure.test_composition`
  - Result: passed, 122 tests.

## Decision

Proceed to S02. Requirements are clear enough and repository evidence supports
a scoped implementation in configuration parsing plus the LXC node provider
adapter, with focused tests and documentation updates.
