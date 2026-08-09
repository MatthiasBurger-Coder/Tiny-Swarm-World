# Requirement Matrix — Issue #192

Source: [Issue #192](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/192)

Execution status: completed locally and independently audited on
2026-08-09. Local quality is the authoritative verification state; live,
browser and external quality-system checks were not run.

| ID | Requirement | Type | Likely implementation area | Verification expectation | Status |
|---|---|---|---|---|---|
| REQ-192-001 | Keep Portainer admin, Portainer deployment and Nexus client behavior stable. | functional/compatibility | `clients/lxc/services/` and facade | focused client tests | VERIFIED_LOCAL |
| REQ-192-002 | Keep manager IP resolution and local URL construction in a small reusable LXC service boundary. | architecture/functional | service resolver/value object | URL and failure-path tests | VERIFIED_LOCAL |
| REQ-192-003 | Preserve explicit `api_url` precedence, session reuse and cookie-clearing semantics where applicable. | functional | Portainer client wrappers | contract regression tests | VERIFIED_LOCAL |
| REQ-192-004 | Keep old imports compatible while updating composition imports. | compatibility | `lxc_swarm_runtime.py`, `composition.py` | import and wiring tests | VERIFIED_LOCAL |
| REQ-192-005 | Do not log credentials or raw sensitive HTTP data. | security | clients, diagnostics and evidence | redaction tests/static checks | VERIFIED_LOCAL |
| REQ-192-006 | Create the required Three-Amigos and responsibility-map evidence. | evidence/governance | `.tiny-swarm-world/evidence/solid-lxc-service-wrappers/` | evidence audit | VERIFIED_LOCAL |
| REQ-192-007 | Keep live/browser verification optional and state-classified. | live-evidence | workflow evidence | explicit applicability/result state | VERIFIED_LOCAL |

## Requirement-to-evidence mapping

| Requirement | Implementation evidence | Verification evidence |
|---|---|---|
| REQ-192-001 | #238 concrete Portainer/Nexus service modules and compatibility facades | service/facade regression tests; full gate |
| REQ-192-002 | services/common.py URL and manager-IP boundary | common URL/retry/failure tests |
| REQ-192-003 | Portainer api_url precedence, injected sessions and admin cookie flow | focused service tests and existing admin regression tests |
| REQ-192-004 | legacy facade exports plus composition concrete imports | architecture and composition tests |
| REQ-192-005 | delegated clients reject credential-bearing URLs and redact errors | security-focused tests; full gate |
| REQ-192-006 | Three-Amigos and before/after responsibility maps | S192-03 audit |
| REQ-192-007 | explicit local/non-live verification classification | verification-policy PASS; audit |

Final matrix decision: all requirements are VERIFIED_LOCAL; no open row blocks
the #186 handoff.
