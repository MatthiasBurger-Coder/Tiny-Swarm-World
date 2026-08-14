# ISMS-light Statement of Applicability

This is a project-specific control applicability map. It summarizes the
security intent without reproducing protected ISO control text and without
claiming certification.

| Control ID | Control theme | Applicability | Rationale | Existing implementation/evidence | Gap | Related risk |
| --- | --- | --- | --- | --- | --- | --- |
| SEC-01 | Access control and admin surfaces | Applicable | Portainer, Traefik and service access can mutate or expose local systems | local-only scope; route/admin docs; #126 planned | authn/authz and route decision require #126/#150 | RISK-123-DOCKER-SOCKET; RISK-123-ADMIN-CREDENTIAL |
| SEC-02 | Secret handling | Applicable | bootstrap material, tokens and generated secrets exist in the workflow | secret policy and Infisical references | authorized runtime rotation evidence pending | RISK-123-SECRET-LEAK; RISK-123-INFISICAL-BOOTSTRAP |
| SEC-03 | Evidence redaction | Applicable | logs, screenshots and command summaries may carry sensitive values | #121 evidence rules and redaction policy | live evidence contract still pending | RISK-123-SECRET-LEAK |
| SEC-04 | Change control | Applicable | security-sensitive changes require ordered review and quality gates | #122 QMS change-control document | branch protection and CI enforcement require #128 | all risks |
| SEC-05 | Logging and trace safety | Applicable | diagnostics can disclose tokens, paths or payloads | redaction rules and existing diagnostic conventions | live logging review pending | RISK-123-SECRET-LEAK; RISK-123-PULSAR-TOKEN |
| SEC-06 | Supplier and dependency security | Applicable | Python dependencies and images are external inputs | #127 supply-chain policy artifacts | current scan/baseline evidence pending | RISK-123-DEPENDENCY; RISK-123-IMAGE |
| SEC-07 | Incident handling | Applicable | secret, admin, socket and partial setup incidents need response | incident-response.md and QMS CAPA link | rehearsal/live evidence pending | all Critical/High risks |
| SEC-08 | Backup and restore of local secret material | Applicable | local bootstrap and generated secret loss can block recovery | secret policy describes no raw backup in repo | authorized backup/restore procedure pending | RISK-123-INFISICAL-BOOTSTRAP |
| SEC-09 | Risk acceptance | Applicable | residual risks remain during staged public-beta work | risk register owner/treatment fields | independent acceptance records pending | all open residual risks |

## Status rules

Existing implementation/evidence means a repository governance artifact exists;
it never means the corresponding runtime control is deployed. Gaps remain open
until an approved evidence source and independent review support a change.
