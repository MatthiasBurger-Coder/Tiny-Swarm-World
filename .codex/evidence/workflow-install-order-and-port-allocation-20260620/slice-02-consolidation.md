# Slice 02 Consolidation

Workflow: `installation-phases-port-registry-v1.0.0`
Workflow ID: `workflow-install-order-and-port-allocation-20260620`
Slice: `02`
Title: `Central Port Registry Contract`

## Stream Results

Backend stream:

- Added parser-independent port registry domain concepts in `tiny_swarm_world.domain.network`.
- Added central desired-state registry at `infra/config/ports.yaml`.
- Kept YAML loading out of domain code; YAML repository work remains deferred to Slice 03.

Tests stream:

- Senior Tester subagent provided focused test recommendations for registry construction, duplicate ports, invalid ranges, invalid service IDs, unsafe metadata, and internal/external semantics.
- Added focused unit tests in `tests/domain/network/test_port_forwarding_plan.py`.
- No setup manifest bridge was added in Slice 02, so preflight manifest tests remain unchanged.

Architecture/security stream:

- Senior System Architect/security subagent gave conditional GO.
- No ADR is required because the registry preserves Traefik `80/443` as the only public ingress baseline.
- High-numbered ports are classified as diagnostic/direct/compatibility allocations, not public ingress replacement.

## Accepted Findings

- `PortRegistry`, `PortRange`, `ServicePortMapping`, and `PortExposureClass` are the Slice 02 domain shape.
- Public ingress mappings must be Traefik-owned ports `80` and `443`.
- Duplicate external ports are rejected.
- Unsafe metadata keys/values for addresses, secrets, tokens, and credential-bearing URLs are rejected.
- Internal container ports remain independent from external host/diagnostic mappings.

## Rejected Findings

- YAML repository tests were rejected for Slice 02 and deferred to Slice 03.
- Setup manifest derivation from the registry was rejected for Slice 02 because the workflow assigns repository/preflight integration to Slice 03.

## Files Changed

- `infra/config/ports.yaml`
- `src/tiny_swarm_world/domain/network/port_forwarding_plan.py`
- `src/tiny_swarm_world/domain/network/__init__.py`
- `tests/domain/network/test_port_forwarding_plan.py`
- `.codex/evidence/workflow-install-order-and-port-allocation-20260620/slice-02-distribution.md`
- `.codex/evidence/workflow-install-order-and-port-allocation-20260620/slice-02-consolidation.md`

## Evidence Path Guard

- Workflow-specific evidence targets were absent before write.
- Generic evidence files were not overwritten, modified, truncated, renamed, or deleted.

## Conflicts

- Conflicts found: none.
- Conflicts resolved: none.

## Tests Executed

- `PYTHONPATH=src python3 -m unittest tests.domain.network.test_port_forwarding_plan tests.domain.preflight.test_preflight_result`: passed, 30 tests.
- Parsed `infra/config/ports.yaml` with `ruamel.yaml` and constructed `PortRegistry`: passed, 11 ranges and 21 mappings.
- `python3 tools/quality_gate.py quality`: passed. The gate ran lint, arch-lint, arch-tests, typecheck, and unit test discovery; 913 tests passed with 18 skipped.

## SonarQube

- Not applicable locally.

## Documentation Updates

- No arc42 update required in Slice 02 because the accepted Traefik ingress baseline is unchanged.
- ADR update status: checked, no update needed.

## Final Integration Decision

Accepted. Slice 02 implements the central port registry contract without YAML parsing in domain code.
