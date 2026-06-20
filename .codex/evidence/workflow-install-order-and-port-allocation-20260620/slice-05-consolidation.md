# Slice 05 Consolidation Evidence

Workflow-ID: workflow-install-order-and-port-allocation-20260620
Slice-ID: 05
Purpose: Service registry and stack alignment.

## Implemented Changes

- Expanded `infra/config/services.yml` from Infisical-only config into a service registry for selected stacks plus Traefik ingress.
- Added `phase_id` and `port_ids` metadata to `ServiceStackContract`.
- Mapped selected stack contracts to installation phases and port registry IDs.
- Preserved Portainer bootstrap-cycle protection by keeping Portainer out of Portainer-managed deployment steps.
- Added `portainer-http` as a compatibility port registry entry.
- Kept current Pulsar baseline explicit and RabbitMQ absent.
- Classified current legacy Compose published ports as `compatibility_published_ports`; Traefik-owned ingress ports remain `ingress_published_ports`.
- Added regression tests for service registry alignment, phase mapping, port mapping, published-port classification, and readiness target separation.

## Subagent Review

- Read-only Slice 05 reviewer reported that config-only edits would be insufficient and that compose/port registry mismatches must not be silently treated as registry-backed.
- Applied recommendation by explicitly classifying legacy published ports as compatibility in `services.yml`.
- Did not perform broad Compose published-port rewrites; that would be a deployment migration slice with higher runtime risk.

## Evidence Path Guard

- Evidence written only below `.codex/evidence/workflow-install-order-and-port-allocation-20260620/`.
- Generic `.codex/evidence/slice-*` files were not used for this slice.
- Prior evidence for `workflow-replace-rabbitmq-with-apache-pulsar` remains out of scope and unchanged.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.domain.deployment.test_service_stack_contract tests.application.services.deployment.test_service_stack_plan tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml tests.infrastructure.adapters.repositories.test_port_registry_yaml_repository`
  - Result: passed, 62 tests.
- YAML static parse check for `infra/config/services.yml`, `infra/config/ports.yaml`, and `infra/config/inventory/desired_inventory.yaml`
  - Result: passed.
- `git diff --check`
  - Result: passed.
- `python3 tools/quality_gate.py quality`
  - Result: passed.
  - Lint: passed.
  - Import-layer contracts: passed, 3 kept, 0 broken.
  - Architecture tests: passed.
  - Typecheck: passed, 403 source files.
  - Unit tests: passed, 934 tests, 18 skipped.

## Architecture And ADR Status

- Deployment domain contracts now carry static registry metadata only.
- Static service registry data still does not claim observed runtime readiness.
- Compose published port migration is explicitly deferred through compatibility classification.
- No live infrastructure commands were executed.
- No ADR required because this slice preserves the documented Traefik ingress baseline and does not change runtime exposure behavior.
