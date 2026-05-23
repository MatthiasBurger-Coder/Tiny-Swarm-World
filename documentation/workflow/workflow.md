# Workflow: Full Installation Integration Verification

## Executive Summary

This workflow defines the governed path for creating and running an opt-in
integration test that proves Tiny Swarm World can perform a complete local
installation and verify full operational functionality.

The target proof is not a mock-only quality gate. It must verify, with recorded
evidence, that a Linux/WSL host can bootstrap Multipass VMs, configure
networking, install Docker, initialize Docker Swarm, join workers, deploy the
service stacks, and reach the expected services from the host.

The workflow does not execute live infrastructure during workflow creation.
Live Multipass, Docker Swarm, netplan, socat and stack deployment commands stay
behind an explicit opt-in gate during workflow execution.

## Target Picture

### Verified Baseline

- The repository default quality gate is `python3 tools/quality_gate.py quality`.
- The default quality gate must not create VMs, change networking, deploy
  Docker stacks or bootstrap local services.
- `AUDIT_REPORT.md` records that full end-to-end operational readiness was not
  verified and that live Multipass/Docker/Swarm evidence is missing.
- `OPERATIONAL_READINESS_CHECKLIST.md` records open readiness items for host,
  VM, network, Docker, Swarm, stack deployment, services, smoke tests,
  observability and documentation.
- The current package entrypoint exposes explicit service choices only:
  `multipass-init-vms`, `network-prepare-netplan`, `network-setup-netplan`,
  `multipass-restart-vms`, `multipass-docker-install`,
  `multipass-docker-swarm-init` and `vm-ip-list`.
- Service stack deployment exists as separate preparation or compose scripts,
  not as a single verified canonical full-install command.

### Target Outcome

The completed workflow must produce:

- a non-destructive live-test contract and preflight gate;
- a canonical full-installation verification path;
- deterministic evidence for every installation phase;
- automated health checks for Docker Swarm and deployed services;
- explicit remediation loops for blockers that can be solved with at least
  90 percent confidence;
- a Three Amigos question-answer escalation path for blockers that require
  product, architecture or test clarification;
- documentation that tells an operator how to run the full integration test and
  interpret failures.

## Requirement Clarification Record

Original request:

```text
Erstelle einen workflow fuer einen Integrationstest, der eine vollstaendige
Installations prueft, vollstaendige funktionsfaehigkeit. Falls blocker
entstehen, diese vollstaendig selbst loesen wenn dies zu 90% moeglich ist,
ansonsten rueckfragen stellen, damit ein 3 Amigo Frage Antwort prozess
gestartet werden kann.
```

Interpreted intent:

- Create a repository workflow for an opt-in integration test that proves the
  full installation and functional readiness of Tiny Swarm World.
- Include all major operational phases from host readiness through service
  reachability.
- Make blocker handling explicit: self-remediate when confidence is at least
  90 percent, otherwise stop and ask Three Amigos clarification questions.
- Preserve root `AGENTS.md`, `QUALITY.md`, hexagonal architecture and live
  infrastructure safety constraints.

Change type:

- Workflow creation and verification-governance planning.
- Future implementation of integration-test harness, preflight checks,
  live-test evidence capture and documentation.

Affected process strand:

- `workflow create`.

Affected architecture area:

- Platform automation: Multipass, VM lifecycle, network, netplan, socat,
  Docker install, Docker Swarm init and worker join.
- Deployment automation: Portainer, compose stack deployment and service
  reachability.
- Shared automation: command workflow, YAML handling, logging, failure
  propagation and evidence capture.
- Documentation and operational readiness.

Explicit requirements:

- Create a workflow for a full installation integration test.
- Verify complete functionality, not only command construction.
- Resolve blockers completely when the solution path is at least 90 percent
  clear.
- Ask clarifying questions and start a Three Amigos Q&A process when blockers
  cannot be solved confidently.

Implicit requirements:

- Do not run live infrastructure commands during normal development gates.
- Make the integration test opt-in and visibly live/destructive-risk aware.
- Separate preflight, dry-run/static checks and live execution.
- Collect logs, command results and endpoint health evidence.
- Keep the Python automation architecture hexagonal.
- Keep `src/main/java` out of scope unless service reachability requires a
  deployed example application in a later clarified workflow.

Assumptions:

- "Complete installation" means the product scope described by the repository:
  Multipass VMs, Docker Swarm and the supported service stacks.
- "Complete functionality" means host reachability and runtime health for the
  deployed local infrastructure services listed in README and AGENTS.md.
- The integration test may add new opt-in tooling, but must not weaken the
  default quality gate.
- Live execution requires an explicit workflow-execution approval before any
  Multipass, Docker Swarm, netplan, socat or stack deployment command runs.

Non-goals:

- No live infrastructure execution during workflow creation.
- No Java deployment-example changes.
- No cloud provider support.
- No Windows-native PowerShell or backslash-path runtime model.
- No default CI job that runs live Multipass or Docker Swarm.
- No secret defaults committed to the repository.

Risks:

- Current orchestration is not proven end-to-end.
- Some existing setup behavior may be destructive or not idempotent.
- Stack deployment may require secret handling and Portainer initialization.
- Network and port-forwarding behavior differs between native Linux and WSL.
- Full live validation can be slow and host-dependent.

Open questions:

- Which services are mandatory for the first "full functionality" proof if a
  host lacks resources for all stacks?
- Should the live test require a clean host, or may it reconcile an existing
  Tiny Swarm World environment?
- Which cleanup mode is acceptable after a successful live run: preserve,
  stop-only, or destroy?

Blocking questions:

- None for workflow creation. The open questions become live-execution gates
  and are handled through the Three Amigos escalation path when they affect a
  concrete run.

Confidence level:

- 92 percent for workflow creation.
- Less than 90 percent for immediate live execution without additional operator
  approval and environment facts.

Decision:

```text
READY_FOR_WORKFLOW
```

EPIC traceability:

- No `documentation/epics` directory exists in the repository.
- Answer to "Does the implementation still match the EPIC?": no EPIC source is
  available; this is recorded as a traceability gap, not a workflow-creation
  blocker.

## Three Amigos Review

### Senior Requirement Engineer

- The requirement is testable when "complete installation" is decomposed into
  host, Python, VM, network, Docker, Swarm, deployment, service reachability,
  evidence and rerun checks.
- The workflow must define mandatory and optional functionality explicitly.
- Open live-run policy questions are non-blocking for workflow authoring.

### Senior System Architect

- The integration test must exercise platform and deployment behavior without
  moving concrete adapter construction out of `infrastructure/composition.py`.
- Live-test tooling must remain outside domain code.
- Stack deployment verification belongs to the Deployment responsibility.
- VM, network, Docker and Swarm verification belongs to the Platform
  responsibility.

### Senior Python Automation Developer

- Preflight, orchestration and probes should be implemented as small
  application use cases behind ports where behavior becomes reusable.
- The live runner can live under `tools/` as an operator entrypoint while using
  application services through composition.
- Constructors must not execute external commands.
- Command results must preserve exit code, stdout, stderr, node identity and
  phase identity.

### Senior React Frontend Developer

- No frontend module exists and this workflow does not introduce one.
- UI verification is endpoint reachability and HTTP/API readiness only.
- If later evidence dashboards are requested, that requires a separate
  frontend workflow.

### Senior Tester

- Default tests must remain mock-based and deterministic.
- Live integration checks must be skipped unless an explicit environment
  variable and command-line confirmation are both present.
- The live test must fail on partial installation, hidden command failure,
  missing health evidence or unreachable mandatory services.
- The workflow needs a dry-run mode before live execution.

### Dependency And Deadlock Validator

- The workflow has one critical chain: preflight -> orchestration contract ->
  platform readiness -> deployment readiness -> live runner -> docs.
- Documentation updates can happen late, but must consume actual command names
  and evidence paths produced by the implementation slices.
- Live execution is gated after implementation and quality gates, so it does
  not deadlock default development verification.

## Complete Functionality Definition

The integration test proves complete functionality only when all mandatory
checks pass:

- Host environment: Linux or WSL detected, Python version supported,
  dependencies installed, Multipass available, Docker CLI available where
  required, and required ports not occupied.
- Python entrypoint: canonical commands are discoverable from repository root.
- VM lifecycle: manager and worker VMs exist or are created according to the
  selected mode, and VM state is verified.
- Network: manager IP, worker IPs, gateway, netplan transfer/application and
  WSL/Linux forwarding checks are verified.
- Docker: Docker daemon is installed and healthy on every node.
- Swarm: manager is active, worker token retrieval succeeds, workers are joined
  and visible through `docker node ls`.
- Deployment: Portainer stack deploys and at least Nexus, Jenkins, RabbitMQ,
  SonarQube and Swagger/NGINX stacks are deployed or explicitly classified as
  resource-gated with Three Amigos approval.
- Reachability: mandatory service endpoints respond from the host or produce
  actionable failure evidence.
- Rerun safety: a second verification run detects existing state and does not
  perform an implicit destructive reset.
- Evidence: logs, command results, endpoint probe results and readiness summary
  are stored under a deterministic ignored artifact directory.

## Scope

In scope:

- Workflow and context documentation.
- Future opt-in live integration test harness.
- Preflight checks for host, Python, Multipass, Docker, ports, secrets and
  resource availability.
- Dry-run command plan verification.
- Full live install sequence verification.
- Health probes for platform and service endpoints.
- Evidence capture and failure reporting.
- Documentation updates and readiness checklist synchronization.

Out of scope:

- Executing live infrastructure during workflow creation.
- Running live infrastructure in default CI.
- Expanding Windows-native support.
- Refactoring unrelated legacy modules.
- Changing Java example application behavior.

## Architecture Constraints

- Preserve hexagonal architecture.
- Domain code must not import application or infrastructure.
- Application services depend on ports and domain objects, not concrete
  adapters.
- Infrastructure adapters implement ports and own technology-specific behavior.
- Standard runtime wiring remains in `src/tiny_swarm_world/infrastructure/composition.py`.
- `src/tiny_swarm_world/__main__.py` stays thin.
- Live-test tooling must make live side effects explicit.
- Secrets must come from environment or ignored local files, never committed
  defaults.
- Linux/WSL and POSIX paths are the only supported runtime model.

## Python Automation Assessment

Expected implementation direction:

- Add a preflight model that validates host/runtime readiness before any live
  command runs.
- Add or expose a canonical full-install command sequence without hiding
  external execution in constructors.
- Add structured phase results for VM, network, Docker, Swarm, deployment and
  service probes.
- Keep command construction deterministic and testable with mocks.
- Preserve `PYTHONPATH=src` or package execution behavior documented by the
  repository until packaging is explicitly changed.

## Frontend Assessment

No frontend changes are planned. The integration test checks operational
endpoints, not browser UX. Any future dashboard, replay UI or evidence viewer
requires a separate frontend workflow and Three Amigos review.

## Test Strategy

Default verification:

```bash
python3 tools/quality_gate.py lint
python3 tools/quality_gate.py arch-lint
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py typecheck
python3 tools/quality_gate.py test
python3 tools/quality_gate.py quality
```

Targeted development checks should use the nearest relevant existing gate from
`QUALITY.md`. New live integration tooling must also include deterministic unit
tests with mocked command execution and mocked endpoint probes.

Live verification:

- introduced by a later implementation slice;
- never included in the default quality gate;
- requires explicit operator confirmation;
- refuses to run without a successful preflight;
- stores evidence in an ignored artifact directory;
- reports every failed phase with owner, command, exit status and remediation
  classification.

## Resilience Requirements

- Every external command must have a timeout.
- Retriable readiness checks must have bounded retries and diagnostics.
- Non-retriable critical failures must abort the live run.
- Cleanup must be explicit and never implicit after failure.
- Reruns must detect existing VMs, Docker state, Swarm state and stacks.
- A failure report must separate host blockers, product defects, configuration
  gaps, secret gaps and resource limits.

## Blocker Remediation And Three Amigos Q&A

When a blocker appears during workflow execution, use this decision path:

1. Capture evidence: phase, command or probe, expected result, actual result,
   logs, exit code, stdout, stderr and affected files.
2. Classify the blocker:
   - host prerequisite missing;
   - configuration or secret missing;
   - deterministic implementation defect;
   - flaky runtime readiness;
   - architecture ambiguity;
   - product-scope ambiguity;
   - resource limitation.
3. Self-remediate only when all are true:
   - root cause confidence is at least 90 percent;
   - the fix stays inside the active slice write scope;
   - the fix does not require new product policy;
   - the fix preserves architecture and safety rules;
   - verification can prove the fix in the current environment.
4. Retry at most three targeted remediation loops for the same blocker.
5. Stop and start Three Amigos Q&A when confidence is below 90 percent, the
   fix requires scope clarification, the environment decision belongs to the
   operator, or the third retry fails.

Three Amigos Q&A must ask concise blocking questions with these roles:

- Requirement: what result must count as successful functionality?
- Architecture: which boundary or runtime behavior is authoritative?
- Testing: what evidence proves the run is acceptable?
- Python automation: which command, adapter or workflow owns the fix?
- Operations: which host, secret, resource or cleanup decision is allowed?

## Ordered Slices

### Slice 01 - Integration Test Contract

Purpose:

- Convert this workflow into a concrete integration-test contract with
  mandatory checks, optional checks, live-run consent and evidence semantics.

```yaml
slice_id: "01"
profile: "FULL_PATH"
owner: "Senior Requirement Engineer"
secondary_reviewers:
  - "Senior Tester"
  - "Senior System Architect"
affected_files:
  - "documentation/workflow/workflow.md"
  - "documentation/workflow/context-pack.md"
  - "documentation/workflow/context-pack.json"
  - "OPERATIONAL_READINESS_CHECKLIST.md"
affected_modules: []
affected_contracts:
  - "full-installation-integration-test-contract"
dependencies: []
parallel_group: "A"
file_locks:
  - "documentation/workflow/**"
  - "OPERATIONAL_READINESS_CHECKLIST.md"
contract_locks:
  - "integration-test-success-criteria"
architecture_locks:
  - "live-infrastructure-safety"
quality_gates:
  targeted:
    - "git diff --check"
  required:
    - "git diff --check"
documentation:
  arc42: "check only"
  adr: "check ADR platform/artifacts/deployment split"
stop_conditions:
  - "mandatory functionality cannot be defined without product clarification"
  - "live-run consent semantics are unclear"
```

Allowed write scope:

- Workflow and readiness documentation only.

Done criteria:

- Mandatory, optional and resource-gated checks are explicit.
- Live side effects require opt-in consent.
- Evidence semantics are documented.

### Slice 02 - Preflight And Configuration Validation

Purpose:

- Add deterministic preflight checks that fail before live side effects when
  host, dependencies, secrets, ports or resource limits are not ready.

```yaml
slice_id: "02"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Tester"
  - "Senior DevOps Engineer"
  - "Senior Security Sandbox Engineer"
affected_files:
  - "src/tiny_swarm_world/application/**"
  - "src/tiny_swarm_world/domain/**"
  - "src/tiny_swarm_world/infrastructure/**"
  - "tests/**"
  - "tools/**"
affected_modules:
  - "tiny_swarm_world.application"
  - "tiny_swarm_world.domain"
  - "tiny_swarm_world.infrastructure"
affected_contracts:
  - "preflight-result"
  - "live-run-consent"
dependencies:
  - "01"
parallel_group: "B"
file_locks:
  - "src/tiny_swarm_world/**"
  - "tests/**"
  - "tools/**"
contract_locks:
  - "preflight-result"
architecture_locks:
  - "hexagonal-import-boundaries"
  - "external-command-safety"
quality_gates:
  targeted:
    - "python3 tools/quality_gate.py test"
    - "python3 tools/quality_gate.py typecheck"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "update if a new preflight concept is introduced"
  adr: "not required unless responsibility boundaries change"
stop_conditions:
  - "preflight would need to execute live infrastructure commands"
  - "secret handling cannot be made explicit"
```

Allowed write scope:

- Python preflight code, tests and tool entrypoints needed for preflight only.

Done criteria:

- Preflight can run without creating VMs or changing networking.
- Missing prerequisites produce actionable failures.
- Unit tests cover each preflight outcome.

### Slice 03 - Canonical Full-Installation Plan

Purpose:

- Define a canonical full-installation plan that sequences existing platform
  services and identifies missing deployment steps before live execution.

```yaml
slice_id: "03"
profile: "FULL_PATH"
owner: "Senior System Architect"
secondary_reviewers:
  - "Senior Python Automation Developer"
  - "Senior Tester"
affected_files:
  - "src/tiny_swarm_world/application/**"
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "src/tiny_swarm_world/__main__.py"
  - "tests/**"
  - "documentation/**"
affected_modules:
  - "tiny_swarm_world.application.services.platform"
  - "tiny_swarm_world.infrastructure.composition"
affected_contracts:
  - "full-installation-plan"
dependencies:
  - "01"
  - "02"
parallel_group: "C"
file_locks:
  - "src/tiny_swarm_world/application/**"
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "src/tiny_swarm_world/__main__.py"
  - "tests/**"
contract_locks:
  - "full-installation-plan"
architecture_locks:
  - "thin-entrypoint"
  - "composition-root-wiring"
quality_gates:
  targeted:
    - "python3 tools/quality_gate.py arch-tests"
    - "python3 tools/quality_gate.py test"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "runtime and deployment view check"
  adr: "check ADR platform/artifacts/deployment split"
stop_conditions:
  - "canonical sequence cannot be defined from current services"
  - "entrypoint would need low-level infrastructure imports"
```

Allowed write scope:

- Full-installation planning use case, composition wiring, thin CLI exposure
  and matching tests.

Done criteria:

- A dry-run plan lists every phase in order.
- The plan has no hidden live execution.
- Tests prove the order and failure propagation.

### Slice 04 - Platform Runtime Readiness Probes

Purpose:

- Implement platform probes for VM state, network readiness, Docker daemon
  health, Swarm manager state, worker join status and rerun safety.

```yaml
slice_id: "04"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior DevOps Engineer"
  - "Senior Tester"
  - "Senior System Architect"
affected_files:
  - "src/tiny_swarm_world/application/**"
  - "src/tiny_swarm_world/domain/**"
  - "src/tiny_swarm_world/infrastructure/**"
  - "infra/config/**"
  - "tests/**"
affected_modules:
  - "tiny_swarm_world.application.services.platform"
  - "tiny_swarm_world.infrastructure.adapters"
affected_contracts:
  - "platform-readiness-result"
dependencies:
  - "03"
parallel_group: "D"
file_locks:
  - "src/tiny_swarm_world/**"
  - "infra/config/**"
  - "tests/**"
contract_locks:
  - "platform-readiness-result"
architecture_locks:
  - "platform-responsibility-boundary"
  - "command-result-evidence"
quality_gates:
  targeted:
    - "python3 tools/quality_gate.py test"
    - "python3 tools/quality_gate.py typecheck"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "runtime view update if probes become product behavior"
  adr: "not required unless ownership changes"
stop_conditions:
  - "probe requires destructive reset as default behavior"
  - "Docker or Swarm output parsing is ambiguous"
```

Allowed write scope:

- Platform readiness code, command result parsing, tests and relevant config
  validation.

Done criteria:

- Probes are mock-testable.
- Live probe failures contain node, command and expected state.
- Rerun safety is explicitly checked.

### Slice 05 - Deployment And Service Readiness Probes

Purpose:

- Implement deployment probes that verify Portainer, stack lifecycle and service
  endpoint health for the supported service set.

```yaml
slice_id: "05"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior DevOps Engineer"
  - "Senior Security Sandbox Engineer"
  - "Senior Tester"
affected_files:
  - "src/tiny_swarm_world/application/**"
  - "src/tiny_swarm_world/domain/**"
  - "src/tiny_swarm_world/infrastructure/**"
  - "infra/config/compose/**"
  - "infra/compose/**"
  - "tests/**"
affected_modules:
  - "tiny_swarm_world.application.services.deployment"
  - "tiny_swarm_world.infrastructure.adapters"
affected_contracts:
  - "deployment-readiness-result"
  - "service-health-probe"
dependencies:
  - "03"
parallel_group: "D"
file_locks:
  - "src/tiny_swarm_world/**"
  - "infra/config/compose/**"
  - "infra/compose/**"
  - "tests/**"
contract_locks:
  - "deployment-readiness-result"
  - "service-health-probe"
architecture_locks:
  - "deployment-responsibility-boundary"
  - "secret-handling"
quality_gates:
  targeted:
    - "python3 tools/quality_gate.py test"
    - "python3 tools/quality_gate.py typecheck"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "deployment view update if deployment behavior changes"
  adr: "not required unless service ownership changes"
stop_conditions:
  - "hardcoded credentials would be required"
  - "stack manifests are not safe for Swarm validation"
  - "mandatory service list cannot be satisfied on target resources"
```

Allowed write scope:

- Deployment readiness code, service health probes, tests and stack validation
  support.

Done criteria:

- Service probes are explicit and timeout-bounded.
- Missing secrets fail before stack deployment.
- Portainer and service endpoint failures produce actionable evidence.

### Slice 06 - Live Integration Runner And Evidence Bundle

Purpose:

- Add the opt-in live runner that executes preflight, dry-run plan,
  full-installation phases, probes and evidence collection.

```yaml
slice_id: "06"
profile: "FULL_PATH"
owner: "Senior DevOps Engineer"
secondary_reviewers:
  - "Senior Python Automation Developer"
  - "Senior Tester"
  - "Senior Security Sandbox Engineer"
affected_files:
  - "tools/**"
  - "src/tiny_swarm_world/**"
  - "tests/**"
  - ".gitignore"
affected_modules:
  - "tiny_swarm_world.application"
  - "tiny_swarm_world.infrastructure"
affected_contracts:
  - "live-integration-runner"
  - "evidence-bundle"
dependencies:
  - "04"
  - "05"
parallel_group: "E"
file_locks:
  - "tools/**"
  - "src/tiny_swarm_world/**"
  - "tests/**"
  - ".gitignore"
contract_locks:
  - "live-integration-runner"
  - "evidence-bundle"
architecture_locks:
  - "live-infrastructure-safety"
  - "failure-propagation"
quality_gates:
  targeted:
    - "python3 tools/quality_gate.py test"
    - "python3 tools/quality_gate.py typecheck"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "runtime view and quality requirements check"
  adr: "not required unless live-test policy changes"
stop_conditions:
  - "runner can execute live commands without explicit confirmation"
  - "evidence artifacts would be committed"
  - "critical command failures can be hidden"
```

Allowed write scope:

- Live runner, evidence paths, ignored artifact directories and tests.

Done criteria:

- The live runner refuses to run without explicit confirmation.
- Dry-run mode is available.
- Evidence output is deterministic and ignored by Git.
- Critical failures produce non-zero exit status.

### Slice 07 - Documentation And Readiness Synchronization

Purpose:

- Update operator documentation, troubleshooting and readiness checklist from
  the implemented integration-test behavior.

```yaml
slice_id: "07"
profile: "FULL_PATH"
owner: "Senior Documentation Engineer"
secondary_reviewers:
  - "Senior Tester"
  - "Senior DevOps Engineer"
  - "Senior System Architect"
affected_files:
  - "README.md"
  - "documentation/**"
  - "OPERATIONAL_READINESS_CHECKLIST.md"
affected_modules: []
affected_contracts:
  - "operator-runbook"
dependencies:
  - "06"
parallel_group: "F"
file_locks:
  - "README.md"
  - "documentation/**"
  - "OPERATIONAL_READINESS_CHECKLIST.md"
contract_locks:
  - "operator-runbook"
architecture_locks:
  - "documentation-authority"
quality_gates:
  targeted:
    - "git diff --check"
  required:
    - "git diff --check"
documentation:
  arc42: "update runtime, deployment, quality and risk sections as needed"
  adr: "not required unless policy changes"
stop_conditions:
  - "documentation would claim live validation without evidence"
  - "runbook contains host-specific secrets or absolute paths"
```

Allowed write scope:

- README, documentation and readiness checklist only.

Done criteria:

- Runbook has exact commands and prerequisites.
- Troubleshooting maps common failures to remediation.
- Readiness checklist reflects implemented and verified behavior.

### Slice 08 - Controlled Live Verification

Purpose:

- Run the implemented opt-in integration test in a suitable Linux/WSL
  environment and record the result without weakening default quality gates.

```yaml
slice_id: "08"
profile: "FULL_PATH"
owner: "Senior Tester"
secondary_reviewers:
  - "Senior DevOps Engineer"
  - "Senior Security Sandbox Engineer"
  - "Senior Requirement Engineer"
affected_files:
  - "documentation/workflow/execution-report.md"
  - "OPERATIONAL_READINESS_CHECKLIST.md"
affected_modules: []
affected_contracts:
  - "live-verification-evidence"
dependencies:
  - "07"
parallel_group: "G"
file_locks:
  - "documentation/workflow/execution-report.md"
  - "OPERATIONAL_READINESS_CHECKLIST.md"
contract_locks:
  - "live-verification-evidence"
architecture_locks:
  - "live-infrastructure-safety"
quality_gates:
  targeted:
    - "python3 tools/quality_gate.py quality"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "check after live evidence"
  adr: "not required unless live policy changes"
stop_conditions:
  - "operator has not explicitly approved live infrastructure execution"
  - "preflight fails"
  - "same blocker has failed three targeted remediation attempts"
  - "confidence is below 90 percent and Three Amigos questions are unresolved"
```

Allowed write scope:

- Execution report and readiness evidence updates only, unless a blocker is
  self-remediated with at least 90 percent confidence inside the owning slice.

Done criteria:

- Live test either passes with evidence or stops with a classified blocker.
- Any self-remediation has targeted verification.
- Any unresolved blocker has Three Amigos questions recorded.

## Slice Dependency Graph

```text
01
  -> 02
      -> 03
          -> 04
          -> 05
              -> 06
                  -> 07
                      -> 08
```

Parallelization:

- Slice 04 and Slice 05 may be implemented in parallel only after Slice 03
  stabilizes shared result contracts.
- Slice 07 documentation can draft structure early, but final content depends
  on Slice 06 command names and evidence paths.
- Slice 08 is always sequential and gated by live-run approval.

## Role Ownership Map

- Senior Requirement Engineer: requirement contract, acceptance criteria,
  Three Amigos Q&A and resource-gated service decisions.
- Senior System Architect: architecture boundaries, responsibility ownership,
  composition root and arc42 alignment.
- Senior Python Automation Developer: preflight, command orchestration,
  readiness probes and testable implementation.
- Senior DevOps Engineer: live runner, host prerequisites, evidence layout,
  runtime diagnostics and shell/script interaction.
- Senior Security Sandbox Engineer: secret handling, destructive command
  controls and live-run consent.
- Senior Tester: unit coverage, live verification strategy, failure evidence
  and final test report.
- Senior Documentation Engineer: runbook, troubleshooting and readiness
  checklist synchronization.

## Quality-Gate Expectations

Required default gate for implementation slices:

```bash
python3 tools/quality_gate.py quality
```

Targeted gates during development:

```bash
python3 tools/quality_gate.py lint
python3 tools/quality_gate.py arch-lint
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py typecheck
python3 tools/quality_gate.py test
```

Documentation-only gate:

```bash
git diff --check
```

Live integration commands introduced by this workflow are not replacements for
the default quality gate. They are additional opt-in evidence commands after
the implementation slices define them.

## Documentation Synchronization Points

- After Slice 01: readiness checklist aligns with success criteria.
- After Slice 03: README and runtime docs know the canonical plan name.
- After Slice 06: runbook records exact live runner command, preflight command,
  dry-run command and evidence path.
- After Slice 08: execution report records pass/fail evidence and unresolved
  blockers.

## Stop Conditions

Stop workflow execution when:

- the active branch is not the workflow branch;
- unrelated worktree changes conflict with the slice write scope;
- a required quality gate fails;
- a live command would run without explicit approval;
- a command failure is not propagated;
- hardcoded secrets would be committed;
- default behavior would delete VMs or stacks implicitly;
- a service success criterion is ambiguous;
- a blocker cannot be solved with at least 90 percent confidence;
- Three Amigos questions are unresolved.

## Commit And Push Plan

- Commit only after the relevant required gates pass.
- Keep workflow creation documentation separate from implementation slices.
- Do not include generated evidence artifacts, logs, local env files or secrets.
- Use git commit preparation before committing or pushing.
- Do not push or open a PR unless explicitly requested.

## Definition Of Done

This workflow is done when:

- the live integration test contract is documented;
- preflight and dry-run modes exist;
- full live install verification is opt-in and safety-gated;
- platform, deployment and service health probes are implemented;
- evidence is deterministic and ignored by Git;
- default quality gate passes;
- live verification either passes or stops with classified blockers and Three
  Amigos questions;
- README, documentation and readiness checklist match the implemented behavior.

## Handoff To Workflow Execute

Workflow execute must begin with Slice 01. It must not skip directly to live
execution. Slice 08 requires explicit live infrastructure approval after
Slices 01 through 07 have passed their required gates.

## arc42 Check Status

Checked files:

- `documentation/arc42/05_building_blocks.adoc`
- `documentation/arc42/06_runtime_view.adoc`
- `documentation/arc42/07_deployment_view.adoc`
- `documentation/arc42/10_quality_requirements.adoc`
- `documentation/arc42/11_risks_and_debt.adoc`
- `documentation/architecture/adr-separate-platform-artifacts-deployment.adoc`

Current status:

- No arc42 content was changed during workflow creation.
- Future slices must update runtime, deployment, quality and risk sections if
  integration-test behavior becomes product behavior.
