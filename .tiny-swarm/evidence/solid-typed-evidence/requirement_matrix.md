# Requirement Matrix — Issue #191

Source: [Issue #191](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/191)

Authoring status: extracted before executable slices; implementation evidence
and test evidence remain open until workflow execution.

| ID | Requirement | Type | Likely implementation area | Verification expectation | Status |
|---|---|---|---|---|---|
| REQ-191-001 | Inventory externally consumed evidence keys and classification values before changing construction. | evidence/functional | node provider, teardown, preflight and deployment evidence paths | before-inventory and consumer map | OPEN |
| REQ-191-002 | Introduce typed constants, enums, value objects or builders where they improve evidence stability. | architecture/functional | evidence builder modules | focused builder tests | OPEN |
| REQ-191-003 | Keep serialized evidence keys and values backward compatible. | compatibility | evidence construction and serialization | representative dictionary regression tests | OPEN |
| REQ-191-004 | Replace scattered broad evidence dictionaries without moving policy into a generic builder. | architecture | lifecycle/profile/resource builders | architecture guard and behavior tests | OPEN |
| REQ-191-005 | Create the required Three-Amigos and before/after evidence-key inventory. | evidence/governance | `.tiny-swarm-world/evidence/solid-typed-evidence/` | evidence audit | OPEN |
| REQ-191-006 | Use local quality as default authority and classify optional live/external checks. | quality/live-evidence | workflow evidence | `quality` gate plus explicit states | OPEN |
