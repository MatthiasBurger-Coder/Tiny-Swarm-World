# Administrative Surface and RBAC Target Model

## Status rule

The models below are expected boundaries, not claims that all service roles or
enforcement already exist. Each state is **Existing**, **Partial**, **Target**
or **Open**. An open auth, route or transport decision blocks exposure.

## Roles

| Role | Intended authority | Allowed scope | Forbidden authority | State |
| --- | --- | --- | --- | --- |
| Operator | Run local workflows and inspect redacted results | Preflight, dry-run, local status and consent prompts | Silent live mutation, raw secret display or bypassing gates | Existing/partial |
| Maintainer | Review and merge repository changes | Branch, PR, docs, tests and approved configuration | Direct main push, force-push or unreviewed admin exposure | Target |
| Security reviewer | Review risks, controls and evidence | Redacted security evidence, risk treatment and incident/CAPA records | Copying secrets or declaring certification | Target |
| Live-run reviewer | Authorize a bounded live validation | Applicability, prerequisites, consent and redacted result review | Unbounded setup, reset or raw credential handling | Target/open |
| Service administrator | Administer one assigned service | Service-specific admin surface after authn/authz approval | Docker socket or unrelated service authority by default | Target/open |
| Read-only reviewer | Inspect status and evidence | Redacted dashboards, logs and review artifacts | Mutating services, secrets or deployment state | Target |

## Service access expectations

| Service | Expected access model | Owner | State | Evidence needed before exposure |
| --- | --- | --- | --- | --- |
| Portainer | Named service admin; read-only reviewer separate; Docker socket risk explicitly reviewed | Service administrator / Security Owner | Partial/open | Authn/authz, socket scope, route/TLS and redacted access result |
| Jenkins | Maintainer/service admin separated from read-only observation | Service administrator | Target/open | Authn, authorization, CSRF/session behavior where Jenkins owns it, route and logs |
| Nexus | Service admin for repository policy; read-only for artifact inspection | Service administrator | Target/open | Authn/authz, repository permissions, image/credential redaction |
| SonarQube | Maintainer/security reviewer for quality/project administration; read-only for reports | Service administrator | Target/open | Authn/authz, project permissions and external result classification |
| Infisical | Security owner controls bootstrap/rotation; operators receive references only | Security Owner | Partial/open | Bootstrap lifecycle, rotation, access policy and no-value evidence |
| Pulsar Admin API | Service administrator only; token is never dashboard-visible | Service administrator / Security Owner | Target/open | Token source, authz, transport, redacted API evidence |
| Service Access dashboard | Read-only default; service-admin actions separately authorized | System Architect / Security Owner | Future/open | Route/TLS, authentication, role mapping, secret-reference and threat evidence |

## Cross-surface boundaries

- The Docker socket is administrative authority; a dashboard is not treated as
  safe merely because it is behind Traefik.
- A role may act only within its named service and approved workflow scope.
- Live-run authority is separate from repository merge authority.
- Secret values are supplied by the approved secret source or local runtime
  boundary and are never rendered into dashboards, screenshots or evidence.
- #150 inherits this model and must close route/auth ownership before enabling
a GUI.
