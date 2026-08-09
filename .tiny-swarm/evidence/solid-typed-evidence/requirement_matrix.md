# Requirement Matrix — Issue #191

Source: [Issue #191](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/191)

Execution status: completed locally and independently audited on
2026-08-09. Local quality is the authoritative verification state; live,
browser and external quality-system checks were not run.

| ID | Requirement | Type | Likely implementation area | Verification expectation | Status |
|---|---|---|---|---|---|
| REQ-191-001 | Inventory externally consumed evidence keys and classification values before changing construction. | evidence/functional | node provider, teardown, preflight and deployment evidence paths | before-inventory and consumer map | VERIFIED_LOCAL |
| REQ-191-002 | Introduce typed constants, enums, value objects or builders where they improve evidence stability. | architecture/functional | evidence builder modules | focused builder tests | VERIFIED_LOCAL |
| REQ-191-003 | Keep serialized evidence keys and values backward compatible. | compatibility | evidence construction and serialization | representative dictionary regression tests | VERIFIED_LOCAL |
| REQ-191-004 | Replace scattered broad evidence dictionaries without moving policy into a generic builder. | architecture | lifecycle/profile/resource builders | architecture guard and behavior tests | VERIFIED_LOCAL |
| REQ-191-005 | Create the required Three-Amigos and before/after evidence-key inventory. | evidence/governance | `.tiny-swarm-world/evidence/solid-typed-evidence/` | evidence audit | VERIFIED_LOCAL |
| REQ-191-006 | Use local quality as default authority and classify optional live/external checks. | quality/live-evidence | workflow evidence | `quality` gate plus explicit states | VERIFIED_LOCAL |

## Requirement-to-evidence mapping

| Requirement | Implementation evidence | Verification evidence |
|---|---|---|
| REQ-191-001 | `evidence-key-inventory-before.md` | S191-01 distribution/consolidation; after-inventory |
| REQ-191-002 | `node/evidence.py` (`EvidenceKey`, `EvidenceBuilder`) | builder unit tests; S191-02 consolidation |
| REQ-191-003 | migrated lifecycle/profile/resource/preflight producers | focused compatibility tests; full quality gate; after-inventory |
| REQ-191-004 | policy remains in producers; builder is serialization-only | architecture boundary test; full quality gate |
| REQ-191-005 | Three-Amigos record and before/after inventories | S191-03 audit |
| REQ-191-006 | workflow status and explicit verification-state classification | verification-policy PASS; full quality gate; audit |

Final matrix decision: all requirements are `VERIFIED_LOCAL`; no open row
blocks the #187 handoff.
