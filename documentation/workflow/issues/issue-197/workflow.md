# Workflow: Issue #197 — Extract WSL Socat Exposure Adapter

Workflow ID: `issue-197-20260809`

Workflow version: `issue-197-v1.0.0`

Status: `READY_FOR_WORKFLOW`

Authoring branch: `feature/workflow-issue-chain-163-156-197-152-144-146-147-148-145-151-153-20260809`

Source: [GitHub Issue #197](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/197)

## Executive Summary

Move WSL Socat process inspection and subprocess startup out of
`infrastructure/composition.py` into a focused infrastructure adapter/service.
Composition remains responsible for construction and wiring; all LiveConsent,
fail-closed and no-live-test behavior remains intact.

## Target Picture

The composition root contains no Socat `pgrep`, `sh`, `nohup` or subprocess
management. A focused adapter owns those details behind existing ports or a
verified infrastructure contract, while the exposed workflow step retains
stable result/evidence semantics and explicit live consent.

## Requirement Clarification Record

- Upstream dependency: `I156-S09` must be `PASS`.
- Requirements and acceptance criteria: [matrix](requirement-matrix.md).
- Change type: hexagonal infrastructure responsibility extraction.
- Assumptions: the existing network adapter package is the valid home; exact
  new module name is selected in S197-S02 after package/import inspection.
- Non-goals: domain/application subprocess calls, Socat behavior changes, live
  command execution, provider/bootstrap changes and new networking modes.
- Risks: composition wiring regressions, consent bypass, changed result order
  and tests that accidentally spawn real commands.
- Confidence: 93%; decision `READY_FOR_WORKFLOW`.

## Verified Baseline

The current composition module contains `_WslSocatExposeStep`, forwarding-plan
construction, process existence checks and command startup. Composition tests
cover native Linux no-op, consent absence, missing Socat and positive/negative
start outcomes. The target infrastructure adapter package exists, but the exact new
module is not yet present and must be selected by the architecture slice.

## Scope

In scope: adapter contract, extraction, composition wiring, exports/import
boundaries, mocked subprocess tests, local quality and issue evidence.

Non-goals: live Socat/LXC/Incus/Docker, application/domain changes, weakened
consent or broad composition refactoring.

## Python, Frontend and Resilience Assessment

- Python automation: `FULL_PATH`; infrastructure adapter and composition only.
- Frontend/browser: `NOT_APPLICABLE`.
- Console/status UI: `NOT_APPLICABLE`.
- Resilience: preserve process-exists/start failure classification, no-command
  fallback and fail-closed consent behavior.

## Ordered Slices

### Slice 01 — Freeze ownership matrix and tests

Purpose: map every current Socat helper, caller, result field, test and safety
guard; verify #156 handoff.

```yaml
slice_id: I197-S01
profile: FULL_PATH
owner: Senior Requirement Engineer
secondary_reviewers: [Senior System Architect, Senior Python Automation Developer, Senior Tester]
affected_files: [src/tiny_swarm_world/infrastructure/composition.py, tests/infrastructure/test_composition.py, src/tiny_swarm_world/application/services/network/socat/**, src/tiny_swarm_world/infrastructure/adapters/network/**]
affected_modules: [composition root, Socat manager, WSL exposure workflow]
affected_contracts: [composition-only-wiring, infrastructure-process-boundary, LiveConsent]
dependencies: [I156-S09]
parallel_group: SERIAL-BASELINE
file_locks: [.tiny-swarm/evidence/issue-197/**]
contract_locks: [I197-current-socat-contract]
architecture_locks: [no-domain-or-application-subprocess]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: review deployment/runtime responsibility sections
  adr: review existing composition/safety decisions
stop_conditions: [missing upstream audit, unknown caller, consent semantics not observable]
```

Done criteria: all six required behavior cases and all current helper calls are
mapped to S197-S02 through S197-S05.

### Slice 02 — Define the focused adapter boundary

Purpose: select a verified module path under `infrastructure/adapters/network`,
define typed inputs/results and keep command/process details out of the
composition root.

```yaml
slice_id: I197-S02
profile: FULL_PATH
owner: Senior System Architect
secondary_reviewers: [Senior Python Automation Developer, Senior Requirement Engineer, Senior Tester]
affected_files: [src/tiny_swarm_world/infrastructure/adapters/network/__init__.py, src/tiny_swarm_world/infrastructure/adapters/network/wsl_socat_exposure.py, src/tiny_swarm_world/application/ports/network/**, tests/architecture/test_hexagonal_imports.py]
affected_modules: [new WSL Socat infrastructure adapter, network ports]
affected_contracts: [forwarding plans, process-exists/start operations, safe result contract]
dependencies: [I197-S01]
parallel_group: SERIAL-CONTRACT
file_locks: [src/tiny_swarm_world/infrastructure/adapters/network/**, src/tiny_swarm_world/application/ports/network/**]
contract_locks: [I197-adapter-api]
architecture_locks: [domain-independent, application-no-subprocess]
quality_gates:
  targeted: [python3 tools/quality_gate.py arch-tests]
  required: []
documentation:
  arc42: record responsibility ownership if changed
  adr: stop if a durable new boundary needs an ADR
stop_conditions: [new path contradicts package boundaries, application imports subprocess, public contract unclear]
```

Done criteria: architecture reviewer approves the module/port boundary and
the adapter can be tested without live commands.

### Slice 03 — Extract process inspection and startup behavior

Purpose: move `pgrep`, `sh` and `nohup` behavior behind the adapter while
preserving command arguments, suppression, status and error semantics.

```yaml
slice_id: I197-S03
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior System Architect, Senior Tester]
affected_files: [src/tiny_swarm_world/infrastructure/adapters/network/wsl_socat_exposure.py, src/tiny_swarm_world/infrastructure/composition.py, tests/infrastructure/adapters/network/test_wsl_socat_exposure.py]
affected_modules: [WSL Socat adapter]
affected_contracts: [process inspection, start command, no-live default]
dependencies: [I197-S02]
parallel_group: SERIAL-IMPLEMENTATION
file_locks: [src/tiny_swarm_world/infrastructure/adapters/network/wsl_socat_exposure.py, src/tiny_swarm_world/infrastructure/composition.py]
contract_locks: [I197-adapter-api]
architecture_locks: [infrastructure-only-subprocess]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.network.test_wsl_socat_exposure]
  required: []
documentation:
  arc42: no change unless verified runtime ownership changes
  adr: none
stop_conditions: [real process starts in test, command semantics change, helper remains in composition]
```

Done criteria: the adapter owns process management; all subprocess calls are
mocked; failure and missing-tool behavior remain explicit.

### Slice 04 — Rewire composition and workflow exports

Purpose: keep `composition.py` as constructor/wiring root and route the expose
step through the extracted adapter without changing workflow ordering.

```yaml
slice_id: I197-S04
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior System Architect, Senior Tester]
affected_files: [src/tiny_swarm_world/infrastructure/composition.py, src/tiny_swarm_world/infrastructure/composition_lxc_runtimes.py, src/tiny_swarm_world/application/services/network/socat/socat_manager.py, tests/infrastructure/test_composition.py]
affected_modules: [composition services, platform expose workflow]
affected_contracts: [composition wiring, exposure-step result/evidence, workflow order]
dependencies: [I197-S03]
parallel_group: SERIAL-WIRING
file_locks: [src/tiny_swarm_world/infrastructure/composition.py, src/tiny_swarm_world/infrastructure/composition_lxc_runtimes.py, src/tiny_swarm_world/application/services/network/socat/**, tests/infrastructure/test_composition.py]
contract_locks: [I197-composed-expose-contract]
architecture_locks: [composition-constructs-only]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition]
  required: []
documentation:
  arc42: update only verified responsibility wording
  adr: preserve existing safety decisions
stop_conditions: [composition still owns process calls, workflow order changes, consent bypass]
```

Done criteria: composition contains no Socat process-management implementation,
the step still uses the service/adapter, and existing status/evidence shape is
preserved.

### Slice 05 — Safety, architecture and regression verification

Purpose: prove native Linux no-op, missing consent, missing Socat, existing
process, start success/failure and no-live command behavior.

```yaml
slice_id: I197-S05
profile: FULL_PATH
owner: Senior Tester
secondary_reviewers: [Senior System Architect, Senior Python Automation Developer, Senior Requirement Engineer]
affected_files: [tests/infrastructure/adapters/network/test_wsl_socat_exposure.py, tests/infrastructure/test_composition.py, tests/architecture/test_hexagonal_imports.py, .tiny-swarm/evidence/issue-197/test_results.md]
affected_modules: [adapter and composition regression tests]
affected_contracts: [REQ-197-03 through REQ-197-07]
dependencies: [I197-S04]
parallel_group: SERIAL-QUALITY
file_locks: [tests/infrastructure/adapters/network/**, tests/infrastructure/test_composition.py, tests/architecture/test_hexagonal_imports.py, .tiny-swarm/evidence/issue-197/**]
contract_locks: [I197-safety-regression]
architecture_locks: [mocked-live-boundary]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition, python3 tools/quality_gate.py arch-tests]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: final runtime/safety check
  adr: no change
stop_conditions: [live command observed, missing safety case, architecture test failure, unclassified quality failure]
```

Done criteria: all issue criteria have passing local evidence or explicit
blockers; no live command is run.

### Slice 06 — Evidence package and independent completion audit

Purpose: complete the required issue evidence and obtain the independent audit
before #152 starts.

```yaml
slice_id: I197-S06
profile: FULL_PATH
owner: Issue Completion Auditor
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Senior Tester]
affected_files: [.tiny-swarm/evidence/issue-197/**]
affected_modules: [issue completion evidence]
affected_contracts: [issue completion discipline, extracted adapter boundary]
dependencies: [I197-S05]
parallel_group: SERIAL-AUDIT
file_locks: [.tiny-swarm/evidence/issue-197/**]
contract_locks: [I197-completion-decision]
architecture_locks: [auditor-independent-from-implementer]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: final reviewed/no-change or verified update status
  adr: final status
stop_conditions: [open requirement, missing evidence, adapter ownership unresolved, unverified live claim]
```

Done criteria: auditor returns `PASS`, `INCOMPLETE` or `BLOCKED`; only `PASS`
releases #152.

## Dependency Graph

```text
I156-S09 -> I197-S01 -> I197-S02 -> I197-S03 -> I197-S04 -> I197-S05 -> I197-S06
```

## Parallel Execution

- Can this workflow run in parallel? No; extraction and composition wiring
  have mandatory ordering and overlapping architecture locks.
- Conflicting workflows: composition refactors, network/Socat workflows and
  any live exposure workflow.
- Shared files: composition root, exposure tests, network ports and evidence.
- Shared infrastructure: none; all commands are mocked/local.
- Requires isolated worktree: yes for every slice.
- Requires serialized live validation: live validation is forbidden by default.
- Merge-order constraints: S01–S06 serial; S06 precedes #152.

## Automatic Work Distribution Policy

The executor analyzes backend, frontend, tests, runtime, documentation,
quality, architecture and security streams, uses real subagents where
available or records role fallback, and requires distribution/consolidation
evidence. Backend/runtime streams may advise only within declared locks;
frontend is not applicable; architecture and security may veto unsafe
extraction. Codex owns consolidation.

## Git Worktree Execution Rule

Every slice uses an isolated worktree and verifies the declared workflow branch
and locks. Workers do not merge directly or execute live commands.

## Issue Completion Discipline

- Requirement matrix path: `documentation/workflow/issues/issue-197/requirement-matrix.md`; execution copy `.tiny-swarm/evidence/issue-197/requirement_matrix.md`.
- Required evidence path: `.tiny-swarm/evidence/issue-197/`.
- Required evidence files: standard six issue-completion files plus adapter ownership and safety test evidence.
- Requirement Lead review: S01 and S06.
- System Architect Reviewer review: S02/S04/S05 and S06.
- Test / Evidence Reviewer review: S05 and S06.
- Issue Completion Auditor review: S06.
- DONE blocking rule: open or unverified requirements force `INCOMPLETE`, `BLOCKED` or `FAILED`.

## Quality-Gate Expectations

Use focused composition/adapter/architecture tests, `python3 tools/quality_gate.py
quality` and `git diff --check` exactly as documented. No live success claim.

## Documentation Synchronization and Arc42 Check Status

Arc42 deployment/runtime responsibility and risks plus existing composition
decisions were reviewed. Update only verified responsibility drift; do not
create an ADR from a guessed module name.

## Stop Conditions and Uncertainty Escalation

Stop if ownership, port boundary, consent semantics, test isolation or module
path is unclear. Escalate architecture to the System Architect, requirements
to the Requirement Engineer and command/test failures to the Senior Tester.

## Definition of Done

All eight matrix rows are evidenced, composition is wiring-only, safety cases
pass, local quality is classified and S06 is `PASS`.

## Handoff to workflow execute

Promote #197 only after I156-S09. Execute S01–S06 serially and do not start
#152 before the independent audit returns `PASS`.
