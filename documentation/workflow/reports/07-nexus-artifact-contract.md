# Slice 07 Report: Nexus And Artifact Registry Contract

## Status

```text
COMPLETED_PENDING_COMMIT
```

## Workflow Context

- Workflow: `Autonomous Runnable Setup`
- Version: `autonomous-runnable-setup-v1.0.0`
- Branch: `codex/workflow-autonomous-setup-20260524`
- Slice: `07`
- Owner: `senior_python_automation_developer`
- Dependency: Slice 05 completed in commit `ec9cd2b`
- Context repair before Slice 07 completed in commit `36d6f2e`

## S3 And S3D Evidence

- `S3_STATUS`: PASS before write-capable Slice 07 work.
- `S3_BRANCH`: PASS; active branch and local ref matched
  `codex/workflow-autonomous-setup-20260524`.
- `S3_SCOPE`: PASS; changed files are inside Slice 07 artifact, Nexus,
  client, compose asset, documentation, test, and report scope.
- `S3_CLASSIFY`: Python automation contract, Nexus/artifact boundary,
  adapter hardening, security-sensitive evidence, tests, documentation.
- `S3D_RESULT`: EXECUTION_PLAN.
- `SLICE_07_DEPENDENCIES`: `05`.
- `SLICE_07_TARGETED_GATES`: artifact workflow tests, Nexus service tests,
  Nexus and Docker client adapter tests, composition tests, live-operation
  surface documentation tests, and arch-tests.
- `SLICE_07_REQUIRED_GATES`: `python3 tools/quality_gate.py test`.

## Subagent Review Evidence

- Senior System Architect: BLOCKED on promoting legacy Nexus bootstrap or
  collapsing artifact ownership into deployment. Addressed by keeping Nexus
  stack lifecycle in Deployment while adding repository readiness contracts
  under the artifact/Nexus application boundary.
- Senior Security/Sandbox Engineer: BLOCKED on hardcoded credentials, raw HTTP
  response body errors, Docker command/stderr leakage, and unconditional
  anonymous Nexus access. Addressed by removing password defaults from the
  application configuration object, sanitizing Nexus and Docker adapter
  failures, rejecting credentials in Nexus base URLs, and making legacy
  anonymous access opt-in in `BootstrapNexus`.
- Senior Python Automation Developer: requested executable artifact contracts
  without image build or push side effects. Addressed with step-based
  `ArtifactPrepareWorkflow` and `ArtifactVerifyWorkflow` contracts that can
  complete only with typed `VerificationResult` evidence.
- Senior Tester: requested mocked regressions for artifact outcomes, Nexus
  repository methods, Docker subprocess behavior, composition fail-closed
  behavior, and architecture boundary checks. Added focused tests with fakes
  and patched subprocess calls only.
- Requirement Engineering: confirmed Slice 07 changes trace to the autonomous
  runnable setup EPIC extension, the setup safety ADR, and the workflow slice
  contract. No EPIC change or new ADR is required because live-consent and
  credential-source semantics did not change.

## Implementation Summary

- Extended `ArtifactPrepareWorkflow` with configured prepare steps,
  verify-after-prepare blocking, completed/failed-to-prepare/failed-to-verify
  statuses, and typed verification evidence.
- Extended `ArtifactVerifyWorkflow` with configured verification checks and
  typed blocked, failed, and completed outcomes.
- Added Nexus repository application contracts for Docker hosted and Maven
  proxy repositories. These services depend on `PortNexusClient`, not
  infrastructure adapters, and return redacted `VerificationResult` evidence.
- Extended `PortNexusClient` and `NexusHttpClient` with repository listing and
  create methods for Docker hosted and Maven proxy repositories.
- Hardened `NexusHttpClient` to reject credentials embedded in the base URL
  and to remove response bodies from HTTP error messages.
- Hardened `DockerCliRuntime` to call subprocess with argv lists, explicit
  `shell=False`, bounded timeouts, and sanitized failures that do not include
  raw command strings or stderr.
- Removed committed password defaults from `NexusBootstrapConfiguration`.
- Made legacy Nexus anonymous access opt-in in `BootstrapNexus`.
- Corrected the Nexus compose asset so `nexus-data` is mounted at
  `/nexus-data`, matching the documented initial administrator password path.
- Kept `build_artifact_services()` fail-closed. Environment variables do not
  cause the composition root to construct Nexus or Docker clients.
- Updated arc42, deployment, and live-operation surface documentation to state
  that Nexus repository contracts are tested while default CLI artifact live
  behavior remains blocked.

## Requirement Classification

- Functional requirement: Nexus Docker hosted and Maven proxy repository
  setup can be represented as artifact contracts with mocked verification.
- Architecture constraint: Artifacts own repository/registry readiness;
  Deployment owns stack lifecycle; application services depend on ports.
- Security requirement: Nexus credentials are not accepted in URLs, committed
  application defaults do not contain passwords, anonymous access is opt-in,
  and adapter failures do not expose raw response bodies, command strings, or
  stderr.
- Observability requirement: artifact workflow results carry typed
  verification evidence rather than raw Nexus, Docker, or command payloads.
- Quality-gate requirement: tests use fakes and patched subprocess calls only;
  no Nexus, Docker, image build, image push, Portainer, or stack operation runs
  during default verification.
- Assumption: image build and publish contracts remain future work; Slice 07
  does not wire live artifact steps into the CLI composition root.

## Verification

Focused targeted checks:

```bash
PYTHONPATH=src python3 -m unittest tests.application.services.artifacts
PYTHONPATH=src python3 -m unittest tests.application.services.nexus
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_nexus_http_client tests.infrastructure.adapters.clients.test_docker_cli_runtime tests.infrastructure.test_composition tests.architecture.test_legacy_surface_documentation
python3 tools/quality_gate.py arch-tests
```

Result: passed. The focused tests ran `11`, `15`, `35`, and `15` tests.

Required gate:

```bash
python3 tools/quality_gate.py test
```

Result: passed, `316` tests, `1` skipped.

Full quality gate:

```bash
python3 tools/quality_gate.py quality
```

Result: passed. The full quality gate executed lint, arch-lint, arch-tests,
typecheck, and unittest using the ignored local `.venv/` tooling where needed.
The final unittest discovery ran `316` tests with `1` skipped.

Whitespace gate:

```bash
git diff --check
```

Result: passed. Git emitted existing CRLF normalization warnings for unrelated
legacy files, but no whitespace errors were reported.

## Live Infrastructure

No live infrastructure commands were run. Slice 07 did not execute Multipass,
Docker Swarm, compose deployment, netplan, socat, Portainer, Nexus, Jenkins,
RabbitMQ, SonarQube, Swagger/NGINX bootstrap, image build, image push, image
login, registry push, or stack upload commands.

## Checkpoint Record

```yaml
CP_RECORD: VERIFIED_PENDING_COMMIT
workflowVersion: autonomous-runnable-setup-v1.0.0
sliceId: "07"
changedFiles:
  - documentation/arc42/05_building_blocks.adoc
  - documentation/arc42/06_runtime_view.adoc
  - documentation/arc42/07_deployment_view.adoc
  - documentation/arc42/11_risks_and_debt.adoc
  - documentation/deployment/system.adoc
  - documentation/system/live-operation-surfaces.adoc
  - infra/config/compose/nexus/docker-compose.yml
  - src/tiny_swarm_world/application/ports/clients/port_nexus_client.py
  - src/tiny_swarm_world/application/services/artifacts/__init__.py
  - src/tiny_swarm_world/application/services/artifacts/workflows.py
  - src/tiny_swarm_world/application/services/nexus/__init__.py
  - src/tiny_swarm_world/application/services/nexus/bootstrap_nexus.py
  - src/tiny_swarm_world/application/services/nexus/ensure_nexus_repository.py
  - src/tiny_swarm_world/application/services/nexus/nexus_bootstrap_configuration.py
  - src/tiny_swarm_world/infrastructure/adapters/clients/docker_cli_runtime.py
  - src/tiny_swarm_world/infrastructure/adapters/clients/nexus_http_client.py
  - tests/application/services/artifacts/test_artifact_service_exports.py
  - tests/application/services/artifacts/test_artifact_workflows.py
  - tests/application/services/nexus/test_bootstrap_nexus.py
  - tests/application/services/nexus/test_nexus_repository_contracts.py
  - tests/architecture/test_hexagonal_imports.py
  - tests/architecture/test_legacy_surface_documentation.py
  - tests/infrastructure/adapters/clients/test_docker_cli_runtime.py
  - tests/infrastructure/adapters/clients/test_nexus_http_client.py
  - tests/infrastructure/test_composition.py
  - documentation/workflow/reports/07-nexus-artifact-contract.md
qualityGateCommands:
  - PYTHONPATH=src python3 -m unittest tests.application.services.artifacts
  - PYTHONPATH=src python3 -m unittest tests.application.services.nexus
  - PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_nexus_http_client tests.infrastructure.adapters.clients.test_docker_cli_runtime tests.infrastructure.test_composition tests.architecture.test_legacy_surface_documentation
  - python3 tools/quality_gate.py arch-tests
  - python3 tools/quality_gate.py test
  - python3 tools/quality_gate.py quality
  - git diff --check
qualityGateResult: PASS
rollbackRef: revert the Slice 07 checkpoint commit
arc42Updated: yes; building blocks, runtime view, deployment view, and risks updated
adrUpdated: checked; not required
```
