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
visibility. Repository-level compose assets, dashboard/NGINX image assets,
service-stack contracts, setup-manifest requirements, and static tests now
exist. This EPIC does not claim provider-native live deployment, service
readiness, Vaultwarden persistence hardening, backup, restore, or a
live-verified central route for the default `lxc_native` provider.

## Relationship To System Unification

The system-unification EPIC defines Tiny Swarm World as one local Python
automation system with in-process responsibility boundaries:

- Platform;
- Artifacts;
- Deployment;
- Shared;
- Console/status UI.

The service-access dashboard and Vaultwarden capability belongs to the
Deployment responsibility boundary as a Docker Swarm service-stack capability.
It is not a new microservice, not a Spring Boot application, not a React
frontend project, and not a Kubernetes-first deployment.

## Relationship To Autonomous Runnable Setup

The autonomous runnable setup EPIC defines the guarded setup path for a local
Linux/WSL Docker Swarm-first environment. Service access and Vaultwarden are
now selected by the full setup profile as repository assets and contracts, but
the selected profile is runnable only after provider-native deployment,
credential-source validation, persistence ownership, readiness evidence, and
documentation are synchronized with actual behavior.

The current implementation state is:

```text
PARTIAL: ASSETS AND CONTRACTS IMPLEMENTED, LIVE RUNTIME UNVERIFIED
```

## Mandatory EPIC Question

Does the implementation currently provide the service-access dashboard and
Vaultwarden stack?

```text
PARTIAL: REPOSITORY ASSETS AND CONTRACTS ONLY
```

The repository contains the workflow and governance baseline, the
service-access compose stack, image-packaged dashboard and NGINX assets,
service-stack contracts, setup-manifest requirements, and static tests. The
default `lxc_native` path still blocks before provider-native image
publication, stack deployment, and service-readiness verification are
complete. Provider-specific evidence is required before default LXD/Incus
runtime success can be claimed.

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

- Deployment-owned Docker Swarm stack assets and contracts for a
  service-access dashboard and Vaultwarden.
- NGINX-first routing as the current repository-backed direction.
- Portainer-managed stack create/update only after Portainer is reachable.
- A dashboard that shows service names, access routes, reachability state,
  credential labels, and Vaultwarden item references.
- Vaultwarden as the credential store and password-visible UI.
- Setup preflight and manifest requirements for required ports and secret
  source names.
- Static and mocked tests for stack contracts, YAML, preflight, deployment
  planning, and secret-safety behavior.
- Documentation and arc42/ADR synchronization.

Out of scope:

- Live deployment during default quality gates.
- Claiming Vaultwarden, dashboard, routing, or service reachability as
  live-installed or healthy before provider-specific evidence exists.
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
- Required secret-source environment variables may be documented, for example
  `TSW_VAULTWARDEN_ADMIN_TOKEN_SECRET`, which names an external Swarm secret.
- Required secret values must come from operator-supplied environment
  variables, command-line inputs that do not persist values, or ignored local
  secret files.

## Runnable State Requirements

The service-access capability can be considered runnable only when all of
these facts are verified through tests or explicit live smoke evidence:

- the service-access stack contract is registered in the selected profile;
- Vaultwarden has a persistent data volume with documented ownership;
- Vaultwarden admin-token source is defined. The committed default may name
  the external Swarm secret, but no committed default may contain the token
  value itself;
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
- Repository assets and contracts for service-access are present without
  weakening the Deployment responsibility boundary.
- Credential display policy is explicit: password values are visible only
  through Vaultwarden's authenticated UI.
- The dashboard is explicitly a service-access infrastructure GUI, not a
  repository React app.
- Vaultwarden bootstrap, persistence, backup, admin-token rotation, and
  rollback responsibilities are decision-recorded before documentation claims
  production-like behavior.
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
- documentation claims this capability is live-installed, reachable, or
  healthy before provider-specific verification evidence exists;
- implementation would require live infrastructure commands without explicit
  user approval;
- architecture or quality gates would be weakened.
