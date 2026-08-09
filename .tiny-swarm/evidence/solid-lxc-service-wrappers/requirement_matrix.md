# Requirement Matrix — Issue #192

Source: [Issue #192](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/192)

Authoring status: extracted before executable slices; #238 already provides
candidate service modules that require compatibility and residual-scope audit.

| ID | Requirement | Type | Likely implementation area | Verification expectation | Status |
|---|---|---|---|---|---|
| REQ-192-001 | Keep Portainer admin, Portainer deployment and Nexus client behavior stable. | functional/compatibility | `clients/lxc/services/` and facade | focused client tests | OPEN |
| REQ-192-002 | Keep manager IP resolution and local URL construction in a small reusable LXC service boundary. | architecture/functional | service resolver/value object | URL and failure-path tests | OPEN |
| REQ-192-003 | Preserve explicit `api_url` precedence, session reuse and cookie-clearing semantics where applicable. | functional | Portainer client wrappers | contract regression tests | OPEN |
| REQ-192-004 | Keep old imports compatible while updating composition imports. | compatibility | `lxc_swarm_runtime.py`, `composition.py` | import and wiring tests | OPEN |
| REQ-192-005 | Do not log credentials or raw sensitive HTTP data. | security | clients, diagnostics and evidence | redaction tests/static checks | OPEN |
| REQ-192-006 | Create the required Three-Amigos and responsibility-map evidence. | evidence/governance | `.tiny-swarm-world/evidence/solid-lxc-service-wrappers/` | evidence audit | OPEN |
| REQ-192-007 | Keep live/browser verification optional and state-classified. | live-evidence | workflow evidence | explicit applicability/result state | OPEN |
