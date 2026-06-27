# Workflow: Traefik Service Routing Through Central Access Configuration

Version: `workflow-traefik-service-routing-v1.0.0`
Workflow ID: `workflow-traefik-service-routing-20260627`
Created: `2026-06-27`
Issue: `https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/157`
Branch: `feature/workflow-traefik-service-routing-20260627`
Status: `PARTIAL_EXECUTION_REQUIRES_ISSUE_157_COMPLETION`
Evidence Root: `.codex/evidence/workflow-traefik-service-routing-20260627/`

## Executive Summary

Make Traefik the preferred HTTP/HTTPS entrypoint for routed Tiny Swarm World
HTTP services through the central port and access configuration. Reconcile the
current mismatch where `ports.yaml` already assigns Traefik public ingress to
`80/443`, while `services.yml`, rendered Traefik compose and ingress tests still
prefer `10080/10443`.

The workflow keeps default verification static or mocked. Live Docker, Swarm,
LXC, Traefik, DNS, hosts-file, browser and Selenium validation remains opt-in
only and writes redacted local evidence under ignored `.tiny-swarm-world/**`
paths.

Revision note:

- The first execution implemented and verified the static/backend routing
  migration, but it did not fully cover Issue #157.
- The missing scope is now explicit in this workflow: service-oriented
  integration coverage for the full route/evidence matrix and an opt-in
  Selenium browser E2E suite that uses routed Service Access links, performs
  approved login flows where credentials are available, records stable
  per-service success conditions, and writes redacted local evidence.
- This workflow must not be considered complete for Issue #157 until the
  additional slices in this revision are executed or explicitly stopped with
  classified blockers.

## Requirement Clarification Gate

Original Request:

- Setze Issue #157 um.
- Create a dedicated branch.
- Run `workflow create`.
- After successful workflow creation, run `workflow execute`.
- Verify the system from backend and user perspectives after successful
  execution.

Interpreted Intent:

- Implement the issue's Traefik-centered routing migration in a guarded,
  slice-based workflow and verify static/backend behavior plus user-facing
  access-link behavior without running live infrastructure unless explicitly
  enabled.

Change Type:

- Runtime/deployment configuration, domain access model, tests, live-test
  structure and documentation synchronization.

Affected Process Strand:

- `workflow create`, then `workflow execute`.

Affected Architecture Area:

- `domain.ingress`, port registry, service registry, compose rendering,
  setup/preflight manifest, Service Access dashboard links, route/evidence
  tests and deployment documentation.

Explicit Requirements:

- Traefik owns preferred public ingress ports `80` and `443`.
- Retained `10080/10443` ports must be diagnostic, compatibility, fallback,
  rollback or transitional only.
- Service Access links must prefer Traefik-routed host URLs when routing is
  enabled.
- Host-based routes must use service internal target ports behind Traefik.
- `exposedByDefault=false` is required and `--api.insecure=true` is forbidden.
- Pulsar broker TCP must not become an HTTP route.
- RabbitMQ must not be generated.
- Default tests must stay static or mocked.
- Live Selenium/browser validation must be opt-in and redacted.

Implicit Requirements:

- Preserve Linux/WSL-only and Docker Swarm-first project direction.
- Preserve the managed LXC through LXD/Incus default provider direction.
- Keep Service Access as a dashboard capability.
- Keep secret and credential display safety unchanged.
- Use existing YAML adapters and domain value objects rather than ad hoc
  string manipulation.
- Update tests because configuration, routing, service links and evidence
  behavior change.

Assumptions:

- Issue #156 direct published-port baseline is already represented locally by
  `infra/config/ports.yaml`, compose rendering tests and setup manifest tests.
- Existing Traefik labels in service compose files are the starting point and
  should be completed rather than replaced by a new gateway policy.
- Route generation may remain static/configuration-driven in this workflow;
  live route success is claimed only when the opt-in live suite is run.
- Selenium test files may be grouped by existing repository conventions if the
  suite remains service-oriented and default-skipped.

Non-Goals:

- No LXC/Incus installation change.
- No Docker installation or Swarm bootstrap behavior change.
- No Kubernetes support.
- No RabbitMQ metadata or routes.
- No automatic Windows hosts-file management.
- No Linux `/etc/hosts` or DNS resolver mutation.
- No automatic TLS or CA lifecycle implementation.
- No committed live evidence under `.tiny-swarm-world/evidence/**`.

Risks:

- Existing tests and documentation still encode `10080/10443` as preferred
  HTTPS ingress.
- Service Access NGINX currently exposes direct dashboard routes and could
  continue to present legacy direct ports as preferred links.
- Traefik label coverage may be uneven across service compose files.
- Live browser success can be confused with static readiness unless evidence
  wording is strict.

Open Questions:

- None blocking. Live validation is explicitly outside default execution and
  must report skipped/not-run rather than success without consent.

Blocking Questions:

- None.

Confidence Level:

- 92 percent.

Decision:

- `READY_FOR_WORKFLOW`

## Five-Role Review

Senior Requirement Engineer:

- The issue has detailed acceptance criteria and identifies ADR-backed
  architecture authority. Implementation must keep direct port compatibility
  separate from preferred Traefik route behavior.

Senior System Architect:

- The work belongs in domain ingress/access value objects, infrastructure YAML
  adapters/rendering, and deployment configuration. Domain may model desired
  routes and redacted evidence but must not import Docker, YAML, HTTP clients
  or browser tooling.

Senior Python Automation Developer:

- Reuse `PortRegistry`, `DesiredHttpsIngress`, compose repository rendering and
  setup manifest seams. Avoid a broad deployment rewrite; migrate the
  conflicting port authority and add tests around route semantics.

Senior React Frontend Developer:

- No React/browser frontend module is present. User-facing scope is the static
  Service Access dashboard and live browser test structure.

Senior Tester:

- Add or update deterministic tests for gateway port authority, Traefik compose
  rendering, Service Access preferred URLs, route evidence, skipped live
  behavior and password-value safety. Live Selenium remains default-skipped.

## Issue #157 Acceptance Traceability

Implemented and verified by the first execution:

- Central gateway/public ingress policy is consistent for `80/443` across
  domain desired state, service registry, Traefik compose, compose rendering,
  setup/preflight expectations, README and arc42.
- Retained `10080/10443` gateway values are no longer preferred ingress and
  are classified as diagnostic/fallback/compatibility where referenced.
- Preferred Service Access links do not use diagnostic gateway suffixes and
  use routed host URLs such as `https://service-access.tsw.local`.
- Traefik internal entrypoints remain `web :80` and `websecure :443`.
- Traefik Swarm discovery keeps `exposedByDefault=false`.
- `--api.insecure=true` is not present.
- Representative HTTP routes use internal service target ports behind Traefik:
  Portainer, Jenkins, SonarQube, Nexus, Swagger, Infisical, Service Access,
  Pulsar Manager GUI and optional Pulsar Admin/API.
- Pulsar broker TCP is not modelled as a normal HTTP route.
- RabbitMQ routes and metadata are not generated.
- Service Access keeps credential display safety; password values are not
  rendered or committed.
- Default quality gate passes without live infrastructure.

Still required for full Issue #157 completion:

- Service-oriented integration tests must be expanded so every enabled routed
  service can be understood and run independently, even if the repository keeps
  shared helpers or grouped files for maintainability.
- The effective access model must expose a structured evidence payload that
  includes gateway/public ports, diagnostic fallback ports, route map, internal
  target ports, Service Access preferred URL source, fallback classification,
  skipped-route reasons and placeholders for per-service live E2E status.
- HTTP health-check expectations must consume the effective Traefik access
  model where routing is enabled, while keeping direct checks explicit
  fallback/debug validation.
- An opt-in Selenium browser E2E suite must exist under `tests/live`, use:

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
```

- When live validation is explicitly enabled, Selenium must open every
  generated routed Service Access link for the active profile.
- For enabled routed services that require authentication and have approved
  credentials available, Selenium must complete login and verify a stable
  success condition.
- The live suite must record redacted per-service evidence under
  `.tiny-swarm-world/evidence/solid-typed-evidence/e2e/` and produce a summary
  of passed, failed and skipped links.
- Skipped live E2E is allowed only for explicit reasons: missing consent,
  disabled service, intentionally unconfigured route, unavailable approved
  credential source, or no login flow.
- Prometheus, Grafana, Tiny Swarm frontend and Tiny Swarm API routes must be
  tested as skipped/not generated unless an active profile/configured route
  enables them.

Acceptance decision:

- Current execution status is `PARTIAL`.
- Static/backend behavior is accepted.
- Full Issue #157 acceptance remains blocked until the follow-up slices below
  are executed and verified.

## Target Picture

Verified baseline:

- Branch is `feature/workflow-traefik-service-routing-20260627`.
- `infra/config/ports.yaml` assigns `traefik-http` to external `80` and
  `traefik-https` to external `443`.
- `infra/config/services.yml` still lists Traefik ingress published ports
  `10080` and `10443`.
- `infra/config/compose/traefik/docker-compose.yml` publishes `10080 -> 80`
  and `10443 -> 443`.
- `domain.ingress.DesiredHttpsIngress` still requires public ports
  `(10080, 10443)`.
- Existing live browser tests are opt-in and currently include direct
  localhost routes.

Target outcome:

- `80/443` are the single preferred public Traefik ingress authority across
  domain model, registry, service registry, compose rendering, setup/preflight
  expectations, tests and docs.
- `10080/10443`, if retained in any artifact, are classified as diagnostic,
  compatibility, fallback, rollback or transitional and are not preferred
  Service Access links.
- Service Access preferred links use host-based Traefik URLs such as
  `https://service-access.tsw.local` and `https://jenkins.tsw.local` when
  routing is enabled.
- Route evidence is structured and redacted, including skipped-route reasons.
- Default verification is static/mocked. Opt-in live Selenium opens routed
  URLs only when explicit live prerequisites are present.

## Scope

In scope:

- `infra/config/ports.yaml`
- `infra/config/services.yml`
- `infra/config/compose/**/docker-compose.yml`
- `infra/config/compose/service-access/dashboard/index.html`
- `src/tiny_swarm_world/domain/ingress/**`
- `src/tiny_swarm_world/domain/network/**`
- `src/tiny_swarm_world/domain/preflight/**`
- `src/tiny_swarm_world/infrastructure/adapters/repositories/**`
- `src/tiny_swarm_world/__main__.py`
- `tests/domain/**`
- `tests/infrastructure/**`
- `tests/integration/**`
- `tests/live/**`
- `documentation/architecture/adr-traefik-https-ingress-existing-ca.adoc`
- `documentation/arc42/07_deployment_view.adoc`
- `documentation/arc42/09_architecture_decisions.adoc`
- `documentation/deployment/system.adoc`
- `README.md`
- `documentation/workflow/**`
- `.codex/evidence/workflow-traefik-service-routing-20260627/**`

Out of scope:

- Live LXC, Incus, LXD, Docker, Swarm, Traefik, DNS, hosts-file, browser or
  Selenium execution without explicit operator opt-in.
- Service extraction or microservice boundary changes.
- Browser React frontend implementation.
- Automatic certificate lifecycle.
- Direct Docker published-port redo from #156 beyond compatibility
  classification needed for #157.

Architecture constraints:

- Preserve hexagonal dependency direction.
- Domain can model desired access, routes and redacted evidence only.
- Application services orchestrate domain objects through ports.
- Infrastructure owns YAML, compose rendering, Docker/Swarm details, HTTP,
  browser and evidence-file adapters.
- Entry point remains thin.

## Python Automation Assessment

This is Python automation and configuration work. The implementation should
prefer small domain value objects and existing YAML repositories over broad
deployment rewrites. Tests must prove that central configuration drives route
and link behavior.

## Frontend Assessment

No React frontend exists. The user-facing behavior is the static Service
Access dashboard and browser-visible routed URLs. Keep the dashboard static and
credential-safe.

## Test Strategy

Targeted checks during execution:

- `PYTHONPATH=src python3 -m unittest tests.domain.ingress.test_desired_state`
- `PYTHONPATH=src python3 -m unittest tests.domain.preflight.test_preflight_result`
- `PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml`
- `PYTHONPATH=src python3 -m unittest tests.test_package_entrypoint`
- `PYTHONPATH=src python3 -m unittest tests.live.test_post_install_browser_live`
- `PYTHONPATH=src python3 -m unittest tests.integration.test_service_access_routing`
- `PYTHONPATH=src python3 -m unittest discover -s tests/integration -t .`
- `PYTHONPATH=src python3 -m unittest discover -s tests/live -t .`
- `git diff --check`

Required final verification:

- `python3 tools/quality_gate.py quality`

Live Selenium/browser validation:

- Default skipped unless explicit live prerequisites and operator consent are
  present.
- Must not be reported as passed when skipped.
- Required opt-in command after Selenium suite implementation and live
  readiness:
  `TSW_RUN_POST_INSTALL_BROWSER_LIVE=1 PYTHONPATH=src python3 -m unittest discover -s tests/live -t .`
- Live evidence must be written under
  `.tiny-swarm-world/evidence/solid-typed-evidence/e2e/` and must not be
  committed.

## Resilience Requirements

- Static route generation is deterministic and rerunnable.
- Evidence must be redacted and free of raw secrets, certificates, local IPs,
  host-specific absolute paths and credential URLs.
- If local `80/443` is unavailable in a live environment, live validation must
  report an environment blocker instead of downgrading to `10080/10443`.
- Direct fallback ports remain explicit, not silent preferred behavior.

## Ordered Slices

### Slice 01 - Baseline Routing Contract Tests

Purpose:

- Add or update deterministic tests that expose the current gateway-port and
  preferred-route mismatch before implementation changes.

Prerequisites:

- Active branch is `feature/workflow-traefik-service-routing-20260627`.
- Working tree changes are task-scoped.

```yaml
slice_id: "01"
profile: "FULL_PATH"
owner: "Senior Tester"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Python Automation Developer"
affected_files:
  - "tests/domain/ingress/test_desired_state.py"
  - "tests/domain/preflight/test_preflight_result.py"
  - "tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py"
  - "tests/live/test_post_install_browser_live.py"
  - ".codex/evidence/workflow-traefik-service-routing-20260627/slice-01-distribution.md"
  - ".codex/evidence/workflow-traefik-service-routing-20260627/slice-01-consolidation.md"
affected_modules:
  - "tiny_swarm_world.domain.ingress"
  - "tiny_swarm_world.domain.preflight"
  - "tiny_swarm_world.infrastructure.adapters.repositories"
affected_contracts:
  - "Traefik preferred ingress ports"
  - "Service Access preferred routed links"
dependencies: []
parallel_group: "serial-traefik-routing"
file_locks:
  - "tests/domain/ingress/test_desired_state.py"
  - "tests/domain/preflight/test_preflight_result.py"
  - "tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py"
  - "tests/live/test_post_install_browser_live.py"
  - ".codex/evidence/workflow-traefik-service-routing-20260627/**"
contract_locks:
  - "80/443 are preferred public ingress"
  - "10080/10443 are not preferred Service Access links"
architecture_locks:
  - "Static and live verification remain separate"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.domain.ingress.test_desired_state"
    - "PYTHONPATH=src python3 -m unittest tests.domain.preflight.test_preflight_result"
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml"
    - "PYTHONPATH=src python3 -m unittest tests.live.test_post_install_browser_live"
  required: []
documentation:
  arc42: "Checked; no edit in Slice 01."
  adr: "Checked; no edit in Slice 01."
stop_conditions:
  - "Stop if tests require live infrastructure by default."
  - "Stop if acceptance criteria require guessing route ownership."
  - "Stop if a test would expose secrets or host-specific local topology."
```

Done criteria:

- Tests encode preferred Traefik `80/443` authority and direct-port fallback
  classification without running live infrastructure.

### Slice 02 - Gateway Port Authority And Route Model

Purpose:

- Reconcile Traefik public ingress ports across domain ingress, service
  registry, compose rendering and setup/preflight expectations.

Prerequisites:

- Slice 01 tests exist and identify the target behavior.

```yaml
slice_id: "02"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior System Architect"
  - "Senior Tester"
  - "Senior DevOps Engineer"
affected_files:
  - "infra/config/services.yml"
  - "infra/config/compose/traefik/docker-compose.yml"
  - "src/tiny_swarm_world/domain/ingress/desired_state.py"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py"
  - "src/tiny_swarm_world/domain/preflight/setup_manifest.py"
  - "tests/domain/ingress/test_desired_state.py"
  - "tests/domain/preflight/test_preflight_result.py"
  - "tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py"
  - ".codex/evidence/workflow-traefik-service-routing-20260627/slice-02-distribution.md"
  - ".codex/evidence/workflow-traefik-service-routing-20260627/slice-02-consolidation.md"
affected_modules:
  - "tiny_swarm_world.domain.ingress"
  - "tiny_swarm_world.domain.preflight"
  - "tiny_swarm_world.infrastructure.adapters.repositories"
affected_contracts:
  - "Traefik public ingress ports"
  - "Compose published-port rendering"
  - "Setup manifest required port classification"
dependencies:
  - "01"
parallel_group: "serial-traefik-routing"
file_locks:
  - "infra/config/services.yml"
  - "infra/config/compose/traefik/docker-compose.yml"
  - "src/tiny_swarm_world/domain/ingress/desired_state.py"
  - "src/tiny_swarm_world/domain/preflight/**"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py"
  - "tests/domain/**"
  - "tests/infrastructure/adapters/repositories/**"
contract_locks:
  - "Traefik `web` maps to public HTTP 80"
  - "Traefik `websecure` maps to public HTTPS 443"
architecture_locks:
  - "Domain route model stays infrastructure-free"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.domain.ingress.test_desired_state"
    - "PYTHONPATH=src python3 -m unittest tests.domain.preflight.test_preflight_result"
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml"
  required: []
documentation:
  arc42: "Update later in Slice 04 if implemented behavior changes deployment view."
  adr: "No ADR change expected; implementation aligns with accepted ADR."
stop_conditions:
  - "Stop if `80/443` cannot be represented without weakening compatibility classifications."
  - "Stop if Traefik insecure API mode appears."
  - "Stop if the Pulsar broker is treated as HTTP."
```

Done criteria:

- Domain, registry, compose rendering and setup/preflight tests agree that
  Traefik preferred public ingress is `80/443`.

### Slice 03 - Service Access Links, Evidence And Live Suite Structure

Purpose:

- Make Service Access preferred URLs and route evidence reflect the Traefik
  host-based model while keeping direct ports as explicit fallback and live
  checks opt-in.

Prerequisites:

- Slice 02 completed.

```yaml
slice_id: "03"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Tester"
  - "Senior DevOps Engineer"
  - "Senior System Architect"
affected_files:
  - "infra/config/compose/service-access/dashboard/index.html"
  - "infra/config/compose/**/docker-compose.yml"
  - "tests/integration/test_service_access_routing.py"
  - "tests/live/test_post_install_browser_live.py"
  - "src/tiny_swarm_world/domain/ingress/desired_state.py"
  - ".codex/evidence/workflow-traefik-service-routing-20260627/slice-03-distribution.md"
  - ".codex/evidence/workflow-traefik-service-routing-20260627/slice-03-consolidation.md"
affected_modules:
  - "service-access dashboard"
  - "tiny_swarm_world.domain.ingress"
  - "tests.integration"
  - "tests.live"
affected_contracts:
  - "Service Access preferred URL source"
  - "Route evidence redaction"
  - "Opt-in live browser validation"
dependencies:
  - "02"
parallel_group: "serial-traefik-routing"
file_locks:
  - "infra/config/compose/service-access/**"
  - "infra/config/compose/**/docker-compose.yml"
  - "tests/integration/**"
  - "tests/live/**"
  - "src/tiny_swarm_world/domain/ingress/**"
contract_locks:
  - "Preferred Service Access URLs use Traefik hostnames"
  - "Direct ports remain fallback/diagnostic only"
  - "Live evidence stays under `.tiny-swarm-world/evidence/**`"
architecture_locks:
  - "Browser tooling stays in tests/live, not product runtime"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.integration.test_service_access_routing"
    - "PYTHONPATH=src python3 -m unittest tests.live.test_post_install_browser_live"
  required: []
documentation:
  arc42: "Update later in Slice 04."
  adr: "No ADR change expected."
stop_conditions:
  - "Stop if preferred links need hosts-file or DNS mutation."
  - "Stop if dashboard changes expose password values."
  - "Stop if live Selenium would run by default."
```

Done criteria:

- Service Access preferred links use routed host URLs.
- Fallback/direct URLs are explicitly classified.
- Static tests prove redacted route evidence and opt-in live behavior.

### Slice 04 - Documentation Sync And Final Verification

Purpose:

- Synchronize documentation and run final backend plus user-facing static
  verification.

Prerequisites:

- Slices 01 through 03 completed or stopped with evidence.

```yaml
slice_id: "04"
profile: "FULL_PATH"
owner: "Senior Documentation Engineer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "README.md"
  - "documentation/deployment/system.adoc"
  - "documentation/arc42/07_deployment_view.adoc"
  - "documentation/arc42/09_architecture_decisions.adoc"
  - "documentation/workflow/workflow.md"
  - "documentation/workflow/context-pack.md"
  - "documentation/workflow/context-pack.json"
  - ".codex/evidence/workflow-traefik-service-routing-20260627/slice-04-distribution.md"
  - ".codex/evidence/workflow-traefik-service-routing-20260627/slice-04-consolidation.md"
affected_modules:
  - "documentation"
affected_contracts:
  - "ADR-backed Traefik routing documentation"
  - "Default static verification versus opt-in live verification"
dependencies:
  - "03"
parallel_group: "serial-traefik-routing"
file_locks:
  - "README.md"
  - "documentation/deployment/system.adoc"
  - "documentation/arc42/**"
  - "documentation/workflow/**"
  - ".codex/evidence/workflow-traefik-service-routing-20260627/**"
contract_locks:
  - "Documentation must distinguish implemented static behavior and live evidence"
architecture_locks:
  - "ADR remains accepted authority; no second gateway policy"
quality_gates:
  targeted:
    - "git diff --check"
    - "PYTHONPATH=src python3 -m unittest tests.domain.ingress.test_desired_state tests.domain.preflight.test_preflight_result tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml tests.integration.test_service_access_routing tests.live.test_post_install_browser_live tests.test_package_entrypoint"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "Update deployment view and architecture decision index when source behavior changes."
  adr: "Do not rewrite ADR history; update implementation status only if needed."
stop_conditions:
  - "Stop if documentation would claim live browser success without opt-in evidence."
  - "Stop if final quality gate fails and cannot be classified safely."
  - "Stop if an ADR is needed before continuing."
```

Done criteria:

- Documentation reflects implemented behavior only.
- Targeted backend and user-facing static checks pass.
- Full quality gate passes or any blocker is classified.

### Slice 05 - Effective Access Evidence And Health-Check Model

Purpose:

- Promote the current routed-link and route-contract behavior into an explicit
  effective access/evidence model that covers the complete Issue #157 evidence
  payload and can drive routed HTTP health-check expectations.

Prerequisites:

- Slices 01 through 04 completed.
- Current implementation branch remains
  `feature/workflow-traefik-service-routing-20260627`.

```yaml
slice_id: "05"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior System Architect"
  - "Senior Tester"
  - "Senior DevOps Engineer"
affected_files:
  - "src/tiny_swarm_world/domain/ingress/**"
  - "src/tiny_swarm_world/application/services/platform/**"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/**"
  - "tests/domain/ingress/**"
  - "tests/integration/test_service_access_routing.py"
  - "documentation/workflow/workflow.md"
  - ".codex/evidence/workflow-traefik-service-routing-20260627/slice-05-distribution.md"
  - ".codex/evidence/workflow-traefik-service-routing-20260627/slice-05-consolidation.md"
affected_modules:
  - "tiny_swarm_world.domain.ingress"
  - "tiny_swarm_world.application.services.platform"
  - "tiny_swarm_world.infrastructure.adapters.repositories"
  - "tests.integration"
affected_contracts:
  - "Effective access model"
  - "Route evidence payload"
  - "Routed HTTP health-check expectations"
dependencies:
  - "04"
parallel_group: "serial-traefik-routing"
file_locks:
  - "src/tiny_swarm_world/domain/ingress/**"
  - "src/tiny_swarm_world/application/services/platform/**"
  - "tests/integration/**"
  - ".codex/evidence/workflow-traefik-service-routing-20260627/**"
contract_locks:
  - "Evidence includes route map, public ports, fallback ports and skipped-route reasons"
  - "Health checks may use routed Traefik URLs but do not silently downgrade to diagnostic ports"
architecture_locks:
  - "Domain model remains infrastructure-free"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.domain.ingress.test_desired_state tests.integration.test_service_access_routing"
  required: []
documentation:
  arc42: "Update only if the effective evidence model changes architecture claims."
  adr: "No ADR rewrite; align with accepted Traefik ADR."
stop_conditions:
  - "Stop if evidence would include secrets, local IP addresses, host-specific paths, raw command payloads or certificate material."
  - "Stop if health-check fallback ports become the preferred route."
  - "Stop if a new gateway policy is needed."
```

Done criteria:

- Effective access evidence includes gateway/public ingress ports, diagnostic
  fallback ports, route map, internal target ports, Service Access preferred
  URL source, fallback classification and skipped-route reasons.
- Routed health-check expectations are represented without running live
  infrastructure by default.

### Slice 06 - Service-Oriented Integration Route Coverage

Purpose:

- Expand integration tests so Issue #157 route/link/evidence behavior is
  service-oriented and covers enabled routes plus explicit skipped/not-generated
  routes.

Prerequisites:

- Slice 05 completed.

```yaml
slice_id: "06"
profile: "FULL_PATH"
owner: "Senior Tester"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior Python Automation Developer"
  - "Senior System Architect"
affected_files:
  - "tests/integration/test_service_access_routing.py"
  - "tests/integration/test_portainer_routing.py"
  - "tests/integration/test_jenkins_routing.py"
  - "tests/integration/test_sonarqube_routing.py"
  - "tests/integration/test_nexus_routing.py"
  - "tests/integration/test_swagger_routing.py"
  - "tests/integration/test_infisical_routing.py"
  - "tests/integration/test_pulsar_routing.py"
  - "tests/integration/test_observability_routing.py"
  - "tests/integration/test_tiny_swarm_app_routing.py"
  - "tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py"
  - ".codex/evidence/workflow-traefik-service-routing-20260627/slice-06-distribution.md"
  - ".codex/evidence/workflow-traefik-service-routing-20260627/slice-06-consolidation.md"
affected_modules:
  - "tests.integration"
  - "tests.infrastructure.adapters.repositories"
affected_contracts:
  - "Service-oriented integration route suite"
  - "Representative Traefik label rendering"
  - "Non-generated route skip semantics"
dependencies:
  - "05"
parallel_group: "serial-traefik-routing"
file_locks:
  - "tests/integration/**"
  - "tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py"
contract_locks:
  - "Every enabled routed HTTP service has independent route/link/evidence assertions"
  - "Prometheus, Grafana, app and api routes are generated only when enabled/configured"
architecture_locks:
  - "Integration tests stay static and do not call live Docker, DNS, browser or network dependencies"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest discover -s tests/integration -t ."
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml"
  required: []
documentation:
  arc42: "No documentation change unless route support changes."
  adr: "No ADR change expected."
stop_conditions:
  - "Stop if tests require live infrastructure by default."
  - "Stop if RabbitMQ route metadata appears."
  - "Stop if Pulsar broker TCP is treated as HTTP."
```

Done criteria:

- Integration tests are service-oriented, independently runnable, and cover
  Portainer, Jenkins, SonarQube, Nexus, Swagger, Infisical, Service Access,
  Pulsar Manager, Pulsar Admin/API, skipped observability routes and skipped
  Tiny Swarm app/API routes.

### Slice 07 - Opt-In Selenium Browser E2E Suite

Purpose:

- Add the explicit opt-in Selenium browser E2E suite required by Issue #157
  without making live validation part of the default quality gate.

Prerequisites:

- Slice 06 completed.
- Live infrastructure commands remain forbidden unless the operator explicitly
  opts into a live validation run.

```yaml
slice_id: "07"
profile: "FULL_PATH"
owner: "Senior Tester"
secondary_reviewers:
  - "Senior DevOps Engineer"
  - "Senior Python Automation Developer"
  - "Senior System Architect"
affected_files:
  - "tests/live/test_service_access_browser_e2e.py"
  - "tests/live/test_portainer_browser_e2e.py"
  - "tests/live/test_jenkins_browser_e2e.py"
  - "tests/live/test_sonarqube_browser_e2e.py"
  - "tests/live/test_nexus_browser_e2e.py"
  - "tests/live/test_swagger_browser_e2e.py"
  - "tests/live/test_infisical_browser_e2e.py"
  - "tests/live/test_pulsar_browser_e2e.py"
  - "tests/live/test_observability_browser_e2e.py"
  - "tests/live/test_tiny_swarm_app_browser_e2e.py"
  - "tests/live/test_post_install_browser_live.py"
  - "tests/live/support/**"
  - ".codex/evidence/workflow-traefik-service-routing-20260627/slice-07-distribution.md"
  - ".codex/evidence/workflow-traefik-service-routing-20260627/slice-07-consolidation.md"
affected_modules:
  - "tests.live"
affected_contracts:
  - "Opt-in Selenium E2E route validation"
  - "Per-service browser success predicates"
  - "Redacted local E2E evidence"
dependencies:
  - "06"
parallel_group: "serial-traefik-routing"
file_locks:
  - "tests/live/**"
  - ".codex/evidence/workflow-traefik-service-routing-20260627/**"
contract_locks:
  - "Selenium imports are exactly `from selenium import webdriver` and `from selenium.webdriver.common.by import By`"
  - "Live E2E opens routed Service Access links, not diagnostic fallback links"
  - "Live E2E writes only ignored redacted evidence under `.tiny-swarm-world/evidence/solid-typed-evidence/e2e/`"
architecture_locks:
  - "Browser tooling stays in tests/live and is not product runtime code"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest discover -s tests/live -t ."
  required: []
documentation:
  arc42: "No architecture claim of live success unless a live run is explicitly executed."
  adr: "No ADR change expected."
stop_conditions:
  - "Stop if Selenium would run by default without `TSW_RUN_POST_INSTALL_BROWSER_LIVE=1` or equivalent explicit consent."
  - "Stop if screenshots, raw passwords, tokens, private keys, local IP addresses or raw command payloads would be persisted."
  - "Stop if live evidence would be committed."
  - "Stop if approved credential source is unclear."
```

Done criteria:

- Live Selenium files exist and are service-oriented.
- Default run skips live browser execution without reporting success.
- Static tests prove live command gating, routed URL selection, per-service
  success predicates, explicit skip reasons and evidence redaction.

### Slice 08 - Live E2E Execution Gate And Final Issue Acceptance

Purpose:

- Define and, only with explicit operator consent and live prerequisites,
  execute the live Selenium gate for every generated routed Service Access
  link in the active profile.

Prerequisites:

- Slice 07 completed.
- Operator explicitly approves live validation.
- Required live prerequisites are available: deployed stack, Traefik route
  resolution for `*.tsw.local`, TLS trust or CA bundle, approved credential
  source and ignored evidence path.

```yaml
slice_id: "08"
profile: "FULL_PATH_LIVE_OPT_IN"
owner: "Senior DevOps Engineer"
secondary_reviewers:
  - "Senior Tester"
  - "Senior Python Automation Developer"
  - "Senior System Architect"
affected_files:
  - "tests/live/**"
  - "documentation/workflow/workflow.md"
  - ".codex/evidence/workflow-traefik-service-routing-20260627/slice-08-distribution.md"
  - ".codex/evidence/workflow-traefik-service-routing-20260627/slice-08-consolidation.md"
affected_modules:
  - "tests.live"
  - "documentation.workflow"
affected_contracts:
  - "Explicit live Selenium acceptance evidence"
  - "Per-service live pass/fail/skip summary"
dependencies:
  - "07"
parallel_group: "serial-live-validation"
file_locks:
  - "tests/live/**"
  - "documentation/workflow/**"
  - ".codex/evidence/workflow-traefik-service-routing-20260627/**"
contract_locks:
  - "Live success is claimed only with explicit live evidence"
  - "Environment blockers do not downgrade product model from `80/443` to `10080/10443`"
architecture_locks:
  - "No host resolver, DNS, Docker, Swarm, LXC or Traefik mutation without separate explicit approval"
quality_gates:
  targeted:
    - "TSW_RUN_POST_INSTALL_BROWSER_LIVE=1 PYTHONPATH=src python3 -m unittest discover -s tests/live -t ."
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "Update only to report verified live evidence status if the live gate actually runs."
  adr: "No ADR change expected."
stop_conditions:
  - "Stop if live validation consent is missing."
  - "Stop if route hostnames do not resolve."
  - "Stop if TLS trust material is unavailable and HTTPS verification would be weakened."
  - "Stop if approved credentials are unavailable for a required login and no explicit skip reason can be recorded."
  - "Stop if generated routed links fail to open."
```

Done criteria:

- If live consent is absent, Slice 08 records an explicit skipped-live blocker
  and the workflow remains not fully accepted for Issue #157.
- If live consent is present, every generated routed Service Access link is
  opened with Selenium and recorded as passed, failed or explicitly skipped.
- Required login flows pass where approved credentials are available.
- Redacted local E2E summary exists under ignored `.tiny-swarm-world/**` and
  is not committed.
- Full quality gate passes after any live-suite code changes.

## Slice Dependency Graph

```text
01 Baseline Routing Contract Tests
  -> 02 Gateway Port Authority And Route Model
    -> 03 Service Access Links, Evidence And Live Suite Structure
      -> 04 Documentation Sync And Final Verification
        -> 05 Effective Access Evidence And Health-Check Model
          -> 06 Service-Oriented Integration Route Coverage
            -> 07 Opt-In Selenium Browser E2E Suite
              -> 08 Live E2E Execution Gate And Final Issue Acceptance
```

## Parallel Execution

- Can this workflow run in parallel? No write-capable parallel execution.
- Conflicting workflows: any workflow touching Traefik ingress, service-access
  dashboard, compose stack publication, setup manifest ports, ingress domain
  objects, effective access/evidence model, live browser tests or deployment
  documentation.
- Shared files: `infra/config/services.yml`, Traefik and Service Access compose
  files, `src/tiny_swarm_world/domain/ingress/**`, `tests/integration/**`,
  `tests/live/**` and docs.
- Shared infrastructure: Docker Swarm, LXC, Traefik and local DNS/hosts state;
  no live shared infrastructure may be used by default.
- Requires isolated worktree: yes for any concurrent workflow execution.
- Requires serialized live validation: yes; live validation is opt-in only and
  belongs to Slice 08.
- Merge-order constraints: execute slices in order 01 through 08.

## Automatic Work Distribution Policy

`workflow execute` must automatically inspect each slice for safe specialist
stream decomposition. Real Codex subagents may be used where supported. If
subagents are unavailable, execute the same checks through explicit role-based
fallback in the main thread and record that fallback in evidence.

Required evidence before implementation:

- `.codex/evidence/workflow-traefik-service-routing-20260627/slice-<number>-distribution.md`

Required evidence after implemented slices:

- `.codex/evidence/workflow-traefik-service-routing-20260627/slice-<number>-consolidation.md`

Stream map:

- Backend/Python: Slices 01, 02, 03 and 05.
- Frontend/React: not applicable.
- Console/status UI: not affected.
- Tests: all slices; Slice 07 owns Selenium test structure and Slice 08 owns
  explicit live execution.
- Runtime/DevOps: Slices 02 and 03 for static configuration; Slice 08 for
  explicit live validation only.
- Documentation: Slices 04 and 08 when live status is known.
- Quality: Slices 04, 07 and 08.
- Architecture: all slices.
- Security: secret redaction, credential display safety and local evidence
  path safety.

Non-parallelization rules:

- Do not parallelize overlapping file edits.
- Do not parallelize unclear architecture ownership.
- Do not parallelize contradictory requirements.
- Do not parallelize mandatory ordered migration from tests to implementation
  to documentation.
- Do not parallelize generated-file conflict resolution.
- Do not parallelize if Three Amigos marks the slice not safely
  parallelizable.
- Do not proceed with unclear secrets handling or weakened safety guards.

Codex remains the final integration owner for consolidation, tests, evidence,
PR readiness and merge readiness.

## Git Worktree Execution Rule

Execute this workflow only from branch
`feature/workflow-traefik-service-routing-20260627` or from an isolated
worktree branch explicitly derived for this workflow. Subagents or stream
workers must verify the active branch before writing files and must not merge
directly. Codex consolidates accepted changes after evidence and tests pass.

## Role Ownership Map

- Senior Workflow Architect: workflow structure, dependencies and execution
  policy.
- Senior Requirement Engineer: Issue #157 and ADR alignment.
- Senior System Architect: hexagonal boundaries and gateway policy alignment.
- Senior Python Automation Developer: domain/config/rendering implementation.
- Senior Documentation Engineer: README, deployment and arc42 sync.
- Senior Tester: static, integration and live-skipped regression tests.
- Senior React Frontend Developer: N/A impact check; no React module exists.
- Senior DevOps Engineer: Docker/Swarm compose and live-validation safety.

## Quality-Gate Expectations

From `QUALITY.md`:

- Preferred full gate: `python3 tools/quality_gate.py quality`
- Targeted gates during development:
  - `python3 tools/quality_gate.py lint`
  - `python3 tools/quality_gate.py arch-lint`
  - `python3 tools/quality_gate.py arch-tests`
  - `python3 tools/quality_gate.py typecheck`
  - `python3 tools/quality_gate.py test`
  - `git diff --check`

The full gate is required for final readiness because this workflow changes
domain behavior, YAML/compose configuration, tests and documentation.

## Documentation Synchronization Points

- Update README and deployment docs for `80/443` preferred ingress.
- Update arc42 deployment view and architecture-decision index if implemented
  behavior changes from pending to repository-supported static routing.
- Keep ADR history intact.
- Explicitly mark live Selenium verification as opt-in and not run by default.

## Stop Conditions

Stop and report if:

- Git repository context or active branch cannot be verified.
- Unrelated uncommitted changes appear.
- Traefik `80/443` cannot be made authoritative without a new ADR.
- `--api.insecure=true` appears.
- Service Access would expose password values.
- Live browser or infrastructure checks would run by default.
- DNS or hosts-file mutation would be required.
- Pulsar broker TCP is treated as HTTP.
- RabbitMQ metadata or routes are introduced.
- Documentation would claim live success without opt-in evidence.
- Any quality failure cannot be safely classified.

## Uncertainty Escalation Rules

- Route gateway-policy ambiguity to Senior System Architect and ADR Steward.
- Route deployment/runtime ambiguity to Senior DevOps.
- Route secret or evidence leakage risk to security review.
- Route failing or flaky tests to Senior Tester and Typed Error Router before
  retries.

## Commit And Push Plan

- Workflow creation publication is authorized as a guarded branch commit and
  push to `origin/feature/workflow-traefik-service-routing-20260627`.
- Slice execution commits are authorized one slice at a time after targeted
  checks pass.
- Slice checkpoint push is not `push auto` and must not create or merge a PR.

## Definition Of Done

- Workflow branch exists and is active.
- `documentation/workflow/workflow.md`,
  `documentation/workflow/context-pack.md`, and
  `documentation/workflow/context-pack.json` describe this workflow.
- Slices contain machine-readable metadata.
- Implementation aligns with Issue #157 and the accepted Traefik ADR.
- Backend/domain/static checks pass.
- User-facing Service Access route/link behavior is verified statically.
- Effective access evidence covers gateway ports, route map, fallback
  classification, internal target ports, Service Access URL source and
  skipped-route reasons.
- Service-oriented integration tests cover every enabled routed HTTP service
  and explicit skipped/not-generated routes for disabled or unconfigured
  services.
- Opt-in Selenium browser E2E files exist, import Selenium exactly as required
  by Issue #157, and are skipped by default without reporting success.
- Full Issue #157 acceptance requires one of these outcomes:
  - live consent is granted, Slice 08 runs, every generated routed Service
    Access link is opened with Selenium, required approved login flows pass,
    and redacted local evidence records pass/fail/skip status;
  - live consent or prerequisites are missing, Slice 08 records a classified
    blocker and the workflow remains `PARTIAL_EXECUTION_REQUIRES_ISSUE_157_COMPLETION`.
- Documentation distinguishes accepted architecture direction, committed
  desired configuration, default static verification and opt-in live
  verification results.
- Full quality gate passes after all code/test/documentation changes.

## Handoff To Workflow Execute

Run `workflow execute` only after confirming:

- active branch:
  `feature/workflow-traefik-service-routing-20260627`
- current workflow status:
  `PARTIAL_EXECUTION_REQUIRES_ISSUE_157_COMPLETION`
- next execution starts at Slice 05 unless a prior slice is deliberately
  reopened with a documented reason
- context pack hashes are current
- no unrelated working-tree changes exist
- live Slice 08 must not run without explicit operator consent and verified
  prerequisites

## Execution Outcome

Current status:

- Partial execution only. Slices 01 through 04 are complete for static/backend
  routing behavior. Slices 05 through 08 remain required for full Issue #157
  acceptance.

- Slice 01 established the baseline routing-contract evidence and confirmed
  existing tests were the correct regression surface.
- Slice 02 reconciled Traefik public ingress authority to `80/443` across the
  domain ingress model, setup manifest, service registry, Traefik compose,
  compose rendering and platform preflight behavior.
- Slice 03 changed Service Access preferred links to Traefik host routes,
  added/verified Traefik route labels for Service Access, Swagger, Pulsar
  Manager and Pulsar Admin API, and added route/link/evidence integration
  tests. Pulsar broker TCP remains direct protocol access.
- Slice 04 synchronized README, deployment docs, arc42 decision index and
  deployment view. Documentation does not claim live browser success.
- Full quality gate passed with `python3 tools/quality_gate.py quality`.
- Live Selenium/browser validation was not run because no explicit live
  infrastructure opt-in was requested for this execution.
- The absence of Selenium browser E2E implementation and execution is now a
  remaining workflow requirement, not an accepted final state.
- Follow-up execution added Slices 05 through 07 artifacts: service-oriented
  integration route tests, opt-in Selenium browser E2E test files, and the
  domain ingress correction that makes Traefik load-balancer target ports use
  internal service ports.
- Full quality gate after follow-up changes passed with 1052 tests and 52
  skipped.
- Slice 08 remains open because live Selenium execution still requires
  explicit live infrastructure opt-in.

## arc42 Check Status

- `documentation/arc42/07_deployment_view.adoc` checked because it documents
  Traefik ingress and service access deployment.
- `documentation/arc42/09_architecture_decisions.adoc` checked because it
  references the accepted Traefik ADR.
- Execution must update arc42 only for implemented repository behavior and must
  not claim live success without opt-in evidence.
