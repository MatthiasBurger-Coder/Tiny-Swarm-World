# Slice 01 Consolidation: Issue 64 Backend Selection Order

Workflow id: `issue-64-backend-selection-order-20260614`
Slice id: `S01`
Slice title: Requirement, repository baseline, and decision gate

## Issue Requirements

Issue #64 requires deterministic managed LXC backend selection:

- Explicit CLI/backend override wins.
- Without explicit override, use configured backend candidate order.
- Do not prefer LXD implicitly because `lxc` exists when Incus is configured
  first and available.
- Selection diagnostics must state selected backend, selection reason, and
  skipped candidates.

## Baseline

- `infra/config/node-providers/provider_config.yaml` declares `incus` before
  `lxd`.
- `NodeProviderConfigYamlRepository` loads `preferred_backend` and
  `backend_candidates`; it validates the required backend set while preserving
  order.
- `NodeProviderSelectionService` passes `preferred_backend` to the readiness
  port.
- `LxcProviderPreflightProbe` currently uses hard-coded auto candidates
  `(INCUS, LXD)` when no explicit backend is supplied.
- When both backends are ready without explicit preference, current preflight
  behavior returns `BACKEND_AMBIGUOUS` instead of selecting the first
  configured ready candidate.

## Subagent Review

Senior Requirement Engineer/System Architect subagent review completed.

Result: S02 may proceed.

Accepted findings:

- Candidate-order behavior is missing from the readiness port and preflight
  adapter.
- Existing CLI override path is present and must keep precedence.
- Diagnostics are partial and need skipped-candidate information.
- No ADR blocker was identified.

## S02 Target Files

- `src/tiny_swarm_world/application/ports/node_provider/port_node_provider_readiness.py`
- `src/tiny_swarm_world/application/services/platform/node_provider_selection.py`
- `src/tiny_swarm_world/infrastructure/adapters/preflight/lxc_provider_preflight.py`
- `src/tiny_swarm_world/infrastructure/composition.py`, if the composed
  default request needs to pass configured candidate order.
- Tests under `tests/infrastructure/adapters/preflight/`,
  `tests/application/services/platform/`, and
  `tests/infrastructure/adapters/repositories/`.

## Architecture Risks

- Do not inject the YAML repository into application services.
- Do not run live `incus` or `lxc` commands in tests.
- Keep diagnostics summary-only and redacted.
- Keep explicit CLI override ahead of configured preferred backend and
  candidate order.

## Tests Executed

```text
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.preflight.test_lxc_provider_preflight tests.infrastructure.adapters.repositories.test_node_provider_config_yaml_repository tests.application.services.platform.test_node_provider_selection
```

Result: passed, 52 tests.

```text
git diff --check
```

Result: passed.

## Final Integration Decision

Accepted for Slice 01 checkpoint commit. S02 may implement candidate-order
selection and diagnostics.
