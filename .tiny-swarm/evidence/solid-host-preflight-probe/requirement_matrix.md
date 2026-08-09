# Requirement Matrix — Issue #187

Source: [Issue #187](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/187)

Execution status: completed locally and independently audited on
2026-08-09. Local quality is the authoritative verification state; live,
browser and external quality-system checks were not run.

| ID | Requirement | Type | Likely implementation area | Verification expectation | Status |
|---|---|---|---|---|---|
| REQ-187-001 | Preserve all current service names and port/fingerprint matching behavior. | functional/compatibility | `preflight/host_preflight_probe.py` and probe modules | old service matrix and unsupported-name tests | VERIFIED_LOCAL |
| REQ-187-002 | Introduce a service probe protocol and registry. | architecture/functional | `preflight/service_probes/` or verified equivalent | registry dispatch tests | VERIFIED_LOCAL |
| REQ-187-003 | Extract the named service probes without expanding into unrelated host detection. | architecture/scope | preflight probe modules | responsibility map and scope guard | VERIFIED_LOCAL |
| REQ-187-004 | Keep the public `port_matches_expected_service` signature unchanged. | compatibility | `HostPreflightProbe` | contract test | VERIFIED_LOCAL |
| REQ-187-005 | Preserve unsupported-service behavior and safe probe failures. | resilience | registry and probe implementations | deterministic failure tests | VERIFIED_LOCAL |
| REQ-187-006 | Create the required Three-Amigos and before/after responsibility evidence. | evidence/governance | `.tiny-swarm-world/evidence/solid-host-preflight-probe/` | evidence audit | VERIFIED_LOCAL |
| REQ-187-007 | Keep live/browser and external verification optional and state-classified. | live-evidence | workflow evidence | explicit applicability/result state | VERIFIED_LOCAL |

## Requirement-to-evidence mapping

| Requirement | Implementation evidence | Verification evidence |
|---|---|---|
| REQ-187-001 | ordered default service registry and HostPreflightProbe delegation | existing service matrix tests; S187-01/S187-02 consolidation; full gate |
| REQ-187-002 | ServiceProbe protocol, strategy classes and ServiceProbeRegistry | focused registry tests; architecture guard |
| REQ-187-003 | responsibility-map-before/after and unchanged host helpers | scope review; full gate |
| REQ-187-004 | unchanged public method signature | HostPreflightProbe regression tests |
| REQ-187-005 | registry fail-closed dispatch and existing safe I/O helpers | unsupported/failure tests; full gate |
| REQ-187-006 | Three-Amigos record and responsibility maps | S187-03 audit |
| REQ-187-007 | workflow and evidence state classification | verification-policy PASS; audit |

Final matrix decision: all requirements are VERIFIED_LOCAL; no open row blocks
the #190 handoff.
