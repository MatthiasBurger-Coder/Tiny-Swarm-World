# Slice 05 Distribution Evidence

Workflow-ID: workflow-install-order-and-port-allocation-20260620
Slice-ID: 05
Purpose: Service registry and stack alignment.

## Evidence Path Guard

- Target evidence root: `.codex/evidence/workflow-install-order-and-port-allocation-20260620/`
- This slice must not write generic evidence files directly under `.codex/evidence/`.
- Existing generic Slice 01 evidence belongs to another workflow and remains out of scope.

## Stream Assignment

- Main executor: service stack contract alignment, service registry config, compose metadata tests, and consolidation.
- Subagent reviewer: read-only Slice 05 risk review for scope, port registry alignment, readiness semantics, and stop conditions.

## Initial Scope

- Add phase and port registry identifiers to service stack contracts.
- Expand the committed service registry with stack phase and port metadata.
- Verify selected stacks map to declared installation phases and port registry entries.
- Keep live deployment, runtime readiness claims, and broad compose port rewrites out of scope.
