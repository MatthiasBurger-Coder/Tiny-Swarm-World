# Slice 01 Scope Amendment

Date: `2026-07-12`

Decision: `APPROVED_IN_SCOPE`

Added allowed file:

- `documentation/arc42/09_decisions/adr-autonomous-setup-safety.adoc`

Reason: the independently approved System Architect decision requires the new
dedicated WSL2 host-platform ADR to narrow the existing setup-safety evidence
rule. The original slice already declared that amendment as an architecture
constraint but omitted the existing ADR file from the machine-readable allowed
path list.

The change is documentation/architecture governance only, introduces no new
FR, does not broaden product implementation, and is required to avoid
contradictory active ADRs. S3D metadata and lock checks must be rerun before the
file is edited.

## Pre-implementation legacy-consumer amendment

Decision: `APPROVED_IN_SCOPE`

Added allowed files:

- `src/tiny_swarm_world/domain/preflight/__init__.py`
- `src/tiny_swarm_world/application/ports/preflight/port_host_preflight_probe.py`
- `src/tiny_swarm_world/application/ports/network/port_network_probe.py`
- `src/tiny_swarm_world/application/services/platform/preflight_service.py`
- `src/tiny_swarm_world/application/services/network/host_integration.py`
- `tests/application/services/platform/test_preflight_service.py`
- `tests/application/services/network/test_host_integration.py`

Reason: the independent Architecture and Tester gates require every legacy
consumer to use the typed detector and fail closed for WSL1, sandbox, and
ambiguous signals. Without these exact port/service paths, preflight or network
diagnostics could still downgrade an unsupported report to native Linux. This
is FR-1 contract consolidation, not FR-7 network preparation. No network or
infrastructure mutation is authorized.

## CI bootstrap-import remediation amendment

Decision: `APPROVED_IN_SCOPE`

Added allowed files:

- `src/tiny_swarm_world/domain/preflight/sanitized_evidence.py`
- `src/tiny_swarm_world/domain/host_environment.py`
- `src/tiny_swarm_world/domain/sanitized_evidence.py`
- `tests/test_install_script.py`

Reason: PR #220 check run `29200070600` proved that the installer must import
before third-party dependency bootstrap. Locating the host model under the
eager `domain.preflight` package loaded `pydantic` before bootstrap, and the
minimal install-script fixture did not copy the new import closure. The fix
moves only the standard-library host model/redaction guard to side-effect-free
domain modules, retains the preflight re-export, and makes the fixture copy the
exact bootstrap import closure. This is an FR-1 compatibility correction, not
a new functional requirement.

Revalidated scope:
`S3D_CI_REMEDIATION_SCOPE=PASS affected_files=50 locks=4/2/2`.
