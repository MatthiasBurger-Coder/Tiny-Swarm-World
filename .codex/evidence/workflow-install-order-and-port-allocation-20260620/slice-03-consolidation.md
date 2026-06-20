# Slice 03 Consolidation Evidence

Workflow-ID: workflow-install-order-and-port-allocation-20260620
Slice-ID: 03
Purpose: Port registry repository and preflight integration.

## Implemented Changes

- Added an application repository port for loading the committed port registry.
- Added a YAML-backed infrastructure adapter for `infra/config/ports.yaml`.
- Wired `build_preflight_service()` to load the registry through infrastructure composition.
- Extended `PreflightService` so host-port checks can come from registry mappings marked `required_for_preflight`.
- Kept post-install preflight behavior unchanged by leaving registry injection out of that path.
- Added repository, preflight, and composition regression tests.

## Evidence Path Guard

- Evidence written only below `.codex/evidence/workflow-install-order-and-port-allocation-20260620/`.
- Generic `.codex/evidence/slice-*` files were not used for this slice.
- Prior evidence for `workflow-replace-rabbitmq-with-apache-pulsar` remains out of scope and must stay unchanged.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_port_registry_yaml_repository tests.application.services.platform.test_preflight_service tests.infrastructure.test_composition`
  - Result: passed, 111 tests.
- `git diff --check`
  - Result: passed.
- `python3 tools/quality_gate.py quality`
  - Result: passed.
  - Lint: passed.
  - Import-layer contracts: passed, 3 kept, 0 broken.
  - Architecture tests: passed.
  - Typecheck: passed, 402 source files.
  - Unit tests: passed, 921 tests, 18 skipped.

## Architecture And ADR Status

- Hexagonal boundary preserved: application depends on a repository port and the YAML implementation remains in infrastructure.
- No live infrastructure commands were executed.
- No ADR required for this slice because it implements the approved workflow-local port registry integration without changing the public ingress architecture decision.
