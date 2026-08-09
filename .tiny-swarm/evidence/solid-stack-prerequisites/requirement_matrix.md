# Requirement Matrix — Issue #190

Source: [Issue #190](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/190)

Execution status: completed locally and independently audited on
2026-08-09. Local quality is the authoritative verification state; live,
browser and external quality-system checks were not run.

| ID | Requirement | Type | Likely implementation area | Verification expectation | Status |
|---|---|---|---|---|---|
| REQ-190-001 | Preserve Traefik, SonarQube and Swagger prerequisite/asset behavior. | functional/compatibility | `clients/lxc/swarm/` and runtime facade | handler and regression tests | VERIFIED_LOCAL |
| REQ-190-002 | Use strategy/registry dispatch for stack prerequisites and asset transfer. | architecture/functional | `stack_prerequisite_registry.py`, `stack_asset_transfer.py` | registry behavior and static generic-runtime guard | VERIFIED_LOCAL |
| REQ-190-003 | Provide a safe default/no-op path for stacks without special prerequisites where needed. | resilience | stack strategy registry | unknown/default stack tests | VERIFIED_LOCAL |
| REQ-190-004 | Keep generic runtime public behavior and command generation stable. | compatibility | `swarm_stack_runtime.py`, `lxc_swarm_runtime.py` | deployment command and transfer regression tests | VERIFIED_LOCAL |
| REQ-190-005 | Create the required Three-Amigos and before/after special-case evidence. | evidence/governance | `.tiny-swarm-world/evidence/solid-stack-prerequisites/` | evidence audit | VERIFIED_LOCAL |
| REQ-190-006 | Reconcile #238's existing partial extraction before adding code. | scope/quality | baseline inventory | residual-scope decision | VERIFIED_LOCAL |

## Requirement-to-evidence mapping

| Requirement | Implementation evidence | Verification evidence |
|---|---|---|
| REQ-190-001 | prerequisite and asset strategies preserve existing paths/commands | stack and runtime regression tests; full gate |
| REQ-190-002 | explicit prerequisite matching and StackAssetTransferRegistry | registry tests; generic-runtime architecture guard |
| REQ-190-003 | registry returns without side effects for unknown stacks | unknown-stack asset test |
| REQ-190-004 | unchanged LxcSwarmStackRuntime orchestration and deploy command | runtime regression tests; full gate |
| REQ-190-005 | Three-Amigos record and before/after inventory | S190-03 audit |
| REQ-190-006 | #238 residual inventory and bounded decision | S190-01 consolidation |

Final matrix decision: all requirements are VERIFIED_LOCAL; no open row blocks
the #192 handoff.
