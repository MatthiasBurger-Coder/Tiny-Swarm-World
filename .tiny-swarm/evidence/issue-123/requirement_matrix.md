# Issue #123 Requirement Matrix

Workflow: issue-123-isms-light-20260812
Issue: #123
Parent roadmap: #120
Predecessor context: #121 audit evidence and #122 QMS-light

Matrix owner: Senior Requirement Engineer
Reviewers: ISMS-light Security Governance Expert, Security And Threat
Modeling, OWASP ASVS Local Infrastructure Expert, Senior System Architect,
Senior Tester, Senior Documentation Engineer

## Status and interpretation

VERIFIED_LOCAL means a repository-local document or check is verified; it does
not mean a security control is deployed or that a live service is secure.
PLANNED, OPEN, EVIDENCE_PENDING, BLOCKED, REFUSED, RESOURCE-GATED,
FAILED_TO_APPLY and FAILED_TO_VERIFY are non-pass states. No real secret, raw
environment payload, host data or certification claim may be committed.

The original issue requires git diff --check and
python3 tools/quality_gate.py quality. The full gate is local evidence only.
#121 and #122 provide the audit/QMS vocabulary. #123 remains incomplete until
the six security documents, evidence package and independent completion audit
are complete.

## Requirement-to-evidence matrix

| ID | Requirement | Type | Planned implementation/evidence | Verification | Status |
| --- | --- | --- | --- | --- | --- |
| REQ-123-001 | Create documentation/security/isms-scope.md. | Required file | S123-02 scope document | File/content review | VERIFIED_LOCAL |
| REQ-123-002 | Create documentation/security/risk-register.md. | Required file | S123-02 risk register | Schema/entry review | VERIFIED_LOCAL |
| REQ-123-003 | Create documentation/security/statement-of-applicability.md. | Required file | S123-02 SoA-style mapping | Control-field review | VERIFIED_LOCAL |
| REQ-123-004 | Create documentation/security/security-controls.md. | Required file | S123-02 controls document | Control review | VERIFIED_LOCAL |
| REQ-123-005 | Create documentation/security/incident-response.md. | Required file | S123-02 incident runbooks | Scenario/runbook review | VERIFIED_LOCAL |
| REQ-123-006 | Create documentation/security/secret-handling-policy.md. | Required file | S123-02 secret policy | Secret/redaction review | VERIFIED_LOCAL |
| REQ-123-007 | Define ISMS-light purpose and local-only product scope. | Scope | isms-scope.md | Scope review against AGENTS | VERIFIED_LOCAL |
| REQ-123-008 | Cover repository, local operator environment and generated local evidence. | Scope/assets | isms-scope.md | Asset-scope review | VERIFIED_LOCAL |
| REQ-123-009 | Cover service-access stack, Infisical, Portainer, Nexus, Jenkins, SonarQube, Pulsar, Swagger/NGINX and Traefik. | Scope/assets | isms-scope.md | Surface inventory review | VERIFIED_LOCAL |
| REQ-123-010 | Cover LXC/LXD/Incus provider interactions. | Scope/assets | isms-scope.md | Provider-boundary review | VERIFIED_LOCAL |
| REQ-123-011 | State out-of-scope unrelated host resources, production cloud deployment and enterprise IdP unless later added. | Scope boundary | isms-scope.md | Boundary wording review | VERIFIED_LOCAL |
| REQ-123-012 | Define asset classes, trust boundaries and local-only assumptions. | Architecture/security | This matrix S123-01 boundary model; isms-scope.md | Trust-boundary review | VERIFIED_LOCAL |
| REQ-123-013 | Risk-register columns include ID, asset/surface, threat, weakness, impact, likelihood, inherent risk, existing controls, treatment, residual risk, owner and evidence link. | Schema | risk-register.md | Column check | VERIFIED_LOCAL |
| REQ-123-014 | Assess Docker socket exposure via Portainer and agent. | Risk | RISK-123-DOCKER-SOCKET | Row/content check | VERIFIED_LOCAL |
| REQ-123-015 | Assess local HTTP exposure and TLS assumptions. | Risk | RISK-123-LOCAL-HTTP | Row/content check | VERIFIED_LOCAL |
| REQ-123-016 | Assess secret leakage through logs, evidence, screenshots and committed files. | Risk | RISK-123-SECRET-LEAK | Row/content check | VERIFIED_LOCAL |
| REQ-123-017 | Assess Infisical bootstrap material protection. | Risk | RISK-123-INFISICAL-BOOTSTRAP | Row/content check | VERIFIED_LOCAL |
| REQ-123-018 | Assess local environment-file permission failure. | Risk | RISK-123-ENV-PERMISSIONS | Row/content check | VERIFIED_LOCAL |
| REQ-123-019 | Assess local administrator credential misuse. | Risk | RISK-123-ADMIN-CREDENTIAL | Row/content check | VERIFIED_LOCAL |
| REQ-123-020 | Assess Pulsar Admin API token exposure. | Risk | RISK-123-PULSAR-TOKEN | Row/content check | VERIFIED_LOCAL |
| REQ-123-021 | Assess dependency vulnerability. | Risk | RISK-123-DEPENDENCY | Row/content check | VERIFIED_LOCAL |
| REQ-123-022 | Assess container image vulnerability. | Risk | RISK-123-IMAGE | Row/content check | VERIFIED_LOCAL |
| REQ-123-023 | Assess live setup changing unintended local infrastructure. | Risk | RISK-123-LIVE-MUTATION | Row/content check | VERIFIED_LOCAL |
| REQ-123-024 | Map access control, secret handling, evidence redaction, change control, logging/trace safety, supplier/dependency security, incident handling, backup/restore and risk acceptance. | SoA | statement-of-applicability.md | Control mapping review | VERIFIED_LOCAL |
| REQ-123-025 | Each SoA control has applicability, rationale, existing implementation/evidence, gap and related risk. | SoA schema | SoA table | Field completeness check | VERIFIED_LOCAL |
| REQ-123-026 | Define no committed secrets and placeholder-only .env.example controls. | Control | security-controls.md | Control wording review | VERIFIED_LOCAL |
| REQ-123-027 | Define ignored local secret files and restrictive permissions where automation writes them. | Control | security-controls.md and secret policy | Control review | VERIFIED_LOCAL |
| REQ-123-028 | Require explicit consent for live commands. | Control/safety | security-controls.md | Consent-policy review | VERIFIED_LOCAL |
| REQ-123-029 | Require evidence redaction and keep admin surfaces local unless explicitly hardened. | Control | security-controls.md | Redaction/exposure review | VERIFIED_LOCAL |
| REQ-123-030 | Treat Docker socket risk as explicitly accepted or reduced with owner and residual state. | Control/risk | Controls and risk register | Cross-link review | VERIFIED_LOCAL |
| REQ-123-031 | Define incident runbooks for committed secret, secret in logs/evidence, unexpected admin exposure, Docker socket event, failed/partial live setup and Infisical bootstrap issue. | Incident | incident-response.md | Scenario/content review | VERIFIED_LOCAL |
| REQ-123-032 | Each incident runbook includes detection, containment, correction, recovery, evidence preservation, CAPA handoff and post-incident review. | Incident schema | Runbook sections | Field completeness review | VERIFIED_LOCAL |
| REQ-123-033 | Define secret classes, allowed/forbidden storage, redaction, rotation triggers, Infisical bootstrap, generated secret and evidence rules. | Secret policy | secret-handling-policy.md | Secret-policy review | VERIFIED_LOCAL |
| REQ-123-034 | Link security controls and findings to #121 evidence and later #126 ASVS work. | Traceability | Cross-links and control IDs | Link review | VERIFIED_LOCAL |
| REQ-123-035 | Every residual risk has treatment, owner and evidence state. | Risk governance | Risk register/SoA | Residual-risk check | VERIFIED_LOCAL |
| REQ-123-036 | Keep documentation-only scope; do not run active scans, attacks, live commands or service bootstrap. | Safety | Evidence and changed-file audit | No-live review | VERIFIED_LOCAL |
| REQ-123-044 | Do not run active checks against live services. | Safety | Workflow and evidence | No-live review | VERIFIED_LOCAL |
| REQ-123-045 | Do not reproduce protected ISO control text; use project-specific control summaries only. | Compliance/documentation | SoA and controls wording | Claim/content review | VERIFIED_LOCAL |
| REQ-123-046 | Use a dedicated approved workflow branch for the implementation. | Process | Branch/context evidence | Branch check | VERIFIED_LOCAL |
| REQ-123-047 | Record security documentation summary, new risks, open treatments, validation and no-live confirmation in PR/issue evidence. | Completion evidence | Evidence package | Evidence-field review | VERIFIED_LOCAL |
| REQ-123-037 | Do not introduce real secrets, raw local data or certification claims. | Security/compliance | All docs/evidence | Secret/redaction/claim scan | VERIFIED_LOCAL |
| REQ-123-038 | Preserve fail-closed, consent and redaction rules and Linux/WSL, Docker Swarm-first governance. | Product constraints | Scope/control wording | AGENTS comparison | VERIFIED_LOCAL |
| REQ-123-039 | Use serial S123-01 -> S123-02 after #121/#122 completion. | Process | Workflow metadata/predecessors | Dependency/order check | VERIFIED_LOCAL |
| REQ-123-040 | Create distribution evidence before each slice and consolidation evidence after each slice. | Execution evidence | .codex/evidence/issue-123 | Evidence-file check | VERIFIED_LOCAL |
| REQ-123-041 | Run git diff --check and python3 tools/quality_gate.py quality; record local-only result. | Quality | Test results | Command review | VERIFIED_LOCAL |
| REQ-123-042 | Provide six issue evidence files and an independent completion audit before DONE. | Completion | .tiny-swarm/evidence/issue-123 | Required-file/auditor review | VERIFIED_LOCAL |
| REQ-123-043 | Trace ISMS-light to the System Unification EPIC as compatible security governance while retaining #120/#123 authority. | Architecture/traceability | Scope document and matrix | EPIC/source review | VERIFIED_LOCAL |
| REQ-123-048 | Link MAJ-01, MAJ-04, MIN-02 and MIN-07 from #121 to relevant ISMS controls and risks. | Traceability | Security documents and #121 registers | Link review | VERIFIED_LOCAL |
| REQ-123-049 | Use the dedicated issue/workflow branch before changes. | Process | Branch/context evidence | Branch check | VERIFIED_LOCAL |
| REQ-123-050 | Record security summary, new risks, open treatment decisions, validation and no-live confirmation in PR/issue evidence. | Completion evidence | Evidence package | Evidence-field review | VERIFIED_LOCAL |
| REQ-123-051 | If the full gate cannot run, record the exact blocker and nearest meaningful checks without claiming success. | Quality/fallback | Test results and workflow | Gate-result review | VERIFIED_LOCAL |

## Slice contract

| Slice | Output | Status |
| --- | --- | --- |
| S123-01 | Matrix, trust boundary and security requirement model | VERIFIED_LOCAL |
| S123-02 | Six ISMS documents, controls, incidents, secret policy and final evidence | VERIFIED_LOCAL |

## S123-01 threat-boundary model

The S123-01 model is deliberately a governance boundary, not a deployed
security claim:

| Boundary | Assets/data | Trust assumption | Required treatment/evidence state |
| --- | --- | --- | --- |
| Operator host -> automation | repository, configuration, local generated evidence and command inputs | operator host is local and not implicitly trusted with committed secrets | explicit consent, redaction, restrictive local secret handling; live state remains planned |
| Automation -> Incus/LXC provider | provider commands, node identity and host/network metadata | provider interaction is a guarded external-action boundary | fail-closed consent and redacted evidence; no live execution in #123 |
| Swarm host -> Docker Engine/socket | Docker socket, Portainer/agent control and service metadata | socket access is administrative authority, not a harmless read-only API | risk RISK-123-DOCKER-SOCKET remains open until #126/#150 treatment |
| Traefik -> service ingress | HTTP/TLS routes, admin surfaces and service endpoints | route configuration is not proof of secure exposure | existing HTTPS ADR is context; ASVS/admin decision is deferred to #126 |
| Secret source -> services/evidence | Infisical bootstrap, generated secrets, env files, tokens and logs | secret material must not cross into repository or raw evidence | allowed/forbidden storage and redaction are defined in S123-02 |
| Repository -> external dependencies/images | dependencies, image sources and artifact metadata | supplier/image trust is a residual risk, not assumed safe | link #127 policy evidence and retain open treatment state |

Asset classes are source/configuration, credentials/secrets, infrastructure
control surfaces, service data/metadata, evidence artifacts and third-party
dependencies/images. The local-only assumption means no production cloud,
enterprise identity provider or unrelated host resource is in scope. Planned
controls are not represented as deployed controls.

## Boundary decisions

- ISMS-light is governance, not proof that controls are deployed.
- #126 owns the detailed ASVS/admin-surface decision; #150 is later.
- The existing Traefik HTTPS ADR is architecture context; no new service
boundary or ADR is invented here.

## S123-01 ownership map

| Area | Owner role | Review/evidence owner |
| --- | --- | --- |
| Scope, assets and trust boundaries | Lead Architect | Senior System Architect |
| Risk IDs and residual treatment | Security Owner | ISMS-light Security Governance Expert |
| Secret classes, redaction and rotation | Security Owner | Security And Threat Modeling |
| Live-consent and provider boundaries | Senior DevOps Engineer | Senior System Architect |
| Evidence status and links | Workflow Executor | Senior Tester and Audit Evidence Manager |
| ASVS/admin-surface handoff | Security Owner | OWASP ASVS Local Infrastructure Expert in #126 |

The implementation still matches the System Unification EPIC: it adds
documentation-only security governance around existing local infrastructure
boundaries, does not create a service boundary, and preserves the existing
hexagonal, consent and redaction rules. The EPIC is architectural context; #120
and #123 remain issue authorities.
