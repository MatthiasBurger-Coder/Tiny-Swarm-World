# ISMS-light Risk Register

Risk status is evidence-honest. Open, evidence-pending, blocked, refused,
resource-gated, failed-to-apply and failed-to-verify are not pass states.
Residual risk is not accepted by documentation presence; an owner, treatment
decision and review evidence are required.

| Risk ID | Asset / surface | Threat scenario | Weakness / exposure | Impact | Likelihood | Inherent risk | Existing controls | Treatment decision | Residual risk | Owner role | Evidence link |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RISK-123-DOCKER-SOCKET | Docker socket, Portainer and agent | compromised admin surface mutates host/Swarm | socket grants high privilege | Critical | Possible | High | local consent/scope rules and candidate-scoped RC1 socket evidence | review powerful socket residuals for current target and changed exposure | Open | Security Owner | ../audit/evidence-matrix.md; ../audit/findings-register.md#maj-04 |
| RISK-123-LOCAL-HTTP | HTTP/TLS ingress and service routes | traffic or admin surface is exposed without intended transport | local HTTP assumptions may be misunderstood | High | Possible | High | managed/operator CA ADR; HTTPS/BasicAuth config and scoped RC1 evidence | verify current route/auth/TLS and changed exposure | Evidence pending | Lead Architect | ../arc42/09_decisions/adr-traefik-managed-or-operator-ca.adoc |
| RISK-123-SECRET-LEAK | logs, evidence, screenshots and repository | credential is copied into a committed or shared artifact | raw output or screenshots can bypass config rules | Critical | Possible | High | redaction and secret policy; review required | prevent, rotate and incident-route any suspected leak | Open | Security Owner | ../audit/evidence-matrix.md; secret-handling-policy.md |
| RISK-123-INFISICAL-BOOTSTRAP | Infisical bootstrap material | bootstrap credential is exposed or reused | bootstrap material is high-value and durable | Critical | Unlikely | High | source-specific handling and no committed secrets | protect, minimize lifetime and document rotation | Evidence pending | Security Owner | secret-handling-policy.md |
| RISK-123-ENV-PERMISSIONS | local environment files | another local user/process reads secret file | permissions may be too broad | High | Possible | High | restrictive permission rule where automation writes files | verify on authorized host run; retain pending state | Evidence pending | Senior DevOps Engineer | security-controls.md |
| RISK-123-ADMIN-CREDENTIAL | local administrator surfaces | credential misuse exposes service control | service authentication exists; complete role separation/rotation remains open | High | Possible | High | isolated-test scope, existing ASVS mapping and authenticated candidate results | reassess authorization and credential lifecycle for current scope | Open | Security Owner | ../audit/findings-register.md#maj-04 |
| RISK-123-PULSAR-TOKEN | Pulsar Admin API token | token leaks through config/log/evidence | token is an admin capability | High | Unlikely | High | redaction and secret-source rules | store externally, rotate on exposure and review access | Evidence pending | Security Owner | secret-handling-policy.md |
| RISK-123-DEPENDENCY | Python dependencies and suppliers | vulnerable dependency is introduced | vulnerability/remediation evidence may lag | Medium | Possible | Medium | closed #127 policy artifacts and dependency review | retain SBOM/SCA review and CAPA on findings | Evidence pending | Senior DevOps Engineer | ../security/supply-chain-security.md; ../audit/evidence-matrix.md |
| RISK-123-IMAGE | container image and registry | vulnerable or untrusted image is deployed | provenance/scan result may be missing | High | Possible | High | image policy and artifact review | require provenance/scan evidence before release | Evidence pending | Senior DevOps Engineer | ../security/container-image-scan-policy.md |
| RISK-123-LIVE-MUTATION | Incus/LXC, Docker, network and stacks | setup changes unintended local infrastructure | external commands are state-changing | Critical | Possible | High | explicit consent, preflight and fail-closed evidence | no execution in docs workflows; test via later live contract | Blocked by consent | Workflow Executor | ../system/live-operation-surfaces.adoc |

## Review and acceptance

A risk review records date, reviewer, evidence links, treatment and residual
state. Risk acceptance is a separate decision with named owner and expiry or
review date. No row above is a certification or deployed-control claim.

These global risk dispositions are not changed by documentation presence.
[RC1 security evidence](rc1-classic-security-evidence.md) records accepted
residuals for its isolated candidate; current or expanded exposure needs its
own treatment review. Historical authorization does not authorize a new run.
