# ISMS-light Security Controls

These are project controls and review expectations. They do not prove that a
live control is deployed.

## Repository and evidence controls

- No committed secrets, passwords, tokens, authorization headers or raw
  environment payloads.
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

- Admin surfaces are local development surfaces until #126 defines
  authentication, authorization, transport and exposure requirements.
- The existing Traefik HTTPS ADR is the architecture context; it does not
  authorize a new public route.
- #150 must not enable unauthenticated or insecure dashboard exposure and must
  carry route, auth, TLS, redaction and evidence decisions forward.

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
- `MIN-07` is explicitly handed to #126 for the ASVS/admin-surface matrix and
  to #150 for any resulting implementation; its evidence source is
  `../audit/findings-register.md#min-07`.

These links trace audit findings to project-specific controls and open
treatments; they do not claim that a runtime control or external audit finding
has been closed.
