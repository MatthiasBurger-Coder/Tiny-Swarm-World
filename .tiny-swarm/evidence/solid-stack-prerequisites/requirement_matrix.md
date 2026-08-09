# Requirement Matrix — Issue #190

Source: [Issue #190](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/190)

Authoring status: extracted before executable slices; current registry and
asset-transfer modules are baseline evidence, not completion evidence.

| ID | Requirement | Type | Likely implementation area | Verification expectation | Status |
|---|---|---|---|---|---|
| REQ-190-001 | Preserve Traefik, SonarQube and Swagger prerequisite/asset behavior. | functional/compatibility | `clients/lxc/swarm/` and runtime facade | handler and regression tests | OPEN |
| REQ-190-002 | Use strategy/registry dispatch for stack prerequisites and asset transfer. | architecture/functional | `stack_prerequisite_registry.py`, `stack_asset_transfer.py` | registry behavior and static generic-runtime guard | OPEN |
| REQ-190-003 | Provide a safe default/no-op path for stacks without special prerequisites where needed. | resilience | stack strategy registry | unknown/default stack tests | OPEN |
| REQ-190-004 | Keep generic runtime public behavior and command generation stable. | compatibility | `swarm_stack_runtime.py`, `lxc_swarm_runtime.py` | deployment command and transfer regression tests | OPEN |
| REQ-190-005 | Create the required Three-Amigos and before/after special-case evidence. | evidence/governance | `.tiny-swarm-world/evidence/solid-stack-prerequisites/` | evidence audit | OPEN |
| REQ-190-006 | Reconcile #238's existing partial extraction before adding code. | scope/quality | baseline inventory | residual-scope decision | OPEN |
