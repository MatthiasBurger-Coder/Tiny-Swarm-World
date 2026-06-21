# Workflow: Console Output Issue 151 Remediation

Version: `console-output-issue-151-v1.0.0`
Workflow ID: `workflow-console-output-issue-151-20260621`
Created: `2026-06-21`
Branch: `fix/workflow-console-output-151-20260621`
Status: `EXECUTED_WITH_EVIDENCE`
Evidence Root: `.codex/evidence/workflow-console-output-issue-151-20260621/`

## Executive Summary

Validate issues `#143` and `#151` before implementation, prove whether either
is already fulfilled, then implement only the remaining console-output gap.
Issue `#143` is already implemented in the repository and is therefore out of
implementation scope. Issue `#151` remains open because the default CLI still
prints raw JSON workflow payloads to stdout.

## Requirement Clarification Gate

Original Request:

- Setze issue `143 / 151` gemaess `workflow execute with subagents` um.
- Beweise vor jeder Umsetzung, ob beide Issues bereits umgesetzt wurden.
- Wenn die Pruefung abgeschlossen ist, soll daraus ein Workflow mit eigenem
  Branch entstehen, um fehlende Implementierung umzusetzen.
- Verwende `@secret-inventory.json` als relevanten Nachweis fuer Secret-/Redaction-Risiken.

Interpreted Intent:

- Execute a guarded, evidence-backed fix workflow for installer and CLI console
  output, but only after proving the current implementation state of both
  issues.

Change Type:

- Product bug-fix workflow for Python CLI output, console UX, tests, workflow
  evidence, and documentation synchronization.

Affected Process Strand:

- `workflow execute`

Affected Architecture Area:

- Infrastructure UI adapters
- Python CLI entrypoint
- Product-behavior tests
- Workflow evidence

Explicit Requirements:

- Check issue `#143` implementation status first.
- Check issue `#151` implementation status first.
- Use subagents for the execute workflow where safe.
- Create a dedicated branch before write-capable work.
- Prove the final implementation with repository evidence and verification.

Implicit Requirements:

- Preserve hexagonal boundaries.
- Keep default console output human-readable.
- Keep machine-readable JSON available only when explicitly requested.
- Do not leak secrets or raw env payloads to stdout/stderr.
- Do not execute live infrastructure commands.

Assumptions:

- Issue `#151` remediation is limited to CLI/console presentation and tests.
- `@secret-inventory.json` is a risk/governance input, not an output target.

Non-Goals:

- No live install, reset, LXD/Incus/LXC, Docker Swarm, compose, or service
  bootstrap execution.
- No browser UI or curses UI work.
- No change to setup orchestration semantics.

Risks:

- Existing entrypoint tests currently assert JSON on stdout and must be updated
  together with the runtime behavior.
- Console summaries must not weaken failure visibility or evidence references.

Open Questions:

- None blocking.

Blocking Questions:

- None.

Confidence Level:

- `95%`

Decision:

- `READY_FOR_WORKFLOW`

## Five-Role Three Amigos Review

Senior Requirement Engineer:

- The request is concrete. Only issue `#151` requires implementation after the
  repository-state check.

Senior System Architect:

- The fix belongs in the CLI/infrastructure presentation surface. Domain and
  application behavior must remain unchanged.

Senior Python Automation Developer:

- The safest path is to gate JSON emission behind an explicit switch and update
  tests around the entrypoint output contract.

Senior React Frontend Developer:

- No browser frontend impact. N/A beyond confirming console-only scope.

Senior Tester:

- Regression coverage must prove that default stdout is human-readable and that
  explicit JSON mode still emits structured payloads.

## Verified Baseline

- Branch precheck before write-capable work started on `main` with a clean tree.
- Dedicated branch `fix/workflow-console-output-151-20260621` was created and
  verified before workflow mutation.
- Issue `#143` is already implemented:
  - `src/tiny_swarm_world/infrastructure/adapters/ui/progress_trace_ui.py`
  - `tests/infrastructure/adapters/ui/test_progress_trace_ui.py`
  - `documentation/user_guide/installer-console-output.md`
- Issue `#151` remains open:
  - `src/tiny_swarm_world/__main__.py` still prints raw JSON by default.
  - `tests/test_package_entrypoint.py` still expects JSON on stdout.
- Secret/redaction risk inventory reviewed:
  - `.tiny-swarm/evidence/secrets/secret-inventory.json`

## Execution Outcome

- Issue `#143` verified as already implemented.
- Issue `#151` implemented on this workflow branch.
- Targeted verification passed.
- Workflow-execute evidence written under
  `.codex/evidence/workflow-console-output-issue-151-20260621/`.
- Full repository-wide `quality_gate.py test` remains red on this Windows host
  for unrelated platform/repository reasons and is explicitly not claimed green.

## Target Outcome

- Default CLI stdout/stderr is line-based and human-readable.
- Raw JSON payloads are no longer printed by default.
- Explicit JSON/debug mode exists for deliberate machine-readable output.
- Tests prove both default human-readable behavior and explicit JSON behavior.
- Evidence documents that issue `#143` required no code changes and issue
  `#151` was remediated.

## Scope

In scope:

- `src/tiny_swarm_world/__main__.py`
- `tests/test_package_entrypoint.py`
- `documentation/workflow/**`
- optional user-guide synchronization if examples change materially

Out of scope:

- live installer runtime changes
- setup phase orchestration semantics
- infrastructure mutation

## Architecture Constraints

- Keep domain free of console formatting.
- Keep application services free of terminal-specific rendering.
- Keep CLI and reporter formatting in infrastructure/entrypoint surfaces.
- Do not print secret-bearing payloads or raw workflow dictionaries by default.

## Test Strategy

Targeted:

- `PYTHONPATH=src python -m unittest tests.test_package_entrypoint`
- `PYTHONPATH=src python -m unittest tests.infrastructure.adapters.ui.test_progress_trace_ui`

Required final:

- `python3 tools/quality_gate.py test`

## Ordered Slices

### Slice 01 - Status Proof And Workflow Evidence

Purpose:

- Record the repository-state proof for issues `#143` and `#151`.

```yaml
slice_id: "01"
profile: "NORMAL_PATH"
owner: "Senior Workflow Architect"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior Tester"
affected_files:
  - "documentation/workflow/workflow.md"
  - "documentation/workflow/context-pack.md"
  - "documentation/workflow/context-pack.json"
  - ".codex/evidence/workflow-console-output-issue-151-20260621/status-check.md"
affected_modules: []
affected_contracts:
  - "workflow evidence"
dependencies: []
parallel_group: "governance"
file_locks:
  - "documentation/workflow/**"
  - ".codex/evidence/workflow-console-output-issue-151-20260621/**"
contract_locks:
  - "issue status proof"
architecture_locks:
  - "hexagonal boundaries unchanged"
quality_gates:
  targeted:
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py test"
documentation:
  arc42: "No arc42 change expected."
  adr: "No ADR change expected."
stop_conditions:
  - "Stop if issue status cannot be proven from repository evidence."
```

### Slice 02 - Default Human Output And Explicit JSON Gate

Purpose:

- Remove default raw JSON emission from the CLI while preserving an explicit
  machine-readable path.

```yaml
slice_id: "02"
profile: "NORMAL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Tester"
  - "Senior System Architect"
affected_files:
  - "src/tiny_swarm_world/__main__.py"
  - "tests/test_package_entrypoint.py"
affected_modules:
  - "tiny_swarm_world.__main__"
affected_contracts:
  - "CLI stdout contract"
dependencies:
  - "01"
parallel_group: "implementation"
file_locks:
  - "src/tiny_swarm_world/__main__.py"
  - "tests/test_package_entrypoint.py"
contract_locks:
  - "default CLI output"
architecture_locks:
  - "console formatting remains outside domain/application"
quality_gates:
  targeted:
    - "PYTHONPATH=src python -m unittest tests.test_package_entrypoint"
  required:
    - "python3 tools/quality_gate.py test"
documentation:
  arc42: "N/A"
  adr: "Existing installer console reporting ADR remains valid."
stop_conditions:
  - "Stop if the fix requires application or domain changes."
  - "Stop if raw JSON remains on default stdout after tests."
```

### Slice 03 - Final Verification And Consolidation Evidence

Purpose:

- Execute focused verification and prove the final state.

```yaml
slice_id: "03"
profile: "NORMAL_PATH"
owner: "Senior Tester"
secondary_reviewers:
  - "Senior Workflow Architect"
affected_files:
  - ".codex/evidence/workflow-console-output-issue-151-20260621/slice-02-distribution.md"
  - ".codex/evidence/workflow-console-output-issue-151-20260621/slice-02-consolidation.md"
affected_modules: []
affected_contracts:
  - "verification evidence"
dependencies:
  - "02"
parallel_group: "verification"
file_locks:
  - ".codex/evidence/workflow-console-output-issue-151-20260621/**"
contract_locks:
  - "verification proof"
architecture_locks: []
quality_gates:
  targeted:
    - "PYTHONPATH=src python -m unittest tests.test_package_entrypoint"
    - "PYTHONPATH=src python -m unittest tests.infrastructure.adapters.ui.test_progress_trace_ui"
  required:
    - "python3 tools/quality_gate.py test"
documentation:
  arc42: "N/A"
  adr: "N/A"
stop_conditions:
  - "Stop if the chosen Python executable cannot run the targeted tests."
```

## Automatic Work Distribution Policy

- Slice `02` is safe for parallel analysis only.
- Real subagents are used for the initial issue-state proof.
- Final code edits stay sequential because `src/tiny_swarm_world/__main__.py`
  and `tests/test_package_entrypoint.py` are tightly coupled.

## Definition Of Done

- Issue `#143` proven already implemented from repository evidence.
- Issue `#151` default JSON emission removed from normal CLI output.
- Explicit JSON mode available and covered by tests.
- Evidence files written under the workflow evidence root.

## Handoff To Workflow Execute

- Execute slices in order `01 -> 02 -> 03`.
- Do not invoke live infrastructure commands.
