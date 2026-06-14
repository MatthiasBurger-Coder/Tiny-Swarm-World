# Slice 03 Distribution: Issue 64 Backend Selection Order

Workflow id: `issue-64-backend-selection-order-20260614`
Slice id: `S03`
Slice title: Focused regression and architecture tests

## Affected Areas

- `tests/**`
- `infra/config/node-providers/**`
- `src/tiny_swarm_world/domain/node_provider/**`

## Execution Mode

Sequential verification.

## Subagents

Real subagent review requested from the Senior Tester stream. No write-capable
subagent was spawned because Slice 03 is verification-only.

## Selected Streams

- tests
- architecture
- quality

## Worktrees

Main issue worktree:

```text
../Tiny-Swarm-World-worktrees/issue-64-backend-selection-order
```

## Conflict Risks

- Test failures may point back to Slice 02 port signatures or evidence
  semantics.
- Architecture failures must not be fixed by weakening import boundaries.

## Quality Gates

- `PYTHONPATH=src python3 -m unittest tests.domain.node_provider.test_provider_model tests.infrastructure.adapters.preflight.test_lxc_provider_preflight tests.application.services.platform.test_node_provider_selection tests.infrastructure.adapters.repositories.test_node_provider_config_yaml_repository tests.infrastructure.test_composition`
- `python3 tools/quality_gate.py arch-tests`
- `python3 tools/quality_gate.py test`
- `git diff --check`

## Consolidation Plan

Run focused regression, architecture, and repository test gates, collect tester
subagent findings, then commit only Slice 03 evidence unless an in-scope defect
is exposed.
