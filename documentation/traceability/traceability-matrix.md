# Requirement-to-Architecture-to-Evidence Matrix

Status values follow
[`verification-state-policy.md`](../process/verification-state-policy.md).
The matrix uses `VERIFIED_LOCAL` only for repository evidence and local/static
checks. `LIVE_CONSENT_MISSING` and `EXTERNAL_GATE_UNAVAILABLE` remain open.

| ID | Requirement | Architecture / ADR | Implementation / config | Test / quality | Evidence / next handoff | Status |
|---|---|---|---|---|---|---|
| REQ-PLATFORM-01 | Linux/WSL-only host boundary | `AGENTS.md`; `07_deployment_view.adoc` | host detection/preflight adapters | preflight test suite; quality gate | #121 evidence; Green-Path | VERIFIED_LOCAL |
| REQ-PLATFORM-02 | LXC-native, Docker Swarm-first target | `adr-lxc-native-node-provider.adoc` | `infra/config/node-providers/`; composition | platform tests; quality gate | #121/#150 evidence | VERIFIED_LOCAL |
| REQ-ARCH-01 | Domain/application/infrastructure direction | `AGENTS.md`; `05_building_blocks.adoc` | `src/tiny_swarm_world/{domain,application,infrastructure}` | import-linter; architecture tests | full gate result | VERIFIED_LOCAL |
| REQ-GOV-01 | Canonical audit evidence states and redaction | #121 audit docs | `documentation/audit/` | path/content review | `.tiny-swarm/evidence/issue-121/` | VERIFIED_LOCAL |
| REQ-GOV-02 | QMS quality/CAPA/change/review controls | #122 QMS docs | `documentation/qms/` | path/content review | `.tiny-swarm/evidence/issue-122/` | VERIFIED_LOCAL |
| REQ-GOV-03 | ISMS risks, controls, incidents and secrets | #123 security docs | `documentation/security/` | path/content review | `.tiny-swarm/evidence/issue-123/` | VERIFIED_LOCAL |
| REQ-GOV-04 | Branch protection and CI quality policy | #128 governance docs | `documentation/governance/` and `QUALITY.md` | quality-gate and policy checks | `.tiny-swarm/evidence/issue-128/` | VERIFIED_LOCAL |
| REQ-GOV-05 | ASVS/admin-surface model | #126 security docs | `documentation/security/owasp-asvs-mapping.md`, RBAC and threat model | path/content review | `.tiny-swarm/evidence/issue-126/` | VERIFIED_LOCAL |
| REQ-ADMIN-01 | Secure Traefik dashboard route | Traefik HTTPS ADR | `infra/config/compose/traefik/dynamic/tls.yml` | compose repository tests | #150 matrix/evidence | VERIFIED_LOCAL |
| REQ-ADMIN-02 | HTTPS, internal dashboard and BasicAuth | Traefik HTTPS ADR; ASVS docs | `api@internal`, `websecure`, users file | compose/config targeted tests | #150 test results | VERIFIED_LOCAL |
| REQ-ADMIN-03 | No insecure mode, raw secrets or extra port | #123/#126 policies; ADR | external secret-name contract only | forbidden-config tests; hygiene | #150 risk/evidence | VERIFIED_LOCAL |
| REQ-ADMIN-04 | Preserve Service Access | `07_deployment_view.adoc` | service-access stack and route contracts | composition/routing regression tests | #150 evidence | VERIFIED_LOCAL |
| REQ-EVIDENCE-01 | Every row has source and status | #121 evidence contract | this directory | path/content review | issue #124 package | VERIFIED_LOCAL |
| REQ-EVIDENCE-02 | Local quality gate is authoritative locally | `QUALITY.md`; policy | `tools/quality_gate.py` | full WSL gate | #150 test results | VERIFIED_LOCAL |
| REQ-EVIDENCE-03 | Missing live evidence is not a pass | verification policy | live map and handoffs | state review | #125 handoff | VERIFIED_LOCAL |
| REQ-LIVE-01 | Fresh install green path | #125 / Green-Path scope | no live implementation claim | not run without consent | #125 and Green-Path | LIVE_CONSENT_MISSING |
| REQ-LIVE-02 | Reconcile/re-run green path | #125 / Green-Path scope | no live implementation claim | not run without consent | #125 and Green-Path | LIVE_CONSENT_MISSING |
| REQ-LIVE-03 | Existing-install update green path | #125 / Green-Path scope | no live implementation claim | not run without consent | #125 and Green-Path | LIVE_CONSENT_MISSING |
| REQ-LIVE-04 | TLS/DNS/browser/admin authentication | #150 live handoff | no live implementation claim | not run without consent | #125 and Green-Path | LIVE_CONSENT_MISSING |
| REQ-LIVE-05 | External SonarQube/quality result | verification policy | no result accessed | external result unavailable | release/#120 review | EXTERNAL_GATE_UNAVAILABLE |

## Open-state interpretation

The open rows are current product acceptance gaps, not missing traceability
documentation. They must remain open until explicit live consent, prerequisites,
redacted evidence and a subsequent audit exist.
