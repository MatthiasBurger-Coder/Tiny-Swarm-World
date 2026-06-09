# Workflow: Live Greenpath Repair Loop

```yaml
workflow_id: live-greenpath-repair-loop-20260606
workflow_version: 1.1.0
branch: feature/live-greenpath-repair-loop-20260606
execution_profile: FULL_PATH
released_for_workflow_execute: true
created_utc: "2026-06-07T15:06:57Z"
request: "Achieve one complete verified greenpath for ./install.sh on local WSL2 LXD/LXC-native Docker Swarm setup, including a new tests/live suite that verifies browser routes and Infisical credential coverage for all credential-requiring services."
decision: READY_FOR_WORKFLOW
confidence: 92
```

## Executive Summary

This workflow executes a controlled live repair loop for the LXC-native Docker
Swarm greenpath. The loop runs `./install.sh`, stores evidence under
`.tiny-swarm-world/evidence`, parses the latest setup evidence, classifies the
first blocker precisely, applies only the current blocker fix, adds or updates
automated tests, runs targeted verification, commits the blocker fix, and
repeats until the final setup status is `completed` or `passed`.

The workflow also creates a new opt-in `tests/live` suite. That suite must
verify post-install browser-facing routes and verify that Infisical contains
credential entries for every service in the selected profile that requires
operator credentials. The test must never log, persist, screenshot, or expose
password values; it verifies item presence and service mapping only.

Live LXD/LXC and Docker Swarm mutation is explicitly authorized by the user
for this workflow only. Safety guards, validations, consent gates, secret
handling, and environment guards must not be bypassed or weakened.

## Requirement Clarification Gate

Original request:

- Create branch `feature/live-greenpath-repair-loop-20260606`.
- Run the full live fresh install.
- Store all evidence under `.tiny-swarm-world/evidence`.
- Parse latest evidence automatically, detect and classify the first blocker,
  fix only that blocker, test it, rerun install, and repeat.
- Stop after 10 iterations, repeated blocker after a fix, manual secrets or
  unknown destructive host changes, weakened safety, or ambiguous LXD/Docker
  host state.
- Implement provider resource resolution for `lxc_native` and precise blocker
  evidence/classifications.
- Add a live post-install browser/path test.
- Additionally verify that Infisical contains all credentials for the
  service set.
- Commit each blocker fix as one separate commit.

User clarification:

- The browser/path and Infisical credential check belongs in a new
  `tests/live` suite.

Interpreted intent:

- Repair the Python automation and LXC-native provider mapping until one local
  WSL2 LXD/LXC-native Docker Swarm setup greenpath completes.
- Keep implementation Python-based and idempotent.
- Treat `vms[].name` as LXD instance names only while resolving reusable
  profile, physical network, and storage pool independently.
- Add opt-in live checks under `tests/live`, not under the existing
  `tests/integration` package.
- Verify Infisical credential inventory coverage for service credentials,
  while keeping password values only in Infisical's authenticated UI.

Change type:

- Python automation behavior change.
- Infrastructure adapter and provider configuration resolution change.
- Evidence classification and reporting change.
- Live platform verification workflow.
- New live test suite and browser-facing verification surface.
- Credential coverage verification with secret-redaction constraints.

Affected process strand:

- `./install.sh` governed fresh-install wrapper, preflight, platform init,
  swarm bootstrap/join, stack deployment, port exposure, browser route
  verification, Infisical credential inventory verification, and final
  verification.

Affected architecture area:

- `src/tiny_swarm_world/domain` only for provider value objects or credential
  inventory value objects if needed.
- `src/tiny_swarm_world/application` for orchestration, ports, and
  verification services if needed.
- `src/tiny_swarm_world/infrastructure` for LXC/LXD command adapters, evidence
  parsing, provider resource resolution, Infisical/browser adapters, and
  composition wiring.
- `infra/config` for explicit provider defaults or service credential mapping
  configuration if needed.
- `tests` for deterministic unit coverage and the new opt-in `tests/live`
  suite.
- `documentation/workflow` and final report.

Explicit requirements:

- Do not bypass safety guards.
- Do not disable validations to make the run green.
- Do not hardcode temporary local hacks unless represented as provider
  configuration or documented local defaults.
- Do not use Ansible.
- Keep implementation Python-based.
- Add `lxc_native` provider resource resolution.
- Resolve profile, network, and storage independently.
- Add dry-run provider resolution verification before platform mutation.
- Add precise blocked classifications and evidence fields.
- Make remediations idempotent.
- Create `tests/live/test_post_install_browser_live.py` for opt-in live
  browser/path verification.
- Use the repository's current `unittest` style for the new live suite unless
  a later explicit tooling change adds `pytest`.
- Write browser/path evidence to
  `.tiny-swarm-world/evidence/post_install_browser_live/`.
- Verify that Infisical contains credential entries for all
  credential-requiring services in the selected service profile.
- Do not require interactive manual credentials during the live test. The test
  may read the ignored live installation environment or explicit environment
  variables produced/supplied for the run.
- Do not log or persist secret values, token values, raw environment payloads,
  credential-bearing URLs, local IP addresses, or screenshots containing
  revealed secrets.

Implicit requirements:

- Preserve hexagonal architecture.
- Keep live host mutation inside explicit install/setup execution.
- Keep committed evidence free of secrets and host-specific sensitive payloads.
- Use mocked tests for command execution and LXD/Docker operations.
- Treat `tests/integration/test_post_install_browser_live.py` as reference
  material only; the workflow output must use the new `tests/live` suite.
- Credential coverage must be derived from setup manifest/service-access
  catalog behavior rather than a duplicated hardcoded password list when
  practical.

Assumptions:

- The local WSL2 environment has LXD/LXC and Docker available enough to execute
  the requested live setup.
- Existing host resources `docker-swarm`, `lxdbr0`, and `default` may be used
  only after independent validation.
- Generated evidence under `.tiny-swarm-world/evidence` is local runtime
  evidence and should not be committed unless a redacted final report
  explicitly requires it.
- Infisical credential item names currently expected by the service-access
  dashboard are `platform/jenkins`, `platform/nexus`, `platform/portainer`,
  `platform/rabbitmq`, and `platform/sonarqube`; `service-access` and
  `swagger` are expected to be marked as no-login services.

Non-goals:

- No Ansible, Terraform, Kubernetes-first migration, Java, Maven, Spring Boot,
  or React frontend scope.
- No weakening of consent, safety, drift, secret, or environment guards.
- No destructive host cleanup beyond explicit fresh reset/install behavior
  already guarded by the project.
- No migration of the whole repository test strategy to `pytest`.
- No dashboard display of password values and no Infisical secret export.

Risks:

- Live setup may require long-running downloads, image pulls, or service
  health checks.
- Host LXD/Docker state may contain ambiguous resources that must stop the loop
  rather than guessing.
- Stack readiness may expose additional blockers after provider mapping is
  fixed.
- Infisical browser automation can accidentally expose secrets through
  screenshots, traces, logs, or assertion messages if not explicitly redacted.
- A bootstrap cycle is possible if required setup credentials are expected to
  come from Infisical before Infisical itself is reachable.

Open questions:

- None blocking after the user selected a new `tests/live` suite.

Blocking questions:

- None.

Decision:

- `READY_FOR_WORKFLOW`.

## Three Amigos Review

Senior Requirement Engineer:

- Requirement is ready. The target outcome is a complete live greenpath plus
  explicit service-access/browser and Infisical credential coverage.
- Acceptance criteria are testable when credential item names and no-login
  services are derived from configuration or documented local defaults.

Senior System Architect:

- `FULL_PATH` is required because the workflow affects live deployment,
  provider resolution, credential verification, evidence semantics, and test
  structure.
- The service-access and Infisical baseline is already accepted in
  `documentation/architecture/adr-service-access-dashboard-infisical.adoc`.
  The workflow must preserve the rule that Infisical is the only approved
  password reveal/copy surface.

Senior Python Automation Developer:

- Provider resolution and evidence parsing should stay in domain/application
  contracts with infrastructure adapters for LXD/LXC, Docker, HTTP, and
  Infisical/browser details.
- Application services must not embed low-level shell, HTTP, or browser
  automation details directly.

Senior React Frontend Developer:

- No React frontend work is authorized. Browser checks target deployed service
  surfaces and static service-access assets only.
- The new `tests/live` suite must not introduce React, TypeScript, Vite,
  TSX/JSX, or package-manager lockfiles.

Senior Tester:

- Default quality gates remain static or mocked.
- New live tests must be skipped unless explicitly enabled and must write
  redacted evidence.
- Credential coverage verification must assert item presence and expected
  service mapping, not password values.

Dependency / Deadlock Validator:

- Slices remain sequential because provider setup, deployment readiness,
  browser routes, Infisical access, and final reporting share live state and
  evidence.
- No parallel write scopes are safe for the live repair loop.

Mandatory EPIC question:

- Does the implementation still match the EPIC? Yes, with live evidence still
  required. This workflow is the controlled live-evidence path for the
  autonomous runnable setup and service-access/Infisical EPIC extensions.

## Target Picture

A fresh reset followed by `./install.sh` completes with final setup status
`completed` or `passed`. LXD instances `swarm-manager`, `swarm-worker-1`, and
`swarm-worker-2` exist and are running. Docker Swarm reports one manager and
two workers. Expected stacks `portainer`, `nexus`, `jenkins`, `rabbitmq`,
`sonarqube`, `swagger`, `infisical`, and `service-access` are deployed.

Applicable published service ports and central service-access routes are
reachable from the host. The new `tests/live/test_post_install_browser_live.py`
suite passes with live tests explicitly enabled. Infisical contains
credential entries for all credential-requiring services and the live evidence
records only redacted item-presence status. Final evidence and a final report
document the greenpath.

## Verified Baseline

- Branch: `feature/live-greenpath-repair-loop-20260606`.
- Branch ref verified locally on 2026-06-07.
- Current observed blocker from user report: `profile_missing` at
  `platform:node:swarm-manager`.
- Desired inventory contains `swarm-manager`, `swarm-worker-1`, and
  `swarm-worker-2` as VM names.
- Local LXD state reportedly includes profile `docker-swarm`, network
  `lxdbr0`, and storage pool `default`.
- Existing post-install browser checks are under
  `tests/integration/test_post_install_browser_live.py`; the requested target
  is a new `tests/live` suite.
- Existing service-access dashboard references Infisical entries for
  Jenkins, Nexus, Portainer, RabbitMQ, and SonarQube.
- Existing arc42 and ADR sources require password values to remain visible
  only through Infisical's authenticated UI.

## Scope

In scope:

- Live greenpath repair for `./install.sh`.
- LXC-native provider resource resolution.
- Blocker classification and redacted evidence.
- New opt-in `tests/live` suite.
- Browser-facing path verification for expected services.
- Infisical credential inventory verification for all credential-requiring
  selected-profile services.
- Final report with blockers, fixes, commit SHAs, and verification evidence.

Out of scope:

- Kubernetes-first deployment.
- Ansible or Terraform.
- Java, Maven, Spring Boot, React, TypeScript, Vite, TSX/JSX.
- Public TLS/certificate automation.
- Displaying, exporting, logging, or snapshotting password values outside
  Infisical.
- Committing live evidence or ignored local secret files.

## Architecture Constraints

- Preserve hexagonal architecture.
- Domain may model provider resources, service credential references, and
  redacted verification results.
- Application may orchestrate provider, deployment, browser, and Infisical
  ports.
- Infrastructure owns LXC/LXD commands, Docker/Swarm commands, YAML parsing,
  HTTP clients, browser automation, Infisical API or UI details, and file
  evidence writing.
- `src/tiny_swarm_world/infrastructure/composition.py` remains the standard
  wiring root.
- Entry points remain thin.
- Live infrastructure commands are allowed only inside this explicitly
  requested live workflow and must keep consent/safety guards intact.

## Python Automation Assessment

Provider resource resolution should be implemented as a small contract that
accepts logical inventory/provider configuration and returns independently
validated instance, profile, network, and storage decisions. It should produce
dry-run evidence before mutation and fail closed when a resource is missing or
ambiguous.

Infisical credential coverage should be implemented with a redacted
verification model. The verifier may authenticate to Infisical with
operator-supplied ignored local environment values, but evidence must record
only service name, expected item reference, observed presence, result, and a
redacted failure reason.

## Frontend Assessment

No repository frontend is created. Browser checks may use Playwright as an
operator-installed live-test dependency, but the project remains a Python
automation repository. The service-access dashboard remains static
infrastructure content packaged into service images.

## Test Strategy

Default and targeted unit tests:

- Use `unittest` and repository quality gates.
- Mock LXD/LXC, Docker, Swarm, Portainer, Infisical, browser, and network
  calls unless a test is explicitly marked as live.
- Cover provider resolution, blocker classification, evidence redaction, and
  credential inventory mapping without live infrastructure.

New live suite:

- Create `tests/live/test_post_install_browser_live.py`.
- Use an explicit guard such as
  `TSW_RUN_POST_INSTALL_BROWSER_LIVE=1` or a documented equivalent live flag.
- Do not run under `python3 tools/quality_gate.py quality` unless explicitly
  enabled by the operator.
- Resolve service endpoints from setup evidence/configuration when available,
  with documented local defaults only as fallback.
- Write redacted JSON evidence to
  `.tiny-swarm-world/evidence/post_install_browser_live/`.
- Fail when a required browser-facing service is unreachable, a published port
  is missing, an endpoint mapping contradicts setup evidence, a service returns
  only an infrastructure error page, or Infisical credential entries are
  missing.

Live test command:

```bash
TSW_RUN_POST_INSTALL_BROWSER_LIVE=1 PYTHONPATH=src python3 -m unittest tests.live.test_post_install_browser_live
```

Repository quality commands:

```bash
git diff --check
python3 tools/quality_gate.py test
python3 tools/quality_gate.py quality
```

## Resilience Requirements

- Repair loop max: 10 iterations.
- Stop if the same blocker appears twice after a fix.
- Stop if a blocker requires manual secrets or unknown destructive host
  changes.
- Stop if a repair would weaken safety, consent, secret, or environment
  guards.
- Stop if LXD/Docker host state is ambiguous and cannot be reconciled safely.
- Stop if Infisical credential coverage would require exposing password
  values outside Infisical's authenticated UI.

## Ordered Slices

### Slice 01: Workflow And Evidence Harness

```yaml
slice_id: S01
profile: FULL_PATH
owner: Senior Workflow Architect
secondary_reviewers: [Senior Tester, Senior DevOps Engineer]
affected_files: [documentation/workflow/**]
affected_modules: [workflow]
affected_contracts: []
dependencies: []
parallel_group: sequential
file_locks: [documentation/workflow]
contract_locks: []
architecture_locks: []
quality_gates:
  targeted: [git diff --check]
  required: [git diff --check]
documentation:
  arc42: checked-no-product-architecture-change
  adr: checked-service-access-infisical-baseline
stop_conditions: [branch_mismatch, dirty_unrelated_worktree]
```

Done criteria:

- Active workflow targets the requested branch and live repair loop.
- New `tests/live` suite requirement and Infisical credential coverage are
  documented.
- Stop conditions and loop limits are documented.

### Slice 02: Provider Resolution Blocker Fix

```yaml
slice_id: S02
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior System Architect, Senior Tester, Senior DevOps Engineer]
affected_files: [src/tiny_swarm_world/**, infra/config/**, tests/**]
affected_modules: [domain, application, infrastructure, tests]
affected_contracts: [lxc_native_provider_resolution]
dependencies: [S01]
parallel_group: sequential
file_locks: [src/tiny_swarm_world, infra/config, tests]
contract_locks: [provider_config]
architecture_locks: [hexagonal]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest <relevant-tests>]
  required: [python3 tools/quality_gate.py test, git diff --check]
documentation:
  arc42: update-if-provider-contract-changes
  adr: not-required-unless-provider-contract-choice-is-irreversible
stop_conditions: [safety_guard_weakened, ambiguous_lxd_state, repeated_blocker]
```

Done criteria:

- First blocker is classified and fixed only for its cause.
- Automated tests cover the blocker.
- Fix is committed as one blocker-scoped commit.

### Slice 03: Live Iteration Loop

```yaml
slice_id: S03
profile: FULL_PATH
owner: Senior DevOps Engineer
secondary_reviewers: [Senior Python Automation Developer, Senior Tester]
affected_files: [.tiny-swarm-world/evidence/**, documentation/workflow/reports/**, src/tiny_swarm_world/**, infra/config/**, tests/**]
affected_modules: [runtime, infrastructure, tests]
affected_contracts: [install_greenpath]
dependencies: [S02]
parallel_group: sequential
file_locks: [.tiny-swarm-world/evidence, documentation/workflow/reports, src/tiny_swarm_world, infra/config, tests]
contract_locks: [install_greenpath]
architecture_locks: [hexagonal]
quality_gates:
  targeted: [./install.sh, PYTHONPATH=src python3 -m unittest <relevant-tests>]
  required: [python3 tools/quality_gate.py test, git diff --check]
documentation:
  arc42: update-if-runtime-contract-changes
  adr: not-required-unless-safety-policy-changes
stop_conditions: [max_10_iterations, same_blocker_twice_after_fix, manual_secret_required, unknown_destructive_host_change, safety_guard_weakened, ambiguous_lxd_or_docker_state]
```

Done criteria:

- Loop reaches final status `completed` or `passed`, or stops with a precise
  blocker report.
- Each blocker fix is committed separately.

### Slice 04: Live Browser And Infisical Credential Suite

```yaml
slice_id: S04
profile: FULL_PATH
owner: Senior Tester
secondary_reviewers: [Senior Python Automation Developer, Senior System Architect, Senior DevOps Engineer]
affected_files: [tests/live/**, src/tiny_swarm_world/**, documentation/workflow/**]
affected_modules: [tests, domain, application, infrastructure]
affected_contracts: [post_install_browser_live, infisical_credential_inventory]
dependencies: [S03]
parallel_group: sequential
file_locks: [tests/live, src/tiny_swarm_world, documentation/workflow]
contract_locks: [service_access_routes, infisical_credential_inventory]
architecture_locks: [hexagonal, secret_redaction]
quality_gates:
  targeted: [TSW_RUN_POST_INSTALL_BROWSER_LIVE=1 PYTHONPATH=src python3 -m unittest tests.live.test_post_install_browser_live]
  required: [python3 tools/quality_gate.py test, git diff --check]
documentation:
  arc42: checked-service-access-and-credential-display-safety
  adr: checked-service-access-infisical-baseline
stop_conditions: [manual_secret_prompt_required, password_value_logged, credential_value_persisted, infisical_bootstrap_cycle, browser_trace_contains_secret, service_mapping_contradicts_evidence]
```

Done criteria:

- `tests/live/test_post_install_browser_live.py` exists and is opt-in only.
- The suite verifies all expected published service entrypoints from
  configuration/evidence with documented local defaults only as fallback.
- The suite verifies browser-relevant HTTP responses, not merely open sockets.
- The suite verifies Infisical contains credential entries for all
  credential-requiring services in the selected profile.
- Expected credential entries are derived from setup/service-access
  configuration where practical and include at least:
  `platform/jenkins`, `platform/nexus`, `platform/portainer`,
  `platform/rabbitmq`, and `platform/sonarqube`.
- The suite records redacted evidence for each service and each expected
  Infisical item. Evidence may include service name, URL, status code,
  reachable flag, content type, expected item reference, item present flag,
  result, and redacted failure reason.
- The suite does not record password values, token values, Basic/Bearer
  headers, raw environment files, Playwright traces, screenshots with secrets,
  or credential-bearing URLs.
- Missing Infisical login material from the ignored live environment is a
  setup blocker, not an interactive prompt.

### Slice 05: Final Report

```yaml
slice_id: S05
profile: FULL_PATH
owner: Senior Documentation Engineer
secondary_reviewers: [Senior Tester, Senior DevOps Engineer]
affected_files: [documentation/workflow/reports/**]
affected_modules: [documentation]
affected_contracts: []
dependencies: [S04]
parallel_group: sequential
file_locks: [documentation/workflow/reports]
contract_locks: []
architecture_locks: []
quality_gates:
  targeted: [git diff --check]
  required: [git diff --check]
documentation:
  arc42: checked
  adr: checked
stop_conditions: [missing_evidence, unverified_success_claim, unredacted_secret_evidence]
```

Done criteria:

- Final report documents every blocker encountered, fix applied, verification
  command, commit SHA, final greenpath evidence location, browser/path result,
  and Infisical credential coverage result.
- Report distinguishes verified live facts from planned or skipped checks.

## Slice Dependency Graph

```text
S01 -> S02 -> S03 -> S04 -> S05
```

Parallelization opportunities:

- None. Live platform state, service deployment, browser checks, Infisical
  checks, and evidence reporting are sequential and share state.

## Role Ownership Map

- Senior Workflow Architect: workflow creation, dependency ordering, handoff.
- Senior Requirement Engineer: EPIC consistency, acceptance criteria,
  assumption tracking.
- Senior System Architect: hexagonal boundaries, service-access ADR/arc42
  alignment, planned-vs-verified claims.
- Senior Python Automation Developer: provider resolution, application
  contracts, infrastructure adapters.
- Senior React Frontend Developer: mandatory N/A impact check; prevents scope
  drift into React/frontend project work.
- Senior Tester: unit, live test, redaction, and acceptance coverage.
- Senior DevOps Engineer: live LXD/LXC, Docker Swarm, deployment, and
  post-install verification execution.
- Senior Documentation Engineer: final report and documentation sync.

## Loop Rules

- Maximum repair iterations: 10.
- Stop if the same blocker appears twice after a fix.
- Stop if a blocker requires manual secrets or unknown destructive host
  changes.
- Stop if a repair would weaken safety, consent, secret, or environment
  guards.
- Stop if LXD/Docker host state is ambiguous and cannot be reconciled safely.
- Stop if Infisical credential verification would expose password values.
- Do not bypass validations or convert failures into success.
- Do not use Ansible.

## Blocker Classifications

The implementation must support precise classification for:

- `inventory_mapping_missing`
- `profile_missing`
- `profile_invalid`
- `network_missing`
- `storage_pool_missing`
- `docker_runtime_not_ready`
- `swarm_bootstrap_failed`
- `swarm_join_failed`
- `port_expose_failed`
- `deployment_apply_failed`
- `deployment_verify_failed`
- `post_install_browser_route_failed`
- `infisical_credential_inventory_missing`

Evidence for provider blockers must include where applicable:

- `phase`
- `node_name`
- `expected_profile`
- `available_profiles`
- `logical_network`
- `resolved_network`
- `available_networks`
- `expected_storage_pool`
- `available_storage_pools`
- `remediation_hint`

Evidence for browser and Infisical blockers must include where applicable:

- `phase`
- `service`
- `url`
- `expected_route`
- `status_code`
- `reachable`
- `content_type`
- `expected_infisical_item`
- `item_present`
- `missing_items`
- `result`
- `failure_reason`
- `remediation_hint`

Browser and Infisical evidence must not include password values, token
values, raw environment payloads, request headers, credential-bearing URLs,
local IP addresses, or screenshots/traces containing secrets.

## Quality Gate Expectations

- Targeted tests first for each blocker fix.
- `python3 tools/quality_gate.py test` after Python test changes where
  practical.
- `python3 tools/quality_gate.py quality` before final push when practical.
- `git diff --check` before commits.
- Live browser/Infisical tests are separate opt-in operator checks and are
  not part of the default quality gate.

## Documentation Synchronization Points

- arc42 checked: service-access and credential display safety already covers
  Infisical-only password visibility.
- ADR checked:
  `documentation/architecture/adr-service-access-dashboard-infisical.adoc`.
- Update arc42 only if provider contracts, runtime behavior, service-access
  routing, credential display policy, or safety policy materially changes.
- Update final report under `documentation/workflow/reports/`.
- Do not commit raw unredacted local evidence.

## Stop Conditions

Stop workflow execution when:

- branch does not match `feature/live-greenpath-repair-loop-20260606`;
- unrelated or unclear worktree changes are present;
- live command would run without explicit consent;
- a fix would weaken safety, consent, secret, environment, or validation
  guards;
- LXD/Docker state is ambiguous;
- the same blocker recurs after a fix;
- the loop reaches 10 iterations;
- a required credential source is missing and cannot be resolved from ignored
  live configuration without interactive prompting;
- Infisical item verification requires exposing or exporting password
  values;
- test or evidence output would contain secrets;
- documentation would claim unverified live success.

## Uncertainty Escalation Rules

- Requirement conflict: Senior Requirement Engineer and Root Architect.
- Architecture or service-boundary conflict: Senior System Architect.
- Secret exposure risk: Secrets and Config Management plus Senior Tester.
- Quality gate failure: Senior Tester and Quality Gate owner.
- Live host ambiguity: Senior DevOps Engineer, then stop.
- Unknown blocker classification: Typed Error Router, then Root Architect.

## Commit And Push Plan

- Do not push directly to `main`.
- Workflow execution uses branch
  `feature/live-greenpath-repair-loop-20260606`.
- Commit each blocker fix separately.
- Use a separate commit for the new `tests/live` suite if it is not part of a
  blocker fix.
- Do not commit ignored live evidence or local secret files.
- Push only when explicitly requested by the user or workflow handoff.

## Definition Of Done

- `./install.sh --confirm-reset` completes the governed reset plus setup run
  with final status `completed` or `passed`.
- Three expected LXD instances exist and are running.
- Docker Swarm has one manager and two workers.
- Expected stacks are deployed:
  `portainer`, `nexus`, `jenkins`, `rabbitmq`, `sonarqube`, `swagger`, and
  `service-access`.
- Applicable published ports and central browser paths are reachable.
- New `tests/live/test_post_install_browser_live.py` passes with live tests
  explicitly enabled.
- Infisical contains credential entries for every credential-requiring
  selected-profile service, and missing no-login services are explicitly
  recorded as not required.
- Final evidence exists under `.tiny-swarm-world/evidence`.
- Final report documents blockers, classifications, fixes, commands, commit
  SHAs, final greenpath verification, post-install browser/path verification,
  and Infisical credential coverage.
- Each blocker fix has its own commit.

## Handoff To Workflow Execute

This workflow is released for controlled live execution on branch
`feature/live-greenpath-repair-loop-20260606`.

Before write-capable execution:

```bash
git status --short --branch
git branch --show-current
git show-ref --verify --quiet refs/heads/feature/live-greenpath-repair-loop-20260606
```

Required execution sequence:

```bash
python3 tools/install_debugger.py
export TSW_INFISICAL_LOGIN_EMAIL="admin@example.com"
export TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD="<infisical-master-password>"
export TSW_SEED_INFISICAL_ITEMS=1
./install.sh --confirm-reset
python3 tools/quality_gate.py test
TSW_RUN_POST_INSTALL_BROWSER_LIVE=1 PYTHONPATH=src python3 -m unittest tests.live.test_post_install_browser_live
git diff --check
```

Operator note:

- `./install.sh --confirm-reset` performs the governed reset and reinstalls
  the service-access profile, including the separate Infisical and
  service-access stacks.
- The live browser/Infisical test reads Infisical login material from the
  ignored `.tiny-swarm-world/local/live-installation.env` file or from the
  explicit `TSW_INFISICAL_LOGIN_EMAIL` and
  `TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD` environment variables.
- Infisical secret-item seeding is optional and intentionally gated by
  `TSW_SEED_INFISICAL_ITEMS=1`. When enabled, the deployment flow creates
  missing secret items for `platform/jenkins`, `platform/nexus`,
  `platform/portainer`, `platform/rabbitmq`, and `platform/sonarqube` from the
  operator-supplied local `TSW_*` credential values.
- If the reset removes Infisical data and `TSW_SEED_INFISICAL_ITEMS` is not
  enabled, restore the account and items manually or rerun with the explicit
  seed flag before running the live credential-coverage test.

## arc42 Check Status

Checked. Existing arc42 and ADR documentation already require:

- service-access and Infisical stay in the Deployment responsibility
  boundary;
- password values are visible only through Infisical's authenticated UI;
- dashboard assets show Infisical item references only;
- evidence must not contain secrets, tokens, raw environment payloads, local
  IP addresses, host-specific paths, or credential-bearing URLs.

No arc42 update is required for workflow creation itself. Any implementation
change that alters credential display policy, routing ownership, deployment
behavior, or evidence semantics must update arc42 during workflow execution.
