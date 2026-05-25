# Workflow: Service Access Dashboard And Vaultwarden

## Executive Summary

This workflow creates the governed implementation plan for adding a
Portainer-managed service-access stack to Tiny Swarm World.

The target is a Docker Swarm-first stack, created with the same repository
patterns as the existing service stacks: compose definitions under
`infra/config/compose`, optional image or runtime assets under `infra/compose`,
deployment contracts through the existing Python automation, and default
verification through mocked or static checks.

The workflow plans:

- a service-access dashboard GUI container that lists how configured Tiny
  Swarm World services are reached;
- a Vaultwarden container for credential storage;
- dashboard credential links that lead operators to Vaultwarden items;
- password values visible to authorized operators through the authenticated
  Vaultwarden UI, not duplicated as plaintext in the service-access dashboard,
  compose files, logs, or evidence;
- NGINX-first HTTP routing, because the repository already contains a
  Swagger/NGINX pattern and has no Traefik surface;
- Portainer as the preferred post-bootstrap stack management surface, not as
  the HTTP router and not as its own bootstrap dependency.

No live infrastructure command may run during workflow creation. Future
workflow execution must not run Multipass, Docker Swarm, compose deployments,
Portainer, Vaultwarden, NGINX, Traefik, or service bootstrap commands unless a
slice explicitly owns that behavior and the user provides live-infrastructure
consent.

## Target Picture

### Verified Baseline At Workflow Creation

- Active workflow version:

```text
service-access-vaultwarden-dashboard-v1.0.0
```

- Active workflow branch:

```bash
feature/workflow-access-vaultwarden-dashboard-20260525
```

- Root `AGENTS.md` defines Tiny Swarm World as Linux/WSL-only, Python
  automation, hexagonal architecture, and Docker Swarm-first.
- Root `QUALITY.md` defines the full quality gate:

```bash
python3 tools/quality_gate.py quality
```

- Existing compose stacks live under `infra/config/compose/<stack>/docker-compose.yml`.
- Existing runtime assets live under `infra/compose/<stack>/**`.
- Existing default service contracts cover Portainer, Nexus, Jenkins,
  RabbitMQ, SonarQube, and Swagger/NGINX.
- Portainer-managed service-stack planning already excludes Portainer itself
  to avoid a bootstrap cycle.
- Swagger/NGINX currently publishes HTTP port `80`; a new HTTP-facing service
  must not silently reuse that port.
- Portainer stack upload currently sends compose content. Additional NGINX or
  dashboard assets must be packaged into an image, prepared through an
  explicit asset boundary, or avoided by using image-native configuration.
- No React frontend build surface is present. The dashboard is an
  infrastructure service GUI, not a new repository React application.
- No Vaultwarden stack or credential-vault contract exists yet.

### Target Outcome

The completed workflow execution should produce:

- a documented requirement and security baseline for the service-access
  dashboard and Vaultwarden;
- an ADR or ADR-equivalent decision when the implementation changes the
  default service set, credential-source model, routing model, persistence
  model, or TLS stance;
- NGINX-first routing with an explicit port or shared-ingress decision that
  avoids collision with the current Swagger/NGINX port `80` binding;
- Portainer-managed stack contracts for the new service-access stack after
  Portainer is reachable;
- password values visible to authorized operators in Vaultwarden's
  authenticated reveal/copy flow;
- compose and optional runtime/image assets that are deterministic,
  Swarm-compatible, and free of committed secrets;
- Python domain, application, and infrastructure changes that preserve
  existing port/adaptor boundaries;
- tests that load the new compose stack, verify stack contracts, reject
  committed secret values, and use fakes for Portainer and Swarm behavior;
- dashboard behavior that displays service reachability state or access method
  only when the evidence source is test-backed;
- documentation synchronized with actual implemented behavior, without
  presenting planned deployment success as already verified.

## Requirement Clarification Record

Original request, normalized to ASCII:

```text
workflow create with subagents:

Create another container using the same technique as the other containers.
This container includes a GUI that shows which server is reachable and which
passwords are needed.

For passwords:
- Vaultwarden as container
- HTTP via NGINX/Traefik

Choose what is better for routing. If this can be solved with Portainer, that
would be preferred.
```

Interpreted intent:

- Create a new active workflow with delegated subagent review.
- Plan a new service-access dashboard and credential-vault capability.
- Use existing Docker Swarm, Portainer-managed stack, compose repository, and
  Python deployment-contract patterns.
- Prefer NGINX routing because repository evidence supports NGINX and not
  Traefik.
- Keep Vaultwarden as the credential store and the password-visible UI.
- Keep the service-access dashboard focused on service reachability, access
  routes, credential labels, and links into Vaultwarden.

Change type:

- FULL_PATH workflow creation for deployment configuration, credential-source
  handling, routing, Python deployment contracts, tests, and documentation.

Affected process strand:

- Service stack deployment and setup readiness extension.

Affected architecture area:

- Deployment boundary, service stack contracts, compose assets, optional
  artifact publishing, setup preflight manifest, Portainer stack management,
  reverse-proxy routing, credential-source handling, service readiness
  verification, documentation, arc42, and ADR index.

Explicit requirements:

- Use subagents.
- Create a workflow.
- Add another container or stack using the same technique as existing
  containers.
- Provide a GUI showing which servers or services are reachable and what
  credentials are needed.
- Make password values visible to authorized operators.
- Use Vaultwarden as a container for password handling.
- Route HTTP through NGINX or Traefik.
- Prefer Portainer if feasible.

Implicit requirements:

- Preserve Linux/WSL-only operation and POSIX command examples.
- Preserve Docker Swarm-first deployment.
- Preserve hexagonal architecture.
- Keep concrete adapter construction in
  `src/tiny_swarm_world/infrastructure/composition.py`.
- Keep application services dependent on ports, not infrastructure adapters.
- Keep runtime stack configuration host-neutral.
- Do not commit passwords, tokens, Vaultwarden admin tokens, local paths,
  local IP addresses, or raw command output.
- Use static and mocked tests by default.
- Record service reachability as unknown or blocked unless observed-state or
  HTTP evidence is test-backed.

Accepted assumptions and decisions:

- The feature is a service-access stack containing at least a dashboard
  service and Vaultwarden. NGINX may be part of the stack or shared ingress,
  depending on the port decision in Slice 02.
- Password values must be visible in Vaultwarden's authenticated UI. The
  service-access dashboard may show credential names, source status, and
  Vaultwarden item links, but must not duplicate or cache password values.
- NGINX is the default routing direction because Swagger/NGINX exists and no
  Traefik configuration exists. Traefik requires a later ADR-level decision.
- Portainer is preferred for post-bootstrap stack create/update. Initial
  bootstrap must avoid depending on Portainer before Portainer is reachable.
- The workflow extends the autonomous runnable setup and system-unification
  EPICs. It does not replace them.
- The regenerated `documentation/workflow/**` directory is intentional under
  the workflow-create regeneration rule.

Non-goals:

- No live deployment during workflow creation.
- No plaintext secrets in the service-access dashboard, compose files, logs,
  documentation, or evidence. Vaultwarden's authenticated UI is the approved
  password-visible surface.
- No new React, TypeScript, Vite, or browser frontend project in the
  repository.
- No Java, Maven, Spring Boot, or Kubernetes-first pivot.
- No direct promotion of legacy scripts as deployment entry points.
- No TLS or certificate automation unless a later ADR accepts that contract.
- No Traefik implementation unless an ADR and tests deliberately add it.

Risks:

- Credential leakage through dashboard content, compose defaults, logs, or
  evidence.
- A circular bootstrap if Vaultwarden credentials are needed before
  Vaultwarden is reachable.
- False health claims if reachability is inferred without observed evidence.
- Port collision with the existing Swagger/NGINX port `80`.
- Portainer stack upload missing runtime assets that are referenced by mounted
  NGINX or dashboard files.
- Security risk from exposing Vaultwarden over unauthenticated plain HTTP
  beyond the local development boundary.
- Scope drift into a browser frontend project.

Open questions:

- None blocking for workflow creation.

Questions intentionally delegated to slices:

- Whether service access should use a shared NGINX ingress or a non-conflicting
  published port.
- Whether dashboard assets are image-packaged, mounted through an explicit
  asset preparation boundary, or provided by an existing image-native
  dashboard.
- Whether Vaultwarden becomes part of the default runnable service set or an
  optional service profile.
- Which exact service names and credential item names the dashboard lists.

Blocking questions:

- None. Any answer that would require showing raw passwords outside
  authenticated Vaultwarden UI, reusing port `80` without a routing decision,
  using Traefik without ADR review, or running live infrastructure defaults to
  a stop condition.

Confidence level:

```text
91 percent
```

Decision:

```text
READY_FOR_WORKFLOW
```

## Execution Profile

```text
executionProfile=FULL_PATH
reason=The workflow can affect deployment behavior, service contracts, routing,
credential handling, persistence, Python wiring, tests, arc42, ADRs, and
operator documentation.
requiredFullReviews=Senior Requirement Engineer, Senior System Architect,
Senior Python Automation Developer, Senior Tester, Senior DevOps Engineer,
Senior Documentation Engineer, Security review for credential handling
allowedImpactChecks=Senior React Frontend Developer as N/A React scope guard
requiredQualityChecks=git diff --check for workflow creation; targeted tests
per slice; python3 tools/quality_gate.py quality before final implementation
release when practical
stopConditions=secrets committed, live commands required without consent,
routing ownership unclear, Traefik selected without ADR, port 80 conflict
unresolved, React project introduced, or architecture boundaries weakened
```

## Subagent Review Summary

Senior Requirement Engineer:

- Raised refinement risks around GUI scope, credential display, reachability
  source, routing, TLS, Vaultwarden bootstrap, and EPIC extension.
- Workflow resolves these as explicit assumptions, non-goals, slice decisions,
  and stop conditions.

Senior System Architect:

- Recommends NGINX first based on existing Swagger/NGINX assets and no Traefik
  evidence.
- Confirms Portainer should orchestrate stacks, not route HTTP.
- Recommends Deployment-owned stack contracts, not a new microservice.

Senior Python Automation Developer:

- Flags the current Swagger/NGINX port `80` binding as a required routing
  decision.
- Flags Portainer stack upload as compose-content-only, so mounted assets need
  image packaging or explicit asset preparation.
- Lists domain, preflight, deployment, composition, artifact, and test areas
  likely affected.

Senior React Frontend Developer:

- Confirms no React frontend repository scope exists.
- Treats the role as an N/A impact check and scope guard.
- Allows an infrastructure-provided GUI only if no React/browser build surface
  is introduced. Password values may be shown only by Vaultwarden's
  authenticated UI.

Senior Tester:

- Recommends regression-first tests for service-stack contracts, preflight,
  compose repository loading, fake Portainer deployment, routing decisions,
  composition, and secret handling.
- Confirms no live infrastructure belongs in default verification.

## Architecture Constraints

- Domain code may hold stack names, credential-source identifiers, and
  validation rules. It must not import YAML parsers, Docker clients,
  Portainer clients, HTTP clients, file managers, logging setup, or dependency
  injection containers.
- Application services may orchestrate ports and domain objects. They must not
  embed shell, Docker, Portainer HTTP, NGINX config generation, or filesystem
  asset-transfer details directly.
- Infrastructure adapters own YAML parsing, HTTP calls, command execution,
  file management, NGINX assets, Docker image publishing, and Portainer
  client behavior.
- `src/tiny_swarm_world/infrastructure/composition.py` remains the concrete
  wiring root.
- `src/tiny_swarm_world/__main__.py` remains thin.
- The service-access stack is a deployment stack, not a new microservice or
  repository frontend project.
- Vaultwarden credential values are operator-owned secrets. Committed files
  may contain required secret names, never secret values.

## Python Automation Assessment

Likely implementation areas:

- `src/tiny_swarm_world/domain/deployment/service_stack_contract.py`
- `src/tiny_swarm_world/domain/preflight/setup_manifest.py`
- `src/tiny_swarm_world/application/services/deployment/service_stack_plan.py`
- `src/tiny_swarm_world/application/services/deployment/ensure_service_stack.py`
- `src/tiny_swarm_world/application/services/deployment/verify_swarm_service_readiness.py`
- `src/tiny_swarm_world/infrastructure/composition.py`
- `src/tiny_swarm_world/domain/artifacts/container_image_contract.py` only if
  a custom dashboard image is introduced.
- `src/tiny_swarm_world/infrastructure/adapters/clients/multipass_container_image_publisher.py`
  only if a custom dashboard image is introduced.

Required boundaries:

- Use `PortComposeFileRepository` for compose lookup.
- Use `PortPortainerClient` for post-bootstrap Portainer stack create/update.
- Use `PortSwarmStackRuntime` or tested HTTP checks for observed readiness.
- Use `PortContainerImagePublisher` only for packaged dashboard assets.
- Keep preflight and setup manifest concerns in domain/application contracts.

## Frontend Assessment

The dashboard request is in scope only as a deployed infrastructure GUI
service.

Out of scope:

- adding `package.json`;
- adding React, TSX/JSX, Vite, browser routers, or frontend state management;
- building a browser application inside the Python repository;
- storing or rendering raw password values outside Vaultwarden's authenticated
  UI.

The dashboard must be usable without color alone, distinguish unknown from
reachable, show source/freshness for status where available, and display
credential requirement labels or Vaultwarden item references only.

## Security And Credential Requirements

- Vaultwarden may store credential values and must provide the authenticated
  UI where authorized operators can reveal or copy password values.
- The service-access dashboard may show credential names, missing/present
  status, and Vaultwarden item references. It must not display, cache, log, or
  export password values itself.
- Compose files must not include Vaultwarden admin tokens, SMTP passwords,
  basic-auth URLs, API keys, tokens, database passwords, or static password
  defaults.
- Required secret names such as `TSW_VAULTWARDEN_ADMIN_TOKEN` may be recorded
  as configuration requirements.
- Verification evidence must reject raw command output, tokens, passwords,
  Swarm join tokens, local IP addresses, host-specific paths, and environment
  payloads.
- Vaultwarden persistence, backup, admin-token rotation, and rollback must be
  defined before the stack is treated as production-like.

## Test Strategy

Default tests must remain static or mocked.

Targeted commands expected during workflow execution:

```bash
git diff --check
PYTHONPATH=src python3 -m unittest tests.domain.deployment.test_service_stack_contract
PYTHONPATH=src python3 -m unittest tests.domain.preflight.test_preflight_result
PYTHONPATH=src python3 -m unittest tests.application.services.deployment
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml
PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py test
python3 tools/quality_gate.py quality
```

Quality commands must come from `QUALITY.md`. Do not invent mutation-testing,
frontend, Traefik, Docker, or live-smoke gates.

Live smoke validation is optional and separate. It requires explicit user
approval, live consent, a disposable or recoverable local target, and redacted
evidence. It is not part of the default quality gate.

## Ordered Slices

### Slice 01 - Requirement, EPIC, And ADR Baseline

Purpose:

- Establish the service-access requirement baseline.
- Decide whether the feature extends the autonomous runnable setup EPIC.
- Create or update ADR material for default service-set, credential-source,
  persistence, and routing-impact decisions.

```yaml
slice_id: "01"
profile: FULL_PATH
owner: Senior Requirement Engineer
secondary_reviewers:
  - Senior System Architect
  - Senior Security Sandbox Engineer
  - Senior Documentation Engineer
  - Senior Tester
affected_files:
  - documentation/epics/service-access-dashboard-vaultwarden.md
  - documentation/epics/autonomous-runnable-setup.md
  - documentation/architecture/adr-service-access-dashboard-vaultwarden.adoc
  - documentation/arc42/09_architecture_decisions.adoc
  - documentation/arc42/11_risks_and_debt.adoc
affected_modules: []
affected_contracts:
  - service-access-requirement-baseline
  - vaultwarden-credential-source-contract
  - default-service-set-decision
dependencies: []
parallel_group: A
file_locks:
  - documentation/epics/**
  - documentation/architecture/**
  - documentation/arc42/**
contract_locks:
  - credential-source-contract
  - service-access-scope-contract
architecture_locks:
  - deployment-boundary
  - credential-evidence-redaction
quality_gates:
  targeted:
    - git diff --check
  required:
    - git diff --check
documentation:
  arc42: documentation/arc42/09_architecture_decisions.adoc; documentation/arc42/11_risks_and_debt.adoc
  adr: documentation/architecture/adr-service-access-dashboard-vaultwarden.adoc
stop_conditions:
  - Password values would be displayed outside authenticated Vaultwarden UI, logged, committed, or persisted as evidence.
  - Vaultwarden persistence or admin-token ownership is undefined.
  - The feature conflicts with the autonomous runnable setup EPIC.
```

Allowed write scope:

- Requirement, EPIC, ADR, arc42 risk/index documentation only.

Done criteria:

- Credential display policy is explicit.
- Vaultwarden bootstrap, persistence, backup, and rollback responsibilities
  are at least decision-recorded.
- Dashboard scope is defined as infrastructure GUI, not React repository app.
- `git diff --check` passes.

### Slice 02 - Routing, Port, And Asset Packaging Decision

Purpose:

- Record the NGINX-first routing decision.
- Resolve the port `80` collision with current Swagger/NGINX before compose
  assets are created.
- Decide whether dashboard and NGINX assets are image-packaged, prepared
  through an explicit asset boundary, or avoided through image-native config.

```yaml
slice_id: "02"
profile: FULL_PATH
owner: Senior System Architect
secondary_reviewers:
  - Senior DevOps Engineer
  - Senior Python Automation Developer
  - Senior Tester
affected_files:
  - documentation/architecture/adr-service-access-dashboard-vaultwarden.adoc
  - documentation/arc42/07_deployment_view.adoc
  - documentation/deployment/system.adoc
affected_modules: []
affected_contracts:
  - reverse-proxy-routing
  - service-access-ingress
  - asset-packaging-boundary
dependencies:
  - "01"
parallel_group: B
file_locks:
  - documentation/architecture/**
  - documentation/arc42/07_deployment_view.adoc
  - documentation/deployment/**
contract_locks:
  - reverse-proxy-routing
  - port-allocation
architecture_locks:
  - deployment-boundary
  - live-operation-surface
quality_gates:
  targeted:
    - git diff --check
  required:
    - git diff --check
documentation:
  arc42: documentation/arc42/07_deployment_view.adoc
  adr: documentation/architecture/adr-service-access-dashboard-vaultwarden.adoc
stop_conditions:
  - The workflow would publish a second service on port 80 without a shared-ingress decision.
  - Traefik is selected without ADR and test scope.
  - NGINX or dashboard config depends on files Portainer cannot deploy.
```

Allowed write scope:

- Routing and deployment documentation, ADR updates, and port-allocation
  decision artifacts only.

Done criteria:

- NGINX-first routing is documented.
- Traefik is rejected or moved behind explicit ADR scope.
- Port `80` collision is resolved before YAML implementation.
- Asset transfer or packaging boundary is explicit.

### Slice 03 - Compose Stack And Secret-Safe Configuration

Purpose:

- Add the service-access and Vaultwarden compose definitions using existing
  stack layout.
- Keep compose files host-neutral and Swarm-compatible.
- Avoid committed secret values.

```yaml
slice_id: "03"
profile: FULL_PATH
owner: Senior DevOps Engineer
secondary_reviewers:
  - Senior Python Automation Developer
  - Senior Security Sandbox Engineer
  - Senior Tester
affected_files:
  - infra/config/compose/service-access/docker-compose.yml
  - infra/compose/service-access/**
  - infra/compose/README.md
  - documentation/system/live-operation-surfaces.adoc
affected_modules:
  - infra/config/compose
  - infra/compose
affected_contracts:
  - service-access-stack-compose
  - vaultwarden-secret-and-data-contract
  - reverse-proxy-routing
dependencies:
  - "01"
  - "02"
parallel_group: C
file_locks:
  - infra/config/compose/service-access/**
  - infra/compose/service-access/**
  - infra/compose/README.md
  - documentation/system/live-operation-surfaces.adoc
contract_locks:
  - service-access-stack
  - vaultwarden-secret-and-data-contract
  - reverse-proxy-routing
architecture_locks:
  - deployment-boundary
  - live-operation-surface
quality_gates:
  targeted:
    - PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml
    - git diff --check
  required:
    - python3 tools/quality_gate.py test
documentation:
  arc42: documentation/arc42/07_deployment_view.adoc
  adr: documentation/architecture/adr-service-access-dashboard-vaultwarden.adoc
stop_conditions:
  - Compose files contain static passwords, tokens, local paths, or host IP addresses.
  - Compose publishes a conflicting port.
  - Compose relies on unprepared mounted assets.
  - Tests would deploy containers or contact Portainer.
```

Allowed write scope:

- New service-access compose directory, service-access runtime assets, live
  operation surface docs, and compose README notes.

Done criteria:

- New YAML loads through the compose repository.
- Required services are named deterministically.
- Named volumes/networks are Swarm-compatible.
- Secret values are absent.
- No live deployment runs.

### Slice 04 - Domain, Preflight, And Deployment Contracts

Purpose:

- Add service-stack and setup manifest contracts for the new service-access
  capability.
- Wire post-bootstrap Portainer-managed planning deliberately.
- Preserve fail-closed verification behavior.

```yaml
slice_id: "04"
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers:
  - Senior System Architect
  - Senior Tester
affected_files:
  - src/tiny_swarm_world/domain/deployment/service_stack_contract.py
  - src/tiny_swarm_world/domain/preflight/setup_manifest.py
  - src/tiny_swarm_world/application/services/deployment/service_stack_plan.py
  - src/tiny_swarm_world/application/services/deployment/ensure_service_stack.py
  - src/tiny_swarm_world/application/services/deployment/verify_swarm_service_readiness.py
  - src/tiny_swarm_world/infrastructure/composition.py
  - tests/domain/deployment/test_service_stack_contract.py
  - tests/domain/preflight/test_preflight_result.py
  - tests/application/services/deployment/test_service_stack_plan.py
  - tests/application/services/deployment/test_ensure_service_stack.py
  - tests/application/services/deployment/test_verify_swarm_service_readiness.py
  - tests/infrastructure/test_composition.py
affected_modules:
  - tiny_swarm_world.domain.deployment
  - tiny_swarm_world.domain.preflight
  - tiny_swarm_world.application.services.deployment
  - tiny_swarm_world.infrastructure.composition
affected_contracts:
  - service-stack-contract
  - setup-manifest-contract
  - deployment-apply-contract
  - deployment-verify-contract
dependencies:
  - "03"
parallel_group: D
file_locks:
  - src/tiny_swarm_world/domain/deployment/**
  - src/tiny_swarm_world/domain/preflight/**
  - src/tiny_swarm_world/application/services/deployment/**
  - src/tiny_swarm_world/infrastructure/composition.py
  - tests/domain/deployment/**
  - tests/domain/preflight/**
  - tests/application/services/deployment/**
  - tests/infrastructure/test_composition.py
contract_locks:
  - service-stack-contract
  - setup-manifest-contract
  - deployment-apply-contract
  - deployment-verify-contract
architecture_locks:
  - hexagonal-domain-independence
  - application-port-dependency
  - composition-root
quality_gates:
  targeted:
    - PYTHONPATH=src python3 -m unittest tests.domain.deployment.test_service_stack_contract
    - PYTHONPATH=src python3 -m unittest tests.domain.preflight.test_preflight_result
    - PYTHONPATH=src python3 -m unittest tests.application.services.deployment
    - PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition
    - python3 tools/quality_gate.py arch-tests
  required:
    - python3 tools/quality_gate.py test
documentation:
  arc42: documentation/arc42/05_building_blocks.adoc; documentation/arc42/07_deployment_view.adoc
  adr: documentation/architecture/adr-service-access-dashboard-vaultwarden.adoc
stop_conditions:
  - Domain imports infrastructure or YAML/HTTP/Docker details.
  - Application services embed Portainer HTTP, shell, Docker, or filesystem transfer details.
  - Portainer becomes a bootstrap dependency for itself.
  - Verification reports reachable without observed evidence.
```

Allowed write scope:

- Deployment/preflight contract code and directly related tests.

Done criteria:

- Stack contracts include the new stack only in the selected service profile.
- Portainer-managed planning is explicit and tested with fakes.
- Setup manifest includes required ports and credential-source names without
  values.
- Architecture tests remain valid.

### Slice 05 - Dashboard UX, Reachability, And Credential References

Purpose:

- Implement or configure the service-access dashboard content.
- Ensure central route links and credential references are deterministic and
  safe.
- Avoid React project scope.

```yaml
slice_id: "05"
profile: FULL_PATH
owner: Senior DevOps Engineer
secondary_reviewers:
  - Senior React Frontend Developer
  - Senior Security Sandbox Engineer
  - Senior Tester
affected_files:
  - infra/compose/service-access/**
  - infra/config/compose/service-access/docker-compose.yml
  - tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py
  - tests/architecture/test_legacy_surface_documentation.py
affected_modules:
  - infra/compose
  - infra/config/compose
affected_contracts:
  - dashboard-service-catalog
  - credential-reference-contract
  - service-readiness-display-contract
dependencies:
  - "03"
  - "04"
parallel_group: E
file_locks:
  - infra/compose/service-access/**
  - infra/config/compose/service-access/**
  - tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py
  - tests/architecture/test_legacy_surface_documentation.py
contract_locks:
  - dashboard-service-catalog
  - credential-reference-contract
architecture_locks:
  - no-react-repository-scope
  - credential-evidence-redaction
quality_gates:
  targeted:
    - PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml
    - python3 tools/quality_gate.py arch-tests
    - git diff --check
  required:
    - python3 tools/quality_gate.py test
documentation:
  arc42: documentation/arc42/07_deployment_view.adoc
  adr: documentation/architecture/adr-service-access-dashboard-vaultwarden.adoc
stop_conditions:
  - package.json, TSX, JSX, Vite, or React project files are introduced.
  - Dashboard displays password values outside Vaultwarden or credential-bearing URLs.
  - Unknown reachability is rendered as healthy.
  - Dashboard assets cannot be delivered by the selected stack mechanism.
```

Allowed write scope:

- Dashboard/runtime assets and static tests for their configuration.

Done criteria:

- Dashboard lists services, access methods, status source/freshness where
  available, and Vaultwarden credential references.
- Dashboard provides a clear route to Vaultwarden where authenticated
  operators can reveal or copy the required password value.
- Unknown, blocked, reachable, unreachable, resource-gated, and
  needs-credentials states are distinguishable without color alone.
- No raw secrets appear in dashboard assets.
- No React build surface is introduced.

### Slice 06 - Documentation, Quality Evidence, And Handoff

Purpose:

- Synchronize user-facing, deployment, arc42, and workflow documentation with
  actual behavior.
- Record verification evidence.
- Prepare handoff to future workflow execution or commit preparation.

```yaml
slice_id: "06"
profile: FULL_PATH
owner: Senior Documentation Engineer
secondary_reviewers:
  - Senior Tester
  - Senior Workflow Architect
  - Senior System Architect
affected_files:
  - README.md
  - documentation/deployment/system.adoc
  - documentation/user_guide/installation.adoc
  - documentation/user_guide/usage.adoc
  - documentation/user_guide/troubleshooting.adoc
  - documentation/arc42/05_building_blocks.adoc
  - documentation/arc42/07_deployment_view.adoc
  - documentation/arc42/10_quality_requirements.adoc
  - documentation/arc42/11_risks_and_debt.adoc
  - documentation/workflow/**
affected_modules: []
affected_contracts:
  - documentation-sync
  - quality-evidence
  - workflow-handoff
dependencies:
  - "01"
  - "02"
  - "03"
  - "04"
  - "05"
parallel_group: F
file_locks:
  - README.md
  - documentation/deployment/**
  - documentation/user_guide/**
  - documentation/arc42/**
  - documentation/workflow/**
contract_locks:
  - documentation-sync
  - quality-evidence
architecture_locks:
  - planned-vs-implemented-documentation
quality_gates:
  targeted:
    - git diff --check
    - python3 tools/quality_gate.py test
  required:
    - python3 tools/quality_gate.py quality
documentation:
  arc42: documentation/arc42/05_building_blocks.adoc; documentation/arc42/07_deployment_view.adoc; documentation/arc42/10_quality_requirements.adoc; documentation/arc42/11_risks_and_debt.adoc
  adr: documentation/architecture/adr-service-access-dashboard-vaultwarden.adoc
stop_conditions:
  - Documentation claims live service reachability without verified evidence.
  - Full quality gate fails or is skipped without recorded justification.
  - Workflow context pack is stale.
```

Allowed write scope:

- Documentation, workflow reports, and quality evidence only.

Done criteria:

- Documentation states what is implemented, blocked, optional, or future work.
- POSIX/Linux/WSL examples are used.
- Quality evidence is recorded exactly.
- Handoff to commit/push is explicit but not performed unless requested.

## Slice Dependency Graph

```text
01 -> 02 -> 03 -> 04 -> 05 -> 06
01 --------> 03
03 --------> 05
04 --------> 06
```

The graph is intentionally mostly sequential because credential policy,
routing, port allocation, and asset packaging must be fixed before parallel
implementation can safely write compose, code, dashboard assets, and docs.

## Parallelization Opportunities

- After Slice 01, a read-only security review may run in parallel with Slice
  02.
- After Slice 02 freezes route and asset packaging contracts, Slice 03 compose
  work and Slice 04 contract-test drafting may be prepared in parallel, but
  writes must remain disjoint.
- Slice 05 can run in parallel with parts of Slice 04 only after the
  dashboard service catalog contract is frozen and file locks do not overlap.
- Slice 06 starts only after previous slices provide verified behavior and
  quality evidence.

## Role And Subagent Ownership Map

| Role | Ownership |
|---|---|
| Senior Workflow Architect | Workflow structure, dependency ordering, metadata, locks, handoff |
| Senior Requirement Engineer | Requirement baseline, EPIC drift, acceptance criteria |
| Senior System Architect | Hexagonal boundaries, routing decision, ADR/arc42 impact |
| Senior Python Automation Developer | Service stack contracts, preflight, deployment wiring |
| Senior DevOps Engineer | Compose assets, NGINX routing, Portainer-managed stack fit |
| Senior React Frontend Developer | N/A React impact guard, dashboard UX safety review |
| Senior Security Sandbox Engineer | Secret handling, Vaultwarden risk, evidence redaction |
| Senior Tester | Targeted tests, quality gates, no-live-infra boundaries |
| Senior Documentation Engineer | README, user guide, deployment, arc42, workflow sync |

## Quality-Gate Expectations

Workflow creation minimum:

```bash
git diff --check
```

Implementation slices:

- Run the nearest targeted tests first.
- Run architecture checks when Python boundaries are touched.
- Run `python3 tools/quality_gate.py test` for behavior/config slices.
- Run `python3 tools/quality_gate.py quality` before final implementation
  release when practical.

No quality gate may create VMs, change networking, initialize Docker Swarm,
deploy stacks, contact Portainer, run Vaultwarden/NGINX/Traefik containers,
or bootstrap service credentials.

## Documentation Synchronization Points

- Slice 01: EPIC, ADR, arc42 decision/risk.
- Slice 02: routing and deployment view.
- Slice 03: compose assets and live-operation surface classification.
- Slice 04: architecture building blocks and deployment contracts.
- Slice 05: dashboard behavior and credential-reference documentation.
- Slice 06: README, deployment docs, user guide, troubleshooting, workflow
  reports, quality evidence.

## Stop Conditions

Stop and report when:

- a live infrastructure command is required without explicit approval;
- secrets, Vaultwarden admin tokens, passwords, credential-bearing URLs, or
  local host details would be committed;
- password values would be shown outside Vaultwarden's authenticated UI;
- a second service would publish port `80` without a shared-ingress decision;
- Traefik is selected without ADR and tests;
- Portainer is made a prerequisite for bootstrapping Portainer;
- service reachability would be claimed without observed evidence;
- domain or application code would import infrastructure concerns;
- React, TypeScript, Vite, or browser frontend project files would be added;
- documentation would describe planned behavior as implemented behavior;
- required quality commands cannot be verified from `QUALITY.md`;
- workflow context-pack hashes are stale.

## Commit And Push Plan

No commit or push is requested by this workflow creation request.

When the user later asks for commit or push preparation:

- inspect `git status --short --branch`;
- review changed files and line-ending noise;
- run the required gates for the changed scope;
- stage only workflow-related files;
- use commit messaging governed by the git commit preparation skills.

## Definition Of Done

- `documentation/workflow/workflow.md` exists and includes complete slice
  metadata.
- `documentation/workflow/context-pack.md` and
  `documentation/workflow/context-pack.json` exist.
- Subagent review findings are reflected in the workflow.
- arc42 impact has been checked and is represented in slice documentation
  requirements.
- Workflow creation verification passes `git diff --check`.
- No live infrastructure command was run.
- No implementation code, stack deployment, or service bootstrap was performed
  during workflow creation.

## Handoff To Workflow Execute

Workflow execution has progressed through Slice 05 on branch
`feature/workflow-access-vaultwarden-dashboard-20260525`. Slice 06 is the
active documentation, quality-evidence and handoff slice.

If execution is resumed, use:

```text
workflow execute with subagents
```

Before execution:

- verify the active branch is
  `feature/workflow-access-vaultwarden-dashboard-20260525`;
- verify the context pack hashes are current;
- verify slice metadata and locks;
- run S3/S3D preflight;
- resume at Slice 06 unless a checkpoint rollback deliberately changes the
  execution state;
- keep writes inside each slice's allowed scope;
- stop on any credential, routing, port, or architecture blocker.

Final publication is checkpoint-only for workflow execution: no `push auto`,
no pull request creation, no merge, no branch cleanup, no force-push and no
push to `main`.

## arc42 Check Status

Checked during workflow creation:

- `documentation/arc42/05_building_blocks.adoc`
- `documentation/arc42/07_deployment_view.adoc`
- `documentation/arc42/09_architecture_decisions.adoc`
- `documentation/arc42/10_quality_requirements.adoc`
- `documentation/arc42/11_risks_and_debt.adoc`

arc42 files are synchronized during workflow execution slices when behavior is
implemented. The post-workflow live smoke test on 2026-05-25 verified the
older service-access route through Swarm node IPs. The current routing baseline
is service-access central NGINX on `http://localhost` with Vaultwarden on
`8086`; it requires a fresh live deployment before browser verification.
