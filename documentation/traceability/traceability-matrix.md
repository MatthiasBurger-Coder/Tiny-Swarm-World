# Requirement-to-Architecture-to-Evidence Matrix

Status values follow
[`verification-state-policy.md`](../process/verification-state-policy.md).
The source mapping below retains the #124 requirement IDs. `VERIFIED_LOCAL`
means only the listed repository artifact or static contract, not a test result
for the current revision. Referenced old issue-local evidence packages may be
unavailable in a fresh checkout; their absence is not replaced by invented proof.
For executed results use the dated qualification sources below and the current
[test/check ownership map](test-coverage-map.md).

| ID | Requirement | Architecture / ADR | Implementation / config | Test / quality | Evidence / next handoff | Status |
|---|---|---|---|---|---|---|
| REQ-124-07 | Linux/WSL-only host boundary | `AGENTS.md`; `documentation/arc42/07_deployment_view.adoc` | `src/tiny_swarm_world/application/services/platform/host/`; `src/tiny_swarm_world/infrastructure/adapters/host/` | `tests/application/services/platform/host/test_detect_host_environment.py`; `tests/architecture/test_host_detection_boundaries.py` | Historical issue-121 package unavailable; current source mapped above | VERIFIED_LOCAL |
| REQ-124-08 | LXC-native, Docker Swarm-first target | `documentation/arc42/09_decisions/adr-lxc-native-node-provider.adoc` | `infra/config/node-providers/`; `src/tiny_swarm_world/infrastructure/composition.py` | `tests/infrastructure/test_composition.py` | Historical issue-121 package unavailable; current source mapped above; `documentation/arc42/07_deployment_view.adoc` | VERIFIED_LOCAL |
| REQ-124-09 | Domain/application/infrastructure direction | `AGENTS.md`; `documentation/arc42/05_building_blocks.adoc` | `src/tiny_swarm_world/domain/`; `src/tiny_swarm_world/application/`; `src/tiny_swarm_world/infrastructure/` | `.importlinter`; `tests/architecture/test_hexagonal_imports.py` | `documentation/release/rc1-candidate-evidence.md` (dated candidate only) | VERIFIED_LOCAL |
| REQ-124-10 | Canonical audit evidence states and redaction | `documentation/audit/README.md`; `documentation/process/verification-state-policy.md` | `documentation/audit/` | `tests/architecture/test_repository_hygiene.py` | Historical issue-121 package unavailable; current source mapped above | VERIFIED_LOCAL |
| REQ-124-11 | QMS quality/CAPA/change/review controls | `documentation/qms/qms-light.md` | `documentation/qms/quality-objectives.md`; `documentation/qms/capa-process.md`; `documentation/qms/change-control.md`; `documentation/qms/internal-audit-process.md` | documentation path review | Historical issue-122 package unavailable; current source mapped above | VERIFIED_LOCAL |
| REQ-124-12 | ISMS risks, controls, incidents and secrets | `documentation/security/isms-scope.md` | `documentation/security/risk-register.md`; `documentation/security/security-controls.md`; `documentation/security/incident-response.md`; `documentation/security/secret-handling-policy.md` | documentation path review | Historical issue-123 package unavailable; current source mapped above | VERIFIED_LOCAL |
| REQ-124-13 | Branch protection and CI quality policy | `documentation/governance/branch-protection.md` | `documentation/governance/ci-quality-gates.md`; `documentation/governance/pr-review-policy.md`; `QUALITY.md` | `tools/quality_gate.py`; `tools/check_verification_policy_consistency.py` | Historical issue-128 package unavailable; current source mapped above | VERIFIED_LOCAL |
| REQ-124-14 | ASVS/admin-surface model | `documentation/security/owasp-asvs-mapping.md` | `documentation/security/admin-surface-rbac.md`; `documentation/security/service-access-threat-model.md` | documentation path review | Historical issue-126 package unavailable; current source mapped above | VERIFIED_LOCAL |
| REQ-124-15 | Secure Traefik dashboard route | `documentation/arc42/09_decisions/adr-traefik-managed-or-operator-ca.adoc` | `infra/config/compose/traefik/docker-compose.yml`; `infra/config/compose/traefik/dynamic/tls.yml` | `tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py` | `documentation/arc42/07_deployment_view.adoc` (repository contract) | VERIFIED_LOCAL |
| REQ-124-16 | HTTPS, internal dashboard, BasicAuth and Service Access preservation | `documentation/arc42/07_deployment_view.adoc` | `infra/config/compose/traefik/`; `infra/config/compose/service-access/` | `tests/infrastructure/test_composition.py`; `tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py` | `documentation/release/rc1-candidate-evidence.md` (dated candidate only) | VERIFIED_LOCAL |
| REQ-124-17 | No insecure mode, raw secrets or extra port | `documentation/security/secret-handling-policy.md`; `documentation/arc42/09_decisions/adr-traefik-managed-or-operator-ca.adoc` | `infra/config/secrets/infisical-secrets.yaml`; `.env.example` | `tests/application/services/deployment/test_secret_management.py`; `tests/architecture/test_repository_hygiene.py` | `documentation/security/rc1-classic-security-evidence.md` (scoped residuals) | VERIFIED_LOCAL |
| REQ-124-18 | Every row has source and status | `documentation/process/verification-state-policy.md` | `documentation/traceability/` | path/content review | Historical issue-124 package unavailable; current source mapped above | VERIFIED_LOCAL |
| REQ-124-19 | Local quality gate is authoritative locally | `QUALITY.md`; `documentation/process/verification-state-policy.md` | `tools/quality_gate.py` | candidate-matched full gate required | `documentation/release/rc1-candidate-evidence.md` (dated candidate only) | VERIFIED_LOCAL |
| REQ-124-20 | Missing live evidence is not a pass | `documentation/process/verification-state-policy.md` | `documentation/traceability/live-evidence-map.md`; `documentation/evidence/live-greenpath-evidence-contract.md` | state review | #125 contract handoff | VERIFIED_LOCAL |
| REQ-124-21 | Fresh install, reconcile and update green paths | `documentation/evidence/live-greenpath-evidence-contract.md` | `documentation/evidence/live-greenpath-evidence-contract.md` | historical candidates documented; new run requires consent | #125 contract; dated #363 validation | Candidate-scoped historical evidence; new run requires consent |
| REQ-124-22 | TLS/DNS/browser/admin authentication evidence | `documentation/arc42/09_decisions/adr-traefik-managed-or-operator-ca.adoc` | `documentation/evidence/live-greenpath-evidence-contract.md` | historical candidates documented; new run requires consent | #125 contract; dated #363 validation | Candidate-scoped historical evidence; new run requires consent |
| REQ-124-23 | External SonarQube/quality result | `documentation/process/verification-state-policy.md` | external system, no repository implementation claim | historical RC1 results retained; current external status not queried | #120/release review | EXTERNAL_GATE_UNAVAILABLE |
| REQ-124-24 | Handoff IDs and canonical navigation targets | `documentation/evidence/live-greenpath-evidence-contract.md`; `documentation/README.adoc` | `documentation/traceability/` | path/link review | #125 for evidence; #129 for navigation | VERIFIED_LOCAL |

## Candidate scope and open-state interpretation

The [RC1 decision](../release/rc1-decision.md) records accepted September
candidates; [Issue #363](../evidence/issue-363-final-validation-20261003.md)
records later native/WSL lifecycle and authenticated checks. They retain their
executed source identities. Current bootstrap changes, other hosts and new
external analyses require their own applicability and evidence.

For a new applicable live run, missing consent, prerequisites, partial and
failed results use the canonical policy states. Missing historical packages
remain unavailable evidence; a current repository source link proves only the
contract it contains. Removed issue workflow paths are retained in Git history,
not used as current navigation targets. Issue #120/global audit closure still
requires its own reviewed disposition; this matrix does not close it.
