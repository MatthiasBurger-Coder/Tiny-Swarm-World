# Workflow: Issue #183 SOLID LXC Swarm Runtime Decomposition

Version: `issue-183-v1.0.0`
Workflow ID: `issue-183-20260808`
Authoring branch: `feature/workflow-issue-183-lxc-runtime-solid-20260808`
Implementation branch requested by issue: `feature/split-lxc-swarm-runtime-solid`
Status: `READY_FOR_EXECUTION`
Execution profile: `FULL_PATH`
Issue: [#183 SOLID: Split lxc_swarm_runtime.py into cohesive LXC client modules](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/183)

This is an implementation and verification plan. It does not claim that the
runtime has been split, that SonarQube has an accepted external result, or that
live Selenium evidence exists. The referenced `PortLocalFileStorage` port was inspected for context;
Issue #183 does not authorize changing it.

## Executive Summary

Issue #183 addresses a large infrastructure adapter module that currently
combines manager shell execution, Swarm stack deployment, stack assets and
prerequisites, container inspection, Portainer and Nexus clients, image
publication, and migration-lock recovery. The workflow extracts those
responsibilities into cohesive packages while keeping the old module as a
compatibility export surface until all consumers migrate.

The change remains inside the existing Python hexagonal modular monolith. It
does not create a microservice, alter application ports, change external
runtime behavior, or broaden the Linux/WSL-only Docker Swarm operating model.
Local verification is deterministic and mocked. The issue-required Selenium
E2E and SonarQube checks are separate live/external gates and must retain their
explicit verification states until actual redacted evidence is available.

## Target Picture

```text
application ports (stable)
        |
        v
infrastructure/adapters/clients/lxc/
  command/       manager shell gateway and bounded diagnostics
  swarm/         stack runtime, assets, prerequisite registry/strategies
  docker/        LXC container runtime adapter
  services/      Portainer admin/client and Nexus HTTP adapters
  images/        image publisher and image-operation errors
        |
        v
lxc_swarm_runtime.py compatibility exports -> existing composition/tests
```

The old module is reduced to compatibility exports or a thin facade. New
responsibility-specific code owns one reason to change, and composition moves
to the concrete packages gradually so each step remains importable and
testable.

## Requirement Clarification Gate

### Original Request

`workflow create issue #183` with the referenced
`src/tiny_swarm_world/application/ports/file_management/port_local_file_storage.py`.

### Interpreted Intent

Create a complete executable workflow for GitHub Issue #183. Inspect the
referenced local-storage port as repository context, but scope implementation
to the cohesive decomposition of
`src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py`
and its verified consumers, tests, architecture evidence, and required
quality/live validation.

### Change Type

Architecture-preserving Python infrastructure refactor with compatibility
exports, composition migration, regression tests, architecture guards,
documentation synchronization, external quality verification, and an
operator-consent-gated browser E2E evidence path.

### Affected Process Strand

`workflow create` -> guarded workflow publication -> later `workflow execute`
on the issue implementation branch. Issue completion remains controlled by
the requirement matrix, evidence package, Three-Amigos perspectives, local
quality gates, external SonarQube evidence, and the Issue Completion Auditor.

### Affected Architecture Area

Infrastructure client adapters and composition wiring under the existing
hexagonal boundary. The change touches deployment, artifacts, and platform
adapter implementations but does not move application responsibilities or
introduce a deployable service boundary.

### Explicit Requirements

The complete requirement matrix is maintained at
`.tiny-swarm/evidence/solid-lxc-swarm-runtime/requirement_matrix.md`.
Implementation may not begin until the Requirement Lead, System Architect,
Python Automation Developer, and Senior Tester have reviewed the matrix and
the Three-Amigos note at
`.tiny-swarm/evidence/solid-lxc-swarm-runtime/three-amigos.md`.

The workflow must:

* keep all public application ports and observable runtime behavior stable;
* extract manager shell execution into a reusable command gateway/runner;
* extract Swarm stack deployment into `lxc/swarm/swarm_stack_runtime.py`;
* extract stack asset transfer into `lxc/swarm/stack_asset_transfer.py`;
* extract stack prerequisite handling into a registry with Strategy-style
  handlers for Traefik, SonarQube, and Swagger;
* extract `LxcContainerRuntime` into an LXC Docker runtime module;
* extract Portainer admin/client and Nexus HTTP wrappers into `lxc/services/`;
* extract image publishing and its rejection/error types into `lxc/images/`;
* preserve compatibility imports from the old module path and update
  composition imports gradually;
* avoid application-port changes unless a verified blocker proves one is
  necessary;
* add focused tests for every extracted module and architecture tests that
  prevent unrelated growth in the compatibility module;
* store before/after responsibility maps in the issue evidence directory;
* add or extend a Selenium test using the issue-specified imports and store
  redacted E2E evidence under
  `.tiny-swarm-world/evidence/solid-lxc-swarm-runtime/e2e/`;
* pass the existing and new test suites, obtain an observable accepted
  SonarQube result, and introduce no new critical/high code smells.

### Implicit Requirements

* Preserve the existing `PortSwarmStackRuntime`, `PortContainerRuntime`,
  `PortContainerImagePublisher`, `PortPortainerAdminClient`,
  `PortPortainerClient`, `PortDeploymentGateway`, and `PortNexusClient`
  contracts.
* Keep infrastructure technology details in infrastructure adapters and keep
  application services dependent on ports rather than concrete adapters.
* Keep `infrastructure/composition.py` as the wiring root and keep
  `__main__.py` thin.
* Preserve bounded timeouts, retries, cleanup, redacted diagnostics, and
  operator-action messages while moving code.
* Preserve the distinction between the existing LXC Docker-engine runtime and
  the extracted container-runtime adapter; do not merge them accidentally.
* Keep local tests free of Incus, Docker Swarm, Portainer, Nexus, credential,
  or browser side effects.
* Treat live browser evidence and SonarQube status as stateful evidence, not as
  implied by static tests or configuration.

### Assumptions

* The GitHub issue is the authoritative requirement source; no relevant EPIC
  exists under `documentation/epics`.
* Existing responsibility decisions in
  `documentation/arc42/09_decisions/adr-separate-platform-artifacts-deployment.adoc`
  and `command-runner-responsibility.adoc` remain authoritative.
* Compatibility exports may remain in the legacy module until all verified
  imports migrate; removing that surface is not assumed.
* Existing browser infrastructure can be extended with an issue-specific,
  ignored evidence root without changing the default consent-gated behavior.
* The issue-required implementation branch name is available or can be
  created during `workflow execute` after this workflow branch is published.

### Non-Goals

* No change to `PortLocalFileStorage` without a separately verified requirement.
* No new REST, gRPC, Protobuf, event, or microservice contract.
* No application-service redesign, provider migration, Kubernetes-first work,
  Java/Maven/Spring Boot structure, or browser React frontend.
* No broad refactor of `composition.py` beyond import/wiring migration required
  by the extracted adapters.
* No behavior changes to stack deployment, image publication, Portainer/Nexus
  interactions, lock recovery, timeout/retry policy, or diagnostics.
* No live Incus, Docker, Swarm, Portainer, Nexus, or credential-backed command
  during local implementation or the default quality gate.
* No claim of SonarQube success or live Selenium success without observable
  result evidence.

### Risks

* Moving private helpers can change quoting, retry, timeout, cleanup, logging,
  redaction, or exception identity even when public method names remain stable.
* The old module is imported by composition, provider-selected composition,
  repository tests, logging tests, and a large adapter test module; incomplete
  compatibility exports can fail far from the changed package.
* Portainer and Nexus adapters mix HTTP behavior with LXC manager address
  discovery; extraction must preserve the existing fallback and error mapping.
* Image publishing transfers bytes and build contexts; a gateway split must not
  leak secrets, alter tar contents, or bypass registry safeguards.
* The requested live E2E path depends on an authorized live installation,
  browser prerequisites, routed HTTPS, and safe credentials.
* SonarQube availability may be external to the local WSL environment; an
  unavailable result is a blocker for issue completion, not a passing result.

### Open Questions

1. Which command-gateway name and constructor shape best preserve the current
   manager/node shell semantics without creating a new application port?
2. Should the prerequisite registry use a typed strategy protocol or a small
   callable registry while keeping stack-specific behavior out of the main
   runtime class?
3. Should the issue-specific E2E evidence root be selected by a test-only
   environment variable or by a dedicated issue test wrapper?
4. Which existing CI/SonarQube result is the authoritative observable result
   for this branch, and how will the exact status be linked in evidence?

These are bounded implementation details. They may be resolved from existing
code and test contracts during the named slices. If repository evidence cannot
resolve one without changing public behavior or governance, stop the affected
slice and escalate to the System Architect; do not guess.

### Blocking Questions

None for workflow authoring. The issue goal, target package map, compatibility
rule, acceptance criteria, evidence paths, and quality expectations are clear.
The open questions above are execution decisions, not blockers to defining the
workflow.

### Confidence and Decision

Confidence: `94%`. Decision: `READY_FOR_WORKFLOW`.

Mandatory roles are represented by Senior Requirement Engineer, Senior System
Architect, Senior Python Automation Developer, and Senior Tester. Senior
DevOps and Senior Documentation Engineer are required for external quality,
live-validation, and documentation synchronization. Console/status UI review
is `NOT_APPLICABLE`; Browser React review is forbidden for this repository
scope.

## Verified Baseline

* `lxc_swarm_runtime.py` is approximately 1,437 lines and contains
  `LxcSwarmRuntime`, `LxcContainerRuntime`, `LxcPortainerAdminClient`,
  `LxcNexusHttpClient`, `LxcPortainerHttpClient`, and
  `LxcContainerImagePublisher`, plus image-operation exception types and
  shared parsing/quoting/diagnostic helpers.
* `LxcSwarmRuntime` owns manager/node shell execution, stack deployment,
  service listing, external secret handling, Infisical migration-lock recovery,
  network/secret prerequisites, published-port reconciliation, asset transfer,
  and dashboard rendering.
* `LxcContainerRuntime` provides container name lookup and file inspection
  through manager-side Docker commands.
* Portainer and Nexus adapters resolve the managed manager address and wrap
  existing HTTP clients; the Portainer adapter implements both Portainer and
  deployment gateway ports.
* `LxcContainerImagePublisher` owns public/build-image availability checks,
  context transfer, registry login, manager-side build/push/load operations,
  and image-operation diagnostics.
* `composition.py` and `composition_lxc_runtimes.py` import the legacy module
  directly. Tests also patch its module-level `subprocess`, `time`, and helper
  names, so compatibility planning must include patch targets.
* `tests/infrastructure/adapters/clients/test_lxc_swarm_runtime.py` is
  approximately 1,418 lines and covers all mixed responsibilities. Existing
  logging, composition, and repository tests import the legacy classes.
* The existing architecture tests enforce inward dependency direction but do
  not yet guard the responsibility surface or growth of this legacy module.
* Existing browser E2E infrastructure already uses
  `from selenium import webdriver` and
  `from selenium.webdriver.common.by import By`, and records redacted local
  evidence under an ignored path; the issue-specific path still needs a
  verified extension.
* `QUALITY.md` and `tools/quality_gate.py` define the authoritative local
  commands. The configured external SonarQube workflow is not evidence until
  its actual result is observed.

## Scope and Architecture Constraints

### In Scope

The extracted `lxc/` package structure, compatibility facade/exports,
composition import migration, focused unit and architecture tests, before/after
responsibility evidence, issue-specific browser E2E evidence routing, Arc42
planned-architecture synchronization, local quality gates, external SonarQube
status review, and the final issue-completion audit.

### Hexagonal Constraints

The extracted modules remain infrastructure adapters implementing existing
application ports. Domain and application code must not import infrastructure.
Application services must not gain shell, filesystem, HTTP, Docker, YAML, or
logging details. `composition.py` remains the concrete-adapter wiring root.
Compatibility imports may point inward from the legacy infrastructure module,
but new application code must not depend on the legacy facade.

### Safety and Resilience Constraints

Preserve the current manager/node backend selection, bounded subprocess
timeouts, retry delays, shell quoting, failure classification, bounded log
text, redacted exception/evidence content, and live-consent boundaries. Any
changed retry or timeout semantics require an explicit requirement mapping and
new deterministic tests. Live validation is serialized and opt-in.

## Python Automation Assessment

This is a Python infrastructure-adapter refactor. Use the Senior Python
Automation Developer for extraction and composition wiring, with focused
`unittest` coverage and type-safe imports. Use existing `requests`, YAML,
subprocess, tar, path, and logging dependencies; do not add a framework or
new runtime dependency merely to support the split.

## Frontend Assessment

Browser React review is `NOT_APPLICABLE` and forbidden because the repository
has no verified React frontend module or frontend quality gate. The Selenium
requirement is a live test/evidence concern only. Console/status UI review is
`NOT_APPLICABLE` because no terminal presentation or progress behavior is in
scope.

## Verification-State Classification

| Check | Classification | Workflow rule |
| --- | --- | --- |
| focused adapter and architecture tests | `APPLICABLE_LOCAL` | Run with mocks/fakes and temporary files. |
| full Python quality gate | `APPLICABLE_LOCAL` | Required before implementation commit. |
| SonarQube quality result | `APPLICABLE_EXTERNAL` | Actual observable passing result required; unavailable is non-success. |
| issue-specific Selenium E2E | `APPLICABLE_LIVE` | Requires explicit live consent, prerequisites, and redacted evidence. |
| live Incus/Docker/Swarm mutation | `NOT_APPLICABLE` to local workflow | Never run during default local gates. |
| browser React checks | `NOT_APPLICABLE` | No frontend module is in scope. |

During workflow authoring, no implementation, live, or external gate is
executed. Later `workflow execute` must record `LIVE_CONSENT_MISSING`,
`LIVE_PREREQUISITE_MISSING`, `LIVE_FAILED_AFTER_MUTATION`, or
`LIVE_VERIFIED` as applicable, and `EXTERNAL_GATE_UNAVAILABLE`,
`EXTERNAL_GATE_FAILED`, or `EXTERNAL_GATE_VERIFIED` for SonarQube.

## Ordered Slices

### Slice 01 — Freeze contracts, responsibility map, and execution evidence

```yaml
slice_id: "01"
profile: "FULL_PATH"
owner: "Senior Requirement Engineer"
secondary_reviewers: ["Senior System Architect", "Senior Python Automation Developer", "Senior Tester"]
affected_files:
  - ".tiny-swarm/evidence/solid-lxc-swarm-runtime/requirement_matrix.md"
  - ".tiny-swarm/evidence/solid-lxc-swarm-runtime/three-amigos.md"
  - ".tiny-swarm/evidence/solid-lxc-swarm-runtime/responsibility-map-before.md"
  - "src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py"
affected_modules: ["infrastructure.adapters.clients.lxc_swarm_runtime", "issue evidence"]
affected_contracts: ["existing application ports", "legacy compatibility import surface"]
dependencies: []
parallel_group: "serial"
file_locks: ["src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py", ".tiny-swarm/evidence/solid-lxc-swarm-runtime/"]
contract_locks: ["public adapter constructors and methods", "exception identity and messages"]
architecture_locks: ["hexagonal dependency direction", "in-process responsibility boundaries"]
quality_gates:
  targeted: ["git diff --check"]
  required: ["requirement matrix review", "Three-Amigos agreement"]
documentation:
  arc42: "documentation/arc42/05_building_blocks.adoc"
  adr: "No new ADR; existing responsibility and command-runner decisions remain authoritative."
stop_conditions: ["missing issue requirement", "public-contract disagreement", "unclear ownership"]
```

Done criteria: every issue bullet and acceptance criterion has a stable
requirement ID; the three required perspectives agree on stable behavior and
scope; the current class/helper responsibility map is stored; no application
port or live behavior change is silently assumed.

### Slice 02 — Extract the LXC command gateway and shared diagnostics

```yaml
slice_id: "02"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers: ["Senior System Architect", "Senior Tester"]
affected_files:
  - "src/tiny_swarm_world/infrastructure/adapters/clients/lxc/command/__init__.py"
  - "src/tiny_swarm_world/infrastructure/adapters/clients/lxc/command/manager_shell_gateway.py"
  - "src/tiny_swarm_world/infrastructure/adapters/clients/lxc/command/diagnostics.py"
  - "src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py"
  - "tests/infrastructure/adapters/clients/lxc/command/"
affected_modules: ["lxc.command", "legacy compatibility facade"]
affected_contracts: ["manager shell execution semantics", "bounded logs", "retry and timeout behavior"]
dependencies: ["01"]
parallel_group: "serial"
file_locks: ["src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py", "src/tiny_swarm_world/infrastructure/adapters/clients/lxc/command/", "tests/infrastructure/adapters/clients/lxc/command/"]
contract_locks: ["manager/node shell invocation", "backend CLI mapping"]
architecture_locks: ["infrastructure-only shell execution", "no new application port"]
quality_gates:
  targeted: ["python3 tools/quality_gate.py lint", "python3 tools/quality_gate.py typecheck", "focused command-gateway unittest"]
  required: ["python3 tools/quality_gate.py arch-lint", "python3 tools/quality_gate.py arch-tests"]
documentation:
  arc42: "documentation/arc42/05_building_blocks.adoc"
  adr: "No new ADR unless the gateway changes the accepted command-runner responsibility."
stop_conditions: ["changed quoting", "unbounded output", "changed retry/timeout semantics", "raw secret logging"]
```

Done criteria: manager and node operations use the extracted gateway; the
legacy path exports compatible names; failure diagnostics remain bounded and
redacted; focused tests cover success, failure, retry, timeout, backend choice,
and exception propagation without invoking Incus or Docker.

### Slice 03 — Extract Swarm stack runtime, assets, and prerequisite strategies

```yaml
slice_id: "03"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers: ["Senior System Architect", "Senior Tester", "Senior DevOps Engineer"]
affected_files:
  - "src/tiny_swarm_world/infrastructure/adapters/clients/lxc/swarm/__init__.py"
  - "src/tiny_swarm_world/infrastructure/adapters/clients/lxc/swarm/swarm_stack_runtime.py"
  - "src/tiny_swarm_world/infrastructure/adapters/clients/lxc/swarm/stack_asset_transfer.py"
  - "src/tiny_swarm_world/infrastructure/adapters/clients/lxc/swarm/stack_prerequisite_registry.py"
  - "src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py"
  - "tests/infrastructure/adapters/clients/lxc/swarm/"
affected_modules: ["lxc.swarm", "PortSwarmStackRuntime implementation"]
affected_contracts: ["stack deployment", "service readiness listing", "external secrets", "migration-lock recovery"]
dependencies: ["02"]
parallel_group: "serial"
file_locks: ["src/tiny_swarm_world/infrastructure/adapters/clients/lxc/swarm/", "src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py", "tests/infrastructure/adapters/clients/lxc/swarm/"]
contract_locks: ["PortSwarmStackRuntime", "stack asset contents", "prerequisite ordering"]
architecture_locks: ["deployment behavior remains infrastructure-owned", "strategy registry does not become a service"]
quality_gates:
  targeted: ["focused Swarm runtime, asset, and prerequisite unittests", "python3 tools/quality_gate.py lint", "python3 tools/quality_gate.py typecheck"]
  required: ["python3 tools/quality_gate.py arch-lint", "python3 tools/quality_gate.py arch-tests"]
documentation:
  arc42: "documentation/arc42/05_building_blocks.adoc; documentation/arc42/11_risks_and_debt.adoc"
  adr: "No new ADR; preserve existing deployment and command-runner decisions."
stop_conditions: ["stack behavior drift", "strategy hard-codes unrelated stacks", "asset or secret leakage", "live command in unit tests"]
```

Done criteria: `LxcSwarmRuntime` behavior is supplied by the extracted swarm
modules; Traefik, SonarQube, and Swagger prerequisite handling is registry/
strategy-based; asset transfer, port reconciliation, secrets, service status,
dashboard rendering, lock recovery, and error behavior retain focused tests.

### Slice 04 — Extract Docker, service clients, image publisher, and errors

```yaml
slice_id: "04"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers: ["Senior System Architect", "Senior Tester", "Senior Security Sandbox Engineer"]
affected_files:
  - "src/tiny_swarm_world/infrastructure/adapters/clients/lxc/docker/__init__.py"
  - "src/tiny_swarm_world/infrastructure/adapters/clients/lxc/docker/lxc_container_runtime.py"
  - "src/tiny_swarm_world/infrastructure/adapters/clients/lxc/services/__init__.py"
  - "src/tiny_swarm_world/infrastructure/adapters/clients/lxc/services/lxc_portainer_admin_client.py"
  - "src/tiny_swarm_world/infrastructure/adapters/clients/lxc/services/lxc_portainer_http_client.py"
  - "src/tiny_swarm_world/infrastructure/adapters/clients/lxc/services/lxc_nexus_http_client.py"
  - "src/tiny_swarm_world/infrastructure/adapters/clients/lxc/images/__init__.py"
  - "src/tiny_swarm_world/infrastructure/adapters/clients/lxc/images/lxc_container_image_publisher.py"
  - "src/tiny_swarm_world/infrastructure/adapters/clients/lxc/images/errors.py"
  - "src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py"
  - "tests/infrastructure/adapters/clients/lxc/docker/"
  - "tests/infrastructure/adapters/clients/lxc/services/"
  - "tests/infrastructure/adapters/clients/lxc/images/"
affected_modules: ["lxc.docker", "lxc.services", "lxc.images"]
affected_contracts: ["PortContainerRuntime", "Portainer ports", "PortDeploymentGateway", "PortNexusClient", "PortContainerImagePublisher"]
dependencies: ["02"]
parallel_group: "serial"
file_locks: ["src/tiny_swarm_world/infrastructure/adapters/clients/lxc/", "src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py", "tests/infrastructure/adapters/clients/lxc/"]
contract_locks: ["public constructors", "HTTP status/error mapping", "image rejection diagnostics"]
architecture_locks: ["existing application ports unchanged", "no cross-responsibility imports from application"]
quality_gates:
  targeted: ["focused Docker, Portainer, Nexus, and image-publisher unittests", "python3 tools/quality_gate.py lint", "python3 tools/quality_gate.py typecheck"]
  required: ["python3 tools/quality_gate.py arch-lint", "python3 tools/quality_gate.py arch-tests"]
documentation:
  arc42: "documentation/arc42/05_building_blocks.adoc; documentation/arc42/05_analysis/responsibility-separation-analysis.md"
  adr: "No new ADR; this is a compatibility-preserving implementation of accepted responsibility direction."
stop_conditions: ["application port change", "credential/raw response leakage", "merging LXC Docker-engine and container-runtime responsibilities", "changed error identity"]
```

Done criteria: each extracted class has one clear reason to change; the
Portainer dual-port behavior, Nexus HTTP mapping, image availability/publish
paths, context transfer, rate-limit diagnostics, and exception types are
covered by focused deterministic tests; no credentials or raw HTTP/command
payloads enter logs or evidence.

### Slice 05 — Migrate composition and preserve the compatibility surface

```yaml
slice_id: "05"
profile: "FULL_PATH"
owner: "Senior System Architect"
secondary_reviewers: ["Senior Python Automation Developer", "Senior Tester", "Senior Documentation Engineer"]
affected_files:
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "src/tiny_swarm_world/infrastructure/composition_lxc_runtimes.py"
  - "src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py"
  - "tests/infrastructure/test_composition.py"
  - "tests/infrastructure/test_lxc_runtime_logging.py"
  - "tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py"
  - "tests/infrastructure/adapters/clients/test_lxc_swarm_runtime.py"
  - "tests/architecture/test_lxc_runtime_boundaries.py"
affected_modules: ["composition root", "legacy compatibility facade", "architecture tests"]
affected_contracts: ["composition bundle construction", "legacy import and patch paths", "provider-selected LXC runtime"]
dependencies: ["03", "04"]
parallel_group: "serial"
file_locks: ["src/tiny_swarm_world/infrastructure/composition.py", "src/tiny_swarm_world/infrastructure/composition_lxc_runtimes.py", "src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py", "tests/infrastructure/", "tests/architecture/test_lxc_runtime_boundaries.py"]
contract_locks: ["composition constructor arguments", "compatibility imports", "test patch targets"]
architecture_locks: ["composition remains wiring root", "legacy module cannot grow unrelated classes"]
quality_gates:
  targeted: ["PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition tests.infrastructure.test_lxc_runtime_logging tests.infrastructure.adapters.clients.test_lxc_swarm_runtime", "python3 tools/quality_gate.py arch-tests"]
  required: ["python3 tools/quality_gate.py quality"]
documentation:
  arc42: "documentation/arc42/05_building_blocks.adoc"
  adr: "No new ADR; architecture guard must reference existing decisions."
stop_conditions: ["composition behavior drift", "broken legacy patch path", "new mixed responsibility in facade", "architecture test weakened"]
```

Done criteria: composition imports concrete extracted modules, the old import
path continues to expose the issue-approved compatibility symbols, existing
tests pass without broad patch rewrites, and architecture tests reject new
unrelated classes/imports in the legacy module.

### Slice 06 — Extend issue-specific browser evidence and validate live boundaries

```yaml
slice_id: "06"
profile: "FULL_PATH"
owner: "Senior Tester"
secondary_reviewers: ["Senior DevOps Engineer", "Senior Python Automation Developer", "Senior Security Sandbox Engineer"]
affected_files:
  - "tests/live/browser_e2e_contract.py"
  - "tests/live/test_post_install_browser_live.py"
  - ".tiny-swarm/evidence/solid-lxc-swarm-runtime/e2e/"
affected_modules: ["live browser evidence harness"]
affected_contracts: ["Selenium import contract", "routed service-access browser behavior", "redacted evidence schema"]
dependencies: ["05"]
parallel_group: "serialized-live"
file_locks: ["tests/live/browser_e2e_contract.py", "tests/live/test_post_install_browser_live.py", ".tiny-swarm/evidence/solid-lxc-swarm-runtime/e2e/"]
contract_locks: ["from selenium import webdriver", "from selenium.webdriver.common.by import By", "live evidence status semantics"]
architecture_locks: ["live checks remain outside default local quality", "no credential persistence"]
quality_gates:
  targeted: ["PYTHONPATH=src python3 -m unittest tests.live.browser_e2e_contract"]
  required: ["authorized issue-specific Selenium run only when live consent and prerequisites exist"]
documentation:
  arc42: "documentation/arc42/07_deployment_view.adoc; documentation/arc42/11_risks_and_debt.adoc"
  adr: "No new ADR; use existing explicit live-consent and evidence policies."
stop_conditions: ["missing explicit live consent", "missing browser/runtime prerequisite", "raw credential or page payload in evidence", "failed mutation without recovery evidence"]
```

Done criteria: static tests prove the exact Selenium imports and evidence
contract; the live run opens the routed dashboard, finds a visible service link
or status using `By`, proves the page is not blank, and writes redacted
evidence under the issue path. If live prerequisites or consent are absent, the
recorded state is non-success and the issue remains open.

### Slice 07 — Full quality, external gate, documentation, and completion audit

```yaml
slice_id: "07"
profile: "FULL_PATH"
owner: "Issue Completion Auditor"
secondary_reviewers: ["Senior Requirement Engineer", "Senior System Architect", "Senior Tester", "Senior DevOps Engineer", "Senior Documentation Engineer"]
affected_files:
  - "documentation/arc42/05_building_blocks.adoc"
  - "documentation/arc42/05_analysis/responsibility-separation-analysis.md"
  - ".tiny-swarm/evidence/solid-lxc-swarm-runtime/responsibility-map-after.md"
  - ".tiny-swarm/evidence/solid-lxc-swarm-runtime/implementation_summary.md"
  - ".tiny-swarm/evidence/solid-lxc-swarm-runtime/changed_files.md"
  - ".tiny-swarm/evidence/solid-lxc-swarm-runtime/test_results.md"
  - ".tiny-swarm/evidence/solid-lxc-swarm-runtime/remaining_risks.md"
  - ".tiny-swarm/evidence/solid-lxc-swarm-runtime/acceptance_checklist.md"
  - ".tiny-swarm/evidence/solid-lxc-swarm-runtime/issue-completion-audit.md"
affected_modules: ["Arc42 architecture documentation", "issue evidence", "quality publication"]
affected_contracts: ["requirement-to-evidence traceability", "SonarQube result", "issue completion decision"]
dependencies: ["06"]
parallel_group: "serial"
file_locks: ["documentation/arc42/", ".tiny-swarm/evidence/solid-lxc-swarm-runtime/"]
contract_locks: ["issue acceptance criteria", "verification-state policy", "completion status"]
architecture_locks: ["planned versus implemented wording", "no stale responsibility map"]
quality_gates:
  targeted: ["git diff --check"]
  required: ["python3 tools/quality_gate.py quality", "observable SonarQube result", "Issue Completion Auditor decision"]
documentation:
  arc42: "documentation/arc42/05_building_blocks.adoc; documentation/arc42/05_analysis/responsibility-separation-analysis.md; documentation/arc42/11_risks_and_debt.adoc"
  adr: "Confirm no new ADR was required; do not rewrite existing ADR history."
stop_conditions: ["open requirement", "missing evidence", "unavailable required external gate", "Arc42 describes planned behavior as implemented"]
```

Done criteria: the full local quality gate and required focused checks pass;
external SonarQube status is observable and satisfies the issue without new
critical/high smells; live evidence is `LIVE_VERIFIED` or the issue is
explicitly `BLOCKED`; every requirement maps to implementation and verification
evidence; the independent auditor decides `PASS` before any DONE claim.

## Dependency Graph

```text
01 contract/evidence baseline
 |\
 | +--> 02 command gateway
 |          |\
 |          +--> 03 swarm extraction --+
 |          +--> 04 docker/services/images -+--> 05 composition and guards
 |                                           |
 +-------------------------------------------+--> 06 live browser evidence
                                                   |
                                                   +--> 07 quality/docs/audit
```

All executable slices are ordered because the legacy module, composition root,
compatibility imports, and shared tests are common locks. The graph is acyclic.

## Parallel Execution

- Can this workflow run in parallel? `No` for implementation slices; only read-only specialist review may be parallelized before Slice 01 is consolidated.
- Conflicting workflows: any workflow changing `lxc_swarm_runtime.py`, `composition.py`, `composition_lxc_runtimes.py`, the LXC client test tree, shared browser evidence helpers, or the same Arc42 sections.
- Shared files: the legacy runtime module, composition modules, existing mixed test module, live browser contract, Arc42 building-block and risk sections, and issue evidence directory.
- Shared infrastructure: Python environment, WSL/Linux quality tools, optional Incus/Docker Swarm installation, routed service-access endpoint, browser driver, and SonarQube result access.
- Requires isolated worktree: `Yes`; every later execution stream must use a dedicated worktree.
- Requires serialized live validation: `Yes`; live Incus/Swarm/browser validation is serialized unless isolated infrastructure is independently provisioned.
- Merge-order constraints: 01 -> 02 -> (03 and 04 in dependency order because they share the facade) -> 05 -> 06 -> 07; no stream worker may merge directly to the workflow or implementation branch.

## Automatic Work Distribution Policy

`workflow execute` must automatically analyze every executable slice for safe
specialist stream decomposition before implementation. It uses real Codex
subagents where supported and performs explicit role-based fallback review when
subagents are unavailable or not visible. Before implementation it must create
`.codex/evidence/slice-<number>-distribution.md`; after an implemented slice it
must create `.codex/evidence/slice-<number>-consolidation.md`. Codex remains the
final integration owner for consolidation, tests, evidence, PR readiness, and
merge readiness.

Stream map:

* backend: Senior Python Automation Developer for infrastructure adapters and
  composition;
* frontend: not applicable; terminal/status review only if verified progress or
  presentation files enter scope;
* tests: Senior Tester for unit, architecture, browser-contract, and evidence
  checks;
* runtime: Senior DevOps Engineer for live Incus/Docker/Swarm/browser and
  external SonarQube prerequisites;
* documentation: Senior Documentation Engineer for Arc42 and evidence wording;
* quality: quality-gate skills and Senior Tester;
* architecture: Senior System Architect for boundaries, compatibility, and
  ADR/Arc42 alignment;
* security: Senior Security Sandbox Engineer for credentials, redaction,
  subprocess, HTTP, archive, and evidence safety.

Do not parallelize overlapping files, unclear architecture, contradictory
requirements, mandatory ordering, shared migrations, strict database/schema
sequencing, generated-file conflicts, unclear secrets handling, weakened
safety guards, or a Three-Amigos decision that says the slice is not safely
parallelizable. This workflow has shared-file and mandatory-ordering conflicts
by default.

## Git Worktree Execution Rule

Every implementation slice requires its own isolated Git worktree. Stream
branches must use the form
`<workflow-branch>-slice-<number>-<stream>`. Workers must verify that their
branch belongs to this workflow and must stop before writing on `main`,
`master`, `develop`, or another shared branch. Workers may not merge directly
to the main workflow or implementation branch; Codex consolidates accepted
results only after distribution evidence, targeted tests, required quality
gates, and consolidation evidence exist.

## Role and Ownership Map

| Role | Responsibility |
| --- | --- |
| Senior Requirement Engineer | Issue extraction, requirement matrix, EPIC drift check, acceptance traceability. |
| Senior System Architect | Hexagonal boundaries, package responsibilities, compatibility facade, Arc42/ADR review. |
| Senior Python Automation Developer | Python adapter extraction, gateway behavior, composition wiring, deterministic implementation. |
| Senior Tester | Focused unit tests, architecture guards, browser contract, quality evidence. |
| Senior Workflow Architect | Slice ordering, locks, worktree policy, workflow regeneration and handoff. |
| Senior DevOps Engineer | External SonarQube status, live prerequisite and runtime safety review. |
| Senior Documentation Engineer | Arc42 synchronization and planned-versus-implemented wording. |
| Senior Security Sandbox Engineer | Credential, shell, HTTP, archive, log and evidence redaction review. |
| Issue Completion Auditor | Independent final PASS/INCOMPLETE/BLOCKED/REJECTED decision. |

## Issue Completion Discipline

- Requirement matrix path: `.tiny-swarm/evidence/solid-lxc-swarm-runtime/requirement_matrix.md`
- Required evidence path: `.tiny-swarm/evidence/solid-lxc-swarm-runtime/`
- Required evidence files: `requirement_matrix.md`, `implementation_summary.md`, `changed_files.md`, `test_results.md`, `remaining_risks.md`, `acceptance_checklist.md`, `three-amigos.md`, `responsibility-map-before.md`, `responsibility-map-after.md`, and `issue-completion-audit.md`; live E2E evidence belongs under `e2e/`.
- Requirement Lead review: Senior Requirement Engineer before implementation and again before completion.
- System Architect Reviewer review: Senior System Architect before extraction and after composition migration.
- Test / Evidence Reviewer review: Senior Tester after focused tests, full quality, and live/external evidence classification.
- Issue Completion Auditor review: required after all evidence is assembled; the implementer cannot approve its own completion.
- DONE blocking rule: any open, partially implemented, unverified, unavailable-required, or unevidenced requirement forces `INCOMPLETE`, `BLOCKED`, or `FAILED`; it must never be reported as `DONE`.

## Quality-Gate Expectations

Use only commands authorized by `QUALITY.md`:

```bash
python3 tools/quality_gate.py lint
python3 tools/quality_gate.py arch-lint
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py typecheck
python3 tools/quality_gate.py test
python3 tools/quality_gate.py quality
git diff --check
```

The full local quality gate is the default authority for local completion. It
does not prove live LXC/Swarm behavior, browser reachability, Selenium success,
or SonarQube status. SonarQube must be reported as
`EXTERNAL_GATE_VERIFIED` only from an observable actual result; otherwise the
issue remains blocked or incomplete according to the evidence.

## Documentation Synchronization Points

* Slice 01 records the before responsibility map and verifies existing ADR
  authority.
* Slice 03 updates the planned LXC Swarm adapter decomposition and residual
  runtime risk wording.
* Slice 04 synchronizes the responsibility-separation analysis without
  claiming a new microservice.
* Slice 06 documents the issue-specific live browser evidence state without
  treating static browser tests as live success.
* Slice 07 records the after map, final risks, evidence links, and Arc42
  implemented-versus-planned status.

## Stop Conditions and Escalation

Stop and report rather than guess when:

* the issue or public port contract cannot be read completely;
* the legacy facade cannot preserve compatibility imports or test patch paths;
* an extracted responsibility would require an application-port change;
* package ownership, architecture direction, or ADR applicability is unclear;
* shell quoting, timeout, retry, cleanup, redaction, archive, HTTP, or error
  semantics cannot be proven unchanged;
* local quality commands fail and the responsible failure is not repaired;
* live consent, browser prerequisites, or evidence redaction is missing;
* SonarQube status is unavailable or fails;
* required issue evidence is missing or a requirement cannot map to a check;
* Arc42 would need to describe planned behavior as implemented;
* continuing would require live infrastructure mutation without explicit
  operator approval.

Typed failures route through the repository policy: architecture failures to
the System Architect, build/type/lint failures to the Python owner and
quality-gate owner, test failures to Senior Tester, documentation failures to
Senior Documentation Engineer, lock conflicts to execution orchestration, and
unknown failures to Root Architect escalation.

## Commit and Push Plan

Workflow authoring output is committed only on
`feature/workflow-issue-183-lxc-runtime-solid-20260808` after workflow,
context-pack, evidence, Arc42, and `git diff --check` validation. Publication
pushes only `HEAD` to
`origin/feature/workflow-issue-183-lxc-runtime-solid-20260808`. It must not
create or merge a PR, delete branches, clean up the branch, force-push, or push
to `main`. `push auto` is not part of this workflow-create publication.

Later implementation commits must be one commit per slice on the verified
implementation branch and follow the active workflow executor's guarded
commit/push/merge policy only after the local, external, live, and audit
requirements are satisfied.

## Definition of Done

### Workflow-authoring completion

* dedicated workflow branch exists and is active;
* `documentation/workflow/workflow.md` is complete and validated;
* context pack is present and hashes governing inputs;
* issue requirement matrix and Three-Amigos gate note exist;
* Arc42 architecture documentation is checked/updated;
* slice metadata, dependencies, locks, stop conditions, evidence paths, and
  quality commands are explicit;
* workflow branch is committed and guarded-pushed.

### Issue-execution completion

* all requirements are implemented without silent scope reduction;
* compatibility and public port behavior are regression-tested;
* local quality is green;
* SonarQube has an observable acceptable result and no new critical/high smells;
* required live browser evidence is `LIVE_VERIFIED`, or the issue is explicitly
  reported as blocked with exact missing evidence;
* required evidence files exist and are internally consistent;
* Issue Completion Auditor returns `PASS`.

## Handoff to workflow execute

The authoring branch is
`feature/workflow-issue-183-lxc-runtime-solid-20260808`. After its guarded
publication, workflow execution must verify or create the issue-requested
implementation branch `feature/split-lxc-swarm-runtime-solid`, confirm the
active branch and local ref, and use isolated slice worktrees for any parallel
stream. It must run Slice 01 first, then follow the dependency graph; it must
not call `workflow create` backwards.

Before implementation, the executor must re-check the current issue, active
workflow, branch ownership, requirement matrix, Three-Amigos note, Arc42
baseline, and all locks. No live infrastructure command is authorized by this
workflow creation. Live Slice 06 requires a separate explicit consent path.

## Arc42 Check Status

`documentation/arc42/05_building_blocks.adoc` and
`documentation/arc42/11_risks_and_debt.adoc` were reviewed. The planned
Issue #183 decomposition is recorded as planned architecture only; existing
responsibility and command-runner ADRs remain authoritative, no new ADR is
required, and no implementation claim is made by this workflow.

## Workflow Handoff Record

* Workflow ID: `issue-183-20260808`
* Workflow version: `issue-183-v1.0.0`
* Authoring branch: `feature/workflow-issue-183-lxc-runtime-solid-20260808`
* Implementation branch: `feature/split-lxc-swarm-runtime-solid` (issue-requested; verify at execution)
* Requirement matrix: `.tiny-swarm/evidence/solid-lxc-swarm-runtime/requirement_matrix.md`
* Three-Amigos note: `.tiny-swarm/evidence/solid-lxc-swarm-runtime/three-amigos.md`
* Live E2E evidence target: `.tiny-swarm-world/evidence/solid-lxc-swarm-runtime/e2e/`
* External gate: SonarQube actual result required; no result claimed during authoring.
* Publication: guarded commit and push of workflow branch only; PR merge and cleanup are out of scope.
