# Slice 02 Consolidation: Issue 64 Backend Selection Order

Workflow id: `issue-64-backend-selection-order-20260614`
Slice id: `S02`
Slice title: Scoped implementation inside the declared architecture boundary

## Stream Results

- backend: accepted. `NodeProviderSelectionRequest` and the readiness port now
  carry configured backend candidate order.
- infrastructure: accepted. LXC preflight auto-selection uses candidate order
  and keeps explicit backend override precedence.
- tests: accepted. Added Incus-first, LXD-first, unavailable candidate, and
  composition-order coverage.
- architecture: accepted. Config loading remains in infrastructure; application
  services depend on ports and value objects.

## Subagent Review

Senior Python Automation Developer/System Architect subagent review completed.

Initial result: two blockers.

Accepted and fixed blockers:

- Selected readiness evidence lost configured candidate order. Fixed by
  allowing selected backend selections to retain candidate lists that include
  the selected backend.
- Skipped diagnostics omitted unavailable candidates before the selected
  backend. Fixed by emitting summary-only skipped candidate names and reasons
  such as `cli_absent` and `lower_priority_ready`.

Final decision: S02 can consolidate after focused tests, lint, typecheck, and
diff checks passed.

## Files Changed Per Stream

- backend:
  `src/tiny_swarm_world/application/ports/node_provider/port_node_provider_readiness.py`,
  `src/tiny_swarm_world/application/services/platform/node_provider_selection.py`,
  `src/tiny_swarm_world/domain/node_provider/provider_model.py`
- infrastructure:
  `src/tiny_swarm_world/infrastructure/adapters/preflight/lxc_provider_preflight.py`,
  `src/tiny_swarm_world/infrastructure/composition.py`
- tests:
  `tests/infrastructure/adapters/preflight/test_lxc_provider_preflight.py`,
  `tests/application/services/platform/test_node_provider_selection.py`,
  `tests/infrastructure/test_composition.py`
- evidence:
  `.codex/evidence/issue-64/slice-02-distribution.md`,
  `.codex/evidence/issue-64/slice-02-consolidation.md`

## Conflicts

No merge conflicts detected.

## Tests Executed

```text
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.preflight.test_lxc_provider_preflight tests.application.services.platform.test_node_provider_selection tests.infrastructure.adapters.repositories.test_node_provider_config_yaml_repository tests.infrastructure.test_composition
```

Initial result: failed once because `build_platform_services` instantiated the
node-provider config repository twice. Fixed by sharing one repository instance
between default request construction and `LxcNodeProvider`.

Final result: passed, 119 tests.

```text
PYTHONPATH=src python3 -m unittest tests.domain.node_provider.test_provider_model tests.infrastructure.adapters.preflight.test_lxc_provider_preflight tests.application.services.platform.test_node_provider_selection tests.infrastructure.adapters.repositories.test_node_provider_config_yaml_repository tests.infrastructure.test_composition
```

Result: passed, 133 tests.

```text
python3 tools/quality_gate.py lint
```

Result: passed.

```text
python3 tools/quality_gate.py typecheck
```

Result: passed, no issues in 391 source files.

```text
git diff --check
```

Result: passed.

## SonarQube Findings

Not run locally. Remote PR checks remain the SonarQube decision point during
`push auto`.

## Documentation Updates

Deferred to Slice 04.

## Final Integration Decision

Accepted for Slice 02 checkpoint commit.
