# Slice 06 Distribution Evidence

Workflow-ID: workflow-install-order-and-port-allocation-20260620
Slice-ID: 06
Purpose: Health check and validation plan registry.

## Evidence Path Guard

- Target evidence root: `.codex/evidence/workflow-install-order-and-port-allocation-20260620/`
- This slice must not write generic evidence files directly under `.codex/evidence/`.
- Existing generic Slice 01 evidence belongs to another workflow and remains out of scope.

## Stream Assignment

- Main executor: health-check registry, validation-plan declarations, workflow fail-closed validation, tests, and consolidation.
- Subagent reviewer: read-only Slice 06 risk review for desired-check versus observed-evidence separation.

## Initial Scope

- Add static health-check and validation-plan YAML declarations.
- Add application helpers that validate observed `VerificationResult` evidence against a declared plan.
- Keep live HTTP or Swarm checks out of default quality gates.
- Prove missing observed evidence fails closed.
