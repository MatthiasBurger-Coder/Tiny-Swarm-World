# Slice 03 Distribution Evidence

Workflow-ID: workflow-install-order-and-port-allocation-20260620
Slice-ID: 03
Purpose: Port registry repository and preflight integration.

## Evidence Path Guard

- Target evidence root: `.codex/evidence/workflow-install-order-and-port-allocation-20260620/`
- Generic evidence paths under `.codex/evidence/slice-*` are reserved for prior workflows and must not be modified.
- No evidence for this slice is written directly below `.codex/evidence/`.

## Stream Assignment

- Main executor: repository adapter, application preflight integration, composition wiring, tests, and consolidation.
- Specialist review inputs already recorded from Slice 02 remain applicable:
  - Senior System Architect: preserve Traefik public ingress semantics and keep diagnostic allocations out of public ingress.
  - Senior Tester: cover registry loading, malformed YAML, duplicate external ports, unsafe metadata, and preflight port selection.

## Initial Scope

- Add an application repository port for loading the committed port registry.
- Add a YAML-backed infrastructure adapter for `infra/config/ports.yaml`.
- Allow preflight checks to derive required host ports from the registry.
- Keep live infrastructure commands out of scope.
