# Service Access Dashboard Threat Model

## Scope and assets

Service Access is treated as a local administrative routing/dashboard surface,
not as a trusted frontend. Assets include service route metadata, role
assignments, authentication state, secret references, Docker/Swarm metadata,
redacted evidence, logs and links to Portainer, Jenkins, Nexus, SonarQube,
Pulsar, Infisical, Swagger/NGINX and Traefik.

## Actors

- Operator running a bounded local workflow.
- Maintainer reviewing repository changes.
- Security reviewer inspecting risks and evidence.
- Live-run reviewer authorizing explicit live validation.
- Service administrator operating one assigned service.
- Read-only reviewer inspecting redacted status.
- Compromised local process, credential holder or exposed route as adversarial
  misuse actors.

## Trust boundaries and entry points

| Boundary/entry point | Assumption | Required control/evidence |
| --- | --- | --- |
| Operator -> dashboard | Local does not mean trusted | Authn/authz, consent and redacted access evidence |
| Traefik -> dashboard route | HTTPS route is not authorization | TLS, route ownership, authentication and authorization decision |
| Dashboard -> service APIs | Each API has its own authority | Per-service role mapping, transport and error/log review |
| Dashboard -> Docker/Swarm metadata | Socket/control metadata is privileged | No implicit socket access; explicit risk treatment and owner |
| Secret source -> dashboard | References may identify capabilities | Show secret references/status only; never raw values |
| Dashboard -> evidence/logs | Output can disclose sensitive data | Redaction, provenance, retention and incident routing |

The implemented Service Access assets render service links and credential
references. The model also considers potential authenticated actions, API
proxies and evidence exports; their inclusion does not claim those features
exist. Traefik's own administrative dashboard separately implements HTTPS and
BasicAuth. Configuration presence is not proof of current runtime security.

## Misuse cases

| Misuse case | Impact | Existing controls | Gap/required evidence |
| --- | --- | --- | --- |
| Unauthenticated dashboard route | Admin mutation or service disclosure | #123 admin-surface risk; #128 merge policy; Traefik HTTPS ADR | Current target/exposure needs applicable authentication and role-policy evidence |
| Read-only reviewer receives admin capability | Unauthorized service change | Role separation target model | Enforced role evidence per service |
| Dashboard exposes a token/password | Credential compromise | #123 secret policy and redaction rules | Redacted UI/evidence check; rotation on exposure |
| Service API token is reused across surfaces | Blast radius increases | Secret-source and rotation policy | Per-service token ownership and access evidence |
| Docker socket is reachable through dashboard | Host/Swarm control | Explicit RISK-123-DOCKER-SOCKET | Socket boundary and compensating-control evidence |
| Route points to unintended service | Data/admin exposure | Review and change-control policy | Route inventory, test and rollback evidence |
| Error/log export leaks paths or payloads | Information disclosure | Redacted evidence rules | Authorized redaction validation |
| Compromised local process calls dashboard/API | Unauthorized mutation | Local-only and consent boundary | Threat response, incident/CAPA and live evidence |

## Required dashboard rule

The dashboard must show secret references, presence/status and ownership
metadata only. It must never show raw passwords, API tokens, join tokens,
authorization headers, private keys, raw environment content or generated
secret values. This applies to UI responses, logs, screenshots, exports and
evidence files.

## Evidence and handoff

For changed administrative exposure, the evidence package must include the applicable
ASVS rows, service owner, route/TLS decision, authentication and authorization
model, secret-reference check, redacted logs, rollback path and remaining-risk
state. #121 MAJ-04, #123 RISK-123-DOCKER-SOCKET and #123 RISK-123-ADMIN-CREDENTIAL
remain linked until the resulting admin surface is independently reviewed.

The [RC1 security record](rc1-classic-security-evidence.md) and
[October validation](../evidence/issue-363-final-validation-20261003.md) retain
candidate-specific authenticated/route results. They do not prove complete
service role separation or qualify subsequent bootstrap changes.
