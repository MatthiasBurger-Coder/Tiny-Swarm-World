# Slice 04 Consolidation Evidence

Workflow-ID: workflow-install-order-and-port-allocation-20260620
Slice-ID: 04
Purpose: Installation phase registry and dependency graph.

## Implemented Changes

- Added `infra/config/installation-plan.yaml` as the committed declarative installation phase registry.
- Added a pure domain `InstallationPlan` and `InstallationPhase` model in `tiny_swarm_world.domain.preflight.installation_plan`.
- Added deterministic dependency ordering with `(order, phase_id)` tie-breaking and cycle detection.
- Added fail-closed validation for missing dependencies, required phase IDs, required services, duplicate setup workflow phase names, and missing required workflow phases.
- Extended `SetupWorkflow` with optional typed `installation_plan` ordering.
- Wired default setup composition to pass `default_installation_plan()` without parsing YAML in domain or application code.
- Kept YAML parsing out of this slice to preserve the hexagonal boundary; a future infrastructure adapter can load the YAML through an application port.

## Subagent Review

- Read-only Slice 04 reviewer checked risks for deterministic ordering, cycle detection, missing required phases/services, and architecture boundaries.
- Reviewer recommendation applied:
  - Phase graph moved to a separate domain module instead of `setup_manifest.py`.
  - YAML is not parsed by domain or `SetupWorkflow`.
  - Tests cover deterministic order, cycles, unknown dependency targets, missing required phases, missing required services, and workflow fail-closed behavior.

## Evidence Path Guard

- Evidence written only below `.codex/evidence/workflow-install-order-and-port-allocation-20260620/`.
- Generic `.codex/evidence/slice-*` files were not used for this slice.
- Prior evidence for `workflow-replace-rabbitmq-with-apache-pulsar` remains out of scope and unchanged.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.application.services.setup.test_setup_workflow tests.domain.preflight.test_preflight_result`
  - Result: passed, 46 tests.
- YAML static parse check for `infra/config/installation-plan.yaml`
  - Result: passed, schema version 1, 13 phases, first `preflight`, last `validation`.
- `git diff --check`
  - Result: passed.
- `python3 tools/quality_gate.py quality`
  - Result: passed.
  - Lint: passed.
  - Import-layer contracts: passed, 3 kept, 0 broken.
  - Architecture tests: passed.
  - Typecheck: passed, 403 source files.
  - Unit tests: passed, 930 tests, 18 skipped.

## Architecture And ADR Status

- Hexagonal boundary preserved: phase-plan domain code imports no YAML, filesystem, infrastructure, command runner, or application service code.
- SetupWorkflow consumes typed domain objects only.
- No live infrastructure commands were executed.
- No ADR required for this slice because it adds deterministic setup ordering within the approved workflow architecture.
