# Requirement Matrix — Issue #184

Source: [Issue #184](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/184)

Authoring status: extracted before executable slices; implementation evidence
and test evidence remain open until workflow execution.

| ID | Requirement | Type | Likely implementation area | Verification expectation | Status |
|---|---|---|---|---|---|
| REQ-184-001 | Separate command execution/result, node lifecycle, lookup, profile, resource, failure, teardown and evidence responsibilities. | architecture/functional | `clients/lxc/{command,node,profile,resource}/` | responsibility map and architecture tests | OPEN |
| REQ-184-002 | Keep `LxcNodeProvider` as lifecycle orchestration only. | architecture | `lxc_node_provider.py` | static/import or architecture boundary test | OPEN |
| REQ-184-003 | Preserve old imports or provide intentional compatibility shims. | compatibility | old module path and package exports | import compatibility tests | OPEN |
| REQ-184-004 | Preserve verify/ensure/reset/destroy behavior and public evidence classifications. | functional/evidence | node provider, evidence builders | regression tests for all lifecycle outcomes | OPEN |
| REQ-184-005 | Reuse the #189 authoritative backend mapping and do not create a duplicate. | architecture | `lxc/command/backend_cli.py` | duplicate mapping guard | OPEN |
| REQ-184-006 | Create the required Three-Amigos, responsibility and evidence packages. | evidence/governance | `.tiny-swarm-world/evidence/solid-lxc-node-provider/` | evidence audit | OPEN |
| REQ-184-007 | Keep live/browser verification opt-in and state-classified. | live-evidence | workflow evidence | explicit live state and redacted evidence if authorized | OPEN |
