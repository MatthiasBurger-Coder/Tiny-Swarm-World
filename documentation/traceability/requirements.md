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

## Stable IDs

| ID | Requirement |
|---|---|
| REQ-124-01 | Create the stable requirement inventory. |
| REQ-124-02 | Map each requirement to architecture. |
| REQ-124-03 | Map each requirement to implementation/configuration. |
| REQ-124-04 | Map each requirement to tests/checks. |
| REQ-124-05 | Map each requirement to quality gates. |
| REQ-124-06 | Map live requirements without fabricating success. |
| REQ-124-07 | Include the Linux/WSL-only operating boundary. |
| REQ-124-08 | Include the Docker Swarm-first/LXC-native architecture. |
| REQ-124-09 | Include hexagonal dependency boundaries. |
| REQ-124-10 | Include audit evidence governance. |
| REQ-124-11 | Include QMS controls. |
| REQ-124-12 | Include ISMS, threat and secret controls. |
| REQ-124-13 | Include branch and CI governance. |
| REQ-124-14 | Include ASVS/admin-surface controls. |
| REQ-124-15 | Include secure Traefik dashboard behavior. |
| REQ-124-16 | Include Service Access preservation. |
| REQ-124-17 | Include secret redaction and value-free evidence. |
| REQ-124-18 | Include fresh-install, reconcile/re-run and update live scenarios. |
| REQ-124-19 | Include live TLS/DNS/browser evidence. |
| REQ-124-20 | Include external quality-gate state. |
| REQ-124-21 | Keep missing, blocked and refused states visible. |
| REQ-124-22 | Provide handoff IDs and canonical navigation targets. |
| REQ-124-23 | Include external quality-gate state. |
| REQ-124-24 | Keep evidence and navigation handoffs separate and explicit. |

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
