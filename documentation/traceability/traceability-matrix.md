# Requirement-to-Architecture-to-Evidence Matrix

Status values follow
[`verification-state-policy.md`](../process/verification-state-policy.md).
The matrix uses `VERIFIED_LOCAL` only for repository evidence and local/static
checks. `LIVE_CONSENT_MISSING` and `EXTERNAL_GATE_UNAVAILABLE` remain open.

| ID | Requirement | Architecture / ADR | Implementation / config | Test / quality | Evidence / next handoff | Status |
|---|---|---|---|---|---|---|
| REQ-124-07 | Linux/WSL-only host boundary | `AGENTS.md`; `documentation/arc42/07_deployment_view.adoc` | `src/tiny_swarm_world/application/services/platform/host/`; `src/tiny_swarm_world/infrastructure/adapters/host/` | `tests/application/services/platform/host/test_detect_host_environment.py`; `tests/architecture/test_host_detection_boundaries.py` | `.tiny-swarm/evidence/issue-121/` | VERIFIED_LOCAL |
| REQ-124-08 | LXC-native, Docker Swarm-first target | `documentation/arc42/09_decisions/adr-lxc-native-node-provider.adoc` | `infra/config/node-providers/`; `src/tiny_swarm_world/infrastructure/composition.py` | `tests/infrastructure/test_composition.py` | `.tiny-swarm/evidence/issue-121/`; `.tiny-swarm/evidence/issue-150/` | VERIFIED_LOCAL |
| REQ-124-09 | Domain/application/infrastructure direction | `AGENTS.md`; `documentation/arc42/05_building_blocks.adoc` | `src/tiny_swarm_world/domain/`; `src/tiny_swarm_world/application/`; `src/tiny_swarm_world/infrastructure/` | `.importlinter`; `tests/architecture/test_hexagonal_imports.py` | `.tiny-swarm/evidence/issue-150/test_results.md` | VERIFIED_LOCAL |
| REQ-124-10 | Canonical audit evidence states and redaction | `documentation/audit/README.md`; `documentation/process/verification-state-policy.md` | `documentation/audit/` | `tests/architecture/test_repository_hygiene.py` | `.tiny-swarm/evidence/issue-121/` | VERIFIED_LOCAL |
| REQ-124-11 | QMS quality/CAPA/change/review controls | `documentation/qms/qms-light.md` | `documentation/qms/quality-objectives.md`; `documentation/qms/capa-process.md`; `documentation/qms/change-control.md`; `documentation/qms/internal-audit-process.md` | documentation path review | `.tiny-swarm/evidence/issue-122/` | VERIFIED_LOCAL |
| REQ-124-12 | ISMS risks, controls, incidents and secrets | `documentation/security/isms-scope.md` | `documentation/security/risk-register.md`; `documentation/security/security-controls.md`; `documentation/security/incident-response.md`; `documentation/security/secret-handling-policy.md` | documentation path review | `.tiny-swarm/evidence/issue-123/` | VERIFIED_LOCAL |
| REQ-124-13 | Branch protection and CI quality policy | `documentation/governance/branch-protection.md` | `documentation/governance/ci-quality-gates.md`; `documentation/governance/pr-review-policy.md`; `QUALITY.md` | `tools/quality_gate.py`; `tools/check_verification_policy_consistency.py` | `.tiny-swarm/evidence/issue-128/` | VERIFIED_LOCAL |
| REQ-124-14 | ASVS/admin-surface model | `documentation/security/owasp-asvs-mapping.md` | `documentation/security/admin-surface-rbac.md`; `documentation/security/service-access-threat-model.md` | documentation path review | `.tiny-swarm/evidence/issue-126/` | VERIFIED_LOCAL |
| REQ-124-15 | Secure Traefik dashboard route | `documentation/arc42/09_decisions/adr-traefik-https-ingress-existing-ca.adoc` | `infra/config/compose/traefik/docker-compose.yml`; `infra/config/compose/traefik/dynamic/tls.yml` | `tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py` | `.tiny-swarm/evidence/issue-150/requirement_matrix.md` | VERIFIED_LOCAL |
| REQ-124-16 | HTTPS, internal dashboard, BasicAuth and Service Access preservation | `documentation/arc42/07_deployment_view.adoc` | `infra/config/compose/traefik/`; `infra/config/compose/service-access/` | `tests/infrastructure/test_composition.py`; `tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py` | `.tiny-swarm/evidence/issue-150/test_results.md` | VERIFIED_LOCAL |
| REQ-124-17 | No insecure mode, raw secrets or extra port | `documentation/security/secret-handling-policy.md`; `documentation/arc42/09_decisions/adr-traefik-https-ingress-existing-ca.adoc` | `infra/config/secrets/infisical-secrets.yaml`; `.env.example` | `tests/application/services/deployment/test_secret_management.py`; `tests/architecture/test_repository_hygiene.py` | `.tiny-swarm/evidence/issue-150/remaining_risks.md` | VERIFIED_LOCAL |
| REQ-124-18 | Every row has source and status | `documentation/process/verification-state-policy.md` | `documentation/traceability/` | path/content review | `.tiny-swarm/evidence/issue-124/` | VERIFIED_LOCAL |
| REQ-124-19 | Local quality gate is authoritative locally | `QUALITY.md`; `documentation/process/verification-state-policy.md` | `tools/quality_gate.py` | full gate recorded in #150 evidence | `.tiny-swarm/evidence/issue-150/test_results.md` | VERIFIED_LOCAL |
| REQ-124-20 | Missing live evidence is not a pass | `documentation/process/verification-state-policy.md` | `documentation/traceability/live-evidence-map.md`; `documentation/evidence/live-greenpath-evidence-contract.md` | state review | #125 contract handoff | VERIFIED_LOCAL |
| REQ-124-21 | Fresh install, reconcile and update green paths | `documentation/workflow/issues/issue-125/workflow.md` | `documentation/evidence/live-greenpath-evidence-contract.md` | no live run authorized | #125 contract; Public-Beta Green-Path | LIVE_CONSENT_MISSING |
| REQ-124-22 | TLS/DNS/browser/admin authentication evidence | `documentation/arc42/09_decisions/adr-traefik-https-ingress-existing-ca.adoc` | `documentation/evidence/live-greenpath-evidence-contract.md` | no live run authorized | #125 contract; Public-Beta Green-Path | LIVE_CONSENT_MISSING |
| REQ-124-23 | External SonarQube/quality result | `documentation/process/verification-state-policy.md` | external system, no repository implementation claim | no external result accessed | #120/release review | EXTERNAL_GATE_UNAVAILABLE |
| REQ-124-24 | Handoff IDs and canonical navigation targets | `documentation/workflow/issues/issue-125/workflow.md`; `documentation/workflow/issues/issue-129/workflow.md` | `documentation/traceability/` | path/link review | #125 for evidence; #129 for navigation | VERIFIED_LOCAL |

## Open-state interpretation

The open rows are current product acceptance gaps, not missing traceability
documentation. They must remain open until explicit live consent, prerequisites,
redacted evidence and a subsequent audit exist.
