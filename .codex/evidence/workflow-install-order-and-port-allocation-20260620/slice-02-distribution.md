# Slice 02 Distribution

Workflow: `installation-phases-port-registry-v1.0.0`
Workflow ID: `workflow-install-order-and-port-allocation-20260620`
Slice: `02`
Title: `Central Port Registry Contract`

## Affected Areas

- backend
- tests
- architecture
- security

## Execution Mode

Sequential integration with parallel read-only subagent review.

## Selected Streams

- backend: domain model and central registry config.
- tests: domain/preflight and network unit tests.
- architecture: hexagonal boundary and parser-independent domain review.
- security: exposure classification, no host-specific addresses, no secrets, no credential URLs.

## Subagents

- Real subagent used: yes.
- Subagents:
  - Senior Tester read-only review.
  - Senior System Architect/security read-only review.
- Fallback role-based review used: no.
- Git worktrees used: no.

## Evidence Path Guard

- Required evidence root: `.codex/evidence/workflow-install-order-and-port-allocation-20260620/`.
- Preflight result: workflow-specific Slice 02 evidence targets were absent before write.
- Generic evidence files are not write targets and must remain unchanged.

## Expected Touched Files

- `infra/config/ports.yaml`
- `src/tiny_swarm_world/domain/network/port_forwarding_plan.py`
- `tests/domain/network/test_port_forwarding_plan.py`
- `tests/domain/preflight/test_preflight_result.py`

`src/tiny_swarm_world/domain/preflight/setup_manifest.py` is in scope but should remain unchanged unless the implementation needs a direct typed link to the registry.

## Conflict Risks

- Domain code must remain parser-independent and must not parse YAML.
- The registry must not replace Traefik `80/443` public ingress with high-numbered gateway ports.
- The registry must reject host-specific addresses, secrets, and credential-bearing URLs.
- Duplicate externally published ports must fail closed unless they are classified as the same ingress-owned shared port by design.

## Quality Gates

- Targeted: `PYTHONPATH=src python3 -m unittest tests.domain.network.test_port_forwarding_plan tests.domain.preflight.test_preflight_result`
- Required by workflow before release: `python3 tools/quality_gate.py quality`

## Consolidation Plan

Implement a parser-independent port registry model in the domain network module, add a committed `infra/config/ports.yaml` desired-state registry, and add unit tests proving duplicate rejection and safety invariants. Use subagent findings to adjust invariants before checkpointing.

## Parallelization Decision

Parallel implementation rejected because Slice 02 has overlapping domain and test locks. Read-only subagent review is safe in parallel with local implementation.
