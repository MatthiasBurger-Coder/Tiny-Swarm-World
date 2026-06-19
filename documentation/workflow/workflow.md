# Workflow: Replace RabbitMQ with Apache Pulsar

```yaml
workflow_id: workflow-replace-rabbitmq-with-apache-pulsar
workflow_version: 1.0.0
authoring_branch: feature/replace-rabbitmq-with-apache-pulsar-20260616
required_execution_branch: feature/replace-rabbitmq-with-apache-pulsar-20260616
repository: Tiny-Swarm-World
branch_type: feature/
execution_mode: Controlled Codex workflow
architecture_style: Hexagonal architecture, declarative infrastructure reconciliation
target_platform: Local Linux / LXD-native Docker Swarm
active_workflow: true
released_for_workflow_execute: true
created_utc: "2026-06-16T00:00:00Z"
decision: READY_FOR_WORKFLOW
confidence: 94
dependencies: []
```

## Executive Summary

Replace RabbitMQ with Apache Pulsar as the Tiny Swarm World platform messaging
service. The migration is treated as a controlled platform stack replacement:
add Apache Pulsar standalone, wire it into inventory, preflight, deployment
contracts, service access, configuration, tests, and documentation, then remove
the RabbitMQ compose stack and verify no active RabbitMQ runtime or config
references remain.

## Requirement Clarification Gate

Original request:

- Create a workflow to replace RabbitMQ with Apache Pulsar.
- Preserve the Linux/WSL-only, Python automation, Docker Swarm, and hexagonal
  architecture constraints.
- Use the branch `feature/replace-rabbitmq-with-apache-pulsar-20260616`.

Interpreted intent:

- Author an executable workflow plan, not execute the implementation yet.
- Use Apache Pulsar standalone for the phase-1 local greenpath.
- Remove RabbitMQ from active desired platform state with no hidden fallback.

Change type:

- Platform service replacement across declarative infrastructure, domain
  contracts, configuration, service access, tests, and documentation.

Affected process strand:

- Docker Swarm service-stack reconciliation.
- Preflight and setup manifest checks.
- Operator configuration and secrets contract.
- Service access dashboard and live validation evidence.

Affected architecture area:

- `infra/config/**`
- `src/tiny_swarm_world/domain/preflight/**`
- `src/tiny_swarm_world/domain/deployment/**`
- `src/tiny_swarm_world/domain/configuration/**`
- `src/tiny_swarm_world/infrastructure/adapters/preflight/**`
- `tests/**`
- `documentation/**`
- `AGENTS.md`, `infra/AGENTS.md`, `README.md`, `OPERATIONAL_READINESS_CHECKLIST.md`

Explicit requirements:

- RabbitMQ is removed from active desired inventory, setup/preflight manifest,
  deployment service stack contract, service access, secrets/env contract, and
  documentation.
- Apache Pulsar is introduced as the platform messaging broker.
- `./install.sh` remains the primary greenpath command.
- Pulsar binary protocol uses port `6650`.
- Pulsar admin HTTP uses internal port `8080` and must not map host `8080`.
- Prefer host `8087` for direct admin HTTP exposure when required.
- The old RabbitMQ compose stack is deleted only after Pulsar is wired through
  inventory, contracts, service access, configuration, tests, and docs.
- Every implementation slice is committed separately.

Implicit requirements:

- Keep domain code independent from infrastructure adapters and YAML/file
  parsing.
- Keep application services dependent on ports, not concrete adapters.
- Use structured YAML handling or existing repository helpers.
- Preserve safety guards and do not execute live infrastructure commands
  without explicit approval.
- Mock Docker, Swarm, network, and node-provider operations in tests unless
  live validation is explicitly requested.

Assumptions:

- Repository evidence continues to show RabbitMQ as platform infrastructure
  rather than deep AMQP runtime coupling.
- No production-grade Pulsar cluster is required for this workflow.
- Decision A applies for service access: expose/link Pulsar Admin API only;
  do not add Pulsar Manager unless tests or documented UX force it.

Non-goals:

- No business-level producer/consumer implementation.
- No `MessagingPort`, `PulsarMessagingAdapter`, topics, DLQ/retry policy,
  Pulsar authentication, or clustered Pulsar topology unless failing tests
  prove the need.
- No RabbitMQ compatibility mode target.
- No Ansible, Kubernetes-first behavior, Multipass, Java, Maven, Spring Boot,
  browser React, or Windows-native behavior.

Risks:

- Pulsar has a higher resource footprint than RabbitMQ.
- Pulsar standalone is not equivalent to a production Pulsar cluster.
- Pulsar admin HTTP uses internal port `8080`, creating collision risk if host
  exposure is configured incorrectly.
- Browser access differs because RabbitMQ Management UI has no direct Pulsar
  standalone UI equivalent without Pulsar Manager.
- Historical evidence files may still contain RabbitMQ references and must be
  classified rather than treated as active product state.

Open questions:

- Whether direct host mapping `8087:8080` is required, or service-access proxy
  is sufficient, must be resolved from existing compose conventions in Slice 02
  and Slice 05.

Blocking questions:

- None for workflow authoring. Implementation must stop if repository evidence
  contradicts the platform-only migration assumption.

Confidence level: 94 percent.

Decision: `READY_FOR_WORKFLOW`.

## Three Amigos Review Gate

Before implementation, create:

```text
.tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/three-amigos-review.md
```

Use this required structure:

```markdown
# Three Amigos Review

## Requirement Engineer
Decision: accepted / changes required
Notes:

## System Architect
Decision: accepted / changes required
Notes:

## Senior Tester
Decision: accepted / changes required
Notes:

## Final Gate Decision
Decision: accepted / blocked
Required changes before implementation:
```

Implementation may continue only when the final gate decision is `accepted`.

## Target Picture

```text
Docker Swarm
  - Apache Pulsar standalone
      - Pulsar broker protocol: 6650
      - Pulsar admin HTTP: internal 8080
      - Optional direct host admin mapping: 8087:8080
  - RabbitMQ absent from active desired platform state
```

## Verified Baseline

- Root `AGENTS.md`, `QUALITY.md`, and `.agents/skills/workflow-authoring/SKILL.md`
  were checked during workflow authoring.
- A lightweight authoring scan found active RabbitMQ references in `.env.example`,
  `AGENTS.md`, `README.md`, `OPERATIONAL_READINESS_CHECKLIST.md`, runtime
  configuration, docs, tests, and historical evidence.
- `rg` is unavailable in this environment; use `grep` on Linux/WSL during
  workflow execution as specified by the slices.

## Scope

In scope:

- Apache Pulsar compose stack.
- Desired inventory and setup/preflight manifest.
- Deployment service stack contract.
- Service-access NGINX/dashboard and post-install browser checks.
- Secrets and environment configuration contract.
- RabbitMQ compose stack removal.
- Documentation, arc42, operational readiness, and agent/infra instructions.
- Migration evidence and residue classification.

Out of scope:

- Live infrastructure mutation during normal development slices.
- Pulsar Manager unless required by tests or documented user experience.
- Pulsar authentication and production cluster hardening.
- Business messaging APIs or application-level broker adapters.

## Architecture Constraints

- Domain modules must not import command runners, file managers, HTTP clients,
  Docker clients, UI adapters, YAML parsers, logging setup, or dependency
  injection containers.
- Infrastructure adapters own concrete YAML, filesystem, HTTP, Docker, and
  command-runner details.
- Declarative inventory and stack contracts remain the source of truth.
- Keep standard runtime wiring in
  `src/tiny_swarm_world/infrastructure/composition.py`.
- Do not move concrete adapter construction into application services.
- Do not add external static-analysis CI configuration.

## Python Automation Assessment

This workflow affects Python automation contracts and tests. Keep Python 3.12
compatibility, package imports, typed domain concepts where changed, and
deterministic unit tests. Use `PYTHONPATH=src` for manual Python test commands
that import `tiny_swarm_world`.

## Frontend Assessment

No browser React frontend work is authorized. Slice 05 touches static
service-access dashboard content only. Console/status UI skills are not primary
unless existing terminal output lists RabbitMQ as an active service.

## Test Strategy

- Run targeted tests after each slice.
- Run `python3 tools/quality_gate.py quality` as the final required local gate.
- Do not delete tests to make the suite green.
- Adapt RabbitMQ expectations to Pulsar.
- Record test limitations when live infrastructure is required but unavailable.

## Resilience Requirements

- Fail closed if service ownership, port exposure, or active versus historical
  RabbitMQ references are ambiguous.
- Do not skip safety guards, disable validations, or silently keep RabbitMQ as
  fallback.
- Store evidence under
  `.tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/`.

## Ordered Slices

### Slice 01: Repository scan and migration baseline

Purpose:

- Capture all RabbitMQ and Pulsar references before implementation changes.
- Complete and record the Three Amigos gate.

```yaml
slice_id: S01
profile: NORMAL_PATH
owner: Senior Requirement Engineer
secondary_reviewers:
  - Senior System Architect
  - Senior Tester
affected_files:
  - .tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/**
affected_modules:
  - workflow evidence
affected_contracts:
  - migration_baseline
dependencies: []
parallel_group: serial
file_locks:
  - .tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/**
contract_locks:
  - migration_baseline
architecture_locks:
  - linux_wsl_only_runtime
quality_gates:
  targeted:
    - git diff --check
  required:
    - python3 tools/quality_gate.py quality
documentation:
  arc42: checked
  adr: checked-no-adr-required-for-authoring
stop_conditions:
  - Three Amigos final decision is not accepted.
  - Baseline scan reveals deep RabbitMQ runtime client coupling that changes the scope.
```

Verification commands:

```bash
mkdir -p .tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar
grep -RIn -e "rabbitmq" -e "RabbitMQ" -e "RABBITMQ" -e "amqp" -e "AMQP" -e "5672" -e "15672" -e "pika" -e "aio_pika" -e "kombu" . --exclude-dir=.git --exclude-dir=.venv --exclude-dir=__pycache__ > .tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/rabbitmq-reference-baseline.txt || true
grep -RIn -e "pulsar" -e "Pulsar" -e "PULSAR" . --exclude-dir=.git --exclude-dir=.venv --exclude-dir=__pycache__ > .tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/pulsar-reference-baseline.txt || true
git diff --check
```

Commit:

```bash
git add .tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar
git commit -m "docs: capture rabbitmq pulsar migration baseline"
```

### Slice 02: Add Apache Pulsar compose stack

Purpose:

- Add `infra/config/compose/pulsar/docker-compose.yml` for Pulsar standalone.

```yaml
slice_id: S02
profile: NORMAL_PATH
owner: Senior Python Automation Developer
secondary_reviewers:
  - Senior System Architect
  - Senior Tester
affected_files:
  - infra/config/compose/pulsar/docker-compose.yml
  - tests/infrastructure/adapters/repositories/**
affected_modules:
  - compose stack repository
affected_contracts:
  - compose_stack_definition
dependencies:
  - S01
parallel_group: compose
file_locks:
  - infra/config/compose/pulsar/**
  - tests/infrastructure/adapters/repositories/**
contract_locks:
  - compose_stack_definition
architecture_locks:
  - declarative_infrastructure
quality_gates:
  targeted:
    - PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml
  required:
    - python3 tools/quality_gate.py quality
documentation:
  arc42: update-if-compose-conventions-change
  adr: checked-update-if-port-or-stack-policy-changes
stop_conditions:
  - Existing compose conventions conflict with the proposed Pulsar layout.
  - Host port 8080 would be exposed directly.
```

Done criteria:

- Pulsar standalone service exists with persistent volumes, healthcheck,
  overlay network convention, `6650`, internal `8080`, and no `8080:8080`.
- RabbitMQ compose file remains untouched in this slice.

Commit:

```bash
git add infra/config/compose/pulsar tests
git commit -m "feat: add apache pulsar compose stack"
```

### Slice 03: Replace RabbitMQ in desired inventory and setup manifest

Purpose:

- Make Pulsar part of active desired platform state and remove RabbitMQ from
  active inventory/preflight checks.

```yaml
slice_id: S03
profile: NORMAL_PATH
owner: Senior Python Automation Developer
secondary_reviewers:
  - Senior System Architect
  - Senior Tester
affected_files:
  - infra/config/inventory/desired_inventory.yaml
  - src/tiny_swarm_world/domain/preflight/setup_manifest.py
  - src/tiny_swarm_world/infrastructure/adapters/preflight/host_preflight_probe.py
  - tests/domain/preflight/**
  - tests/infrastructure/adapters/preflight/**
affected_modules:
  - preflight
  - desired inventory
affected_contracts:
  - desired_platform_state
  - preflight_port_contract
dependencies:
  - S02
parallel_group: platform-state
file_locks:
  - infra/config/inventory/**
  - src/tiny_swarm_world/domain/preflight/**
  - src/tiny_swarm_world/infrastructure/adapters/preflight/**
  - tests/domain/preflight/**
  - tests/infrastructure/adapters/preflight/**
contract_locks:
  - desired_platform_state
  - preflight_port_contract
architecture_locks:
  - hexagonal_architecture
quality_gates:
  targeted:
    - PYTHONPATH=src python3 -m unittest tests.domain.preflight.test_preflight_result
    - PYTHONPATH=src python3 -m unittest discover tests/infrastructure/adapters/preflight
  required:
    - python3 tools/quality_gate.py quality
documentation:
  arc42: update-if-runtime-or-deployment-view-changes
  adr: checked
stop_conditions:
  - RabbitMQ remains active in desired inventory or preflight.
  - Preflight embeds infrastructure details into domain code.
```

Commit:

```bash
git add infra/config/inventory src/tiny_swarm_world/domain/preflight src/tiny_swarm_world/infrastructure/adapters/preflight tests
git commit -m "feat: replace rabbitmq with pulsar in desired platform state"
```

### Slice 04: Update service stack contract

Purpose:

- Replace RabbitMQ with Pulsar in the deployment service stack contract.

```yaml
slice_id: S04
profile: NORMAL_PATH
owner: Senior System Architect
secondary_reviewers:
  - Senior Python Automation Developer
  - Senior Tester
affected_files:
  - src/tiny_swarm_world/domain/deployment/service_stack_contract.py
  - tests/domain/deployment/test_service_stack_contract.py
  - documentation/workflow/issues/issue-4/swarm-stack-validation-baseline.md
affected_modules:
  - deployment contracts
affected_contracts:
  - service_stack_contract
dependencies:
  - S03
parallel_group: platform-state
file_locks:
  - src/tiny_swarm_world/domain/deployment/**
  - tests/domain/deployment/**
  - documentation/workflow/issues/issue-4/swarm-stack-validation-baseline.md
contract_locks:
  - service_stack_contract
architecture_locks:
  - hexagonal_architecture
quality_gates:
  targeted:
    - PYTHONPATH=src python3 -m unittest tests.domain.deployment.test_service_stack_contract
  required:
    - python3 tools/quality_gate.py quality
documentation:
  arc42: update-if-stack-contract-changes-runtime-view
  adr: checked
stop_conditions:
  - Stack contract still requires RabbitMQ.
  - Contract validation skips the Pulsar compose stack.
```

Commit:

```bash
git add src/tiny_swarm_world/domain/deployment tests/domain/deployment documentation/workflow/issues/issue-4
git commit -m "feat: update service stack contract for pulsar"
```

### Slice 05: Update service-access and dashboard

Purpose:

- Replace RabbitMQ dashboard/service-access entries with Pulsar Admin API
  entries using Decision A.

```yaml
slice_id: S05
profile: NORMAL_PATH
owner: Senior Documentation Engineer
secondary_reviewers:
  - Senior System Architect
  - Senior Tester
affected_files:
  - infra/config/compose/service-access/nginx/default.conf
  - infra/config/compose/service-access/dashboard/index.html
  - tests/integration/test_post_install_browser_live.py
  - documentation/system/live-operation-surfaces.adoc
  - .tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/**
affected_modules:
  - service access
affected_contracts:
  - operator_browser_access
dependencies:
  - S04
parallel_group: service-access
file_locks:
  - infra/config/compose/service-access/**
  - tests/integration/test_post_install_browser_live.py
  - documentation/system/live-operation-surfaces.adoc
  - .tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/**
contract_locks:
  - operator_browser_access
architecture_locks:
  - declarative_infrastructure
quality_gates:
  targeted:
    - PYTHONPATH=src python3 -m unittest tests.integration.test_post_install_browser_live
  required:
    - python3 tools/quality_gate.py quality
documentation:
  arc42: update-if-user-facing-runtime-surface-changes
  adr: checked
stop_conditions:
  - Pulsar Manager is added without test or documentation evidence requiring UI parity.
  - Service access proxies a conflicting or unsafe admin path.
```

If the live browser test cannot run locally, record the reason in:

```text
.tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/test-limitations.md
```

Commit:

```bash
git add infra/config/compose/service-access tests/integration documentation/system .tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar
git commit -m "feat: update service access for pulsar"
```

### Slice 06: Update secrets and environment contract

Purpose:

- Remove active RabbitMQ secrets/config and add minimal Pulsar values only if
  required.

```yaml
slice_id: S06
profile: NORMAL_PATH
owner: Senior Python Automation Developer
secondary_reviewers:
  - Senior Requirement Engineer
  - Senior Tester
affected_files:
  - .env.example
  - infra/config/secrets/infisical-secrets.yaml
  - documentation/configuration/operator-configuration-contract.md
  - documentation/configuration/config-contract-inventory.md
  - src/tiny_swarm_world/domain/configuration/configuration_contract.py
  - tests/**
affected_modules:
  - configuration contract
affected_contracts:
  - operator_configuration
  - secret_manifest
dependencies:
  - S05
parallel_group: configuration
file_locks:
  - .env.example
  - infra/config/secrets/**
  - documentation/configuration/**
  - src/tiny_swarm_world/domain/configuration/**
  - tests/**
contract_locks:
  - operator_configuration
  - secret_manifest
architecture_locks:
  - hexagonal_architecture
quality_gates:
  targeted:
    - PYTHONPATH=src python3 -m unittest discover tests -k configuration
  required:
    - python3 tools/quality_gate.py quality
documentation:
  arc42: update-if-configuration-model-changes
  adr: checked-update-if-auth-policy-changes
stop_conditions:
  - RabbitMQ credentials remain active.
  - Pulsar passwords are invented without authentication being enabled.
```

Commit:

```bash
git add .env.example infra/config/secrets documentation/configuration src/tiny_swarm_world/domain/configuration tests
git commit -m "feat: update configuration contract for pulsar"
```

### Slice 07: Remove RabbitMQ compose stack

Purpose:

- Delete the old RabbitMQ compose stack after Pulsar is fully wired.

```yaml
slice_id: S07
profile: NORMAL_PATH
owner: Senior System Architect
secondary_reviewers:
  - Senior Python Automation Developer
  - Senior Tester
affected_files:
  - infra/config/compose/rabbitmq/docker-compose.yml
  - infra/config/compose/**
affected_modules:
  - compose stack repository
affected_contracts:
  - compose_stack_definition
dependencies:
  - S06
parallel_group: serial
file_locks:
  - infra/config/compose/rabbitmq/**
  - infra/config/compose/**
contract_locks:
  - compose_stack_definition
architecture_locks:
  - declarative_infrastructure
quality_gates:
  targeted:
    - PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml
    - PYTHONPATH=src python3 -m unittest tests.domain.deployment.test_service_stack_contract
  required:
    - python3 tools/quality_gate.py quality
documentation:
  arc42: update-if-deployment-view-changes
  adr: checked
stop_conditions:
  - Active references to infra/config/compose/rabbitmq remain.
```

Safety check:

```bash
grep -RIn -e "infra/config/compose/rabbitmq" -e "compose/rabbitmq" -e "rabbitmq/docker-compose.yml" . --exclude-dir=.git --exclude-dir=.venv --exclude-dir=__pycache__
```

Commit:

```bash
git add -A infra/config/compose
git commit -m "feat: remove rabbitmq compose stack"
```

### Slice 08: Update documentation and arc42

Purpose:

- Align README, guides, arc42, epics, operational readiness, and agent docs
  with Pulsar as the platform messaging stack.

```yaml
slice_id: S08
profile: NORMAL_PATH
owner: Senior Documentation Engineer
secondary_reviewers:
  - Senior System Architect
  - Senior Requirement Engineer
affected_files:
  - README.md
  - documentation/**
  - OPERATIONAL_READINESS_CHECKLIST.md
  - infra/AGENTS.md
  - AGENTS.md
affected_modules:
  - documentation
  - architecture documentation
affected_contracts:
  - operator_documentation
  - arc42_runtime_deployment_view
dependencies:
  - S07
parallel_group: documentation
file_locks:
  - README.md
  - documentation/**
  - OPERATIONAL_READINESS_CHECKLIST.md
  - infra/AGENTS.md
  - AGENTS.md
contract_locks:
  - operator_documentation
  - arc42_runtime_deployment_view
architecture_locks:
  - linux_wsl_only_runtime
  - docker_swarm_first
quality_gates:
  targeted:
    - git diff --check
  required:
    - python3 tools/quality_gate.py quality
documentation:
  arc42: required-update
  adr: checked-update-if-pulsar-standalone-decision-requires-record
stop_conditions:
  - Active documentation still claims RabbitMQ is part of the current stack.
  - Pulsar standalone limitations are not documented.
```

Commit:

```bash
git add README.md documentation OPERATIONAL_READINESS_CHECKLIST.md infra/AGENTS.md AGENTS.md
git commit -m "docs: document pulsar platform messaging stack"
```

### Slice 09: Global RabbitMQ residue check

Purpose:

- Record final RabbitMQ and Pulsar reference scans and classify remaining
  RabbitMQ references.

```yaml
slice_id: S09
profile: NORMAL_PATH
owner: Senior Tester
secondary_reviewers:
  - Senior Requirement Engineer
  - Senior System Architect
affected_files:
  - .tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/**
affected_modules:
  - workflow evidence
affected_contracts:
  - residue_classification
dependencies:
  - S08
parallel_group: serial
file_locks:
  - .tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/**
contract_locks:
  - residue_classification
architecture_locks:
  - platform_service_contract
quality_gates:
  targeted:
    - git diff --check
  required:
    - python3 tools/quality_gate.py quality
documentation:
  arc42: checked
  adr: checked
stop_conditions:
  - Any remaining RabbitMQ reference is active runtime, config, or contract state.
```

Create:

```text
.tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/final-reference-classification.md
```

Classify each remaining RabbitMQ reference as `historical documentation`,
`migration evidence`, `deprecated compatibility note`, or `bug - must be
removed`.

Commit:

```bash
git add .tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar
git commit -m "test: record final rabbitmq pulsar reference validation"
```

### Slice 10: Full automated test run

Purpose:

- Run the strongest available local quality checks and store evidence.

```yaml
slice_id: S10
profile: NORMAL_PATH
owner: Senior Tester
secondary_reviewers:
  - Quality Gate Orchestrator
affected_files:
  - .tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/full-test-run.txt
  - tests/**
affected_modules:
  - quality gates
affected_contracts:
  - repository_quality_gate
dependencies:
  - S09
parallel_group: serial
file_locks:
  - .tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/**
  - tests/**
contract_locks:
  - repository_quality_gate
architecture_locks:
  - hexagonal_architecture
quality_gates:
  targeted:
    - python3 tools/quality_gate.py test
  required:
    - python3 tools/quality_gate.py quality
documentation:
  arc42: checked
  adr: checked
stop_conditions:
  - Full quality gate fails with migration-related regressions.
  - A failure is undocumented or classified by guessing.
```

Run and store output:

```bash
python3 tools/quality_gate.py quality | tee .tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/full-test-run.txt
./install.sh --help || true
find . -maxdepth 3 -type f \( -name "Makefile" -o -name "pyproject.toml" -o -name "tox.ini" -o -name "noxfile.py" -o -name "QUALITY.md" \) -print
```

Commit:

```bash
git add .tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar tests
git commit -m "test: verify pulsar migration test suite"
```

### Slice 11: Live greenpath validation

Purpose:

- Validate `./install.sh` and deployed platform state on a suitable Linux/LXD
  native environment.

```yaml
slice_id: S11
profile: LIVE_VALIDATION
owner: Senior DevOps Engineer
secondary_reviewers:
  - Senior Tester
  - Senior System Architect
affected_files:
  - .tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/live-greenpath/**
  - .tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/live-greenpath-not-run.md
affected_modules:
  - live platform validation
affected_contracts:
  - install_greenpath
  - pulsar_admin_api_credential_login
dependencies:
  - S10
parallel_group: serial-live
file_locks:
  - .tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/**
contract_locks:
  - install_greenpath
  - pulsar_admin_api_auth
architecture_locks:
  - linux_wsl_only_runtime
  - docker_swarm_first
quality_gates:
  targeted:
    - ./install.sh
  required:
    - python3 tools/quality_gate.py quality
documentation:
  arc42: checked-update-if-live-behavior-differs
  adr: checked
stop_conditions:
  - Live infrastructure approval or suitable environment is unavailable.
  - Safety guards would need to be skipped.
  - RabbitMQ deploys during the live greenpath.
  - Pulsar Admin API accepts unauthenticated requests.
  - Pulsar Admin API rejects the configured admin token.
  - Pulsar credentials are missing from the local secret source or Infisical item inventory.
```

Required evidence if run:

```text
.tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/live-greenpath/install-output.txt
.tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/live-greenpath/docker-service-ls.txt
.tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/live-greenpath/docker-stack-ls.txt
.tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/live-greenpath/pulsar-healthcheck.txt
.tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/live-greenpath/pulsar-auth-check.txt
.tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/live-greenpath/service-access-check.txt
```

Pulsar live validation must verify both credential storage and authenticated
access:

```bash
grep -q '^TSW_PULSAR_ADMIN_TOKEN=' .tiny-swarm-world/local/live-installation.env
curl -sS -o /dev/null -w '%{http_code}\n' http://localhost:8087/admin/v2/clusters
curl -fsS -H "Authorization: Bearer ${TSW_PULSAR_ADMIN_TOKEN}" \
  http://localhost:8087/admin/v2/clusters
TSW_RUN_POST_INSTALL_BROWSER_LIVE=1 PYTHONPATH=src python3 -m unittest \
  tests.live.test_post_install_browser_live.PostInstallBrowserLiveTest.test_07_pulsar_admin_api_requires_and_accepts_configured_token
```

The unauthenticated curl must return `401` or `403`; the authenticated request
must include `standalone` in the cluster list. Do not print the token value in
evidence.

If not run, create `live-greenpath-not-run.md` with reason, environment,
commands that would be run, remaining risk, and required manual validation.

Commit if run or documented:

```bash
git add .tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar
git commit -m "test: verify live pulsar greenpath"
```

### Slice 12: Pull request preparation

Purpose:

- Prepare PR body, final evidence references, and merge-readiness checks.

```yaml
slice_id: S12
profile: PR_READINESS
owner: Senior Workflow Architect
secondary_reviewers:
  - Senior Tester
  - Senior System Architect
affected_files:
  - .tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/**
affected_modules:
  - pull request readiness
affected_contracts:
  - pr_readiness
dependencies:
  - S11
parallel_group: serial
file_locks:
  - .tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/**
contract_locks:
  - pr_readiness
architecture_locks:
  - release_governance
quality_gates:
  targeted:
    - git status --short
    - git log --oneline --decorate -n 20
  required:
    - python3 tools/quality_gate.py quality
documentation:
  arc42: checked
  adr: checked
stop_conditions:
  - Required quality or residue evidence is missing.
  - Mergeability or required checks cannot be verified.
```

PR title:

```text
Replace RabbitMQ with Apache Pulsar platform messaging stack
```

PR body:

```markdown
## Summary

This PR replaces RabbitMQ with Apache Pulsar as the platform messaging service for Tiny Swarm World.

## Scope

- Added Apache Pulsar compose stack.
- Removed RabbitMQ from active desired inventory.
- Updated setup/preflight contracts.
- Updated deployment service stack contract.
- Updated service-access/dashboard references.
- Updated secrets and environment configuration.
- Removed RabbitMQ compose stack.
- Updated documentation and arc42.
- Added migration evidence.

## Architecture decision

This PR uses Apache Pulsar standalone mode for the local Docker Swarm greenpath. This is sufficient for local development and controlled platform validation. A production-like Pulsar cluster with separate brokers/bookies/metadata store is explicitly deferred.

## Validation

- [ ] Three Amigos gate completed
- [ ] Compose/YAML tests passed
- [ ] Preflight tests passed
- [ ] Deployment contract tests passed
- [ ] Full quality gate passed
- [ ] RabbitMQ residue scan completed
- [ ] Live `./install.sh` greenpath completed or documented as not run

## Risks

- Pulsar has a higher resource footprint than RabbitMQ.
- Pulsar standalone mode is not equivalent to a production cluster.
- Pulsar admin HTTP uses internal port 8080, so external mapping must avoid collisions.
- Existing downstream code must not assume RabbitMQ Management UI semantics.

## Evidence

See `.tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/`.
```

## Slice Dependency Graph

```text
S01 -> S02 -> S03 -> S04 -> S05 -> S06 -> S07 -> S08 -> S09 -> S10 -> S11 -> S12
```

## Parallel Execution

- Can this workflow run in parallel? Limited. Default execution is serial
  because platform contracts, inventory, docs, and residue validation are
  tightly coupled.
- Conflicting workflows: any active workflow touching `infra/config/**`,
  service stack contracts, preflight, configuration contracts, service-access,
  README, arc42, or documentation workflow evidence.
- Shared files: `infra/config/**`, `src/tiny_swarm_world/domain/**`,
  `tests/**`, `documentation/**`, `AGENTS.md`, `README.md`.
- Shared infrastructure: Docker Swarm, LXD/Incus/LXC, service-access, host
  ports `6650`, `8080`, and `8087`.
- Requires isolated worktree: yes for any stream execution.
- Requires serialized live validation: yes.
- Merge-order constraints: preserve slice order; do not delete RabbitMQ compose
  before Pulsar is wired into inventory, contracts, service access,
  configuration, tests, and documentation.

## Automatic Work Distribution Policy

During `workflow execute`, Codex must inspect each slice for safe specialist
stream decomposition. Use real Codex subagents where supported; otherwise
perform explicit role-based fallback review in the main execution thread and
record the fallback in evidence.

For every slice, create `.codex/evidence/slice-<number>-distribution.md`
before implementation and `.codex/evidence/slice-<number>-consolidation.md`
after implemented slices. Codex remains the final integration owner.

Stream map:

- Backend/Python: S03, S04, S06.
- Runtime/DevOps: S02, S07, S11.
- Tests/Quality: S01, S09, S10, S12.
- Documentation/Architecture: S05, S08.
- Frontend: static service-access dashboard only in S05; no React stream.
- Security/configuration: S06.

Do not split work when files overlap, architecture is unclear, requirements
contradict, ordering is mandatory, generated files may conflict, secrets
handling is unclear, a Three Amigos decision marks the slice not safely
parallelizable, or safety guards would be weakened.

## Git Worktree Execution Rule

Parallel stream work must use isolated Git worktrees. Stream branch names must
follow:

```text
feature/replace-rabbitmq-with-apache-pulsar-20260616-slice-<number>-<stream>
```

Stream workers must verify the active branch or worktree branch belongs to this
workflow before modifying files. Stream workers must not merge directly to the
integration branch; Codex consolidates accepted changes after evidence and
tests pass.

## Role And Ownership Map

- Senior Requirement Engineer: Three Amigos requirement gate and residue
  acceptance.
- Senior System Architect: Pulsar standalone architecture, stack contracts,
  deletion sequencing, arc42 alignment.
- Senior Python Automation Developer: inventory, preflight, deployment, and
  configuration contract code.
- Senior React Frontend Developer: no-impact review; static dashboard only.
- Senior Tester: targeted tests, full quality gate, final residue validation.
- Senior DevOps Engineer: compose stack and live greenpath validation.
- Senior Documentation Engineer: README, guides, arc42, operational readiness,
  and agent instructions.

## Quality-Gate Expectations

Workflow authoring:

```bash
git diff --check
```

Workflow execution:

```bash
python3 tools/quality_gate.py test
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py quality
```

For focused tests, use `PYTHONPATH=src python3 -m unittest ...` unless the
repository has a verified pytest equivalent in the current environment.

## Documentation Synchronization Points

- Update README and user guide when operator-facing service lists or access
  URLs change.
- Update `documentation/arc42/**` when runtime view, deployment view, quality
  requirements, concepts, or risks change.
- Update operator configuration docs when env/secrets contracts change.
- Add or update ADRs only if execution introduces an architecture-significant
  policy decision beyond the accepted Pulsar standalone phase-1 direction.

## Stop Conditions

Stop and report when:

- The working tree is dirty before implementation starts.
- The active branch is not `feature/replace-rabbitmq-with-apache-pulsar-20260616`.
- Three Amigos final decision is not `accepted`.
- Repository evidence shows deep RabbitMQ application runtime coupling.
- Pulsar cannot satisfy stack contract or preflight requirements without
  weakening guards.
- RabbitMQ must be kept as hidden fallback to pass tests.
- Live infrastructure commands would be required without explicit approval.
- Quality gates fail and cannot be fixed inside the declared slice scope.
- Any active RabbitMQ runtime/config/contract reference remains after S09.

## Uncertainty Escalation Rules

- Requirement ambiguity: Senior Requirement Engineer.
- Platform/architecture ambiguity: Senior System Architect and Root Architect.
- Port exposure or live validation ambiguity: Senior DevOps Engineer.
- Config/secrets ambiguity: security and configuration owners.
- Quality failures: Senior Tester and Quality Gate Orchestrator.

## Commit And Push Plan

- Commit each implementation slice separately using the commit messages
  declared in the relevant slice.
- Do not make multi-slice commits.
- Do not create or merge a PR until required quality gates and residue
  validation have passed or limitations are explicitly documented.
- `push auto`, if requested later, must follow the full guarded lifecycle from
  `AGENTS.md`.

## Definition Of Done

This workflow is done when:

- Branch `feature/replace-rabbitmq-with-apache-pulsar-20260616` exists.
- RabbitMQ compose stack is removed.
- Pulsar compose stack exists.
- Desired inventory, setup/preflight manifest, deployment service stack
  contract, service-access/dashboard, env/secrets config, docs, and arc42 use
  Pulsar instead of RabbitMQ for active platform messaging.
- Tests and `python3 tools/quality_gate.py quality` pass, or unrelated failures
  are documented with evidence.
- No active RabbitMQ runtime/config/contract reference remains.
- Live greenpath is successful or explicitly documented as not executable in
  the current environment.
- PR is prepared with risks and evidence.

## Rollback Strategy

If Pulsar cannot be made green without unsafe shortcuts:

1. Stop implementation.
2. Do not silently reintroduce RabbitMQ.
3. Create a rollback commit that restores the last known green RabbitMQ stack.
4. Document the blocker in:

```text
.tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/blockers.md
```

Rollback commit message:

```bash
git commit -m "revert: restore rabbitmq stack after pulsar migration blocker"
```

## Handoff To Workflow Execute

This is the active workflow in `documentation/workflow/workflow.md`.
`workflow execute` may run it only after verifying the active branch,
slice metadata, locks, Three Amigos gate, and quality commands from
`QUALITY.md`.

## arc42 Check Status

- arc42 impact: required during execution because platform runtime and
  deployment views change from RabbitMQ to Pulsar.
- ADR impact: checked during authoring; execution should add or update an ADR
  only if a new architecture-significant decision is made beyond local Pulsar
  standalone as the phase-1 greenpath.
