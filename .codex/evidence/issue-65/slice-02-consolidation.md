# Slice 02 Consolidation: Issue 65 Implementation

Workflow id: `issue-65-backend-resource-mapping-20260614`
Slice id: `S02`
Slice title: Scoped implementation inside the declared architecture boundary

## Stream Results

- Backend stream completed.
- Test stream completed.
- Architecture review stream completed read-only.

## Accepted Findings

- `provider_resource_resolution` is now backend-specific through
  `provider_resource_resolution.backends.incus` and
  `provider_resource_resolution.backends.lxd`.
- `LxcNodeProvider` resolves network and storage resources through the selected
  backend before profile checks, node lookup, launch, or mutation.
- Missing selected-backend mapping blocks with `inventory_mapping_missing`
  before runner commands are executed.
- Evidence includes the selected backend separately and keeps remediation hints
  backend-neutral to preserve summary-only evidence safety.
- Repository validation requires Incus and LXD resource mappings because both
  backends are supported candidates.

## Rejected Findings

- None.

## Files Changed Per Stream

Backend:

- `infra/config/node-providers/provider_config.yaml`
- `src/tiny_swarm_world/infrastructure/adapters/repositories/node_provider_config_yaml_repository.py`
- `src/tiny_swarm_world/infrastructure/adapters/clients/lxc_node_provider.py`

Tests:

- `tests/infrastructure/adapters/repositories/test_node_provider_config_yaml_repository.py`
- `tests/infrastructure/adapters/clients/test_lxc_node_provider.py`

Evidence:

- `.codex/evidence/issue-65/slice-02-distribution.md`
- `.codex/evidence/issue-65/slice-02-consolidation.md`

## Conflicts Found

- Existing LXC node provider tests encoded LXD-specific resource names for
  Incus selections.
- Initial backend-specific remediation text contained provider command-like
  words in `remediation_hint`, which violated evidence safety.

## Conflicts Resolved

- Tests now assert Incus uses `incusbr0`, LXD uses `lxdbr0`, and selected
  backend mappings are isolated.
- Remediation hints are backend-neutral while the `backend` evidence key
  records the selected backend.

## Tests Executed

- `PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_node_provider_config_yaml_repository tests.infrastructure.adapters.clients.test_lxc_node_provider`
  - First run failed on evidence-safety validation for backend-specific
    remediation text.
  - Final run passed, 61 tests.
- `PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition tests.infrastructure.adapters.preflight.test_lxc_provider_preflight tests.application.services.platform.test_node_provider_selection`
  - Passed, 95 tests.
- `python3 tools/quality_gate.py lint`
  - Passed.
- `python3 tools/quality_gate.py typecheck`
  - Passed, no issues in 391 source files.
- `git diff --check`
  - Passed.

## SonarQube Findings

- No local SonarQube findings were available during this slice.

## Documentation Updates

- S04 must document the hard schema migration from global
  `provider_resource_resolution.network_mappings/storage_pool` to
  backend-specific `provider_resource_resolution.backends.<backend>`.

## Final Integration Decision

Accept S02. The implementation satisfies Issue #65 behavior inside
configuration and infrastructure boundaries without live infrastructure
execution.
