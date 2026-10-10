# ISMS-light Security Controls

These are project controls and review expectations. They do not prove that a
live control is deployed.

## Repository and evidence controls

- No real operator secrets, passwords, tokens, authorization headers or raw
  environment payloads. Public disposable internal-test catalog values are
  explicitly scoped in the credential catalog; they must not be used as real
  production or shared-system credentials.
- .env.example and similar examples contain placeholders only.
- Local secret files are ignored and, where automation writes them, use
  restrictive permissions appropriate to the local host.
- Evidence, screenshots, diagnostics and logs are summarized and redacted.
  Private paths, IP addresses, join tokens and raw stdout/stderr are excluded.
- A suspected secret leak blocks closure and triggers incident response,
  rotation and CAPA.

## External-action controls

- Incus/LXC, Docker, Swarm, network, stack, service bootstrap and reset commands
  require explicit operator consent under the approved live-validation flow.
- Missing consent, prerequisites or observable evidence is a blocked/refused
  state, never a pass.
- Documentation and tests must use mocks or static checks unless live consent
  is separately recorded.
- The Docker socket is treated as administrative authority. Portainer, agents
  and Traefik routes are not assumed safe from configuration presence alone.

## Admin surface and transport controls

- Admin surfaces remain isolated internal-test surfaces. The ASVS mapping and
  RBAC model define expectations; implemented routing/authentication does not
  prove all authorization roles or production exposure controls.
- The accepted managed-or-operator CA ADR defines current HTTPS ownership.
  Traefik uses external certificate/authentication secrets; new public exposure
  needs its own scope and security review.
- Traefik dashboard configuration implements HTTPS and BasicAuth without
  insecure API mode. Preserve these contracts and verify changes against the
  current target; historical acceptance is not current deployment proof.

## Supply-chain and review controls

- Dependencies and images require the applicable #127 policy and evidence.
- Security-sensitive changes require Security Owner, System Architect and
  Test/Evidence review.
- The PR/issue evidence records affected risks, controls, validation, no-live
  confirmation, open residual risks and rollback/recovery considerations.
- Controls are reviewed at internal audit and after security incidents,
  material architecture decisions or repeated gate failures.

## Audit-finding traceability

- `MAJ-01` is addressed by this scope, the risk register and the SoA; its
  evidence source is `../audit/findings-register.md#maj-01`.
- `MAJ-04` is addressed by the Docker-socket/admin-surface controls and
  `RISK-123-DOCKER-SOCKET`; its evidence source is
  `../audit/findings-register.md#maj-04`.
- `MIN-02` remains linked to dependency and image governance through the
  existing #127 policy artifacts; its evidence source is
  `../audit/findings-register.md#min-02`.
- `MIN-07` maps to the existing ASVS/admin-surface matrix and implemented
  Traefik configuration; independent global finding disposition remains open.
  Its evidence source is
  `../audit/findings-register.md#min-07`.

These links trace audit findings to project-specific controls and open
treatments; they do not claim that a runtime control or external audit finding
has been closed.
