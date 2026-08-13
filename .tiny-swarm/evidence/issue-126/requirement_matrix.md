# Issue #126 Requirement Matrix

Workflow: `issue-126-owasp-asvs-admin-surface-20260812`
Issue: #126
Predecessors: #123 ISMS-light and #128 branch/CI governance

Matrix owner: Senior System Architect
Reviewers: OWASP ASVS Local Infrastructure Expert, ISMS-light Security
Governance Expert, Security And Threat Modeling, Requirement Engineer and
Senior Tester

## Status and scope

`VERIFIED_LOCAL` means that the mapping or governance decision is present in
repository evidence. It is not ASVS certification and does not prove that a
runtime control or admin surface is deployed securely. Open, future and
partial applicability remain explicit in the documents.

## Requirement-to-evidence matrix

| ID | Requirement | Type | Implementation/evidence | Verification | Status |
| --- | --- | --- | --- | --- | --- |
| REQ-126-001 | Create owasp-asvs-mapping.md. | Required file | S126-02 mapping | File/content review | VERIFIED_LOCAL |
| REQ-126-002 | Create admin-surface-rbac.md. | Required file | S126-02 RBAC model | File/content review | VERIFIED_LOCAL |
| REQ-126-003 | Create service-access-threat-model.md. | Required file | S126-02 threat model | File/content review | VERIFIED_LOCAL |
| REQ-126-004 | Map V1 architecture/design/threat modeling. | ASVS | owasp-asvs-mapping.md | Area row review | VERIFIED_LOCAL |
| REQ-126-005 | Map V2 authentication. | ASVS | owasp-asvs-mapping.md | Area row review | VERIFIED_LOCAL |
| REQ-126-006 | Map V3 session management as not directly applicable unless a local service owns it. | ASVS | owasp-asvs-mapping.md | Applicability review | VERIFIED_LOCAL |
| REQ-126-007 | Map V4 access control. | ASVS | owasp-asvs-mapping.md | Area row review | VERIFIED_LOCAL |
| REQ-126-008 | Map V5 validation, sanitization and encoding. | ASVS | owasp-asvs-mapping.md | Area row review | VERIFIED_LOCAL |
| REQ-126-009 | Map V6 stored cryptography and secret handling. | ASVS | owasp-asvs-mapping.md | Area row review | VERIFIED_LOCAL |
| REQ-126-010 | Map V7 error handling and logging. | ASVS | owasp-asvs-mapping.md | Area row review | VERIFIED_LOCAL |
| REQ-126-011 | Map V8 data protection. | ASVS | owasp-asvs-mapping.md | Area row review | VERIFIED_LOCAL |
| REQ-126-012 | Map V9 communications security. | ASVS | owasp-asvs-mapping.md | Area row review | VERIFIED_LOCAL |
| REQ-126-013 | Map V10 code integrity and dependency considerations. | ASVS | owasp-asvs-mapping.md | Area row review | VERIFIED_LOCAL |
| REQ-126-014 | Map V12 file/resource handling. | ASVS | owasp-asvs-mapping.md | Area row review | VERIFIED_LOCAL |
| REQ-126-015 | Map V13 API/service communication where applicable. | ASVS | owasp-asvs-mapping.md | Area row review | VERIFIED_LOCAL |
| REQ-126-016 | Map V14 configuration. | ASVS | owasp-asvs-mapping.md | Area row review | VERIFIED_LOCAL |
| REQ-126-017 | Cover CLI live-consent model. | Surface | owasp-asvs-mapping.md | Surface inventory | VERIFIED_LOCAL |
| REQ-126-018 | Cover install.sh wrapper. | Surface | owasp-asvs-mapping.md | Surface inventory | VERIFIED_LOCAL |
| REQ-126-019 | Cover local secret files. | Surface | owasp-asvs-mapping.md | Surface inventory | VERIFIED_LOCAL |
| REQ-126-020 | Cover Infisical. | Surface | owasp-asvs-mapping.md | Surface inventory | VERIFIED_LOCAL |
| REQ-126-021 | Cover Service Access dashboard. | Surface | owasp-asvs-mapping.md | Surface inventory | VERIFIED_LOCAL |
| REQ-126-022 | Cover Portainer, Jenkins, Nexus, SonarQube and Pulsar Admin API. | Surface | owasp-asvs-mapping.md | Surface inventory | VERIFIED_LOCAL |
| REQ-126-023 | Cover Swagger/NGINX and Traefik. | Surface | owasp-asvs-mapping.md | Surface inventory | VERIFIED_LOCAL |
| REQ-126-024 | Cover evidence files and compose stack assets. | Surface | owasp-asvs-mapping.md | Surface inventory | VERIFIED_LOCAL |
| REQ-126-025 | Give every ASVS row applicability, surfaces, evidence, gap, remediation and finding. | Mapping schema | owasp-asvs-mapping.md | Column review | VERIFIED_LOCAL |
| REQ-126-026 | Use applicable, partially applicable, not applicable and future states. | Mapping status | owasp-asvs-mapping.md | Status vocabulary review | VERIFIED_LOCAL |
| REQ-126-027 | Define Operator, Maintainer, Security reviewer, Live-run reviewer, Service administrator and Read-only reviewer roles. | RBAC | admin-surface-rbac.md | Role review | VERIFIED_LOCAL |
| REQ-126-028 | Define access boundaries and forbidden authority for each role. | RBAC | admin-surface-rbac.md | Boundary review | VERIFIED_LOCAL |
| REQ-126-029 | Define expected models for Portainer, Jenkins, Nexus, SonarQube, Infisical, Pulsar and Service Access. | RBAC | admin-surface-rbac.md | Service table review | VERIFIED_LOCAL |
| REQ-126-030 | Mark target, existing, partial and open states without overclaiming implementation. | RBAC status | admin-surface-rbac.md | Status review | VERIFIED_LOCAL |
| REQ-126-031 | Define Service Access assets, actors, boundaries, entry points and assumptions. | Threat model | service-access-threat-model.md | Threat-model schema | VERIFIED_LOCAL |
| REQ-126-032 | Define misuse cases, existing controls, gaps and required evidence. | Threat model | service-access-threat-model.md | Threat-model schema | VERIFIED_LOCAL |
| REQ-126-033 | Require the dashboard to show secret references, never raw values. | Secret safety | threat model/RBAC | Rule review | VERIFIED_LOCAL |
| REQ-126-034 | Link #123 risks, #121 evidence and #128 review/merge policy. | Traceability | all three docs | Link review | VERIFIED_LOCAL |
| REQ-126-035 | Hand applicable controls, owner, auth/TLS and residual-risk decisions to #150. | Handoff | RBAC/threat model | Handoff review | VERIFIED_LOCAL |
| REQ-126-036 | Review the existing Traefik HTTPS ADR; do not invent a new ADR without a verified decision. | Architecture | mapping and workflow | ADR review | VERIFIED_LOCAL |
| REQ-126-037 | Keep documentation-only scope: no active scan, live command, secret or certification claim. | Safety | evidence and changed-file audit | No-live review | VERIFIED_LOCAL |
| REQ-126-038 | Use dedicated branch and serial S126-01 -> S126-02 after #123/#128. | Process | workflow/context | Order review | VERIFIED_LOCAL |
| REQ-126-039 | Run git diff --check and python3 tools/quality_gate.py quality. | Quality | test_results.md | Command review | VERIFIED_LOCAL |
| REQ-126-040 | Provide six issue evidence files and independent completion audit. | Completion | .tiny-swarm/evidence/issue-126 | Required-file/audit review | EVIDENCE_PENDING |

## Boundary decisions

- ASVS is used as a project-specific control vocabulary, not as a certification
  claim or a web-application checklist applied without applicability analysis.
- #123 owns risk/secret governance; #128 owns review/merge quality governance;
  #126 owns the security decision space; #150 owns only the later feature.
- The Traefik HTTPS ADR is reviewed context. Route/auth ownership remains open
  until the approved #150 design and evidence contract exist.
