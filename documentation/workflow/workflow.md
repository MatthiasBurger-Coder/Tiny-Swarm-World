# Workflow: Live Greenpath Repair Loop

```yaml
workflow_id: live-greenpath-repair-loop-20260606
workflow_version: 1.0.0
branch: feature/live-greenpath-repair-loop-20260606
execution_profile: FULL_PATH
released_for_workflow_execute: true
created_utc: "2026-06-06T00:00:00Z"
request: "Achieve one complete verified greenpath for ./install.sh on local WSL2 LXD/LXC-native Docker Swarm setup."
decision: READY_FOR_WORKFLOW
confidence: 91
```

## Executive Summary

This workflow executes a controlled live repair loop for the LXC-native Docker Swarm greenpath. The loop runs `./install.sh`, stores evidence under `.tiny-swarm-world/evidence`, parses the latest setup evidence, classifies the first blocker precisely, applies only the current blocker fix, adds or updates automated tests, runs targeted verification, commits the blocker fix, and repeats until the final setup status is completed or passed.

Live LXD/LXC and Docker Swarm mutation is explicitly authorized by the user for this workflow only. Safety guards, validations, consent gates, secret handling, and environment guards must not be bypassed or weakened.

## Requirement Clarification Gate

Original request:

- Create branch `feature/live-greenpath-repair-loop-20260606`.
- Run the full live fresh install.
- Store all evidence under `.tiny-swarm-world/evidence`.
- Parse latest evidence automatically, detect and classify the first blocker, fix only that blocker, test it, rerun install, and repeat.
- Stop after 10 iterations, repeated blocker after a fix, manual secrets or unknown destructive host changes, weakened safety, or ambiguous LXD/Docker host state.
- Implement provider resource resolution for `lxc_native` and precise blocker evidence/classifications.
- Commit each blocker fix as one separate commit.

Interpreted intent:

- Repair the Python automation and LXC-native provider mapping until one local WSL2 LXD/LXC-native Docker Swarm setup greenpath completes.
- Keep implementation Python-based and idempotent.
- Treat `vms[].name` as instance names only while resolving reusable profile, physical network, and storage pool independently.

Change type:

- Python automation behavior change.
- Infrastructure adapter and provider configuration resolution change.
- Evidence classification and reporting change.
- Live platform verification workflow.

Affected process strand:

- `./install.sh` fresh reset, preflight, platform init, swarm bootstrap/join, stack deployment, port exposure, and final verification.

Affected architecture area:

- `src/tiny_swarm_world/domain` only for provider value objects if needed.
- `src/tiny_swarm_world/application` for orchestration and ports if needed.
- `src/tiny_swarm_world/infrastructure` for LXC/LXD command adapters, evidence parsing, provider resource resolution, and composition wiring.
- `infra/config` for explicit provider defaults if needed.
- `tests` for deterministic unit coverage.
- `documentation/workflow` and final report.

Explicit requirements:

- Do not bypass safety guards.
- Do not disable validations to make the run green.
- Do not hardcode temporary local hacks unless represented as provider configuration or documented local defaults.
- Do not use Ansible.
- Keep implementation Python-based.
- Add `lxc_native` provider resource resolution.
- Resolve profile, network, and storage independently.
- Add dry-run provider resolution verification before platform mutation.
- Add precise blocked classifications and evidence fields.
- Make remediations idempotent.

Implicit requirements:

- Preserve hexagonal architecture.
- Keep live host mutation inside explicit install/setup execution.
- Keep committed evidence free of secrets and host-specific sensitive payloads.
- Use mocked tests for command execution and LXD/Docker operations.

Assumptions:

- The local WSL2 environment has LXD/LXC and Docker available enough to execute the requested live setup.
- Existing host resources `docker-swarm`, `lxdbr0`, and `default` may be used only after independent validation.
- Generated evidence under `.tiny-swarm-world/evidence` is local runtime evidence and should not be committed unless a redacted final report explicitly requires it.

Non-goals:

- No Ansible, Terraform, Kubernetes-first migration, Java, Maven, Spring Boot, or React frontend scope.
- No weakening of consent, safety, drift, secret, or environment guards.
- No destructive host cleanup beyond explicit fresh reset/install behavior already guarded by the project.

Risks:

- Live setup may require long-running downloads, image pulls, or service health checks.
- Host LXD/Docker state may contain ambiguous resources that must stop the loop rather than guessing.
- Stack readiness may expose additional blockers after provider mapping is fixed.

Open questions:

- None blocking.

Blocking questions:

- None.

Decision:

- `READY_FOR_WORKFLOW`.

## Target Picture

A fresh reset followed by `./install.sh` completes with final setup status `completed` or `passed`. LXD instances `swarm-manager`, `swarm-worker-1`, and `swarm-worker-2` exist and are running. Docker Swarm reports one manager and two workers. Expected stacks `portainer`, `nexus`, `jenkins`, `rabbitmq`, `sonarqube`, `swagger`, and `service-access` are deployed. Applicable published service ports are reachable from the host. Final evidence and a final report document the greenpath.

## Verified Baseline

- Branch: `feature/live-greenpath-repair-loop-20260606`.
- Current observed blocker from user report: `profile_missing` at `platform:node:swarm-manager`.
- Desired inventory contains `swarm-manager`, `swarm-worker-1`, and `swarm-worker-2` as VM names.
- Local LXD state reportedly includes profile `docker-swarm`, network `lxdbr0`, and storage pool `default`.

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
  adr: not-required
stop_conditions: [branch_mismatch, dirty_unrelated_worktree]
```

Done criteria:

- Active workflow targets the requested branch and live repair loop.
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
affected_files: [.tiny-swarm-world/evidence, documentation/workflow/reports/**, src/tiny_swarm_world/**, infra/config/**, tests/**]
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

- Loop reaches final status `completed` or `passed`, or stops with a precise blocker report.
- Each blocker fix is committed separately.

### Slice 04: Final Report

```yaml
slice_id: S04
profile: FULL_PATH
owner: Senior Documentation Engineer
secondary_reviewers: [Senior Tester, Senior DevOps Engineer]
affected_files: [documentation/workflow/reports/**]
affected_modules: [documentation]
affected_contracts: []
dependencies: [S03]
parallel_group: sequential
file_locks: [documentation/workflow/reports]
contract_locks: []
architecture_locks: []
quality_gates:
  targeted: [git diff --check]
  required: [git diff --check]
documentation:
  arc42: checked
  adr: not-required
stop_conditions: [missing_evidence, unverified_success_claim]
```

Done criteria:

- Final report documents every blocker encountered, fix applied, verification command, commit SHA, and final greenpath evidence location.

## Loop Rules

- Maximum repair iterations: 10.
- Stop if the same blocker appears twice after a fix.
- Stop if a blocker requires manual secrets or unknown destructive host changes.
- Stop if a repair would weaken safety, consent, secret, or environment guards.
- Stop if LXD/Docker host state is ambiguous and cannot be reconciled safely.
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

Evidence for blockers must include where applicable:

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

## Quality Gate Expectations

- Targeted tests first for each blocker fix.
- `python3 tools/quality_gate.py test` after Python test changes where practical.
- `python3 tools/quality_gate.py quality` before final push when practical.
- `git diff --check` before commits.

## Documentation Synchronization

- Update arc42 only if provider contracts, runtime behavior, or safety policy materially changes.
- Update final report under `documentation/workflow/reports/`.
- Do not commit raw unredacted local evidence unless explicitly reviewed.

## Definition Of Done

- `./install.sh` fresh setup completes with final status `completed` or `passed`.
- Three expected LXD instances exist and are running.
- Docker Swarm has one manager and two workers.
- Expected stacks are deployed.
- Applicable published ports are reachable.
- Final evidence exists under `.tiny-swarm-world/evidence`.
- Final report documents blockers, fixes, commands, and final verification.
- Each blocker fix has its own commit.

## Handoff To Workflow Execute

This workflow is released for immediate controlled live execution on branch `feature/live-greenpath-repair-loop-20260606`.
