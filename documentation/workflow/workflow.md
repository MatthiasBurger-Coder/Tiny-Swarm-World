# Workflow: Service Access Dashboard HTML Deployment Asset Synchronization

Version: `workflow-service-access-dashboard-html-v1.0.0`
Workflow ID: `workflow-service-access-dashboard-html-20260629`
Created: `2026-06-29`
Issue: `local-high-service-access-dashboard-html-deployment-sync`
Branch: `fix/workflow-service-access-dashboard-html-20260629`
Status: `READY_FOR_WORKFLOW_EXECUTE_LOCAL_ONLY_REMOTE_PUBLICATION_BLOCKED`
Evidence Root: `.codex/evidence/workflow-service-access-dashboard-html-20260629/`

## Executive Summary

Fix the high-priority deployment gap where
`ComposeFileRepositoryYaml.render_service_access_dashboard()` generates the
Service Access dashboard HTML, but the rendered service-access compose file
expects Docker Swarm to read
`${TSW_REMOTE_STACK_ROOT}/service-access/dashboard/index.html` during stack
deployment.

The workflow makes that generated HTML an explicit deployment asset. Before the
service-access stack is deployed, the same freshly rendered dashboard content
must be written to the configured remote stack root path. Static repository
dashboard files may remain packaging or review assets, but they must not be
the hidden source of truth for live deployment.

Default verification is static and mocked. This workflow must not run Incus,
LXC, Docker Swarm, Portainer, stack deployment, `socat`, or service bootstrap
commands without a later explicit live-infrastructure request.

## Requirement Clarification Gate

Original Request:

- "Hoch"
- Dashboard HTML is still not visibly written as a deployment file.
- `render_service_access_dashboard()` generates HTML.
- The Compose renderer expects
  `${TSW_REMOTE_STACK_ROOT}/service-access/dashboard/index.html`.
- A clear step is missing that writes or synchronizes the generated HTML to
  exactly that path before deployment.
- The user referenced `.tiny-swarm/secrets/generated.local.env` context.

Interpreted Intent:

- Create a guarded workflow that makes Service Access dashboard HTML
  generation and remote deployment-file synchronization an explicit,
  test-backed deployment behavior.

Change Type:

- Deployment asset synchronization, infrastructure adapter behavior,
  composition sequencing, tests and documentation synchronization.

Affected Process Strand:

- `workflow create`; later `workflow execute`.

Affected Architecture Area:

- Infrastructure compose rendering, LXC Swarm stack asset transfer,
  deployment workflow pre-apply sequencing, Service Access deployment
  documentation and static tests.

Explicit Requirements:

- Generate Service Access dashboard HTML from the effective access model.
- Write or synchronize the generated HTML to
  `${TSW_REMOTE_STACK_ROOT}/service-access/dashboard/index.html` before the
  service-access stack deployment consumes the compose config.
- Keep the rendered compose config file path and the remote asset transfer
  path aligned for the configured `remote_stack_root`.
- Make the deployment write step visible in implementation and tests.
- Preserve mocked/static verification by default.

Implicit Requirements:

- Preserve Linux/WSL-only behavior and POSIX paths.
- Preserve Docker Swarm-first and managed LXC through Incus direction.
- Preserve hexagonal boundaries: domain stays independent; infrastructure owns
  file transfer, shell commands and compose/YAML details.
- Do not read, parse, copy or commit `.tiny-swarm/secrets/generated.local.env`.
- Do not expose password values in dashboard HTML, logs, tests or evidence.
- Keep Portainer, Nexus, Jenkins, Pulsar, SonarQube, Swagger and Infisical
  live operations behind explicit consent.
- Update tests because deployment asset behavior changes.

Assumptions:

- The current compose renderer already points the Swarm config to
  `${TSW_REMOTE_STACK_ROOT:-/var/lib/tiny-swarm-world/stacks}/service-access/dashboard/index.html`.
- `LxcSwarmRuntime` is the currently relevant provider-native path for writing
  files under the remote stack root before `docker stack deploy`.
- The existing committed dashboard file can remain a static packaging/review
  asset if runtime deployment uses freshly rendered content.
- The referenced `generated.local.env` file is secret/local state and is not
  needed for workflow authoring.

Non-Goals:

- No live infrastructure execution.
- No Incus daemon, LXC profile, Docker, Swarm, Portainer, service or network
  mutation.
- No React frontend implementation.
- No new Java, Maven or Spring surface.
- No Kubernetes-first behavior.
- No redesign of Service Access links, Traefik routing or Infisical credential
  ownership beyond the dashboard deployment-file synchronization.
- No committed secret recovery file or generated local evidence.

Risks:

- The static `infra/config/compose/service-access/dashboard/index.html` file
  can mask a missing runtime synchronization step when it happens to match the
  generated renderer output.
- A test that only compares the committed static file to the renderer would
  not catch deployment drift.
- Adding file-transfer behavior in the wrong layer could couple application
  services to infrastructure details.
- Documentation may already describe the dashboard as rendered; execution must
  distinguish committed static assets from the generated deployment file.

Open Questions:

- None blocking. If execution discovers that a Portainer-managed path consumes
  the same `${TSW_REMOTE_STACK_ROOT}` config file without an asset-preparation
  seam, Slice 03 must extend the same synchronization contract there or report
  the missing adapter boundary as a blocker.

Blocking Questions:

- None.

Confidence Level:

- 94 percent.

Decision:

- `READY_FOR_WORKFLOW`

## Five-Role Review

Senior Requirement Engineer:

- The requirement is narrow and behavior-oriented: generated dashboard HTML
  must be materialized at the deployment file path before stack deployment.
  The selected local secret file is not requirement input and must remain
  unread.

Senior System Architect:

- This belongs to infrastructure adapters and deployment composition. Domain
  may continue to model the effective access data only. Application services
  must not gain shell, remote filesystem or Docker implementation details.

Senior Python Automation Developer:

- Prefer an injected or explicitly wired dashboard asset renderer over hidden
  global lookups. The LXC manager transfer should use the existing quoted
  remote path and `input_text` flow.

Senior React Frontend Developer:

- No React frontend exists. The affected user-facing surface is a generated
  static HTML deployment asset only.

Senior Tester:

- The regression must fail against stale static files. Use a temporary
  project path with a deliberately stale dashboard asset and assert that the
  remote transfer receives freshly rendered HTML.

## Requirement Matrix

| ID | Requirement | Type | Likely files | Implementation evidence | Verification evidence | Status |
|----|-------------|------|--------------|-------------------------|-----------------------|--------|
| REQ-001 | Service Access dashboard deployment content is generated from `render_service_access_dashboard()` or the same effective access model renderer. | Functional | `compose_file_repository_yaml.py`, `lxc_swarm_runtime.py` | Renderer or injected asset provider wired into stack asset transfer. | Unit test compares transferred `input_text` to generated dashboard HTML. | Planned |
| REQ-002 | Generated HTML is written to `${TSW_REMOTE_STACK_ROOT}/service-access/dashboard/index.html` before service-access stack deployment consumes the compose config. | Functional | `lxc_swarm_runtime.py`, `composition.py` | Asset transfer runs before `docker stack deploy` and uses configured `remote_stack_root`. | Unit test verifies call order and exact remote path. | Planned |
| REQ-003 | Static committed dashboard HTML is not the hidden deployment source of truth. | Regression | `tests/infrastructure/adapters/clients/test_lxc_swarm_runtime.py` | Runtime transfer uses generated content even when a temporary static file is stale. | Regression fixture with stale static file. | Planned |
| REQ-004 | The service-access deployment workflow makes the asset preparation step visible. | Process | `composition.py`, `composition_lxc_runtimes.py`, tests | Service-access stack asset pre-apply or deploy-time preparation is explicit and named. | Composition test checks `deployment:service-access-stack-assets` where applicable. | Planned |
| REQ-005 | No secret file or password value is read, written, logged or committed for this synchronization. | Security | tests, docs, runtime adapter | No dependency on `.tiny-swarm/secrets/generated.local.env`; dashboard remains password-value free. | Static tests and diff review. | Planned |
| REQ-006 | Documentation describes the generated remote deployment asset and keeps live verification separate. | Documentation | `documentation/arc42/**`, `documentation/system/**`, `documentation/user_guide/**` | Documentation update, if execution changes documented behavior. | `git diff --check`; review of doc wording. | Planned |

## Target Picture

Verified baseline:

- Active branch is `fix/workflow-service-access-dashboard-html-20260629`.
- `ComposeFileRepositoryYaml.get_compose_of("service-access")` injects a
  config file path under
  `${TSW_REMOTE_STACK_ROOT:-/var/lib/tiny-swarm-world/stacks}/service-access/dashboard/index.html`
  and a SHA-256 environment marker derived from generated dashboard HTML.
- `ComposeFileRepositoryYaml.render_service_access_dashboard()` returns the
  generated dashboard HTML from the effective access model.
- `LxcSwarmRuntime._transfer_stack_assets("service-access", ...)` currently
  reads `infra/config/compose/service-access/dashboard/index.html`, which can
  hide stale deployment content.
- `build_lxc_deployment_services(...).workflows.apply.pre_apply_steps`
  currently prepares `traefik` and `swagger` assets explicitly, but not
  `service-access`.

Target outcome:

- The generated Service Access dashboard HTML is the deployment source for
  `${TSW_REMOTE_STACK_ROOT}/service-access/dashboard/index.html`.
- The remote file is written before `docker stack deploy` for the
  service-access stack.
- The compose config path, configured `remote_stack_root`, deployment
  environment `TSW_REMOTE_STACK_ROOT`, and transfer target path are aligned.
- Tests prove the runtime does not silently use a stale static dashboard file.
- The deployment workflow exposes service-access asset preparation clearly.
- Documentation distinguishes generated remote deployment assets from
  committed static/package assets and from live verification evidence.

## Scope

In scope:

- `src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py`
- `src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py`
- `src/tiny_swarm_world/infrastructure/composition.py`
- `src/tiny_swarm_world/infrastructure/composition_lxc_runtimes.py`
- `tests/infrastructure/adapters/clients/test_lxc_swarm_runtime.py`
- `tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py`
- `tests/infrastructure/test_composition.py`
- `tests/application/services/deployment/test_deployment_workflows.py`
- `documentation/arc42/07_deployment/system.adoc`
- `documentation/arc42/07_deployment_view.adoc`
- `documentation/arc42/08_configuration/config-contract-inventory.md`
- `documentation/system/live-operation-surfaces.adoc`
- `documentation/user_guide/installation.adoc`
- `documentation/user_guide/usage.adoc`
- `documentation/workflow/**`
- `.codex/evidence/workflow-service-access-dashboard-html-20260629/**`

Out of scope:

- Live provider execution and observed service readiness.
- Service route redesign.
- Infisical secret sync changes.
- Docker image build or registry publication changes, unless execution proves
  they are the only safe place to materialize the generated asset.
- Browser, Selenium or Playwright live checks.

Architecture constraints:

- Preserve hexagonal dependency direction.
- Domain modules must not import infrastructure adapters, YAML, command
  runners, Docker or filesystem code.
- Application services may depend on ports only.
- Infrastructure adapters own generated asset transfer, quoted remote paths,
  compose/YAML behavior and manager-shell calls.
- Standard wiring remains in `src/tiny_swarm_world/infrastructure/composition.py`.
- Constructors must not execute external commands or write deployment files.

## Python Automation Assessment

This is Python infrastructure automation. The implementation should be small:
add an explicit dashboard asset rendering seam, use it from LXC stack asset
transfer, and wire that seam in composition. Avoid broad deployment rewrites.

## Frontend Assessment

No browser frontend or React project exists. The dashboard is generated static
HTML served by the service-access stack. Keep HTML content credential-safe and
English-language.

## Test Strategy

Targeted checks during execution:

- `PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_lxc_swarm_runtime`
- `PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml`
- `PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition`
- `PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_deployment_workflows`
- `git diff --check`

Required final verification:

- `python3 tools/quality_gate.py quality`

All commands must run inside WSL/Linux. From this Windows host, wrap project
Python commands as:

```bash
wsl bash -lc 'cd /mnt/d/Projects/Tiny-Swarm-World_2 && <command>'
```

No live infrastructure command is part of the default verification.

## Resilience Requirements

- Dashboard generation and transfer are deterministic and rerunnable.
- The remote directory creation and file write are idempotent.
- The file write must use quoted POSIX paths and existing safe command input
  plumbing.
- If dashboard rendering fails, deployment must fail before `docker stack
  deploy` rather than deploying stale or missing content.
- Secret-like values must remain redacted from logs and evidence.

## Ordered Slices

### Slice 01 - Regression Contract For Generated Dashboard Deployment Asset

Purpose:

- Add failing deterministic tests that expose the missing generated-dashboard
  synchronization step without live infrastructure.

Prerequisites:

- Active branch is `fix/workflow-service-access-dashboard-html-20260629`.
- Working tree changes are task-scoped.

```yaml
slice_id: "01"
profile: "NORMAL_PATH"
owner: "Senior Tester"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Python Automation Developer"
affected_files:
  - "tests/infrastructure/adapters/clients/test_lxc_swarm_runtime.py"
  - "tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py"
  - "tests/infrastructure/test_composition.py"
  - ".codex/evidence/workflow-service-access-dashboard-html-20260629/slice-01-distribution.md"
  - ".codex/evidence/workflow-service-access-dashboard-html-20260629/slice-01-consolidation.md"
affected_modules:
  - "tiny_swarm_world.infrastructure.adapters.clients"
  - "tiny_swarm_world.infrastructure.adapters.repositories"
  - "tiny_swarm_world.infrastructure.composition"
affected_contracts:
  - "Service Access generated dashboard deployment asset"
  - "TSW_REMOTE_STACK_ROOT service-access dashboard path"
dependencies: []
parallel_group: "serial-dashboard-asset-sync"
file_locks:
  - "tests/infrastructure/adapters/clients/test_lxc_swarm_runtime.py"
  - "tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py"
  - "tests/infrastructure/test_composition.py"
contract_locks:
  - "Generated dashboard HTML must be written before deployment"
  - "Committed static dashboard file must not mask stale deployment content"
architecture_locks:
  - "Tests remain static and mocked"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_lxc_swarm_runtime"
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml"
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition"
  required: []
documentation:
  arc42: "Checked; no edit in Slice 01."
  adr: "Checked; no ADR edit expected."
stop_conditions:
  - "Stop if a regression test requires live Incus, LXC, Docker, Swarm or Portainer."
  - "Stop if the only possible assertion reads `.tiny-swarm/secrets/generated.local.env`."
  - "Stop if the expected asset source is ambiguous."
```

Done criteria:

- Tests fail against a stale static dashboard file and require the generated
  dashboard HTML to be transferred to the remote service-access dashboard
  path.
- Tests verify the target path includes the configured `remote_stack_root` and
  `/service-access/dashboard/index.html`.

### Slice 02 - Generated Dashboard Asset Transfer In LXC Swarm Runtime

Purpose:

- Implement the deployment asset synchronization so the LXC stack runtime
  writes freshly generated dashboard HTML before service-access stack deploy.

Prerequisites:

- Slice 01 tests exist and fail for the current behavior.

```yaml
slice_id: "02"
profile: "NORMAL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior System Architect"
  - "Senior Tester"
  - "Senior DevOps Engineer"
affected_files:
  - "src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py"
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "tests/infrastructure/adapters/clients/test_lxc_swarm_runtime.py"
  - "tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py"
  - ".codex/evidence/workflow-service-access-dashboard-html-20260629/slice-02-distribution.md"
  - ".codex/evidence/workflow-service-access-dashboard-html-20260629/slice-02-consolidation.md"
affected_modules:
  - "tiny_swarm_world.infrastructure.adapters.clients.lxc_swarm_runtime"
  - "tiny_swarm_world.infrastructure.adapters.repositories.compose_file_repository_yaml"
  - "tiny_swarm_world.infrastructure.composition"
affected_contracts:
  - "Generated Service Access dashboard asset"
  - "LXC remote stack root asset transfer"
dependencies:
  - "01"
parallel_group: "serial-dashboard-asset-sync"
file_locks:
  - "src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py"
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "tests/infrastructure/adapters/clients/test_lxc_swarm_runtime.py"
  - "tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py"
contract_locks:
  - "Remote dashboard file content equals rendered dashboard HTML"
  - "Remote dashboard file path matches compose config path semantics"
architecture_locks:
  - "No infrastructure dependency is introduced into domain or application services"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_lxc_swarm_runtime"
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml"
  required: []
documentation:
  arc42: "No documentation edit unless implementation changes the documented deployment contract."
  adr: "No ADR change expected; existing service-access ADR allows a tested asset-preparation boundary."
stop_conditions:
  - "Stop if generated dashboard content cannot be obtained without hidden global lookups or constructor side effects."
  - "Stop if the fix would deploy stale committed dashboard HTML."
  - "Stop if remote paths would become host-specific, Windows-specific or unquoted."
  - "Stop if password values could be rendered, logged or persisted."
```

Done criteria:

- `prepare_stack_assets("service-access")` writes generated dashboard HTML to
  `<remote_stack_root>/service-access/dashboard/index.html`.
- `deploy_stack(StackDefinition(name="service-access", ...))` writes the
  generated dashboard before invoking `docker stack deploy`.
- Existing Swagger and Traefik asset transfer behavior remains unchanged.

### Slice 03 - Deployment Composition Visibility And Pre-Apply Sequencing

Purpose:

- Make service-access dashboard asset preparation visible in deployment
  composition and guard it with tests.

Prerequisites:

- Slice 02 generated asset transfer exists.

```yaml
slice_id: "03"
profile: "NORMAL_PATH"
owner: "Senior DevOps Engineer"
secondary_reviewers:
  - "Senior Python Automation Developer"
  - "Senior Tester"
  - "Senior System Architect"
affected_files:
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "src/tiny_swarm_world/infrastructure/composition_lxc_runtimes.py"
  - "tests/infrastructure/test_composition.py"
  - "tests/application/services/deployment/test_deployment_workflows.py"
  - ".codex/evidence/workflow-service-access-dashboard-html-20260629/slice-03-distribution.md"
  - ".codex/evidence/workflow-service-access-dashboard-html-20260629/slice-03-consolidation.md"
affected_modules:
  - "tiny_swarm_world.infrastructure.composition"
  - "tiny_swarm_world.infrastructure.composition_lxc_runtimes"
  - "tiny_swarm_world.application.services.deployment.workflows"
affected_contracts:
  - "Deployment pre-apply stack asset preparation"
  - "Service Access setup profile deployment sequence"
dependencies:
  - "02"
parallel_group: "serial-dashboard-asset-sync"
file_locks:
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "src/tiny_swarm_world/infrastructure/composition_lxc_runtimes.py"
  - "tests/infrastructure/test_composition.py"
  - "tests/application/services/deployment/test_deployment_workflows.py"
contract_locks:
  - "Service-access dashboard asset preparation is explicit before stack apply"
  - "Default/static verification does not run live deployment commands"
architecture_locks:
  - "Composition remains the concrete wiring root"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition"
    - "PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_deployment_workflows"
  required: []
documentation:
  arc42: "Check deployment docs for wording drift after composition changes."
  adr: "No ADR change expected."
stop_conditions:
  - "Stop if adding service-access pre-apply would duplicate unsafe live writes in a default non-live gate."
  - "Stop if service-access asset preparation order relative to Infisical readiness becomes ambiguous."
  - "Stop if Portainer-managed deployment path is found to consume the same remote file without a tested preparation seam."
```

Done criteria:

- The service-access setup profile exposes a named
  `deployment:service-access-stack-assets` preparation step where the
  deployment workflow requires it, or execution documents why deploy-time
  preparation alone is the verified single source of truth.
- Tests verify the step order and that no pre-apply step runs outside an
  explicitly invoked live deployment workflow.

### Slice 04 - Documentation, Evidence And Quality Gate

Purpose:

- Synchronize documentation and complete verification evidence for the
  dashboard deployment asset fix.

Prerequisites:

- Slices 01 through 03 completed.

```yaml
slice_id: "04"
profile: "NORMAL_PATH"
owner: "Senior Documentation Engineer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior Tester"
  - "Senior System Architect"
affected_files:
  - "documentation/arc42/07_deployment/system.adoc"
  - "documentation/arc42/07_deployment_view.adoc"
  - "documentation/arc42/08_configuration/config-contract-inventory.md"
  - "documentation/system/live-operation-surfaces.adoc"
  - "documentation/user_guide/installation.adoc"
  - "documentation/user_guide/usage.adoc"
  - "documentation/workflow/workflow.md"
  - "documentation/workflow/context-pack.md"
  - "documentation/workflow/context-pack.json"
  - ".codex/evidence/workflow-service-access-dashboard-html-20260629/slice-04-distribution.md"
  - ".codex/evidence/workflow-service-access-dashboard-html-20260629/slice-04-consolidation.md"
affected_modules:
  - "documentation"
  - "documentation.workflow"
affected_contracts:
  - "Generated Service Access dashboard deployment asset documentation"
  - "Issue completion evidence package"
dependencies:
  - "03"
parallel_group: "serial-dashboard-asset-sync"
file_locks:
  - "documentation/arc42/**"
  - "documentation/system/live-operation-surfaces.adoc"
  - "documentation/user_guide/**"
  - "documentation/workflow/**"
  - ".codex/evidence/workflow-service-access-dashboard-html-20260629/**"
contract_locks:
  - "Documentation must not claim live Service Access reachability without live evidence"
architecture_locks:
  - "ADR history remains intact"
quality_gates:
  targeted:
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "Update if implemented behavior changes the deployment asset contract."
  adr: "No ADR edit expected unless execution discovers an asset-boundary decision gap."
stop_conditions:
  - "Stop if documentation would describe planned behavior as implemented behavior."
  - "Stop if full quality gate cannot be run or failures cannot be classified."
  - "Stop if issue-completion evidence is missing or inconsistent."
```

Done criteria:

- Documentation states that generated dashboard HTML is synchronized to the
  remote service-access dashboard config file before stack deployment.
- Evidence files exist for requirements, implementation, changed files, test
  results, risks and acceptance checklist.
- `git diff --check` and `python3 tools/quality_gate.py quality` pass, or any
  failure is classified with exact blockers.

## Slice Dependency Graph

```text
01 Regression Contract For Generated Dashboard Deployment Asset
  -> 02 Generated Dashboard Asset Transfer In LXC Swarm Runtime
    -> 03 Deployment Composition Visibility And Pre-Apply Sequencing
      -> 04 Documentation, Evidence And Quality Gate
```

## Parallel Execution

- Can this workflow run in parallel? No write-capable parallel execution.
- Conflicting workflows: any workflow touching Service Access dashboard
  rendering, service-access compose configs, LXC stack asset transfer,
  deployment composition, setup/deployment apply ordering, or deployment docs.
- Shared files: `lxc_swarm_runtime.py`, `compose_file_repository_yaml.py`,
  `composition.py`, `tests/infrastructure/test_composition.py`,
  Service Access deployment docs and `documentation/workflow/**`.
- Shared infrastructure: Docker Swarm, LXC, Portainer and remote stack root;
  no shared live infrastructure is used by default.
- Requires isolated worktree: yes for any concurrent execution.
- Requires serialized live validation: yes; live validation is out of scope
  unless explicitly requested later.
- Merge-order constraints: execute slices in order 01 through 04.

## Automatic Work Distribution Policy

`workflow execute` must automatically inspect each slice for safe specialist
stream decomposition. Real Codex subagents may be used where supported. If
subagents are unavailable, execute the same checks through explicit role-based
fallback in the main thread and record that fallback in evidence.

Required evidence before implementation:

- `.codex/evidence/workflow-service-access-dashboard-html-20260629/slice-<number>-distribution.md`

Required evidence after implemented slices:

- `.codex/evidence/workflow-service-access-dashboard-html-20260629/slice-<number>-consolidation.md`

Stream map:

- Backend/Python: Slices 01, 02 and 03.
- Frontend/React: not applicable.
- Console/status UI: not affected.
- Tests: all slices, led by Slice 01.
- Runtime/DevOps: Slices 02 and 03.
- Documentation: Slice 04.
- Quality: Slice 04.
- Architecture: all slices.
- Security: secret-file avoidance and password-value redaction.

Non-parallelization rules:

- Do not parallelize overlapping file edits.
- Do not parallelize unclear architecture ownership.
- Do not parallelize contradictory requirements.
- Do not parallelize mandatory ordered test-then-implementation work.
- Do not parallelize generated-file conflict resolution.
- Do not parallelize if Three Amigos marks the slice not safely
  parallelizable.
- Do not proceed with unclear secrets handling or weakened safety guards.

Codex remains the final integration owner for consolidation, tests, evidence,
PR readiness and merge readiness.

## Git Worktree Execution Rule

Execute this workflow only from branch
`fix/workflow-service-access-dashboard-html-20260629` or from an isolated
worktree branch explicitly derived for this workflow. Subagents or stream
workers must verify the active branch before writing files and must not merge
directly. Codex consolidates accepted changes after evidence and tests pass.

## Role Ownership Map

- Senior Workflow Architect: workflow structure, dependencies and execution
  policy.
- Senior Requirement Engineer: requirement matrix and drift checks.
- Senior System Architect: hexagonal boundaries and deployment boundary fit.
- Senior Python Automation Developer: generated asset rendering and runtime
  transfer implementation.
- Senior DevOps Engineer: stack asset preparation order and deployment safety.
- Senior Documentation Engineer: arc42, user-guide and workflow sync.
- Senior Tester: regression tests, targeted checks and quality evidence.
- Senior React Frontend Developer: N/A impact check; no React module exists.

## Issue Completion Discipline

- Requirement matrix path:
  `.tiny-swarm/evidence/workflow-service-access-dashboard-html-20260629/requirement_matrix.md`
- Required evidence path:
  `.tiny-swarm/evidence/workflow-service-access-dashboard-html-20260629/`
- Required evidence files:
  `requirement_matrix.md`, `implementation_summary.md`, `changed_files.md`,
  `test_results.md`, `remaining_risks.md`, `acceptance_checklist.md`
- Requirement Lead review: Senior Requirement Engineer must confirm REQ-001
  through REQ-006 are captured and mapped.
- System Architect Reviewer review: Senior System Architect must confirm the
  solution keeps file transfer and command execution in infrastructure.
- Test / Evidence Reviewer review: Senior Tester must confirm every
  requirement has test or static evidence.
- Issue Completion Auditor review: required before final `DONE`.
- DONE blocking rule: any open or unverified requirement forces `INCOMPLETE`,
  `BLOCKED` or `FAILED`; the implementer cannot mark the issue done alone.

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

The full gate is required for final readiness because the workflow changes
Python infrastructure adapter behavior, deployment composition, tests and
documentation.

## Documentation Synchronization Points

- Update deployment docs if execution changes the documented Service Access
  asset contract.
- Keep ADR history intact. If execution discovers that an ADR is needed for a
  new asset-preparation boundary, stop and escalate rather than silently
  updating the ADR.
- Do not claim live dashboard reachability or service readiness without an
  explicit live run and redacted evidence.
- Keep paths POSIX-style in examples and documentation.

## Stop Conditions

Stop and report if:

- Git repository context or active branch cannot be verified.
- Unrelated uncommitted changes appear.
- Generated dashboard HTML cannot be obtained without reading local secret
  files or adding constructor side effects.
- The implementation would keep stale committed dashboard HTML as the
  deployment source of truth.
- Remote file paths become host-specific, Windows-specific or unquoted.
- Any fix requires live Incus, LXC, Docker, Swarm, Portainer or service
  mutation without explicit approval.
- Password values, tokens, private keys, local IP addresses or host-specific
  paths would be committed, logged or added to evidence.
- Documentation would claim live success without live evidence.
- A quality failure cannot be safely classified.

## Uncertainty Escalation Rules

- Route asset-boundary ambiguity to Senior System Architect and ADR Steward.
- Route deployment-order ambiguity to Senior DevOps.
- Route secret or evidence leakage risk to security review.
- Route failing or flaky tests to Senior Tester and Typed Error Router before
  retries.

## Commit And Push Plan

- Workflow creation publication is authorized as a guarded branch commit and
  push to `origin/fix/workflow-service-access-dashboard-html-20260629`.
- Stage only `documentation/workflow/**` for workflow creation unless a
  directly required governance file is changed.
- Do not create, merge or clean up a pull request during workflow creation.
- Do not force-push and do not push to `main`.
- If remote SSH access is unavailable, keep the local workflow commit and
  report publication blocked with the exact Git error.

## Definition Of Done

- Workflow branch exists and is active.
- `documentation/workflow/workflow.md`,
  `documentation/workflow/context-pack.md`, and
  `documentation/workflow/context-pack.json` describe this workflow.
- Slices contain machine-readable metadata.
- Requirement matrix maps REQ-001 through REQ-006 to implementation and
  verification evidence.
- Service Access generated dashboard HTML is written to the remote stack root
  dashboard path before service-access stack deployment.
- Tests prove stale static dashboard files do not become the deployment source
  of truth.
- Documentation distinguishes generated deployment asset behavior from live
  reachability evidence.
- Full quality gate passes after implementation, or blockers are reported.

## Handoff To Workflow Execute

Run `workflow execute` only after confirming:

- active branch:
  `fix/workflow-service-access-dashboard-html-20260629`
- current workflow status:
  `READY_FOR_WORKFLOW_EXECUTE_LOCAL_ONLY_REMOTE_PUBLICATION_BLOCKED`
- context pack hashes are current
- no unrelated working-tree changes exist
- no live infrastructure commands are run without explicit operator consent
- Slice 01 starts with regression tests before implementation

## arc42 Check Status

- `documentation/arc42/07_deployment/system.adoc` checked because it documents
  Service Access deployment assets and warns against relying on bind-mounted
  repository files without a tested asset-preparation boundary.
- `documentation/arc42/07_deployment_view.adoc` checked because it documents
  Service Access and Traefik deployment direction.
- `documentation/arc42/09_decisions/adr-service-access-dashboard-vaultwarden.adoc`
  checked because it authorizes Service Access dashboard assets and requires a
  tested asset-preparation boundary before relying on repository files.
- No ADR update is required during workflow authoring.
