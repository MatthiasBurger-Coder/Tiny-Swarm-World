# EPIC: Service Access Dashboard And Vaultwarden

## Status

```text
ACTIVE_BASELINE_EXTENSION
```

## Requirement Source

This EPIC extends `documentation/epics/system-unification.md` and
`documentation/epics/autonomous-runnable-setup.md` from these
repository-visible sources:

- user request: create another container using the same technique as existing
  service containers;
- user request: the container should include a GUI showing which servers are
  reachable and which passwords are needed;
- user clarification: password values must be visible;
- active workflow `documentation/workflow/workflow.md`, version
  `service-access-vaultwarden-dashboard-v1.0.0`;
- root `AGENTS.md` Linux/WSL-only, Docker Swarm-first, Python automation
  identity;
- root `QUALITY.md` quality-gate authority;
- current Deployment responsibility direction in
  `documentation/architecture/adr-separate-platform-artifacts-deployment.adoc`;
- autonomous setup safety contract in
  `documentation/architecture/adr-autonomous-setup-safety.adoc`.

This EPIC is the requirement baseline for service access and credential
visibility. It does not claim that a Vaultwarden stack, dashboard stack,
routing configuration, persistence, backup, readiness check, or live deployment
is implemented.

## Relationship To System Unification

The system-unification EPIC defines Tiny Swarm World as one local Python
automation system with in-process responsibility boundaries:

- Platform;
- Artifacts;
- Deployment;
- Shared;
- Console/status UI.

The service-access dashboard and Vaultwarden capability belongs to the
Deployment responsibility boundary as a future Docker Swarm service stack. It
is not a new microservice, not a Spring Boot application, not a React frontend
project, and not a Kubernetes-first deployment.

## Relationship To Autonomous Runnable Setup

The autonomous runnable setup EPIC defines the guarded setup path for a local
Linux/WSL Docker Swarm-first environment. Service access and Vaultwarden may
become part of a selected runnable profile only after implementation provides
test-backed stack contracts, credential-source validation, persistence
ownership, readiness evidence, and documentation synchronized with actual
behavior.

Until then, the current implementation state remains:

```text
NO, REQUIREMENT BASELINE ONLY
```

## Mandatory EPIC Question

Does the implementation currently provide the service-access dashboard and
Vaultwarden stack?

```text
NO, REQUIREMENT BASELINE ONLY
```

The repository currently contains the workflow and governance baseline. It
does not contain a committed service-access compose stack, Vaultwarden stack,
dashboard asset, route, Portainer-managed stack wiring, service readiness
verification, or live deployment evidence for this capability.

## Intent

Tiny Swarm World should provide a local service-access capability that helps
operators understand:

- which configured services are expected in the selected profile;
- how each service should be reached;
- whether reachability is confirmed, blocked, unknown, or failed;
- which credential entry is needed for each service;
- where an authorized operator can reveal or copy the password value in
  Vaultwarden.

The service-access dashboard must link or refer to Vaultwarden credential
items. Vaultwarden's authenticated UI is the only approved surface for
password reveal or copy behavior.

## Scope

In scope:

- Deployment-owned Docker Swarm stack planning for a service-access dashboard
  and Vaultwarden.
- NGINX-first routing as the current repository-backed direction.
- Portainer-managed stack create/update only after Portainer is reachable.
- A dashboard that shows service names, access routes, reachability state,
  credential labels, and Vaultwarden item references.
- Vaultwarden as the credential store and password-visible UI.
- Setup preflight and manifest planning for required ports and secret source
  names.
- Static and mocked tests for stack contracts, YAML, preflight, deployment
  planning, and secret-safety behavior.
- Documentation and arc42/ADR synchronization.

Out of scope:

- Live deployment during requirement-baseline slices.
- Claiming Vaultwarden, dashboard, routing, or service reachability as
  implemented before evidence exists.
- Displaying, caching, logging, exporting, or persisting password values
  outside Vaultwarden's authenticated UI.
- Committed Vaultwarden admin token values, default passwords,
  credential-bearing URLs, host-specific IP addresses, or local filesystem
  paths.
- React, TypeScript, Vite, TSX/JSX, or browser frontend project setup in the
  repository.
- Traefik implementation without a later ADR and tests.
- TLS or certificate automation without a later ADR.
- Kubernetes-first deployment.

## Credential And Visibility Model

Password values must be visible to authorized operators. The approved
visibility model is:

- Vaultwarden stores credential values.
- Vaultwarden's authenticated UI provides reveal/copy behavior for password
  values.
- The service-access dashboard shows credential labels, missing or configured
  source status, and Vaultwarden item references only.
- The service-access dashboard does not display, cache, export, log, or
  persist password values.
- Required secret names may be documented, for example
  `TSW_VAULTWARDEN_ADMIN_TOKEN`.
- Required secret values must come from operator-supplied environment
  variables, command-line inputs that do not persist values, or ignored local
  secret files.

## Runnable State Requirements

The service-access capability can be considered runnable only when all of
these facts are verified through tests or explicit live smoke evidence:

- the service-access stack contract is registered in the selected profile;
- Vaultwarden has a persistent data volume with documented ownership;
- Vaultwarden admin-token source is defined and contains no committed default;
- Vaultwarden backup and restore behavior is documented;
- stack rollback behavior is documented, including whether credential data is
  preserved or removed;
- HTTP routing avoids collision with the current Swagger/NGINX port `80`
  binding;
- the dashboard can reach its configured service catalog without embedding
  secrets;
- service reachability state is based on observed-state or HTTP evidence;
- unknown reachability is not rendered as healthy;
- evidence is redacted and does not persist raw command output, passwords,
  tokens, local paths, local IP addresses, or environment payloads.

## Acceptance Criteria

- This EPIC is linked from system-unification and autonomous setup EPICs.
- The ADR for service access and Vaultwarden exists and is indexed in arc42.
- Credential display policy is explicit: password values are visible only
  through Vaultwarden's authenticated UI.
- The dashboard is explicitly a service-access infrastructure GUI, not a
  repository React app.
- Vaultwarden bootstrap, persistence, backup, admin-token rotation, and
  rollback responsibilities are decision-recorded before implementation
  claims production-like behavior.
- NGINX-first routing is accepted as the baseline direction, with port or
  shared-ingress details deferred to the routing slice.
- Default verification remains static or mocked and must not run live
  infrastructure commands.
- Documentation uses Linux/WSL and POSIX wording.

## Non-Functional Requirements

- Linux/WSL-only operation remains the baseline.
- Docker Swarm remains the runtime target.
- Python automation remains the architecture driver.
- Service stack behavior stays inside the Deployment responsibility boundary.
- Verification must fail closed when credential sources, persistence, routing,
  or readiness evidence are missing.
- Dashboard status text must not rely on color alone.
- Local development may use HTTP only when documented as local/dev scope.
  Wider exposure, TLS, certificate automation, or external access needs later
  ADR coverage.

## Risks And Debt

- Existing compatibility assets contain legacy password-like defaults for some
  services. This EPIC does not migrate them automatically and must not copy
  those defaults into the new dashboard or Vaultwarden baseline.
- Vaultwarden admin-token ownership, rotation, persistence, backup, and
  rollback are blockers before production-like claims.
- Routing can collide with the current Swagger/NGINX port `80` binding unless
  Slice 02 resolves the ingress model.
- Portainer stack upload may not transfer referenced dashboard or NGINX files,
  so asset packaging or preparation must be decided before compose execution.
- Service reachability can be misleading unless it is tied to observed-state
  evidence.

## Stop Conditions

Stop execution when:

- password values would be shown outside Vaultwarden's authenticated UI;
- Vaultwarden admin-token source, persistence, backup, rotation, or rollback
  is undefined;
- routing would reuse port `80` without a shared-ingress or alternate-port
  decision;
- Traefik is selected without ADR and tests;
- Portainer becomes a bootstrap dependency for Portainer;
- service reachability is claimed without observed evidence;
- documentation claims this capability is implemented before code, config, and
  verification evidence exist;
- implementation would require live infrastructure commands without explicit
  user approval;
- architecture or quality gates would be weakened.
