# Slice 06 Consolidation Evidence

Workflow-ID: workflow-install-order-and-port-allocation-20260620
Slice-ID: 06
Purpose: Health check and validation plan registry.

## Implemented Changes

- Added `infra/config/health-checks.yaml` with static desired readiness checks.
- Added `infra/config/validation-plan.yaml` with greenpath required evidence targets.
- Added `ValidationPlan` evaluation in deployment workflows.
- Required validation evidence now fails closed when missing, blocked, failed, or verified only by static/non-observed evidence.
- Added observed-evidence marker `evidence_kind=swarm_service_replicas` to Swarm readiness evidence.
- Added tests that align health checks with service registry, service contracts, installation phases, and validation targets.
- Kept live health checks out of default quality gates; YAML has `live_default: false`.

## Subagent Review

- Read-only Slice 06 reviewer identified that YAML declarations alone would not enforce missing evidence failures.
- Applied recommendation by adding an explicit validation-plan evaluator and tests for missing/static/blocked observed evidence.
- Added Traefik readiness target to health checks and validation plan to avoid service registry drift.

## Evidence Path Guard

- Evidence written only below `.codex/evidence/workflow-install-order-and-port-allocation-20260620/`.
- Generic `.codex/evidence/slice-*` files were not used for this slice.
- Prior evidence for `workflow-replace-rabbitmq-with-apache-pulsar` remains out of scope and unchanged.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_verify_swarm_service_readiness tests.application.services.deployment.test_deployment_workflows tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml`
  - Result: passed, 66 tests.
- YAML static parse check for `infra/config/health-checks.yaml` and `infra/config/validation-plan.yaml`
  - Result: passed.
- `git diff --check`
  - Result: passed.
- `python3 tools/quality_gate.py quality`
  - Result: passed.
  - Lint: passed.
  - Import-layer contracts: passed, 3 kept, 0 broken.
  - Architecture tests: passed.
  - Typecheck: passed, 403 source files.
  - Unit tests: passed, 940 tests, 18 skipped.

## Architecture And ADR Status

- Static health-check and validation-plan declarations are separate from observed runtime evidence.
- Missing observed evidence reports `FAILED_TO_VERIFY`, never healthy.
- No live infrastructure commands were executed.
- No ADR required for this slice because it strengthens validation semantics without changing runtime topology.
