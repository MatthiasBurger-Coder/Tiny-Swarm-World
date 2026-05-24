# Slice 06 Report: Portainer Deployment Contract

## Status

```text
COMPLETED_PENDING_COMMIT
```

## Workflow Context

- Workflow: `Autonomous Runnable Setup`
- Version: `autonomous-runnable-setup-v1.0.0`
- Branch: `codex/workflow-autonomous-setup-20260524`
- Slice: `06`
- Owner: `senior_devops`
- Dependency: Slice 05 completed in commit `ec9cd2b`
- Context repair before Slice 06 completed in commit `fa175c0`

## S3 And S3D Evidence

- `S3_STATUS`: PASS before write-capable Slice 06 work.
- `S3_BRANCH`: PASS; active branch and local ref matched
  `codex/workflow-autonomous-setup-20260524`.
- `S3_SCOPE`: PASS; changed files are inside Slice 06 deployment,
  Portainer client, compose repository, Portainer compose asset,
  documentation, test, and report scope.
- `S3_CLASSIFY`: runtime/DevOps contract, Python automation, deployment
  boundary, security documentation, tests.
- `S3D_RESULT`: EXECUTION_PLAN.
- `SLICE_06_DEPENDENCIES`: `05`.
- `SLICE_06_TARGETED_GATES`: deployment service tests, compose repository
  tests, Portainer HTTP adapter tests, composition tests, package entrypoint
  tests, legacy surface catalog tests, arch-lint, and arch-tests.
- `SLICE_06_REQUIRED_GATES`: `python3 tools/quality_gate.py test`.

## Subagent Review Evidence

- Senior DevOps: BLOCKED on an out-of-scope direct Docker Swarm deployer and
  on live apply being possible without post-apply verification. Addressed by
  keeping Slice 06 as a Portainer API contract only and leaving CLI
  `deployment apply` fail-closed.
- Senior System Architect: BLOCKED on the Portainer first-bootstrap cycle and
  a possible completed apply result without observed verification. Addressed
  by documenting `EnsurePortainerStack` as post-bootstrap only and requiring
  verified `VerificationResult` evidence before `DeploymentApplyWorkflow`
  can complete.
- Senior Tester: requested regressions for blocked apply, Portainer create and
  update behavior, sanitized HTTP errors, compose path validation, CLI
  composition, and static documentation. Added focused tests.
- Senior Security/Sandbox Engineer: BLOCKED until privileged Portainer compose
  socket and Docker volume mounts were cataloged as live-operation surface
  risk. Addressed in `documentation/system/live-operation-surfaces.adoc` and
  architecture documentation tests.
- Senior Requirement Engineer: BLOCKED until `DeploymentApplyWorkflow` no
  longer had a completed path without verification evidence. Addressed.
- Security Recheck: APPROVED; residual risk is that the Portainer compose
  asset remains privileged Docker-control configuration and must stay limited
  to intentional local Swarm bootstrap.
- Requirement Recheck: APPROVED; docs do not present Portainer live setup as
  implemented and apply completion now requires verified evidence.

## Implementation Summary

- Added `EnsurePortainerStack` as a deployment application service that reads
  compose content through `PortComposeFileRepository`, resolves the target
  endpoint through `PortPortainerClient`, then creates or updates a
  Portainer-managed stack through the port.
- Exported `EnsurePortainerStack` from the deployment service namespace.
- Extended `DeploymentApplyWorkflow` so configured steps are blocked before
  apply unless they expose verify-after-apply behavior. Apply can complete
  only after a `VerificationResult` with `VerificationStatus.VERIFIED`.
- Added deployment apply failure and verification failure statuses without
  leaking raw exception payloads into operator-facing reasons.
- Kept `src/tiny_swarm_world/infrastructure/composition.py` fail-closed:
  `build_deployment_services()` still wires an empty `DeploymentApplyWorkflow`
  and does not construct a Portainer client from environment variables.
- Hardened `PortainerHttpClient` by rejecting credentials embedded in the
  base URL and removing response bodies from HTTP error messages.
- Expanded Portainer HTTP adapter coverage for endpoint lookup, stack lookup,
  JWT caching, create fallback, update payloads, missing JWT, and sanitized
  errors. Tests use fakes only and do not contact Portainer.
- Hardened `ComposeFileRepositoryYaml` with stack-name validation and
  summary-only logging so traversal-like names and absolute-path leakage are
  not accepted.
- Corrected the committed Portainer compose asset to use
  `/var/run/docker.sock` instead of the nonstandard `/var/run/sock`.
- Cataloged the Portainer compose asset as privileged Docker-control
  configuration in the live-operation surface documentation.
- Updated arc42 and deployment documentation to state that the Portainer
  contract is tested and post-bootstrap, while CLI `deployment apply` remains
  blocked until first-time bootstrap and observed-state verification exist.

## Requirement Classification

- Functional requirement: Portainer stack create/update behavior is available
  through a port-backed application service with mocked tests.
- Architecture constraint: deployment application services depend on ports and
  domain objects; HTTP and filesystem details remain in infrastructure
  adapters.
- Security requirement: Portainer credentials are not accepted in URLs, HTTP
  response bodies are not exposed in errors, and privileged compose mounts are
  documented as live-operation risk.
- Resilience requirement: deployment apply remains fail-closed unless
  verify-after-apply evidence exists.
- Observability requirement: deployment workflow results can carry typed
  verification evidence instead of raw Portainer or command output.
- Quality-gate requirement: default verification remains mocked or static and
  does not contact Portainer or deploy a stack.
- Assumption: first-time Portainer bootstrap and observed service readiness are
  future deployment slices; Slice 06 therefore does not wire the Portainer
  contract into the CLI composition root as executable live apply behavior.

## Verification

Focused targeted checks:

```bash
PYTHONPATH=src python3 -m unittest tests.application.services.deployment
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_portainer_http_client
PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition
PYTHONPATH=src python3 -m unittest tests.test_package_entrypoint
```

Result: passed. The focused tests ran `14`, `6`, `9`, `16`, and `18` tests.

Additional targeted regression bundle:

```bash
PYTHONPATH=src python3 -m unittest tests.application.services.deployment tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml tests.infrastructure.adapters.clients.test_portainer_http_client tests.infrastructure.test_composition tests.test_package_entrypoint tests.architecture.test_legacy_surface_documentation
```

Result: passed, `69` tests.

Architecture gates:

```bash
python3 tools/quality_gate.py arch-lint
python3 tools/quality_gate.py arch-tests
```

Result: passed. `arch-lint` kept all three import-linter contracts;
`arch-tests` ran `14` tests.

Required gate:

```bash
python3 tools/quality_gate.py test
```

Result: passed, `300` tests, `1` skipped.

Full quality gate:

```bash
python3 tools/quality_gate.py quality
```

Result: passed. The full quality gate executed lint, arch-lint, arch-tests,
typecheck, and unittest using the ignored local `.venv/` tooling where needed.

Whitespace gate:

```bash
git diff --check
```

Result: passed.

## Live Infrastructure

No live infrastructure commands were run. Slice 06 did not execute Multipass,
Docker Swarm, compose deployment, netplan, socat, Portainer, Nexus, Jenkins,
RabbitMQ, SonarQube, Swagger/NGINX bootstrap, image build, image push, or
stack upload commands.

## Checkpoint Record

```yaml
CP_RECORD: VERIFIED_PENDING_COMMIT
workflowVersion: autonomous-runnable-setup-v1.0.0
sliceId: "06"
changedFiles:
  - documentation/arc42/05_building_blocks.adoc
  - documentation/arc42/06_runtime_view.adoc
  - documentation/arc42/07_deployment_view.adoc
  - documentation/deployment/system.adoc
  - documentation/system/live-operation-surfaces.adoc
  - infra/config/compose/portainer/docker-compose.yml
  - src/tiny_swarm_world/application/services/deployment/__init__.py
  - src/tiny_swarm_world/application/services/deployment/ensure_portainer_stack.py
  - src/tiny_swarm_world/application/services/deployment/workflows.py
  - src/tiny_swarm_world/infrastructure/adapters/clients/portainer_http_client.py
  - src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py
  - tests/application/services/deployment/test_deployment_service_exports.py
  - tests/application/services/deployment/test_deployment_workflows.py
  - tests/application/services/deployment/test_ensure_portainer_stack.py
  - tests/architecture/test_legacy_surface_documentation.py
  - tests/infrastructure/adapters/clients/test_portainer_http_client.py
  - tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py
  - tests/infrastructure/test_composition.py
  - documentation/workflow/reports/06-portainer-deployment-contract.md
qualityGateCommands:
  - PYTHONPATH=src python3 -m unittest tests.application.services.deployment
  - PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml
  - PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_portainer_http_client
  - PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition
  - PYTHONPATH=src python3 -m unittest tests.test_package_entrypoint
  - PYTHONPATH=src python3 -m unittest tests.architecture.test_legacy_surface_documentation
  - python3 tools/quality_gate.py arch-lint
  - python3 tools/quality_gate.py arch-tests
  - python3 tools/quality_gate.py test
  - python3 tools/quality_gate.py quality
  - git diff --check
qualityGateResult: PASS
rollbackRef: revert the Slice 06 checkpoint commit
arc42Updated: yes; building blocks, runtime view, and deployment view updated
adrUpdated: checked; not required
```
