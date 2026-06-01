# Workflow: Portainer Admin Initialization Rejection Gate

## Metadata

```yaml
workflow_id: portainer-admin-init-rejection-v1.0.0
created: 2026-06-01
branch: feature/workflow-portainer-admin-init-20260601
status: READY_FOR_EXECUTION
request: "Create a self-checking workflow that validates the desired result, sends uncertain decisions through the requirements process, retries stop-signal refinement up to three times, pushes only above 92 percent confidence, and continues workflow execute with subagents until all slices are complete or a blocker is reported."
process_strand: S3D
execution_profile: NORMAL_PATH
primary_boundary: Deployment
secondary_boundaries:
  - Application ports
  - LXC-native adapter
  - Multipass legacy adapter
  - Quality governance
live_infrastructure_default: false
```

## Executive Summary

This workflow protects the Portainer admin bootstrap behavior in deployment
automation. Transient initialization failures must be retried, but an explicit
Portainer rejection after the endpoint is reachable must fail fast through the
typed application-port exception `PortainerAdminInitializationRejected`.

The workflow is self-checking: every execution slice has a verification command
that must fail when the desired behavior is absent. Stop signals are classified
through the Typed Error Router. If a stop signal exposes unclear requirements
instead of a local defect, execution returns to the Requirements process. The
requirement-refinement loop and targeted-fix loop are each capped at three
attempts. Commit and push are allowed only when confidence is strictly greater
than 0.92 and required D8 quality gates pass.

## Requirement Clarification Gate

```yaml
gate: requirement_clarification
status: READY_FOR_WORKFLOW
confidence: 0.94
decision: READY_FOR_WORKFLOW
requirement_cycles_completed: 3
confidence_threshold_for_push: "> 0.92"
```

Original request:

- Analyze the problem deeply.
- Create a workflow that checks whether the desired result occurs.
- Route uncertain decisions through the Requirements process.
- After three passes, push only when confidence is greater than 92 percent.
- Execute the workflow with subagents until all slices are complete.
- On a blocker that cannot be fixed locally, stop with an exact problem
  description and solution proposals.

Interpreted intent:

- The active behavior to protect is Portainer admin initialization retry versus
  rejection semantics during deployment setup.
- The regression risk is retrying a deterministic Portainer rejection as though
  it were only a transient readiness failure.
- The workflow must prove this behavior through mocked unit tests before commit
  or push.

Requirement process passes:

1. Senior Requirement Engineer classified the request as a functional
   deployment requirement, quality-gate requirement, and workflow-governance
   requirement. The first blocker was the missing concrete target behavior.
2. Repository evidence identified the target behavior in the Portainer admin
   access service, application port, LXC adapter, Multipass legacy adapter, and
   focused unit tests.
3. Senior Tester and Senior System Architect confirmed the behavior is testable
   without live infrastructure and preserves hexagonal boundaries.

Accepted assumptions:

- "Desired result" means the current Portainer admin initialization behavior
  visible in source and tests.
- Existing Multipass code remains explicit legacy/fallback surface and is
  verified only as an adapter boundary.
- No live infrastructure execution is authorized by this workflow.
- Subagent execution is represented by required project roles and skills unless
  callable subagent tooling is explicitly available during execution.

Non-goals:

- No live Portainer, LXD, Incus, LXC, Multipass, Docker Swarm, compose, Nexus,
  Jenkins, RabbitMQ, SonarQube, or Swagger/NGINX operation.
- No browser UI, React frontend, Java, Maven, Spring Boot, or Kubernetes-first
  behavior.
- No broad deployment refactor beyond the Portainer admin initialization
  contract.

## Verified Baseline At Authoring

- Active branch verified:
  `feature/workflow-portainer-admin-init-20260601`.
- `PortainerAdminInitializationRejected` exists in the application port module.
- `EnsurePortainerAdminAccess.run()` re-raises
  `PortainerAdminInitializationRejected` and retries other initialization
  exceptions until `max_attempts`.
- `LxcPortainerAdminClient.initialize_admin_user()` raises
  `PortainerAdminInitializationRejected` when Portainer returns HTTP failure
  and the requested credentials still cannot authenticate.
- `MultipassPortainerAdminClient.initialize_admin_user()` follows the same
  rejection contract for the explicit legacy adapter.
- `tests.application.services.deployment.test_ensure_portainer_admin_access`
  contains focused tests for transient retry and fail-fast rejection.

## Target Picture

After `workflow execute with subagents` completes:

- focused application-service tests prove transient initialization errors are
  retried;
- focused application-service tests prove typed rejection fails fast after one
  initialization attempt;
- adapter checks prove LXC-native and Multipass legacy clients raise the typed
  rejection instead of a generic runtime error for rejected admin bootstrap;
- arc42 documents the runtime and quality rule;
- required gates pass or execution stops with a typed failure report;
- slice checkpoint commits and pushes are allowed only after D8 quality passes.

## Architecture Constraints

- Domain code must not import Portainer clients, HTTP clients, command runners,
  logging setup, or infrastructure adapters.
- Application services may depend on the application port and the typed
  application-port exception.
- Infrastructure adapters own HTTP status interpretation and translate it into
  application-port semantics.
- Default provider direction remains LXC-native through LXD or Incus.
- Multipass remains explicit legacy/fallback provider surface only.
- No live infrastructure command is part of default verification.

## Role Ownership

- Senior Requirement Engineer: requirement normalization, three-pass confidence
  review, and unresolved ambiguity routing.
- Senior System Architect: hexagonal boundary and arc42 alignment.
- Senior Python Automation Developer: service and adapter contract behavior.
- Senior Tester: regression tests and self-check evidence.
- Senior DevOps Engineer: no-live-infrastructure gate review.

## Self-Checking Loop

For every stop signal during execution:

1. Classify through the Typed Error Router.
2. If the failure is a local implementation or test defect, attempt a targeted
   fix within the current slice.
3. If the failure changes intended behavior, return to the Requirements
   process and re-run the Three Amigos gate.
4. Repeat requirement-refinement plus targeted-fix cycles at most three times.
5. Continue only when confidence is strictly greater than 0.92 and required
   quality gates pass.
6. Stop after the third unresolved cycle with the exact blocker, inspected
   evidence, and solution proposals.

## Slice Plan

### Slice 01 - Requirement And Architecture Baseline

```yaml
slice_id: "01"
profile: NORMAL_PATH
owner: Senior Requirement Engineer
secondary_reviewers:
  - Senior System Architect
  - Senior Tester
affected_files:
  - documentation/workflow/**
  - documentation/arc42/06_runtime_view.adoc
  - documentation/arc42/10_quality_requirements.adoc
affected_modules:
  - workflow governance
  - deployment requirements
affected_contracts:
  - portainer-admin-initialization-contract
dependencies: []
parallel_group: serial-01
file_locks:
  - workflow-portainer-admin-init
  - arc42-runtime-view
  - arc42-quality-requirements
contract_locks:
  - portainer-admin-initialization-contract
architecture_locks:
  - deployment-hexagonal-boundary
quality_gates:
  targeted:
    - git diff --check
  required:
    - git diff --check
documentation:
  arc42: updated
  adr: not required
stop_conditions:
  - The desired Portainer admin initialization behavior cannot be stated as a testable result.
  - The behavior conflicts with the autonomous setup EPIC or provider direction.
```

Done criteria:

- Requirement, assumptions, non-goals, and confidence threshold are recorded.
- arc42 runtime and quality documentation mention the Portainer admin
  initialization rejection gate.
- No planned behavior is presented as live infrastructure success.

### Slice 02 - Application Service Self-Check

```yaml
slice_id: "02"
profile: NORMAL_PATH
owner: Senior Python Automation Developer
secondary_reviewers:
  - Senior Tester
  - Senior System Architect
affected_files:
  - src/tiny_swarm_world/application/ports/clients/port_portainer_admin_client.py
  - src/tiny_swarm_world/application/services/deployment/ensure_portainer_admin_access.py
  - tests/application/services/deployment/test_ensure_portainer_admin_access.py
affected_modules:
  - tiny_swarm_world.application.ports.clients
  - tiny_swarm_world.application.services.deployment
affected_contracts:
  - PortPortainerAdminClient
  - EnsurePortainerAdminAccess
dependencies:
  - "01"
parallel_group: serial-02
file_locks:
  - portainer-admin-application-service
contract_locks:
  - portainer-admin-initialization-contract
architecture_locks:
  - application-depends-on-ports
quality_gates:
  targeted:
    - PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_ensure_portainer_admin_access
  required:
    - PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_ensure_portainer_admin_access
    - git diff --check
documentation:
  arc42: no-change-expected
  adr: not required
stop_conditions:
  - Typed rejection is retried instead of failing fast.
  - Transient initialization failures no longer retry.
  - Test evidence would require live Portainer.
```

Done criteria:

- The focused test fails if typed Portainer rejection is not re-raised.
- The focused test fails if transient initialization failure is not retried.
- No secrets or raw credentials appear in verification evidence.

### Slice 03 - Adapter Contract Self-Check

```yaml
slice_id: "03"
profile: NORMAL_PATH
owner: Senior Python Automation Developer
secondary_reviewers:
  - Senior Tester
  - Senior DevOps Engineer
affected_files:
  - src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py
  - src/tiny_swarm_world/infrastructure/adapters/clients/multipass_portainer_admin_client.py
  - tests/infrastructure/adapters/clients/**
affected_modules:
  - tiny_swarm_world.infrastructure.adapters.clients
affected_contracts:
  - LxcPortainerAdminClient
  - MultipassPortainerAdminClient
dependencies:
  - "02"
parallel_group: serial-03
file_locks:
  - portainer-admin-client-adapters
contract_locks:
  - portainer-admin-initialization-contract
architecture_locks:
  - infrastructure-implements-ports
quality_gates:
  targeted:
    - PYTHONPATH=src python3 -m unittest discover -s tests/infrastructure/adapters/clients
  required:
    - PYTHONPATH=src python3 -m unittest discover -s tests/infrastructure/adapters/clients
    - git diff --check
documentation:
  arc42: no-change-expected
  adr: not required
stop_conditions:
  - Adapter tests would require live LXC, Incus, Multipass, Docker, or Portainer.
  - HTTP rejection semantics cannot be verified through mocked sessions.
```

Done criteria:

- Adapter tests verify HTTP rejection maps to
  `PortainerAdminInitializationRejected`.
- Adapter tests verify existing credentials after HTTP rejection do not raise.
- Default LXC-native direction remains separate from Multipass legacy behavior.

### Slice 04 - Full Quality Gate And Checkpoint Push

```yaml
slice_id: "04"
profile: NORMAL_PATH
owner: Senior Tester
secondary_reviewers:
  - Senior System Architect
  - Senior DevOps Engineer
affected_files:
  - documentation/workflow/**
  - documentation/arc42/**
  - src/tiny_swarm_world/application/**
  - src/tiny_swarm_world/infrastructure/adapters/clients/**
  - tests/**
affected_modules:
  - quality gate
  - workflow execution report
affected_contracts:
  - D8 quality decision
dependencies:
  - "03"
parallel_group: serial-04
file_locks:
  - quality-result-report
contract_locks:
  - D8-quality-decision
architecture_locks:
  - hexagonal-architecture-quality
quality_gates:
  targeted:
    - git diff --check
  required:
    - python3 tools/quality_gate.py quality
documentation:
  arc42: checked
  adr: not required
stop_conditions:
  - Full quality gate fails and cannot be classified into a typed route.
  - Commit or push would include files outside completed slice scope.
  - Active branch is not feature/workflow-portainer-admin-init-20260601.
```

Done criteria:

- Required D8 gates pass.
- `git diff --check` and `git diff --cached --check` pass before commit.
- A slice-scoped checkpoint commit is created.
- The workflow branch is pushed to `origin`.

## Dependency Graph

```text
01 -> 02 -> 03 -> 04
```

Execution is serial. The slices share the Portainer admin initialization
contract and must not run in parallel.

## Quality Gate Expectations

Targeted checks:

```bash
PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_ensure_portainer_admin_access
PYTHONPATH=src python3 -m unittest discover -s tests/infrastructure/adapters/clients
git diff --check
```

Required final gate:

```bash
python3 tools/quality_gate.py quality
```

## Stop Conditions

Stop and report when:

- the branch is not `feature/workflow-portainer-admin-init-20260601`;
- the worktree has unrelated or unclear changes;
- the desired behavior no longer matches the accepted requirement;
- a required test needs live infrastructure;
- architecture boundaries would require application code to import concrete
  infrastructure adapters;
- quality failures cannot be classified;
- retry or requirement-refinement cycles exceed three attempts;
- confidence after three cycles is less than or equal to 0.92.

## Definition Of Done

- All slices are complete.
- Required self-checks prove the desired behavior.
- arc42 runtime and quality documentation are synchronized.
- D8 quality gates pass or a Stop.Signal records the exact unresolved blocker.
- Changes are committed and pushed only from the workflow branch.

## Handoff To Workflow Execute

`workflow execute with subagents` may start after verifying:

```bash
git branch --show-current
git show-ref --verify --quiet refs/heads/feature/workflow-portainer-admin-init-20260601
git status --short --branch
```

Expected branch:

```text
feature/workflow-portainer-admin-init-20260601
```

## arc42 Check Status

`documentation/arc42/06_runtime_view.adoc` and
`documentation/arc42/10_quality_requirements.adoc` are updated by Slice 01.
