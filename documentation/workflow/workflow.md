# Workflow: Portainer Local Endpoint Bootstrap Diagnostics

```yaml
workflow_id: portainer-local-endpoint-bootstrap-diagnostics-v1.0.0
workflow_version: 1.0.0
branch: work/fix-workflow-portainer-local-endpoint-20260606
execution_profile: FULL_PATH
released_for_workflow_execute: true
created_utc: "2026-06-06T00:00:00Z"
request: "Fix deployment:portainer-local-endpoint after platform init, platform reconcile, platform expose, Portainer stack registration, and Portainer admin authentication already completed."
decision: READY_FOR_WORKFLOW
confidence: 92
```

## Executive Summary

Live installation evidence shows the setup path now reaches Portainer bootstrap and
fails specifically at `deployment:portainer-local-endpoint`:

```text
RuntimeError. Portainer local endpoint could not be registered.
```

This workflow creates a focused repair plan for the Portainer endpoint bootstrap
step. It does not reopen platform init, platform expose, LXC proxy, Swarm
bootstrap, Portainer port exposure, or Portainer admin credentials as the first
investigation path because the provided log states those phases already completed.

Repository inspection found that the current `PortainerHttpClient` already:

* queries `GET /api/endpoints`;
* treats an existing endpoint named `local` as success;
* accepts a single socket-backed endpoint as a local fallback;
* creates a socket-backed Docker endpoint with `POST /api/endpoints` when missing.

Therefore the remaining workflow target is not generic idempotency from scratch.
The executable target is to harden and verify the bootstrap contract for
Portainer 2.39.x, surface real HTTP status and response-body diagnostics through
safe evidence, and document that Tiny Swarm World's current authoritative
Portainer endpoint model is the socket-backed local Docker endpoint.

## Requirement Clarification Gate

Original request:

* The live installation fails after successful platform init, platform
  reconcile, platform expose, Portainer stack registration, and Portainer admin
  authentication.
* Failure target is `deployment:portainer-local-endpoint`.
* Error is `RuntimeError: Portainer local endpoint could not be registered`.
* Do not investigate LXC proxy, Swarm bootstrap, or Portainer port exposure
  first.
* Fix the Portainer local endpoint bootstrap step.
* Make endpoint registration idempotent through `GET /api/endpoints`.
* If endpoint `local` already exists, treat the step as success.
* If missing, create it through the correct Portainer 2.39.x API contract.
* Log and surface the real HTTP status code and response body when registration
  fails.
* Add regression coverage for existing endpoint, successful creation, failed
  creation with HTTP diagnostics, and retry/backoff while Portainer or agent
  readiness is still transient.
* Decide and document whether the stack should register a socket endpoint or an
  agent endpoint.
* After implementation, `./install.sh` must pass
  `deployment:portainer-local-endpoint` and continue to artifact preparation and
  deployment apply.

Interpreted intent:

* Create an executable workflow to repair only the Portainer local endpoint
  bootstrap failure.
* Preserve existing platform, exposure, admin-access, and service-stack
  boundaries.
* Keep the implementation in Python hexagonal boundaries: application service
  orchestration, application port contracts, infrastructure HTTP adapter, tests,
  and documentation.
* Use mocked tests by default and reserve `./install.sh` for explicit live
  validation during workflow execution.

Change type:

* Python automation behavior change.
* Infrastructure HTTP adapter diagnostics change.
* Deployment bootstrap evidence change.
* Documentation synchronization for Portainer endpoint model.

Affected process strand:

* `setup run --live` deployment bootstrap phase.
* `deployment bootstrap` step sequence.
* `deployment:portainer-local-endpoint`.
* Portainer-managed application stack precondition.

Affected architecture area:

* `src/tiny_swarm_world/application/services/deployment`.
* `src/tiny_swarm_world/application/ports/clients/port_portainer_client.py` if a
  diagnostic exception contract is needed.
* `src/tiny_swarm_world/infrastructure/adapters/clients/portainer_http_client.py`.
* Deployment tests under `tests/application/services/deployment` and
  `tests/infrastructure/adapters/clients`.
* `documentation/deployment/system.adoc` and arc42 runtime or deployment view.

Explicit requirements:

* Endpoint lookup must remain first.
* Existing endpoint named `local` must be success.
* Missing endpoint must be created using the verified Portainer 2.39.x contract.
* Failed endpoint creation must report HTTP status and response body in
  redacted, operator-actionable evidence.
* Retry/backoff must cover transient readiness before final failure.
* The endpoint model must be documented without ambiguity.
* Live infrastructure commands must not run during normal workflow creation or
  unit-test verification.

Implicit requirements:

* Do not weaken existing safe-text and secret-redaction rules.
* Do not expose Portainer password, JWT, Authorization header, or secret-bearing
  payloads in logs or workflow evidence.
* Do not add direct shell, Docker, LXC, or HTTP details to domain modules.
* Do not move adapter construction out of
  `src/tiny_swarm_world/infrastructure/composition.py`.
* Preserve current stack ordering: Portainer stack, admin access, local
  endpoint, then Nexus bootstrap.
* Preserve the current Docker Swarm-first and Linux/WSL-only operating model.

Assumptions:

* Current authoritative endpoint model is socket-backed local Docker endpoint:
  `unix:///var/run/docker.sock`.
* The Portainer agent remains deployed for Swarm/agent compatibility and
  cluster behavior, but it is not the endpoint registered by
  `deployment:portainer-local-endpoint` unless implementation evidence proves a
  Portainer 2.39.x contract mismatch.
* Portainer error bodies can be surfaced after applying the repository's
  redaction policy.
* The live failure is reproducible by the endpoint creation or verification
  path, not by prior platform phases.

Non-goals:

* No Kubernetes-first behavior.
* No Multipass provider restoration.
* No Java, Maven, Spring Boot, browser React, or external static-analysis CI.
* No reset of platform lifecycle or LXC proxy investigation unless endpoint
  evidence proves the failure depends on them.
* No direct live `incus`, `lxc`, `docker swarm`, compose, Portainer, Nexus,
  Jenkins, RabbitMQ, SonarQube, Swagger, or `./install.sh` run without explicit
  live-infrastructure request.

Risks:

* Portainer 2.39.x may reject the current multipart endpoint payload even though
  tests cover the intended request shape.
* Response-body diagnostics could leak secrets if added as raw exception text.
* Deployment workflow redaction currently treats terms such as `response body`
  as unsafe and can erase useful diagnostics unless structured evidence is used.
* Retrying all failures equally could delay deterministic 4xx contract failures.
* Switching from socket endpoint to agent endpoint without evidence could break
  later stack deployment, which expects a Swarm-capable endpoint ID.

Open questions:

* None blocking for workflow authoring.
* During execution, verify whether Portainer 2.39.x still accepts
  `EndpointCreationType=1`, `ContainerEngine=docker`, and
  `URL=unix:///var/run/docker.sock` for the local endpoint.

Blocking questions:

* None for workflow execution. If the verified Portainer 2.39.x contract differs
  from the current socket payload, Slice 02 must stop and document the evidence
  before changing the endpoint model.

Decision:

* `READY_FOR_WORKFLOW`.

## Execution Profile

```text
executionProfile=FULL_PATH
reason=Deployment bootstrap behavior, Portainer API diagnostics, tests, and architecture documentation are affected.
requiredFullReviews=Senior Requirement Engineer, Senior System Architect, Senior Python Automation Developer, Senior React Frontend Developer, Senior Tester
allowedImpactChecks=Senior React Frontend Developer may record no browser/React impact after verifying no frontend module is touched.
requiredQualityChecks=targeted unittest commands first; python3 tools/quality_gate.py quality before commit or push when practical.
stopConditions=unclear Portainer endpoint model, unredacted secret evidence, architecture boundary violation, live infrastructure command required without explicit approval.
```

## Five-Role Three Amigos Findings

Senior Requirement Engineer:

* The implementation still matches `documentation/epics/autonomous-runnable-setup.md`
  when it keeps endpoint bootstrap inside the deployment boundary and does not
  claim full runnable setup until observed evidence exists.
* The live symptom is specific enough for workflow execution.
* Existing workflow `fresh-install-reset-full-deploy` is superseded for the
  active workflow directory by this narrower endpoint-bootstrap fix.

Senior System Architect:

* Application orchestration may change in
  `EnsurePortainerEndpoint`.
* Portainer 2.39.x HTTP details belong in
  `PortainerHttpClient` and optional typed infrastructure/application-port
  diagnostics.
* Domain modules must not import Portainer, HTTP, request, Docker, or logging
  details.

Senior Python Automation Developer:

* Existing `ensure_local_endpoint` already performs lookup-before-create.
* Required implementation work is likely in diagnostic exception/evidence shape,
  retry classification, and Portainer endpoint payload verification.
* If a typed exception is introduced, it should carry sanitized diagnostic
  fields such as `status_code`, `response_body`, `endpoint_name`,
  `endpoint_model`, and `attempt_count`.

Senior React Frontend Developer:

* No browser React module is in scope.
* Console/status evidence surfaces may display improved messages indirectly, but
  no React component, frontend state, or browser build change is allowed in this
  workflow.

Senior Tester:

* Start with failing regression tests.
* Tests must use fakes/mocks for Portainer HTTP responses and transient
  readiness.
* Required targeted tests are:
  `PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_portainer_http_client`
  and
  `PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_ensure_portainer_endpoint tests.application.services.deployment.test_deployment_workflows`.

## Target Picture

When `deployment:portainer-local-endpoint` runs:

1. It authenticates to Portainer without logging credentials or JWTs.
2. It queries `GET /api/endpoints`.
3. If endpoint `local` exists, it returns success and verification evidence
   includes endpoint name, endpoint ID presence, endpoint model, and
   `endpoint_state=registered`.
4. If endpoint `local` is missing, it creates the current authoritative local
   Docker socket endpoint through the verified Portainer 2.39.x API contract.
5. If creation fails, the deployment result is `failed_to_apply` and evidence
   contains redacted HTTP status and response-body diagnostics.
6. If Portainer is reachable but the local Docker endpoint is temporarily not
   ready, the step retries with bounded backoff before final failure.
7. Setup proceeds to Nexus, artifacts prepare, and deployment apply only after
   the endpoint is registered and verified.

## Creation-Time Verified Baseline

* Repository root: `/mnt/d/Projects/Tiny-Swarm-World`.
* Active branch after workflow creation preflight:
  `work/fix-workflow-portainer-local-endpoint-20260606`.
* Working tree was clean before workflow regeneration.
* `QUALITY.md` defines `python3 tools/quality_gate.py quality` as the preferred
  full local gate.
* `src/tiny_swarm_world/application/services/deployment/ensure_portainer_endpoint.py`
  owns `deployment:portainer-local-endpoint`.
* `EnsurePortainerEndpoint.run()` retries `portainer_client.ensure_local_endpoint`
  and currently raises generic `RuntimeError("Portainer local endpoint could not
  be registered.")`.
* `PortainerHttpClient.ensure_local_endpoint()` already fetches endpoints before
  creating a local Docker endpoint.
* `PortainerHttpClient._create_local_docker_endpoint()` currently posts multipart
  fields:
  `Name`, `EndpointCreationType=1`, `ContainerEngine=docker`, and
  `URL=unix:///var/run/docker.sock`.
* `PortainerHttpClient._ensure_success()` currently raises
  `RuntimeError("Failed to <action>. HTTP <status>.")` without response body.
* `DeploymentApplyWorkflow._apply_failure_evidence()` currently captures
  `phase`, `failure_class`, and sometimes `diagnostic=http_status_*`, but not a
  response body.
* `infra/config/compose/portainer/docker-compose.yml` uses
  `portainer/portainer-ce:2.39.2`, mounts `/var/run/docker.sock` into the
  Portainer server, and also deploys `portainer/agent:2.39.2`.
* `documentation/deployment/system.adoc` states deployment bootstrap ensures the
  local Docker endpoint named `local` exists.
* `documentation/arc42/06_runtime_view.adoc` states deployment bootstrap
  registers the local Docker endpoint in Portainer.

## Scope

In scope:

* Add or adjust regression tests for endpoint idempotency, successful creation,
  failed creation diagnostics, and transient readiness retries.
* Add structured, redacted diagnostics for Portainer endpoint creation failures.
* Preserve or refine retry behavior for transient readiness and avoid masking
  deterministic contract failures.
* Verify and document the Portainer endpoint model.
* Update deployment and arc42 documentation after implementation evidence.

Out of scope:

* Reworking LXC proxy creation.
* Reworking Docker Swarm bootstrap.
* Reworking Portainer admin initialization except where diagnostic evidence is
  shared through deployment workflow helpers.
* Live `./install.sh` execution during unit-test quality gates.

## Architecture Constraints

* Domain code remains independent from application and infrastructure.
* Application services depend on ports and typed diagnostic contracts, not
  concrete HTTP adapters.
* Infrastructure adapters contain Portainer HTTP and request details.
* `composition.py` remains the standard runtime wiring location.
* Entry-point code remains thin.
* Live infrastructure commands require explicit user approval.
* Secret-bearing diagnostics must be redacted before logs, evidence, or console
  status output.

## Python Automation Assessment

This is Python automation work. The likely implementation path is:

* introduce or reuse a typed Portainer diagnostic exception;
* make `PortainerHttpClient` include redacted HTTP response-body diagnostics for
  endpoint creation and lookup failures;
* make `EnsurePortainerEndpoint` preserve the final actionable diagnostic in its
  failure message or evidence path;
* make deployment workflow evidence carry structured diagnostics when available.

## Frontend Assessment

No React or browser frontend work is authorized. Terminal and setup status output
may reflect improved deployment evidence, but any UI change must stay inside
existing console/status contracts and be justified by the Python automation
slice.

## Test Strategy

Run targeted tests first:

```bash
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_portainer_http_client
PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_ensure_portainer_endpoint tests.application.services.deployment.test_deployment_workflows
```

Run the documentation/governance check after workflow or documentation edits:

```bash
git diff --check
```

Before commit or push when practical, run:

```bash
python3 tools/quality_gate.py quality
```

Do not run `./install.sh` unless the user explicitly requests live
infrastructure validation. If live validation is approved, record the command,
timestamp, exact result, and whether execution continued past
`deployment:portainer-local-endpoint`.

## Resilience Requirements

* Keep bounded retry/backoff for transient Portainer or endpoint readiness.
* Do not retry indefinitely.
* Do not treat deterministic 4xx/5xx contract failures as silent success.
* Surface final failure diagnostics with status, redacted body, endpoint name,
  endpoint model, and attempt count.

## Ordered Slices

### Slice 01 - Regression Characterization

Purpose:

Add failing or strengthening tests that pin the desired endpoint bootstrap
behavior before implementation changes.

Prerequisites:

* Active branch is `work/fix-workflow-portainer-local-endpoint-20260606`.
* No live infrastructure commands.

```yaml
slice_id: "01"
profile: FULL_PATH
owner: Senior Tester
secondary_reviewers:
  - Senior Python Automation Developer
  - Senior System Architect
affected_files:
  - tests/infrastructure/adapters/clients/test_portainer_http_client.py
  - tests/application/services/deployment/test_ensure_portainer_endpoint.py
  - tests/application/services/deployment/test_deployment_workflows.py
affected_modules:
  - tests.infrastructure.adapters.clients
  - tests.application.services.deployment
affected_contracts:
  - PortPortainerClient.ensure_local_endpoint
  - deployment:portainer-local-endpoint
dependencies: []
parallel_group: portainer-tests
file_locks:
  - tests/infrastructure/adapters/clients/test_portainer_http_client.py
  - tests/application/services/deployment/test_ensure_portainer_endpoint.py
  - tests/application/services/deployment/test_deployment_workflows.py
contract_locks:
  - Portainer endpoint bootstrap diagnostics
architecture_locks:
  - Deployment application/infrastructure boundary
quality_gates:
  targeted:
    - PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_portainer_http_client
    - PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_ensure_portainer_endpoint tests.application.services.deployment.test_deployment_workflows
  required:
    - git diff --check
documentation:
  arc42:
    - documentation/arc42/06_runtime_view.adoc
  adr: []
stop_conditions:
  - Tests require live Portainer, LXC, Docker, or Swarm access.
  - Expected endpoint model cannot be expressed without changing architecture boundaries.
```

Done criteria:

* Existing endpoint named `local` remains success.
* Missing endpoint with successful create remains success.
* Failed create asserts status and redacted response body are available in
  operator-facing evidence.
* Transient readiness retry is deterministic and does not sleep in tests.

Verification commands:

```bash
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_portainer_http_client
PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_ensure_portainer_endpoint tests.application.services.deployment.test_deployment_workflows
```

### Slice 02 - Portainer HTTP Diagnostic Contract

Purpose:

Implement structured Portainer HTTP diagnostics and verify the Portainer 2.39.x
local socket endpoint creation contract.

Prerequisites:

* Slice 01 regression tests exist.

```yaml
slice_id: "02"
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers:
  - Senior System Architect
  - Senior Tester
affected_files:
  - src/tiny_swarm_world/application/ports/clients/port_portainer_client.py
  - src/tiny_swarm_world/infrastructure/adapters/clients/portainer_http_client.py
  - tests/infrastructure/adapters/clients/test_portainer_http_client.py
affected_modules:
  - tiny_swarm_world.application.ports.clients
  - tiny_swarm_world.infrastructure.adapters.clients
affected_contracts:
  - PortPortainerClient.ensure_local_endpoint
  - Portainer 2.39.x /api/endpoints
dependencies:
  - "01"
parallel_group: portainer-implementation
file_locks:
  - src/tiny_swarm_world/application/ports/clients/port_portainer_client.py
  - src/tiny_swarm_world/infrastructure/adapters/clients/portainer_http_client.py
  - tests/infrastructure/adapters/clients/test_portainer_http_client.py
contract_locks:
  - Portainer endpoint HTTP diagnostics
  - Portainer endpoint creation payload
architecture_locks:
  - Deployment infrastructure adapter boundary
quality_gates:
  targeted:
    - PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_portainer_http_client
  required:
    - python3 tools/quality_gate.py lint
documentation:
  arc42:
    - documentation/arc42/06_runtime_view.adoc
  adr: []
stop_conditions:
  - Portainer 2.39.x API evidence contradicts the socket endpoint model.
  - Response-body diagnostics cannot be redacted safely.
  - Domain code would need to import HTTP or Portainer details.
```

Done criteria:

* Endpoint creation failures expose status code and redacted body through a typed
  diagnostic path.
* `ensure_local_endpoint("local")` remains idempotent.
* The current socket endpoint payload is either verified for Portainer 2.39.x or
  changed with documented evidence.
* Tests prove no password, JWT, Authorization header, or secret assignment leaks.

Verification commands:

```bash
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_portainer_http_client
python3 tools/quality_gate.py lint
```

### Slice 03 - Deployment Bootstrap Evidence And Retry

Purpose:

Make `deployment:portainer-local-endpoint` preserve actionable diagnostics when
retries are exhausted and ensure deployment apply evidence includes structured
HTTP details.

Prerequisites:

* Slice 02 diagnostic contract exists.

```yaml
slice_id: "03"
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers:
  - Senior Tester
  - Senior System Architect
affected_files:
  - src/tiny_swarm_world/application/services/deployment/ensure_portainer_endpoint.py
  - src/tiny_swarm_world/application/services/deployment/workflows.py
  - tests/application/services/deployment/test_ensure_portainer_endpoint.py
  - tests/application/services/deployment/test_deployment_workflows.py
affected_modules:
  - tiny_swarm_world.application.services.deployment
affected_contracts:
  - deployment:portainer-local-endpoint
  - DeploymentApplyWorkflow failure evidence
dependencies:
  - "02"
parallel_group: portainer-implementation
file_locks:
  - src/tiny_swarm_world/application/services/deployment/ensure_portainer_endpoint.py
  - src/tiny_swarm_world/application/services/deployment/workflows.py
  - tests/application/services/deployment/test_ensure_portainer_endpoint.py
  - tests/application/services/deployment/test_deployment_workflows.py
contract_locks:
  - deployment bootstrap failure evidence
architecture_locks:
  - Deployment application service boundary
quality_gates:
  targeted:
    - PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_ensure_portainer_endpoint tests.application.services.deployment.test_deployment_workflows
  required:
    - python3 tools/quality_gate.py lint
documentation:
  arc42:
    - documentation/arc42/06_runtime_view.adoc
  adr: []
stop_conditions:
  - Failure evidence loses HTTP status or response body.
  - Retry/backoff sleeps slow down tests.
  - Unsafe raw payloads appear in reason, message, logs, or evidence.
```

Done criteria:

* Exhausted retries include endpoint name, attempts, final failure class,
  diagnostic status, and redacted response body when available.
* Deployment workflow `failed_to_apply` evidence carries structured HTTP
  diagnostics.
* Transient readiness still retries before failing.
* Deterministic creation failure does not hide behind the generic message.

Verification commands:

```bash
PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_ensure_portainer_endpoint tests.application.services.deployment.test_deployment_workflows
python3 tools/quality_gate.py lint
```

### Slice 04 - Endpoint Model Documentation

Purpose:

Document the authoritative endpoint model and remove ambiguity between Docker
socket endpoint and Portainer agent endpoint for the current stack.

Prerequisites:

* Slice 02 verifies endpoint creation contract.
* Slice 03 verifies evidence behavior.

```yaml
slice_id: "04"
profile: FULL_PATH
owner: Senior Documentation Engineer
secondary_reviewers:
  - Senior Requirement Engineer
  - Senior System Architect
  - Senior Tester
affected_files:
  - documentation/deployment/system.adoc
  - documentation/arc42/06_runtime_view.adoc
  - documentation/arc42/07_deployment_view.adoc
  - documentation/system/live-operation-surfaces.adoc
affected_modules:
  - documentation
affected_contracts:
  - deployment bootstrap documentation
dependencies:
  - "02"
  - "03"
parallel_group: documentation-sync
file_locks:
  - documentation/deployment/system.adoc
  - documentation/arc42/06_runtime_view.adoc
  - documentation/arc42/07_deployment_view.adoc
  - documentation/system/live-operation-surfaces.adoc
contract_locks:
  - Portainer endpoint model
architecture_locks:
  - arc42 runtime and deployment view
quality_gates:
  targeted:
    - git diff --check
  required:
    - git diff --check
documentation:
  arc42:
    - documentation/arc42/06_runtime_view.adoc
    - documentation/arc42/07_deployment_view.adoc
  adr: []
stop_conditions:
  - Documentation would claim live install success without live evidence.
  - Documentation contradicts implementation evidence.
```

Done criteria:

* Documentation states socket-backed `local` endpoint is authoritative for
  current bootstrap.
* Documentation states the agent remains deployed but is not the endpoint
  registration target unless a future workflow changes it.
* Documentation distinguishes endpoint registration from service readiness.

Verification commands:

```bash
git diff --check
```

### Slice 05 - Quality Gate And Optional Live Handoff

Purpose:

Run repository gates and define the live validation handoff for `./install.sh`.

Prerequisites:

* Slices 01 through 04 complete.

```yaml
slice_id: "05"
profile: FULL_PATH
owner: Senior Tester
secondary_reviewers:
  - Senior DevOps Engineer
  - Senior Python Automation Developer
affected_files: []
affected_modules:
  - quality
affected_contracts:
  - workflow quality gate
  - optional live installation validation
dependencies:
  - "01"
  - "02"
  - "03"
  - "04"
parallel_group: final-validation
file_locks: []
contract_locks:
  - QUALITY.md gate authority
architecture_locks: []
quality_gates:
  targeted:
    - PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_portainer_http_client
    - PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_ensure_portainer_endpoint tests.application.services.deployment.test_deployment_workflows
    - git diff --check
  required:
    - python3 tools/quality_gate.py quality
documentation:
  arc42:
    - documentation/arc42/06_runtime_view.adoc
    - documentation/arc42/07_deployment_view.adoc
  adr: []
stop_conditions:
  - Required quality gate fails.
  - Live validation is requested but operator consent or prerequisites are missing.
```

Done criteria:

* Targeted tests pass.
* Full quality gate is run or a documented, explicit reason is recorded.
* If live validation is explicitly requested, `./install.sh` passes
  `deployment:portainer-local-endpoint` or reports the exact remaining
  diagnostic evidence.

Verification commands:

```bash
python3 tools/quality_gate.py quality
```

Optional live validation command only after explicit live request:

```bash
./install.sh
```

## Slice Dependency Graph

```text
01 Regression Characterization
  -> 02 Portainer HTTP Diagnostic Contract
      -> 03 Deployment Bootstrap Evidence And Retry
          -> 04 Endpoint Model Documentation
              -> 05 Quality Gate And Optional Live Handoff
```

## Parallelization Opportunities

No write-capable parallel execution is recommended for Slices 01 through 03
because they share Portainer diagnostic and deployment evidence contracts. Slice
04 may begin read-only documentation review while Slice 03 is in progress, but
documentation writes must wait for implementation evidence.

## Role And Ownership Map

* Senior Workflow Architect: workflow structure, slice dependency order, handoff.
* Senior Requirement Engineer: EPIC alignment and requirement drift.
* Senior System Architect: hexagonal boundary and endpoint-model authority.
* Senior Python Automation Developer: application service, port, adapter
  implementation.
* Senior React Frontend Developer: no-impact confirmation for browser frontend.
* Senior Tester: regression tests and quality gates.
* Senior Documentation Engineer: deployment and arc42 synchronization.
* Senior DevOps Engineer: optional live validation readiness only after explicit
  user approval.

No subagents are assigned by this workflow because the user did not request
delegated or parallel agent work.

## Documentation Synchronization Points

Update documentation only after source and tests prove the behavior:

* `documentation/deployment/system.adoc`: endpoint bootstrap behavior,
  diagnostics, and endpoint model.
* `documentation/arc42/06_runtime_view.adoc`: runtime deployment bootstrap flow.
* `documentation/arc42/07_deployment_view.adoc`: deployment endpoint model and
  Portainer agent/socket distinction.
* `documentation/system/live-operation-surfaces.adoc`: privileged Portainer
  socket/agent surface remains explicit.

Do not document planned behavior as implemented behavior before Slice 05
evidence exists.

## Stop Conditions

Stop workflow execution and report if:

* Active branch is not `work/fix-workflow-portainer-local-endpoint-20260606`.
* Existing local changes overlap a slice lock.
* Portainer 2.39.x API contract cannot be verified from tests or primary
  implementation evidence.
* Diagnostics would expose unredacted credentials, JWTs, Authorization headers,
  secret values, or unsafe payloads.
* Implementation requires domain imports of infrastructure, HTTP, Docker, or
  logging details.
* Any live infrastructure command is required without explicit user approval.
* EPIC, arc42, or implementation evidence contradict the endpoint model.

## Uncertainty Escalation Rules

* Portainer API contract uncertainty routes to Senior Python Automation
  Developer and Senior System Architect.
* Endpoint model contradiction routes to Root Architect escalation through Senior
  System Architect.
* Secret-redaction conflict routes to Senior Tester and security review before
  diagnostics are widened.
* Quality failure routes through the Typed Error Router before retry.

## Commit And Push Plan

Commit and push are not part of `workflow create` unless the user requests them.
If requested after execution:

1. Review `git status --short`.
2. Run required gates or document skips.
3. Stage only workflow-approved files.
4. Commit with a message prepared from the completed slice evidence.
5. Push the active workflow branch only after successful commit and explicit
   approval or user instruction.

## Definition Of Done

The workflow is done when:

* `documentation/workflow/workflow.md` exists with slice metadata for every
  slice.
* `documentation/workflow/context-pack.md` and
  `documentation/workflow/context-pack.json` exist.
* Requirement, architecture, Python automation, frontend impact, and tester
  reports exist under `documentation/workflow/reports`.
* arc42 impact is checked and recorded.
* `git diff --check` passes for workflow artifacts.

The implementation is done later, during `workflow execute`, when:

* all slices complete;
* targeted tests pass;
* `python3 tools/quality_gate.py quality` passes or an explicit documented skip
  is accepted;
* optional live `./install.sh` validation, if requested, passes
  `deployment:portainer-local-endpoint` and continues to later setup phases.

## Handoff To Workflow Execute

Execute with:

```text
workflow execute
```

Workflow execute must run S3/S3D preflight, verify the active branch, verify
locks, then start with Slice 01. It must not run `./install.sh` unless the user
explicitly asks for live infrastructure validation during execution.

## arc42 Check Status

Checked during workflow creation:

* `documentation/arc42/06_runtime_view.adoc`
* `documentation/arc42/07_deployment_view.adoc`

The current arc42 runtime view already identifies deployment bootstrap as the
place where the local Docker endpoint is registered. Slice 04 must update arc42
after implementation evidence so documentation names the socket-backed endpoint
model and the agent distinction without claiming unverified live success.
