# Slice 02 Distribution: Issue 64 Backend Selection Order

Workflow id: `issue-64-backend-selection-order-20260614`
Slice id: `S02`
Slice title: Scoped implementation inside the declared architecture boundary

## Affected Areas

- `src/tiny_swarm_world/application/ports/node_provider/port_node_provider_readiness.py`
- `src/tiny_swarm_world/application/services/platform/node_provider_selection.py`
- `src/tiny_swarm_world/infrastructure/adapters/preflight/lxc_provider_preflight.py`
- `src/tiny_swarm_world/infrastructure/composition.py`
- `tests/**`

## Execution Mode

Sequential implementation.

## Subagents

Real subagent review requested for architecture and test adequacy after the
initial patch. Work is not split because port signature, preflight behavior,
composition wiring, and tests are coupled.

## Selected Streams

- backend
- infrastructure
- tests
- architecture

## Worktrees

Main issue worktree:

```text
../Tiny-Swarm-World-worktrees/issue-64-backend-selection-order
```

## Conflict Risks

- Readiness-port signature changes must update all implementations and test
  doubles.
- Composition must use configuration without leaking YAML repository details
  into application services.
- Diagnostics must remain summary-only and free of raw command output.

## Quality Gates

- `PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.preflight.test_lxc_provider_preflight tests.application.services.platform.test_node_provider_selection tests.infrastructure.adapters.repositories.test_node_provider_config_yaml_repository tests.infrastructure.test_composition`
- `python3 tools/quality_gate.py typecheck`
- `git diff --check`

## Consolidation Plan

Verify focused tests and typecheck, collect subagent review, then commit only
Slice 02 code, tests, and evidence.
