# Requirements Inventory

This inventory is the stable ID source for the current Public-Beta execution
chain. It is intentionally scoped to requirements that affect architecture,
quality, security, evidence or live acceptance after #150.

## ID groups

| Group | Meaning | Primary source |
|---|---|---|
| `REQ-PLATFORM-*` | Linux/WSL, LXC-native, Docker Swarm-first platform boundaries | `AGENTS.md`, arc42 deployment view |
| `REQ-ARCH-*` | Hexagonal and deployment architecture constraints | `AGENTS.md`, arc42 building blocks |
| `REQ-GOV-*` | Audit, QMS, ISMS, branch/CI and ASVS governance | issues #121, #122, #123, #128, #126 |
| `REQ-ADMIN-*` | Secure Traefik admin surface and Service Access preservation | issue #150, Traefik ADR |
| `REQ-LIVE-*` | Live install, reconcile, update, TLS, DNS and browser acceptance | #125 handoff and Green-Path contract |
| `REQ-EVIDENCE-*` | Traceability, redaction, evidence state and external-gate semantics | #121 and verification-state policy |

## Authority rules

1. The issue-local workflow and repository files are the source of expected
   behavior.
2. The implementation, tests and committed evidence are the source of local
   verification claims.
3. Live or external success requires its own executed evidence and must not be
   inferred from configuration, skipped tests or a URL.
4. Missing or blocked evidence remains visible and is handed to #125, the
   Green-Path gate or #120 as applicable.

The detailed mapping is in
[`traceability-matrix.md`](traceability-matrix.md).
