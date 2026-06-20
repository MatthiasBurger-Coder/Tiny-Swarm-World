# Slice 04 Distribution Evidence

Workflow-ID: workflow-install-order-and-port-allocation-20260620
Slice-ID: 04
Purpose: Installation phase registry and dependency graph.

## Evidence Path Guard

- Target evidence root: `.codex/evidence/workflow-install-order-and-port-allocation-20260620/`
- This slice must not write generic evidence files directly under `.codex/evidence/`.
- Existing generic Slice 01 evidence belongs to another workflow and remains out of scope.

## Stream Assignment

- Main executor: domain phase-plan model, setup workflow ordering, central config, targeted tests, and consolidation.
- Subagent reviewer: read-only Slice 04 risk review for deterministic ordering, cycle detection, missing required phase fail-closed behavior, and architecture boundaries.

## Initial Scope

- Add a central installation phase declaration at `infra/config/installation-plan.yaml`.
- Add domain validation for acyclic phase dependencies and deterministic topological ordering.
- Integrate optional installation-plan ordering into `SetupWorkflow`.
- Add regression tests for ordering, cycles, and missing required workflow phases.
