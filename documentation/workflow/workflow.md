# ARCH-03.12 — Introduce Explicit Operation Results and Failure Model

Workflow ID: issue-355-operation-results
workflowVersion: 1.0
Status: EXECUTING; S355-01 accepted, S355-02 through S355-07 not started
Issue: [#355](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/355)
Parent: [#313](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/313)
Branch: `architecture/workflow-355-operation-results-20260926`
Baseline: `3487ce322bb2b251a45695fc88a70ffa8132b0de`
Execution profile: FULL_PATH — shared application contracts, adapter translation and lifecycle compatibility.

## Executive Summary and Target Picture

Standardize expected lifecycle operation outcomes and actionable failure context
across platform, artifacts, deployment and setup while preserving CLI/installer
compatibility. Adapters translate technical failures; workflows retain confirmed
progress and originating failures. Existing recovery supplies truthful rolled_back
semantics. See [requirement matrix](requirement-matrix.md) and
[proposed ADR](../arc42/09_decisions/adr-explicit-operation-results.adoc).

## Requirement Clarification Gate

- Original Request: `[ARCH-03.12] Introduce Explicit Operation Results and Failure Model`, then `workflow create`.
- Interpreted Intent: author and publish an executable plan for #355; implementation follows a later workflow execute.
- Change Type: architecture hardening and compatible failure-contract migration.
- Affected Process Strand: workflow create.
- Affected Architecture Area: application-port contracts, lifecycle services, adapters, CLI/installer reporting.
- Explicit Requirements: R355-01 through R355-14 from issue goal, scope and acceptance criteria.
- Implicit Requirements: R355-15, safe cause handling, cancellation, truthful partial/rollback, four result families and installer compatibility.
- Assumptions: use additive operation_result fields; keep legacy status and exit mappings; existing recover is the rollback producer.
- Non-Goals: new retries, automatic rollback, idempotency policies (#356), installer decomposition, provider/process replacement, new persistence schemas, live operations, Java/React/Kubernetes scope.
- Risks: premature success, swallowed defects/cancellation, sensitive diagnostics, lost nested context, status/JSON/exit drift and oversized adapter migration.
- Open Questions: none blocking authoring. S355-01 must resolve exact inventory, error taxonomy and per-boundary migration before product changes.
- Blocking Questions: none for authoring; an unaccepted ADR or incomplete inventory blocks S355-02.
- Confidence Level: 94 percent; clarification attempt 1, maxRetries 3.
- Decision: READY_FOR_WORKFLOW, with explicit S355-01 architecture acceptance gate.
- Existing workflow relationship: replace completed #352 workflow entirely on this dedicated branch. Previous plan remains in Git at baseline; no prior issue evidence is deleted.

## Verified Baseline and Scope

Four existing result families are in platform/workflow/results.py, artifacts/workflows.py,
deployment/workflows.py and setup/workflow.py. Platform runtime and setup contain
broad exception catches. AsyncPortCommandRunner raises infrastructure-owned
CommandExecutionError. LXC node commands lose the async failure hint; update state
storage can leak technical errors. Existing update observation has a typed port
error; update recover already verifies image/task convergence. CLI success depends
on completed. Installer preserves child exits plus timeout/interruption 124/130.

Inventory all reachable lifecycle-facing process, provider/runtime, HTTP,
configuration, state and evidence boundaries. Directory scopes below authorize
only the inventory's result/failure migration, never unrelated refactoring. Every
omitted surface needs evidence that it is already compliant or outside lifecycle
reachability. Stop for reviewed scope correction when required work falls outside
allowed paths. No permission to silently reduce the four-family scope.

Predecessors #353 and #354 are closed; #354 process architecture is present at
baseline. Recheck source and dependency state at execution. EPIC alignment is
preserved: no domain dependency inversion, new engine or safety-policy changes.

## Architecture Constraints and Proposed Semantics

The proposed shared file is `src/tiny_swarm_world/application/ports/operation_result.py`.
It must not depend on services or infrastructure; domain must not import it.
Use immutable values and explicit expected port failures. Existing result wrappers
remain capability-owned and add operation_result with compatible defaults. Keep
lifecycle dispatch thin and concrete wiring in infrastructure composition.

Success obeys existing verification. Partial requires confirmed completed work;
executed=True or a timeout alone proves no successful effect. Preserve uncertain
effects separately. Rolled_back requires observed restoration through existing
recover; metadata/attempts/advice cannot establish it. Keep blocked/refused distinct. A legacy blocked result can follow prior mutation;
retain that status while reporting partial confirmed work and any uncertain effects.
Failure fields: operation, component, safe cause code, recoverability and recommended
action. No raw exceptions, commands, secrets or arbitrary str(exc). Cancellation
and control-flow exceptions propagate through adapters/workflows; existing entrypoint
interruption mappings remain intact. Unexpected defects are distinguishable.
No blanket BaseException translation. Suppress unsafe exception chains at adapters.

New ADR is proposed, not accepted: S355-01 accepts or rejects it with architecture
review before product work. Existing layer, process, provider, consent, Classic
update and installer-reporting ADRs remain authoritative.

## Python Automation Assessment

Python 3.12 / Linux / WSL; existing asyncio orchestration, ports and unittest seams.
Reuse centralized process runners. No runtime commands during import/construction.
Explicitly proposed new files: operation_result.py, its test suite, inventory and ADR.
All other paths must exist at execution preflight; no inferred filenames are authority.

## Frontend Assessment

Console/status UI review is required for compatibility and safe actionable output.
No browser frontend or React work. Human-readable output remains default; JSON is
explicit --json or TSW_DEBUG_JSON=true. Rendering never executes recommended actions.
Verified recovery keeps completed/exit 0 even when operation_result is rolled_back;
failed apply remains nonzero. No intentional exit correction is pre-authorized.

## Test Strategy and Resilience Requirements

Use deterministic mocked adapters and real value serialization. Cover valid/invalid
outcome combinations; missing executable, permission denial, nonzero exit, timeout,
HTTP/provider/configuration/filesystem failures; mutation-before/after failure;
verification failure; partial children; successful/failed/repeated recovery; retained
original failures; cancellation; programming defects; nested secret-safe context.
Test repr, serialized result, exception traceback, logs and CLI output for leaks.

Local contract/installation-orchestration checks: APPLICABLE_LOCAL. Actual installation,
Incus/Docker/Swarm/bootstrap/network checks: NOT_APPLICABLE / LIVE_NOT_APPLICABLE
for this contract migration. Browser/Selenium: NOT_APPLICABLE. External gates:
EXTERNAL_GATE_NOT_APPLICABLE to branch-only authoring publication; reassess required
SonarQube/CI at any later PR, reporting unavailable or failed states honestly.
If runtime behavior scope changes, reclassify and require separate live consent.
No live or external success follows from local tests.

## Ordered Slices and Dependency Graph

`S355-01 -> S355-02 -> S355-03 -> S355-04 -> S355-05 -> S355-06 -> S355-07`

All slices NOT STARTED. Every slice has exactly one checkpoint commit. Common
allowed evidence/status writes: `.tiny-swarm/evidence/issue-355/**`, that slice's
`.codex/evidence/slice-<number>-distribution.md` and consolidation file, plus active
workflow status, matrix and context-pack refresh. Serialize these shared files.
No product changes are authorized during workflow create.

### Slice 01 — Inventory lifecycle failures and accept the contract

Purpose: Inventory every platform (including update/recover), artifact, deployment, setup, installer and simple-installer producer/consumer and reachable lifecycle port. Classify existing typed results, expected/unexpected exceptions, mutation evidence, rollback applicability, CLI contracts and technical boundary owners. Record exact per-boundary failure mappings and files to edit. Accept or reject the proposed ADR with Requirement, Architect, Python and Test review; no product edits. If required paths exceed later scopes, obtain reviewed scope/lock correction before writes.

Prerequisites: verified branch, governing hashes and S3/S3D preflight.

Requirement-to-verification mapping: R355-01, R355-05, R355-11, R355-12, R355-13, R355-15. The targeted commands below plus inventory-specific static evidence must substantiate these rows.

Allowed write scope and locks:

```yaml
{
  "slice_id": "S355-01",
  "profile": "FULL_PATH",
  "owner": "Senior System Architect",
  "secondary_reviewers": [
    "Senior Requirement Engineer",
    "Senior System Architect",
    "Senior Python Automation Developer",
    "Senior Tester"
  ],
  "affected_files": [
    "documentation/workflow/lifecycle-failure-inventory.md",
    "documentation/arc42/09_decisions/adr-explicit-operation-results.adoc"
  ],
  "affected_modules": [
    "operation results",
    "lifecycle failure boundaries"
  ],
  "affected_contracts": [
    "application result/failure",
    "legacy CLI compatibility"
  ],
  "dependencies": [],
  "parallel_group": "serial",
  "file_locks": [
    "documentation/workflow/lifecycle-failure-inventory.md",
    "documentation/arc42/09_decisions/adr-explicit-operation-results.adoc",
    ".tiny-swarm/evidence/issue-355/**",
    ".codex/evidence/slice-*-distribution.md",
    ".codex/evidence/slice-*-consolidation.md",
    "documentation/workflow/**"
  ],
  "contract_locks": [
    "operation-result-contract",
    "lifecycle-failure-compatibility"
  ],
  "architecture_locks": [
    "ports-adapters-workflows"
  ],
  "quality_gates": {
    "targeted": [
      "python3 tools/quality_gate.py arch-tests"
    ],
    "required": [
      "git diff --check"
    ]
  },
  "documentation": {
    "arc42": "documentation/arc42/05_analysis/arch-03-12-operation-results.md",
    "adr": "documentation/arc42/09_decisions/adr-explicit-operation-results.adoc"
  },
  "stop_conditions": [
    "Unaccepted architecture decision or unresolved inventory",
    "Scope or ownership mismatch",
    "Unsafe diagnostics or changed safety/exit semantics",
    "Failed required quality gate"
  ]
}
```

Done criteria: Complete inventory with no unowned boundary; accepted ADR and per-consumer mapping; every required path fits later scopes. Unresolved decisions block S355-02.

Parallel execution eligibility: serial until Three Amigos proves disjoint inventory-derived scopes and stable contracts. Conflicting workflows: #313 siblings and all holders of listed locks. Shared files: common evidence/context and listed contracts. Shared infrastructure: none used. Requires isolated worktree: yes for execution/streams. Serialized live validation: yes if separately approved. Merge-order constraint: predecessor first. Parallelization status: NOT_SAFELY_PARALLELIZABLE by default.

Evidence: `.tiny-swarm/evidence/issue-355/`; record exact test names and results per requirement. Rollback: revert this slice commit only after checking dependent slices; no runtime rollback action.

### Slice 02 — Introduce and integrate the shared operation contract

Purpose: Implement immutable outcomes/failures and valid combinations per accepted ADR. Add compatible typed port error translation on the real async command path and a real workflow-result consumer. Preserve legacy exception imports/attributes with a compatible bridge where required, public constructors and result fields. New types must be connected to executable behavior in this slice, not scaffolding only.

Prerequisites: S355-01 accepted with evidence and checkpoint; repeat S3/S3D and lock checks.

Requirement-to-verification mapping: R355-01, R355-02, R355-03, R355-05, R355-06, R355-07, R355-08, R355-09, R355-10, R355-11, R355-14, R355-15. The targeted commands below plus inventory-specific new tests must substantiate these rows.

Allowed write scope and locks:

```yaml
{
  "slice_id": "S355-02",
  "profile": "FULL_PATH",
  "owner": "Senior Python Automation Developer",
  "secondary_reviewers": [
    "Senior Requirement Engineer",
    "Senior System Architect",
    "Senior Python Automation Developer",
    "Senior Tester"
  ],
  "affected_files": [
    "src/tiny_swarm_world/application/ports/operation_result.py",
    "src/tiny_swarm_world/application/ports/commands/port_command_runner.py",
    "src/tiny_swarm_world/infrastructure/adapters/command_runner/async_command_runner.py",
    "src/tiny_swarm_world/infrastructure/adapters/exceptions/exception_command_execution.py",
    "src/tiny_swarm_world/application/services/platform/workflow/results.py",
    "tests/application/ports/test_operation_result.py",
    "tests/infrastructure/adapters/command_runner/test_async_command_runner.py",
    "tests/application/services/platform/test_platform_workflows.py",
    "tests/infrastructure/adapters/ui/test_command_runner_ui_failure_semantics.py"
  ],
  "affected_modules": [
    "operation results",
    "lifecycle failure boundaries"
  ],
  "affected_contracts": [
    "application result/failure",
    "legacy CLI compatibility"
  ],
  "dependencies": [
    "S355-01"
  ],
  "parallel_group": "serial",
  "file_locks": [
    "src/tiny_swarm_world/application/ports/operation_result.py",
    "src/tiny_swarm_world/application/ports/commands/port_command_runner.py",
    "src/tiny_swarm_world/infrastructure/adapters/command_runner/async_command_runner.py",
    "src/tiny_swarm_world/infrastructure/adapters/exceptions/exception_command_execution.py",
    "src/tiny_swarm_world/application/services/platform/workflow/results.py",
    "tests/application/ports/test_operation_result.py",
    "tests/infrastructure/adapters/command_runner/test_async_command_runner.py",
    "tests/application/services/platform/test_platform_workflows.py",
    "tests/infrastructure/adapters/ui/test_command_runner_ui_failure_semantics.py",
    ".tiny-swarm/evidence/issue-355/**",
    ".codex/evidence/slice-*-distribution.md",
    ".codex/evidence/slice-*-consolidation.md",
    "documentation/workflow/**"
  ],
  "contract_locks": [
    "operation-result-contract",
    "lifecycle-failure-compatibility"
  ],
  "architecture_locks": [
    "ports-adapters-workflows"
  ],
  "quality_gates": {
    "targeted": [
      "PYTHONPATH=src python3 -m unittest tests.application.ports.test_operation_result tests.infrastructure.adapters.command_runner.test_async_command_runner tests.infrastructure.adapters.ui.test_command_runner_ui_failure_semantics tests.application.services.platform.test_platform_workflows"
    ],
    "required": [
      "git diff --check",
      "python3 tools/quality_gate.py quality"
    ]
  },
  "documentation": {
    "arc42": "documentation/arc42/05_analysis/arch-03-12-operation-results.md",
    "adr": "documentation/arc42/09_decisions/adr-explicit-operation-results.adoc"
  },
  "stop_conditions": [
    "Unaccepted architecture decision or unresolved inventory",
    "Scope or ownership mismatch",
    "Unsafe diagnostics or changed safety/exit semantics",
    "Failed required quality gate"
  ]
}
```

Done criteria: Invariant and serialization tests pass; command nonzero/launch/timeout mapping preserves cause; cancellation and secret-safe traceback tests pass; existing command and workflow behavior remains compatible.

Parallel execution eligibility: serial until Three Amigos proves disjoint inventory-derived scopes and stable contracts. Conflicting workflows: #313 siblings and all holders of listed locks. Shared files: common evidence/context and listed contracts. Shared infrastructure: none used. Requires isolated worktree: yes for execution/streams. Serialized live validation: yes if separately approved. Merge-order constraint: predecessor first. Parallelization status: NOT_SAFELY_PARALLELIZABLE by default.

Evidence: `.tiny-swarm/evidence/issue-355/`; record exact test names and results per requirement. Rollback: revert this slice commit only after checking dependent slices; no runtime rollback action.

### Slice 03 — Translate lifecycle adapter failures

Purpose: Migrate the S355-01 enumerated lifecycle-facing adapter boundaries only: LXC node command and manager shell gateway, Docker/Swarm/node adapters, update observation/state storage, lifecycle HTTP clients and configuration/evidence repositories. Carry existing process failure classifications through typed results. Translate expected filesystem, configuration, HTTP/provider and process failures at the owning adapter, suppress unsafe cause chains, and preserve data/return contracts. The directory scopes are bounded by the accepted inventory; unrelated client behavior and new persistence formats are forbidden. Every intermediate checkpoint must preserve existing catches and exits: use compatible exception bridges until consumer migration, particularly OSError/ValueError catches around JsonUpdateStateStore. If a bridge is infeasible, stop for a reviewed narrowly scoped consumer adaptation before changing that boundary; never permit an intermediate raw-error regression.

Prerequisites: S355-02 accepted with evidence and checkpoint; repeat S3/S3D and lock checks.

Requirement-to-verification mapping: R355-06, R355-07, R355-08, R355-09, R355-10, R355-11, R355-12, R355-14, R355-15. The targeted commands below plus inventory-specific new tests must substantiate these rows.

Allowed write scope and locks:

```yaml
{
  "slice_id": "S355-03",
  "profile": "FULL_PATH",
  "owner": "Senior Python Automation Developer",
  "secondary_reviewers": [
    "Senior Requirement Engineer",
    "Senior System Architect",
    "Senior Python Automation Developer",
    "Senior Tester"
  ],
  "affected_files": [
    "src/tiny_swarm_world/application/ports/clients/**",
    "src/tiny_swarm_world/application/ports/node_provider/**",
    "src/tiny_swarm_world/application/ports/update/**",
    "src/tiny_swarm_world/application/ports/repositories/**",
    "src/tiny_swarm_world/infrastructure/adapters/clients/**",
    "src/tiny_swarm_world/infrastructure/adapters/update/**",
    "src/tiny_swarm_world/infrastructure/adapters/repositories/**",
    "tests/infrastructure/adapters/clients/**",
    "tests/infrastructure/adapters/update/**",
    "tests/infrastructure/adapters/repositories/**",
    "src/tiny_swarm_world/application/ports/configuration/**",
    "src/tiny_swarm_world/infrastructure/adapters/configuration/**",
    "tests/infrastructure/adapters/configuration/**",
    "src/tiny_swarm_world/application/ports/file_management/port_local_file_storage.py",
    "src/tiny_swarm_world/infrastructure/adapters/file_management/local_file_storage.py",
    "tests/infrastructure/adapters/file_management/test_local_file_storage.py",
    "src/tiny_swarm_world/infrastructure/adapters/preflight/host_preflight_probe.py",
    "src/tiny_swarm_world/infrastructure/adapters/preflight/artifact_readiness.py",
    "tests/infrastructure/adapters/preflight/test_host_preflight_probe.py",
    "tests/infrastructure/adapters/preflight/test_artifact_readiness.py",
    "src/tiny_swarm_world/application/ports/network/port_wsl_socat_exposure.py",
    "src/tiny_swarm_world/infrastructure/adapters/network/wsl_socat_exposure.py",
    "tests/infrastructure/adapters/network/test_wsl_socat_exposure.py",
    "src/tiny_swarm_world/infrastructure/composition_runtime.py",
    "src/tiny_swarm_world/infrastructure/composition_probes.py",
    "tests/infrastructure/test_composition.py",
    "tests/infrastructure/test_composition_configuration.py",
    "tests/infrastructure/test_composition_probes.py",
    "src/tiny_swarm_world/infrastructure/adapters/host/wsl_host_preparation.py",
    "src/tiny_swarm_world/application/ports/host/port_host_preparation.py",
    "tests/infrastructure/adapters/host/test_host_preparation.py",
    "src/tiny_swarm_world/application/ports/preflight/port_host_preflight_probe.py"
  ],
  "affected_modules": [
    "operation results",
    "lifecycle failure boundaries"
  ],
  "affected_contracts": [
    "application result/failure",
    "legacy CLI compatibility"
  ],
  "dependencies": [
    "S355-02"
  ],
  "parallel_group": "serial",
  "file_locks": [
    "src/tiny_swarm_world/application/ports/clients/**",
    "src/tiny_swarm_world/application/ports/node_provider/**",
    "src/tiny_swarm_world/application/ports/update/**",
    "src/tiny_swarm_world/application/ports/repositories/**",
    "src/tiny_swarm_world/infrastructure/adapters/clients/**",
    "src/tiny_swarm_world/infrastructure/adapters/update/**",
    "src/tiny_swarm_world/infrastructure/adapters/repositories/**",
    "tests/infrastructure/adapters/clients/**",
    "tests/infrastructure/adapters/update/**",
    "tests/infrastructure/adapters/repositories/**",
    ".tiny-swarm/evidence/issue-355/**",
    ".codex/evidence/slice-*-distribution.md",
    ".codex/evidence/slice-*-consolidation.md",
    "documentation/workflow/**",
    "src/tiny_swarm_world/application/ports/configuration/**",
    "src/tiny_swarm_world/infrastructure/adapters/configuration/**",
    "tests/infrastructure/adapters/configuration/**",
    "src/tiny_swarm_world/application/ports/file_management/port_local_file_storage.py",
    "src/tiny_swarm_world/infrastructure/adapters/file_management/local_file_storage.py",
    "tests/infrastructure/adapters/file_management/test_local_file_storage.py",
    "src/tiny_swarm_world/infrastructure/adapters/preflight/host_preflight_probe.py",
    "src/tiny_swarm_world/infrastructure/adapters/preflight/artifact_readiness.py",
    "tests/infrastructure/adapters/preflight/test_host_preflight_probe.py",
    "tests/infrastructure/adapters/preflight/test_artifact_readiness.py",
    "src/tiny_swarm_world/application/ports/network/port_wsl_socat_exposure.py",
    "src/tiny_swarm_world/infrastructure/adapters/network/wsl_socat_exposure.py",
    "tests/infrastructure/adapters/network/test_wsl_socat_exposure.py",
    "src/tiny_swarm_world/infrastructure/composition_runtime.py",
    "src/tiny_swarm_world/infrastructure/composition_probes.py",
    "tests/infrastructure/test_composition.py",
    "tests/infrastructure/test_composition_configuration.py",
    "tests/infrastructure/test_composition_probes.py",
    "src/tiny_swarm_world/infrastructure/adapters/host/wsl_host_preparation.py",
    "src/tiny_swarm_world/application/ports/host/port_host_preparation.py",
    "tests/infrastructure/adapters/host/test_host_preparation.py",
    "src/tiny_swarm_world/application/ports/preflight/port_host_preflight_probe.py"
  ],
  "contract_locks": [
    "operation-result-contract",
    "lifecycle-failure-compatibility"
  ],
  "architecture_locks": [
    "ports-adapters-workflows"
  ],
  "quality_gates": {
    "targeted": [
      "PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.lxc.command.test_node_command tests.infrastructure.adapters.clients.test_docker_swarm_runtime tests.infrastructure.adapters.clients.test_lxc_node_provider tests.infrastructure.adapters.update.test_lxc_runtime_observer tests.infrastructure.adapters.update.test_json_state_store tests.infrastructure.process.test_execution_contract",
      "PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.file_management.test_local_file_storage tests.infrastructure.adapters.preflight.test_host_preflight_probe tests.infrastructure.adapters.preflight.test_artifact_readiness tests.infrastructure.adapters.network.test_wsl_socat_exposure tests.infrastructure.adapters.host.test_host_preparation tests.infrastructure.test_composition_probes tests.infrastructure.test_composition_configuration"
    ],
    "required": [
      "git diff --check",
      "python3 tools/quality_gate.py quality"
    ]
  },
  "documentation": {
    "arc42": "documentation/arc42/05_analysis/arch-03-12-operation-results.md",
    "adr": "documentation/arc42/09_decisions/adr-explicit-operation-results.adoc"
  },
  "stop_conditions": [
    "Unaccepted architecture decision or unresolved inventory",
    "Scope or ownership mismatch",
    "Unsafe diagnostics or changed safety/exit semantics",
    "Failed required quality gate"
  ]
}
```

Done criteria: Every inventoried expected technical failure is translated with named adapter test evidence; no raw technical error leaks through the port; unexpected defects/cancellation remain distinguishable. Add focused tests for every changed adapter beyond the listed minimum.

Parallel execution eligibility: serial until Three Amigos proves disjoint inventory-derived scopes and stable contracts. Conflicting workflows: #313 siblings and all holders of listed locks. Shared files: common evidence/context and listed contracts. Shared infrastructure: none used. Requires isolated worktree: yes for execution/streams. Serialized live validation: yes if separately approved. Merge-order constraint: predecessor first. Parallelization status: NOT_SAFELY_PARALLELIZABLE by default.

Evidence: `.tiny-swarm/evidence/issue-355/`; record exact test names and results per requirement. Rollback: revert this slice commit only after checking dependent slices; no runtime rollback action.

### Slice 04 — Integrate platform aggregation and verified recovery

Purpose: Consume typed failures across platform mutation, verification, pre-apply guards, evidence and existing update/recover. Preserve originating context and confirmed progress, distinguish uncertain effects from confirmed completion, and derive partial only from evidence. Existing recover may report rolled_back only after observed original-image convergence, including verified no-op recovery. Preserve original transition metadata and both failures when recovery fails. Keep lifecycle.py dispatch-only; no automatic rollback or new retries.

Prerequisites: S355-03 accepted with evidence and checkpoint; repeat S3/S3D and lock checks.

Requirement-to-verification mapping: R355-01, R355-02, R355-03, R355-04, R355-05, R355-06, R355-07, R355-12, R355-14, R355-15. The targeted commands below plus inventory-specific new tests must substantiate these rows.

Allowed write scope and locks:

```yaml
{
  "slice_id": "S355-04",
  "profile": "FULL_PATH",
  "owner": "Senior Python Automation Developer",
  "secondary_reviewers": [
    "Senior Requirement Engineer",
    "Senior System Architect",
    "Senior Python Automation Developer",
    "Senior Tester"
  ],
  "affected_files": [
    "src/tiny_swarm_world/application/services/platform/workflow/**",
    "src/tiny_swarm_world/application/services/platform/incus/lxc_docker_install.py",
    "src/tiny_swarm_world/application/services/platform/lifecycle.py",
    "tests/application/services/platform/test_platform_workflows.py",
    "tests/application/services/platform/test_platform_lifecycle.py",
    "tests/application/services/platform/test_classic_update_workflow.py",
    "tests/application/services/platform/test_lxc_docker_install.py",
    "src/tiny_swarm_world/application/services/platform/preflight_service.py",
    "tests/application/services/platform/test_preflight_service.py"
  ],
  "affected_modules": [
    "operation results",
    "lifecycle failure boundaries"
  ],
  "affected_contracts": [
    "application result/failure",
    "legacy CLI compatibility"
  ],
  "dependencies": [
    "S355-03"
  ],
  "parallel_group": "serial",
  "file_locks": [
    "src/tiny_swarm_world/application/services/platform/workflow/**",
    "src/tiny_swarm_world/application/services/platform/incus/lxc_docker_install.py",
    "src/tiny_swarm_world/application/services/platform/lifecycle.py",
    "tests/application/services/platform/test_platform_workflows.py",
    "tests/application/services/platform/test_platform_lifecycle.py",
    "tests/application/services/platform/test_classic_update_workflow.py",
    "tests/application/services/platform/test_lxc_docker_install.py",
    ".tiny-swarm/evidence/issue-355/**",
    ".codex/evidence/slice-*-distribution.md",
    ".codex/evidence/slice-*-consolidation.md",
    "documentation/workflow/**",
    "src/tiny_swarm_world/application/services/platform/preflight_service.py",
    "tests/application/services/platform/test_preflight_service.py"
  ],
  "contract_locks": [
    "operation-result-contract",
    "lifecycle-failure-compatibility"
  ],
  "architecture_locks": [
    "ports-adapters-workflows"
  ],
  "quality_gates": {
    "targeted": [
      "PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_platform_workflows tests.application.services.platform.test_platform_lifecycle tests.application.services.platform.test_classic_update_workflow tests.application.services.platform.test_lxc_docker_install tests.application.services.platform.test_preflight_service"
    ],
    "required": [
      "git diff --check",
      "python3 tools/quality_gate.py quality"
    ]
  },
  "documentation": {
    "arc42": "documentation/arc42/05_analysis/arch-03-12-operation-results.md",
    "adr": "documentation/arc42/09_decisions/adr-explicit-operation-results.adoc"
  },
  "stop_conditions": [
    "Unaccepted architecture decision or unresolved inventory",
    "Scope or ownership mismatch",
    "Unsafe diagnostics or changed safety/exit semantics",
    "Failed required quality gate"
  ]
}
```

Done criteria: Before-mutation failure, later-step failure, verify failure, success, no-op and actual recovery mappings pass. Add blocked-after-mutation regressions for missing/blocked verification: retain executed/effect evidence and classify confirmed partial work without changing legacy blocked status. Attempted/failed recovery never reports rolled_back. Preserve recovery completed status and safety/ordering.

Parallel execution eligibility: serial until Three Amigos proves disjoint inventory-derived scopes and stable contracts. Conflicting workflows: #313 siblings and all holders of listed locks. Shared files: common evidence/context and listed contracts. Shared infrastructure: none used. Requires isolated worktree: yes for execution/streams. Serialized live validation: yes if separately approved. Merge-order constraint: predecessor first. Parallelization status: NOT_SAFELY_PARALLELIZABLE by default.

Evidence: `.tiny-swarm/evidence/issue-355/`; record exact test names and results per requirement. Rollback: revert this slice commit only after checking dependent slices; no runtime rollback action.

### Slice 05 — Propagate results through artifacts deployment and setup

Purpose: Integrate the shared contract into all remaining lifecycle result families and their inventoried steps. Replace ordinary expected-failure broad catch classification with declared typed handling; retain a distinct compatibility policy for unexpected defects. Propagate nested operation/component/cause/recoverability/action without rewriting origin, retain completed phase/step evidence and incomplete work. Preserve setup dependency ordering, timeout/cancellation, fail-fast and concurrency policy; no false success from partial child results. Composition edits are only wiring/typing required by this integration.

Prerequisites: S355-04 accepted with evidence and checkpoint; repeat S3/S3D and lock checks.

Requirement-to-verification mapping: R355-01, R355-02, R355-03, R355-04, R355-06, R355-07, R355-12, R355-14, R355-15. The targeted commands below plus inventory-specific new tests must substantiate these rows.

Allowed write scope and locks:

```yaml
{
  "slice_id": "S355-05",
  "profile": "FULL_PATH",
  "owner": "Senior Python Automation Developer",
  "secondary_reviewers": [
    "Senior Requirement Engineer",
    "Senior System Architect",
    "Senior Python Automation Developer",
    "Senior Tester"
  ],
  "affected_files": [
    "src/tiny_swarm_world/application/services/artifacts/**",
    "src/tiny_swarm_world/application/services/deployment/**",
    "src/tiny_swarm_world/application/services/setup/**",
    "tests/application/services/artifacts/**",
    "tests/application/services/deployment/**",
    "tests/application/services/setup/**",
    "src/tiny_swarm_world/infrastructure/composition_artifacts.py",
    "src/tiny_swarm_world/infrastructure/composition_deployment.py",
    "src/tiny_swarm_world/infrastructure/composition_setup.py",
    "tests/infrastructure/test_composition.py"
  ],
  "affected_modules": [
    "operation results",
    "lifecycle failure boundaries"
  ],
  "affected_contracts": [
    "application result/failure",
    "legacy CLI compatibility"
  ],
  "dependencies": [
    "S355-04"
  ],
  "parallel_group": "serial",
  "file_locks": [
    "src/tiny_swarm_world/application/services/artifacts/**",
    "src/tiny_swarm_world/application/services/deployment/**",
    "src/tiny_swarm_world/application/services/setup/**",
    "tests/application/services/artifacts/**",
    "tests/application/services/deployment/**",
    "tests/application/services/setup/**",
    "src/tiny_swarm_world/infrastructure/composition_artifacts.py",
    "src/tiny_swarm_world/infrastructure/composition_deployment.py",
    "src/tiny_swarm_world/infrastructure/composition_setup.py",
    "tests/infrastructure/test_composition.py",
    ".tiny-swarm/evidence/issue-355/**",
    ".codex/evidence/slice-*-distribution.md",
    ".codex/evidence/slice-*-consolidation.md",
    "documentation/workflow/**"
  ],
  "contract_locks": [
    "operation-result-contract",
    "lifecycle-failure-compatibility"
  ],
  "architecture_locks": [
    "ports-adapters-workflows"
  ],
  "quality_gates": {
    "targeted": [
      "PYTHONPATH=src python3 -m unittest tests.application.services.artifacts.test_artifact_workflows tests.application.services.deployment.test_deployment_workflows tests.application.services.setup.test_setup_workflow tests.infrastructure.test_composition"
    ],
    "required": [
      "git diff --check",
      "python3 tools/quality_gate.py quality"
    ]
  },
  "documentation": {
    "arc42": "documentation/arc42/05_analysis/arch-03-12-operation-results.md",
    "adr": "documentation/arc42/09_decisions/adr-explicit-operation-results.adoc"
  },
  "stop_conditions": [
    "Unaccepted architecture decision or unresolved inventory",
    "Scope or ownership mismatch",
    "Unsafe diagnostics or changed safety/exit semantics",
    "Failed required quality gate"
  ]
}
```

Done criteria: All four families expose consistent operation results; nested partial/failed context survives setup and deployment wrappers; no later dependent mutation follows blocking failure; concurrent evidence aggregation remains deterministic.

Parallel execution eligibility: serial until Three Amigos proves disjoint inventory-derived scopes and stable contracts. Conflicting workflows: #313 siblings and all holders of listed locks. Shared files: common evidence/context and listed contracts. Shared infrastructure: none used. Requires isolated worktree: yes for execution/streams. Serialized live validation: yes if separately approved. Merge-order constraint: predecessor first. Parallelization status: NOT_SAFELY_PARALLELIZABLE by default.

Evidence: `.tiny-swarm/evidence/issue-355/`; record exact test names and results per requirement. Rollback: revert this slice commit only after checking dependent slices; no runtime rollback action.

### Slice 06 — Preserve CLI installer and reporting compatibility

Purpose: Expose additive operation_result data through explicit JSON opt-in and safe human-readable failure summaries. Inventory and preserve installer/simple-installer result propagation, child exit codes, timeout 124 and interruption 130. Preserve existing workflow statuses and keys, default human-readable output, consent exit 2, unsuccessful workflow exit 1, and completed verified recovery exit 0. Rendering is informational and must never invoke recovery. Preserve composition/programming failure propagation separately from expected adapter failures. No root-module redesign or new process imports.

Prerequisites: S355-05 accepted with evidence and checkpoint; repeat S3/S3D and lock checks.

Requirement-to-verification mapping: R355-08, R355-10, R355-13, R355-14, R355-15. The targeted commands below plus inventory-specific new tests must substantiate these rows.

Allowed write scope and locks:

```yaml
{
  "slice_id": "S355-06",
  "profile": "FULL_PATH",
  "owner": "Senior Python Automation Developer",
  "secondary_reviewers": [
    "Senior Requirement Engineer",
    "Senior System Architect",
    "Senior Python Automation Developer",
    "Senior Tester",
    "Console/status UI reviewer"
  ],
  "affected_files": [
    "src/tiny_swarm_world/__main__.py",
    "src/tiny_swarm_world/installer.py",
    "src/tiny_swarm_world/simple_installer.py",
    "src/tiny_swarm_world/infrastructure/adapters/ui/install_reporter.py",
    "src/tiny_swarm_world/application/ports/install_reporter.py",
    "tests/test_package_entrypoint.py",
    "tests/test_classic_update_cli.py",
    "tests/test_installer.py",
    "tests/test_simple_installer.py",
    "tests/infrastructure/adapters/ui/test_install_reporter.py",
    "documentation/user_guide/installer-console-output.md"
  ],
  "affected_modules": [
    "operation results",
    "lifecycle failure boundaries"
  ],
  "affected_contracts": [
    "application result/failure",
    "legacy CLI compatibility"
  ],
  "dependencies": [
    "S355-05"
  ],
  "parallel_group": "serial",
  "file_locks": [
    "src/tiny_swarm_world/__main__.py",
    "src/tiny_swarm_world/installer.py",
    "src/tiny_swarm_world/simple_installer.py",
    "src/tiny_swarm_world/infrastructure/adapters/ui/install_reporter.py",
    "src/tiny_swarm_world/application/ports/install_reporter.py",
    "tests/test_package_entrypoint.py",
    "tests/test_classic_update_cli.py",
    "tests/test_installer.py",
    "tests/test_simple_installer.py",
    "tests/infrastructure/adapters/ui/test_install_reporter.py",
    "documentation/user_guide/installer-console-output.md",
    ".tiny-swarm/evidence/issue-355/**",
    ".codex/evidence/slice-*-distribution.md",
    ".codex/evidence/slice-*-consolidation.md",
    "documentation/workflow/**"
  ],
  "contract_locks": [
    "operation-result-contract",
    "lifecycle-failure-compatibility"
  ],
  "architecture_locks": [
    "ports-adapters-workflows"
  ],
  "quality_gates": {
    "targeted": [
      "PYTHONPATH=src python3 -m unittest tests.test_package_entrypoint tests.test_classic_update_cli tests.test_installer tests.test_simple_installer tests.infrastructure.adapters.ui.test_install_reporter"
    ],
    "required": [
      "git diff --check",
      "python3 tools/quality_gate.py quality"
    ]
  },
  "documentation": {
    "arc42": "documentation/arc42/05_analysis/arch-03-12-operation-results.md",
    "adr": "documentation/arc42/09_decisions/adr-explicit-operation-results.adoc"
  },
  "stop_conditions": [
    "Unaccepted architecture decision or unresolved inventory",
    "Scope or ownership mismatch",
    "Unsafe diagnostics or changed safety/exit semantics",
    "Failed required quality gate"
  ]
}
```

Done criteria: Exit/status/JSON compatibility matrix and redacted human-readable summaries pass; no command/exception/internal object dump; setup counts/timing/evidence links retained; guards still run before mutation.

Parallel execution eligibility: serial until Three Amigos proves disjoint inventory-derived scopes and stable contracts. Conflicting workflows: #313 siblings and all holders of listed locks. Shared files: common evidence/context and listed contracts. Shared infrastructure: none used. Requires isolated worktree: yes for execution/streams. Serialized live validation: yes if separately approved. Merge-order constraint: predecessor first. Parallelization status: NOT_SAFELY_PARALLELIZABLE by default.

Evidence: `.tiny-swarm/evidence/issue-355/`; record exact test names and results per requirement. Rollback: revert this slice commit only after checking dependent slices; no runtime rollback action.

### Slice 07 — Enforce architecture synchronize documentation and audit completion

Purpose: Add contract import and unsafe boundary regression probes without weakening existing rules. Update arc42 to executed facts, include the accepted ADR in the index, refresh only provenance hashes made stale by approved doc changes, and complete all issue evidence. Obtain independent Requirement, Architect, Test/Evidence and issue-completion-auditor reviews. Reconcile every inventory row and all R355 requirements; no omission may be described as done.

Prerequisites: S355-06 accepted with evidence and checkpoint; repeat S3/S3D and lock checks.

Requirement-to-verification mapping: R355-01, R355-02, R355-03, R355-04, R355-05, R355-06, R355-07, R355-08, R355-09, R355-10, R355-11, R355-12, R355-13, R355-14, R355-15. The targeted commands below plus inventory-specific new tests must substantiate these rows.

Allowed write scope and locks:

```yaml
{
  "slice_id": "S355-07",
  "profile": "FULL_PATH",
  "owner": "Senior Tester",
  "secondary_reviewers": [
    "Senior Requirement Engineer",
    "Senior System Architect",
    "Senior Python Automation Developer",
    "Senior Tester"
  ],
  "affected_files": [
    "tests/architecture/test_hexagonal_imports.py",
    "tests/architecture/test_process_spawn_boundaries.py",
    ".importlinter",
    "documentation/arc42/05_analysis/arch-03-12-operation-results.md",
    "documentation/arc42/09_decisions/adr-explicit-operation-results.adoc",
    "documentation/arc42/09_architecture_decisions.adoc",
    "documentation/arc42/05_building_blocks.adoc",
    "documentation/arc42/06_runtime_view.adoc",
    "documentation/arc42/08_concepts.adoc",
    "documentation/process/skills/audit/skill-registry.json"
  ],
  "affected_modules": [
    "operation results",
    "lifecycle failure boundaries"
  ],
  "affected_contracts": [
    "application result/failure",
    "legacy CLI compatibility"
  ],
  "dependencies": [
    "S355-06"
  ],
  "parallel_group": "serial",
  "file_locks": [
    "tests/architecture/test_hexagonal_imports.py",
    "tests/architecture/test_process_spawn_boundaries.py",
    ".importlinter",
    "documentation/arc42/05_analysis/arch-03-12-operation-results.md",
    "documentation/arc42/09_decisions/adr-explicit-operation-results.adoc",
    "documentation/arc42/09_architecture_decisions.adoc",
    "documentation/arc42/05_building_blocks.adoc",
    "documentation/arc42/06_runtime_view.adoc",
    "documentation/arc42/08_concepts.adoc",
    "documentation/process/skills/audit/skill-registry.json",
    ".tiny-swarm/evidence/issue-355/**",
    ".codex/evidence/slice-*-distribution.md",
    ".codex/evidence/slice-*-consolidation.md",
    "documentation/workflow/**"
  ],
  "contract_locks": [
    "operation-result-contract",
    "lifecycle-failure-compatibility"
  ],
  "architecture_locks": [
    "ports-adapters-workflows"
  ],
  "quality_gates": {
    "targeted": [
      "python3 tools/quality_gate.py arch-lint",
      "python3 tools/quality_gate.py arch-tests"
    ],
    "required": [
      "git diff --check",
      "python3 tools/quality_gate.py quality"
    ]
  },
  "documentation": {
    "arc42": "documentation/arc42/05_analysis/arch-03-12-operation-results.md",
    "adr": "documentation/arc42/09_decisions/adr-explicit-operation-results.adoc"
  },
  "stop_conditions": [
    "Unaccepted architecture decision or unresolved inventory",
    "Scope or ownership mismatch",
    "Unsafe diagnostics or changed safety/exit semantics",
    "Failed required quality gate"
  ]
}
```

Done criteria: All requirements implemented and verified, full local quality PASS, six required evidence files consistent, independent audit PASS; no unresolved scope or compatibility correction.

Parallel execution eligibility: serial until Three Amigos proves disjoint inventory-derived scopes and stable contracts. Conflicting workflows: #313 siblings and all holders of listed locks. Shared files: common evidence/context and listed contracts. Shared infrastructure: none used. Requires isolated worktree: yes for execution/streams. Serialized live validation: yes if separately approved. Merge-order constraint: predecessor first. Parallelization status: NOT_SAFELY_PARALLELIZABLE by default.

Evidence: `.tiny-swarm/evidence/issue-355/`; record exact test names and results per requirement. Rollback: revert this slice commit only after checking dependent slices; no runtime rollback action.

## Parallel Execution

- Can this workflow run in parallel? Read-only reviews may; implementation chain is serial until an explicitly reviewed stream split.
- Conflicting workflows: ARCH-03 siblings touching installers, ports, lifecycle, adapters or composition; determine conflict from actual locks.
- Shared files: operation contract, result wrappers, CLI, evidence and context packs.
- Shared infrastructure: none for local tests.
- Requires isolated worktree: yes for future workflow execution; this authoring uses the verified dedicated branch in the current checkout.
- Requires serialized live validation: yes if later classified applicable and authorized.
- Merge-order constraints: follow the seven-slice chain; Codex integrates accepted stream results.

## Automatic Work Distribution Policy

Every workflow execute must inspect each slice for safe specialist streams, use
real Codex subagents where supported, or record explicit role-based fallback if
unavailable. Before implementation write `.codex/evidence/slice-<number>-distribution.md`;
after consolidation write `.codex/evidence/slice-<number>-consolidation.md`. Codex
remains final integration, test, evidence and publication owner.

| Stream | Owner |
|---|---|
| Backend | Senior Python Automation Developer |
| Frontend | Console/status UI reviewer; no browser frontend |
| Tests | Senior Tester |
| Runtime | Senior DevOps impact review; no live actions |
| Documentation | Senior Documentation Engineer |
| Quality | Senior Tester / Quality Gate Orchestrator |
| Architecture | Senior System Architect |
| Security | Senior Security Sandbox Engineer for failure redaction |

Do not parallelize overlapping files, unclear boundaries, contradictory requirements,
mandatory ordering, shared migrations, schema sequencing, generated-file conflicts,
unclear secrets handling, weakened guards or a Three Amigos not-safely-parallelizable
decision. Adapter test streams may split only after shared contracts stabilize and
exact files are disjoint. Shared evidence integration remains serial.

## Git Worktree Execution Rule

Use the declared workflow branch in an isolated execution worktree; verify clean
state and branch ownership before moving a checked-out branch. Do not create a
replacement workflow branch. Stream branches are
`architecture/workflow-355-operation-results-20260926-slice-<number>-<stream>` in separate worktrees. Workers never merge directly
to the workflow branch. Codex consolidates after review and tests. Recheck branch,
source baseline drift and locks before every write-capable assignment.

## Issue Completion Discipline

- Requirement matrix path: `.tiny-swarm/evidence/issue-355/requirement_matrix.md`, seeded from `documentation/workflow/requirement-matrix.md` in S355-01.
- Required evidence path: `.tiny-swarm/evidence/issue-355/`.
- Required evidence files: `requirement_matrix.md`, `implementation_summary.md`, `changed_files.md`, `test_results.md`, `remaining_risks.md`, `acceptance_checklist.md`.
- Requirement Lead review: verify all R355-01–15 and parent constraints at S355-01 and S355-07.
- System Architect Reviewer review: accept contract before product edits; review adapter ownership and final dependency integrity.
- Test / Evidence Reviewer review: every row has executed verification; skips and unavailable checks remain non-success.
- Issue Completion Auditor review: independent reviewer applies issue-completion-auditor in S355-07; implementer cannot be sole completion authority.
- DONE blocking rule: open or unverified requirements force INCOMPLETE, BLOCKED or FAILED. Authoring readiness never means issue implementation DONE.

## Quality-Gate Expectations

Use targeted tests above first, then full `python3 tools/quality_gate.py quality`
for every product slice. It runs verification-policy, lint, arch-lint, arch-tests,
typecheck and test. Manual tests require PYTHONPATH=src. New module tests become
executable only after their declared files exist. S355-01 is documentation-only;
run architecture checks and diff validation. Never weaken tests or guards.

Authoring validation: diff check, metadata/path/hash/link review and four-role review.
See authoring-review.md for executed commands and any justified quality skip.

## Documentation Synchronization and arc42 Check Status

CHECKED and updated with a PLANNED analysis and proposed ADR. Existing layer,
lifecycle, process, Classic update, live-consent and reporting documents remain
authoritative. S355-07 updates architecture runtime/building-block/concept records
to implemented facts and adds the accepted ADR to the index. Refresh affected
registry provenance hashes only; no registry/governance semantic changes.

## Stop Conditions and Uncertainty Escalation

Stop for branch mismatch, unrelated edits, stale governing hashes, lock conflicts,
missing paths/owners, scope gaps, unaccepted ADR, unsafe diagnostics, false partial
or rollback claims, changed safety/exit behavior, missing evidence or failed gates.
Typed Error Router: ARCH_VIOLATION -> Architect; TEST_FAILURE -> Tester and owner;
BUILD_FAILURE -> Python/DevOps; DOC_GOVERNANCE_FAILURE -> documentation/requirements;
LOCK_CONFLICT -> S3D orchestrator; UNKNOWN_FAILURE -> Root Architect.
Fix ordinary in-scope defects without weakening gates. Never call workflow create
backwards from workflow execute; reviewed scope amendments precede affected writes.

## Definition of Done

All fifteen requirements implemented, verified and independently audited; truthful
results in all four lifecycle families; expected boundary failures translated;
CLI/installer compatibility and redaction retained; full local quality PASS;
evidence complete and arc42 accurate. Live/external state remains separate.

## Commit and Push Plan

Workflow-create publication uses git-commit-preparation and message-preparation:
review only regenerated workflow files, planned analysis and proposed ADR, commit,
then push HEAD only to `origin/architecture/workflow-355-operation-results-20260926`. No PR, merge, force-push, branch deletion
or cleanup. Workflow-create-only push auto remains guarded. Later workflow execute
creates exactly one commit and branch checkpoint push per accepted slice.

## Handoff to workflow execute

Verify publication commit from Git and matching remote ref; check workflowVersion,
branch, clean state, all governing hashes, actual source/issue drift and S3/S3D locks.
Begin S355-01; do not skip the inventory/ADR decision. All implementation slices
remain NOT STARTED. Context packs are navigation aids, never authority. Final
publication SHA and remote verification are recorded in the authoring handoff;
resolve the commit containing this file rather than embedding a self-reference.

## S355-01 inventory scope amendment

The lifecycle inventory identifies additional existing file-storage, preflight, WSL
exposure/preparation and composition-helper boundaries. S355-03 metadata includes
the exact translation-only paths and tests. NEW file: tests/infrastructure/adapters/
file_management/test_local_file_storage.py. No new platform behavior is authorized.
Architecture review accepted the narrow additions; final inventory review records
Four-Role acceptance before any product edits. See lifecycle-failure-inventory.md.

## Execution progress

- S355-01 ACCEPTED: complete lifecycle inventory, concrete schema, reviewed scope amendments and accepted ADR. Four independent role reviews PASS; arch-tests 26 PASS; diff/path checks PASS. Product implementation starts in S355-02.
- Execution worktree: /mnt/d/Projects/Tiny-Swarm-World-worktrees/issue-355; workflow branch unchanged.
