# ISMS-light Statement of Applicability

This is a project-specific control applicability map. It summarizes the
security intent without reproducing protected ISO control text and without
claiming certification.

| Control ID | Control theme | Applicability | Rationale | Existing implementation/evidence | Gap | Related risk |
| --- | --- | --- | --- | --- | --- | --- |
| SEC-01 | Access control and admin surfaces | Applicable | Portainer, Traefik and service access can mutate or expose local systems | local-only scope; existing ASVS/RBAC docs; HTTPS/BasicAuth configuration | full role enforcement and changed target/exposure need evidence | RISK-123-DOCKER-SOCKET; RISK-123-ADMIN-CREDENTIAL |
| SEC-02 | Secret handling | Applicable | bootstrap material, tokens, catalog credentials and managed cryptographic material exist in the workflow | secret policy and Infisical references | authorized runtime rotation evidence pending | RISK-123-SECRET-LEAK; RISK-123-INFISICAL-BOOTSTRAP |
| SEC-03 | Evidence redaction | Applicable | logs, screenshots and command summaries may carry sensitive values | existing evidence/redaction contract; dated RC1/#363 results | current run redaction must be verified | RISK-123-SECRET-LEAK |
| SEC-04 | Change control | Applicable | security-sensitive changes require ordered review and quality gates | #122 QMS change-control document | branch/CI policies and workflows exist; external enforcement settings remain unverified | all risks |
| SEC-05 | Logging and trace safety | Applicable | diagnostics can disclose tokens, paths or payloads | redaction rules and existing diagnostic conventions | live logging review pending | RISK-123-SECRET-LEAK; RISK-123-PULSAR-TOKEN |
| SEC-06 | Supplier and dependency security | Applicable | Python dependencies and images are external inputs | #127 supply-chain policy artifacts | historical candidate scan results exist; a new candidate needs applicable scans | RISK-123-DEPENDENCY; RISK-123-IMAGE |
| SEC-07 | Incident handling | Applicable | secret, admin, socket and partial setup incidents need response | incident-response.md and QMS CAPA link | rehearsal/live evidence pending | all Critical/High risks |
| SEC-08 | Backup and restore of local secret material | Applicable | local bootstrap and operator-override loss can block recovery | secret policy describes no raw backup in repo | authorized backup/restore procedure pending | RISK-123-INFISICAL-BOOTSTRAP |
| SEC-09 | Risk acceptance | Applicable | residual risks remain during staged public-beta work | risk register owner/treatment fields | independent acceptance records pending | all open residual risks |

## Status rules

Existing implementation/evidence means a repository governance artifact exists;
it never means the corresponding runtime control is deployed. Gaps remain open
until an approved evidence source and independent review support a change.

The [RC1 security record](rc1-classic-security-evidence.md) identifies executed
scans and accepted residuals for its candidate. The [audit findings register](../audit/findings-register.md)
retains global finding dispositions. Artifact presence and scoped acceptance
do not independently close those findings or qualify later revisions.
