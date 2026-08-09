# Requirement Matrix — Issue #187

Source: [Issue #187](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/187)

Authoring status: extracted before executable slices; implementation evidence
and test evidence remain open until workflow execution.

| ID | Requirement | Type | Likely implementation area | Verification expectation | Status |
|---|---|---|---|---|---|
| REQ-187-001 | Preserve all current service names and port/fingerprint matching behavior. | functional/compatibility | `preflight/host_preflight_probe.py` and probe modules | old service matrix and unsupported-name tests | OPEN |
| REQ-187-002 | Introduce a service probe protocol and registry. | architecture/functional | `preflight/service_probes/` or verified equivalent | registry dispatch tests | OPEN |
| REQ-187-003 | Extract the named service probes without expanding into unrelated host detection. | architecture/scope | preflight probe modules | responsibility map and scope guard | OPEN |
| REQ-187-004 | Keep the public `port_matches_expected_service` signature unchanged. | compatibility | `HostPreflightProbe` | contract test | OPEN |
| REQ-187-005 | Preserve unsupported-service behavior and safe probe failures. | resilience | registry and probe implementations | deterministic failure tests | OPEN |
| REQ-187-006 | Create the required Three-Amigos and before/after responsibility evidence. | evidence/governance | `.tiny-swarm-world/evidence/solid-host-preflight-probe/` | evidence audit | OPEN |
| REQ-187-007 | Keep live/browser and external verification optional and state-classified. | live-evidence | workflow evidence | explicit applicability/result state | OPEN |
