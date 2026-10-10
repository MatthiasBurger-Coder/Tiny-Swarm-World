# Tiny Swarm World OWASP ASVS Applicability Mapping

## Scope and status

This is a project-specific mapping for local infrastructure automation and
service administration. It is not an ASVS certification, penetration test or
proof that a live service is secure. Statuses are **Applicable**, **Partially
applicable**, **Not directly applicable**, and **Future/open**.

Repository delivery is distinct from control effectiveness. The current
Traefik compose contract implements HTTPS, managed/operator CA selection and
BasicAuth for its administrative dashboard. ASVS, RBAC, threat and evidence
contracts exist. [RC1 security evidence](rc1-classic-security-evidence.md) and
[Issue #363 validation](../evidence/issue-363-final-validation-20261003.md)
are dated, candidate-scoped results; current control effectiveness, broader
role enforcement and changed exposure still require applicable evidence.

## Area mapping

| Area | Applicability | Tiny Swarm World surfaces | Existing evidence | Gap | Planned remediation | Related finding |
| --- | --- | --- | --- | --- | --- | --- |
| V1 Architecture, design and threat modeling | Applicable | CLI consent, provider boundary, Service Access, Traefik and compose assets | #123 boundary model; #121 audit evidence; existing Traefik ADR | Changed exposure and complete RBAC still require review | Preserve accepted route ownership; review changes against current target evidence | MAJ-01; MAJ-04 |
| V2 Authentication | Applicable | Portainer, Jenkins, Nexus, SonarQube, Infisical, Pulsar and Service Access | #123 risk/control policy; local service configuration references | Authn mechanisms and bootstrap evidence vary by service | Retain scoped authenticated results; verify changed services and targets | MAJ-04; MIN-07 |
| V3 Session management | Not directly applicable | CLI is non-session-based; local services may own sessions | Service boundaries and local-only scope | Any service-owned web session needs its own review | Reclassify per service if a session-bearing surface is exposed | MIN-07 |
| V4 Access control | Applicable | RBAC roles, Docker socket, dashboards and admin APIs | #123 Docker-socket risk; RBAC target model | Enforced role assignments are not verified | Verify the target role model separately from existing service authentication | MAJ-04; MIN-07 |
| V5 Validation, sanitization and encoding | Partially applicable | CLI inputs, route/config values, API/service payloads | Existing command/config tests and quality gate | Full service-specific input review is not in this docs slice | Add focused validation evidence when a surface changes | None identified |
| V6 Stored cryptography and secrets | Applicable | Infisical, local secret files, catalog credentials, managed cryptographic material and evidence | #123 secret-handling policy; #127 supply-chain policy | Runtime rotation/backup evidence is pending | Use secret references, redaction and authorized rotation evidence | MAJ-01; MAJ-04 |
| V7 Error handling and logging | Applicable | CLI diagnostics, service logs, evidence summaries and screenshots | #121 redaction rules; #123 incident/secret policy | Live log review is pending | Preserve redaction and add live evidence only under #125 | MAJ-01; MIN-07 |
| V8 Data protection | Partially applicable | Service metadata, credentials, evidence and local host data | Local-only scope and redaction policy | Retention/access controls for each service are not verified | Define evidence retention and service-specific handling | MAJ-01 |
| V9 Communications security | Applicable | Traefik HTTPS, Swagger/NGINX routes, admin/service ingress | Managed/operator CA ADR, Traefik compose and scoped RC1 evidence | Current target TLS/auth and changed exposure require verification | Preserve accepted HTTPS/BasicAuth contracts; obtain applicable current evidence | MAJ-04; MIN-07 |
| V10 Code integrity and dependency security | Applicable | Python source, compose assets, images and dependencies | #127 policy artifacts; #128 CI gate policy | Hosted scan/enforcement status is unknown | Carry scan/SBOM evidence into release governance | MIN-02 |
| V12 File and resource handling | Applicable | install.sh, local files, compose resources, Docker socket and provider assets | #123 scope/risk model; repository quality checks | Live permission/resource evidence is pending | Verify authorized host behavior in later live workflow | MAJ-04 |
| V13 API and service communication | Applicable | Pulsar Admin API, Service Access, Portainer, Jenkins, Nexus and Swagger | Existing contracts/configuration; #123 risk model | Service-specific authz and transport evidence is open | Map API evidence when surfaces are changed | MAJ-04; MIN-07 |
| V14 Configuration | Applicable | YAML/compose, environment placeholders, Traefik and Infisical references | #123 secret policy; #128 governance; repository config contracts | External setting/runtime drift is not verified | Reconcile configuration with evidence contract and review | MAJ-01; MAJ-04 |

## Required surface inventory

| Surface | Owner/decision | Current state | Evidence expectation |
| --- | --- | --- | --- |
| CLI live-consent model | Workflow Executor | Existing policy | Consent and fail-closed result |
| `install.sh` wrapper | Senior DevOps | Existing wrapper boundary | Redacted command/result evidence |
| Local secret files | Security Owner | Policy/target | Permission and redaction evidence |
| Infisical | Security Owner | Bootstrap/sync implemented; general rotation open | Bootstrap/rotation evidence without values |
| Service Access dashboard | System Architect | Route/assets implemented; full RBAC open | RBAC, route, TLS and threat evidence |
| Portainer | Service Administrator owner | Existing surface; exposure risk open | Authz, socket and route evidence |
| Jenkins | Service Administrator owner | Existing stack surface | Authn/authz and secret-reference evidence |
| Nexus | Service Administrator owner | Existing stack surface | Repository/admin authz and image evidence |
| SonarQube | Service Administrator owner | Existing stack/workflow surface | External result state and access evidence |
| Pulsar Admin API | Service Administrator owner | Existing surface; token risk open | Token handling, authz and transport evidence |
| Swagger/NGINX | System Architect | Existing route surface | Route, transport and documentation evidence |
| Traefik | System Architect | HTTPS/BasicAuth GUI implemented; current target evidence separate | HTTPS, authn/authz and exposure evidence |
| Evidence files | Senior Tester | Existing governance artifact | Status, provenance and redaction evidence |
| Compose stack assets | Senior DevOps | Existing configuration | No-secret, image and route review |

## Administrative surface review boundary

The implemented dashboard retains the applicable V1/V2/V4/V6/V7/V9/V13/V14
route/TLS, authentication and secret-reference contracts. Changes must carry
those decisions, owners and evidence scope forward. Open role/enforcement or
exposure controls remain blockers for expanding the accepted access boundary.
