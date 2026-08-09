# Workflow: Issue #151 — Line-Based Console Summaries Without Raw JSON

Workflow ID: `issue-151-20260809`

Workflow version: `issue-151-v1.0.0`

Status: `READY_FOR_WORKFLOW`

Authoring branch: `feature/workflow-issue-chain-163-156-197-152-144-146-147-148-145-151-153-20260809`

Source: [GitHub Issue #151](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/151)

## Executive Summary

Ensure normal installer/setup/reset/deployment output is concise, line-based
and human-readable rather than raw JSON, while preserving structured evidence
and an explicit `--json`/`TSW_DEBUG_JSON` mode.

## Target Picture

Default stdout shows workflow/phase/status, important counts, final status,
recovery guidance and evidence directory without object dumps. Structured
results remain persisted where required and are emitted only through explicit
machine-readable/debug mode. Output remains deterministic across Linux/WSL and
LXC-native paths.

## Clarification, Baseline and Scope

Upstream dependency: `I145-S07`. The current CLI already has summary and JSON
branches, while installer/reporting paths require an inventory to locate the
observed raw dumps. Requirements are in the [matrix](requirement-matrix.md).
Console/status UI review is mandatory; browser React is forbidden. Confidence
92%, `READY_FOR_WORKFLOW`.

## Ordered Slices

### Slice 01 — Inventory stdout and structured-output paths

Purpose: trace all normal install/reset/update/setup result emission and classify
human, evidence and explicit JSON channels.

```yaml
slice_id: I151-S01
profile: FULL_PATH
owner: Senior Requirement Engineer
secondary_reviewers: [Console/status UI Developer, Senior System Architect, Senior Python Automation Developer, Senior Tester]
affected_files: [src/tiny_swarm_world/__main__.py, src/tiny_swarm_world/installer.py, src/tiny_swarm_world/infrastructure/adapters/ui/install_reporter.py, src/tiny_swarm_world/infrastructure/adapters/ui/progress_trace_ui.py, tests/test_package_entrypoint.py, tests/test_installer.py]
affected_modules: [CLI output, installer reporter, progress UI]
affected_contracts: [default stdout, debug JSON, evidence persistence]
dependencies: [I145-S07]
parallel_group: SERIAL-BASELINE
file_locks: [.tiny-swarm/evidence/issue-151/**]
contract_locks: [I151-output-inventory]
architecture_locks: [console-adapter-boundary]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: review installer console reporting ADR
  adr: preserve adr-installer-console-reporting-policy
stop_conditions: [output source/freshness unclear, structured evidence would be lost, issue behavior contradicted by source]
```

Done criteria: every raw/default JSON path and required summary field is mapped.

### Slice 02 — Implement deterministic summary formatter

Purpose: create or extend a dedicated formatter for workflow/phase/status,
counts, final state, evidence path and redacted recovery hints.

```yaml
slice_id: I151-S02
profile: FULL_PATH
owner: Console/status UI Developer
secondary_reviewers: [Senior Python Automation Developer, Senior Tester, Senior System Architect]
affected_files: [src/tiny_swarm_world/__main__.py, src/tiny_swarm_world/infrastructure/adapters/ui/install_reporter.py, tests/test_package_entrypoint.py]
affected_modules: [line-based console summary]
affected_contracts: [human-readable default output, deterministic formatting]
dependencies: [I151-S01]
parallel_group: SERIAL-FORMATTER
file_locks: [src/tiny_swarm_world/__main__.py, src/tiny_swarm_world/infrastructure/adapters/ui/install_reporter.py, tests/test_package_entrypoint.py]
contract_locks: [I151-summary-format]
architecture_locks: [UI-adapter-only]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.test_package_entrypoint]
  required: []
documentation:
  arc42: console reporting contract review
  adr: preserve existing console ADR
stop_conditions: [raw nested object emitted, important error/evidence hidden, nondeterministic output]
```

Done criteria: formatter returns stable line tuples and retains important
operator information without credentials/raw payloads.

### Slice 03 — Integrate default CLI and installer paths

Purpose: route normal `./install.sh`, `--confirm-reset`, `--update` and setup
flows through summaries while preserving exit codes and log/evidence files.

```yaml
slice_id: I151-S03
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Console/status UI Developer, Senior Tester, Senior System Architect]
affected_files: [src/tiny_swarm_world/__main__.py, src/tiny_swarm_world/installer.py, src/tiny_swarm_world/infrastructure/adapters/ui/install_reporter.py, tests/test_package_entrypoint.py, tests/test_installer.py]
affected_modules: [default CLI/installer reporting]
affected_contracts: [no raw JSON default, preserved exit/evidence semantics]
dependencies: [I151-S02]
parallel_group: SERIAL-INTEGRATION
file_locks: [src/tiny_swarm_world/__main__.py, src/tiny_swarm_world/installer.py, src/tiny_swarm_world/infrastructure/adapters/ui/install_reporter.py, tests/test_package_entrypoint.py, tests/test_installer.py]
contract_locks: [I151-default-output]
architecture_locks: [installer-evidence-preserved]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.test_package_entrypoint]
  required: []
documentation:
  arc42: no runtime architecture change expected
  adr: preserve console policy
stop_conditions: [exit code changes, evidence/log lost, normal path still dumps JSON]
```

Done criteria: normal output is summary-only and default behavior works in
deterministic mocked CLI/installer fixtures.

### Slice 04 — Preserve explicit debug/machine-readable JSON

Purpose: ensure `--json` and `TSW_DEBUG_JSON=true` remain explicit opt-ins and
structured data remains persisted to evidence/logs.

```yaml
slice_id: I151-S04
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Console/status UI Developer, Senior Tester]
affected_files: [src/tiny_swarm_world/__main__.py, src/tiny_swarm_world/installer.py, src/tiny_swarm_world/application/services/setup/workflow.py, tests/test_package_entrypoint.py, tests/application/services/setup/test_setup_workflow.py]
affected_modules: [debug JSON and evidence persistence]
affected_contracts: [explicit JSON flag/env, persisted structured result]
dependencies: [I151-S03]
parallel_group: SERIAL-DEBUG-MODE
file_locks: [src/tiny_swarm_world/__main__.py, src/tiny_swarm_world/installer.py, src/tiny_swarm_world/application/services/setup/workflow.py, tests/**]
contract_locks: [I151-json-opt-in]
architecture_locks: [no-default-json-regression]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.test_package_entrypoint]
  required: []
documentation:
  arc42: evidence/console distinction review
  adr: preserve existing policy
stop_conditions: [JSON becomes default, evidence persistence removed, raw secret output]
```

Done criteria: opt-in JSON is tested and default output remains clean.

### Slice 05 — Error, recovery and evidence summary behavior

Purpose: retain failed/blocked/timed-out guidance, important counts and
evidence paths without dumping nested raw result objects.

```yaml
slice_id: I151-S05
profile: FULL_PATH
owner: Console/status UI Developer
secondary_reviewers: [Senior Tester, Senior Python Automation Developer, Senior System Architect]
affected_files: [src/tiny_swarm_world/infrastructure/adapters/ui/install_reporter.py, src/tiny_swarm_world/__main__.py, src/tiny_swarm_world/installer.py, tests/test_package_entrypoint.py, tests/test_installer.py]
affected_modules: [failure/recovery console output]
affected_contracts: [operator action, failure status, evidence path]
dependencies: [I151-S04]
parallel_group: SERIAL-ERRORS
file_locks: [src/tiny_swarm_world/infrastructure/adapters/ui/install_reporter.py, src/tiny_swarm_world/__main__.py, src/tiny_swarm_world/installer.py, tests/test_package_entrypoint.py, tests/test_installer.py]
contract_locks: [I151-error-summary]
architecture_locks: [redaction-and-evidence]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.test_installer]
  required: []
documentation:
  arc42: console quality review
  adr: preserve recovery reporting policy
stop_conditions: [failure hidden, recovery action omitted, sensitive raw evidence printed]
```

Done criteria: error fixtures show actionable summaries and no raw JSON blocks.

### Slice 06 — Cross-platform tests and documentation/ADR review

Purpose: test successful setup/reset output, important fields, no raw JSON,
explicit JSON mode and Linux/WSL/LXC-native compatibility; synchronize the
existing console output guide/ADR only from verified behavior.

```yaml
slice_id: I151-S06
profile: FULL_PATH
owner: Senior Tester
secondary_reviewers: [Console/status UI Developer, Senior Documentation Engineer, Senior System Architect]
affected_files: [tests/test_package_entrypoint.py, tests/test_installer.py, tests/infrastructure/adapters/ui/test_progress_trace_ui.py, documentation/user_guide/installer-console-output.md, documentation/arc42/09_decisions/adr-installer-console-reporting-policy.adoc]
affected_modules: [console regression suite and docs]
affected_contracts: [default summary, debug JSON, cross-platform wording]
dependencies: [I151-S05]
parallel_group: SERIAL-QUALITY
file_locks: [tests/**, documentation/user_guide/installer-console-output.md, documentation/arc42/09_decisions/adr-installer-console-reporting-policy.adoc]
contract_locks: [I151-tested-output]
architecture_locks: [no-browser-react]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.test_package_entrypoint]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: synchronize only verified console behavior
  adr: update consequence only if source behavior changed
stop_conditions: [live install required, docs contradict tests, cross-platform path unverified, quality failure unclassified]
```

Done criteria: all eight matrix rows have tests/docs/evidence and local gate
state is exact.

### Slice 07 — Evidence package and independent completion audit

Purpose: audit the UX, evidence, compatibility and safety requirements before
the final handbook issue.

```yaml
slice_id: I151-S07
profile: FULL_PATH
owner: Issue Completion Auditor
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Senior Tester, Console/status UI Developer]
affected_files: [.tiny-swarm/evidence/issue-151/**]
affected_modules: [issue completion evidence]
affected_contracts: [I151-completion-decision]
dependencies: [I151-S06]
parallel_group: SERIAL-AUDIT
file_locks: [.tiny-swarm/evidence/issue-151/**]
contract_locks: [I151-completion-decision]
architecture_locks: [auditor-independent-from-implementer]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: final reviewed status
  adr: final status
stop_conditions: [raw JSON default, missing evidence, hidden error, unverified live claim]
```

Done criteria: S07 is `PASS`; only then #153 may start.

## Dependency Graph

```text
I145-S07 -> I151-S01 -> I151-S02 -> I151-S03 -> I151-S04 -> I151-S05 -> I151-S06 -> I151-S07
```

## Parallel Execution

- Can this workflow run in parallel? No; all slices share output contracts and
  console files.
- Conflicting workflows: console/status, installer, setup orchestration and
  observability changes touching the same output paths.
- Shared files: `__main__.py`, `installer.py`, reporters, CLI tests and ADR.
- Shared infrastructure: none by default; live install not run.
- Requires isolated worktree: yes for every slice.
- Requires serialized live validation: live installation is opt-in and serialized.
- Merge-order constraints: S07 precedes #153.

## Automatic Work Distribution Policy

Analyze backend/frontend/tests/runtime/docs/quality/architecture/security and
Console streams; frontend means terminal only and browser React is forbidden.
Use subagents or explicit fallback, distribution/consolidation evidence, and
Codex final integration. Do not parallelize shared formatters, generated
output, secrets, unclear output ownership or weakened diagnostics.

## Git Worktree Execution Rule

Every slice is isolated and lock-verified; workers do not merge directly or run
live installation commands.

## Issue Completion Discipline

- Requirement matrix path: `documentation/workflow/issues/issue-151/requirement-matrix.md`; execution copy `.tiny-swarm/evidence/issue-151/requirement_matrix.md`.
- Required evidence path: `.tiny-swarm/evidence/issue-151/`.
- Required evidence files: standard six plus stdout inventory, renderer fixtures, JSON opt-in and error-output evidence.
- Requirement Lead review: S01/S07.
- System Architect Reviewer review: S01/S03/S06/S07.
- Test / Evidence Reviewer review: S06/S07.
- Issue Completion Auditor review: S07.
- DONE blocking rule: open or unverified requirements force `INCOMPLETE`, `BLOCKED` or `FAILED`.

## Quality-Gate Expectations

Use CLI/installer/reporter tests, full `python3 tools/quality_gate.py quality`
and `git diff --check`. No live installation claim is implied.

## Documentation Synchronization and Arc42 Check Status

The existing installer console reporting ADR and user guide were reviewed.
Update only verified output behavior and preserve the default local/live
evidence distinction.

## Stop Conditions and Uncertainty Escalation

Stop for unclear output source, lost evidence, hidden errors, raw sensitive
payloads or missing terminal compatibility. Escalate to Console reviewer,
System Architect and Senior Tester.

## Definition of Done

All eight requirements are implemented/tested/evidenced, default stdout is
human-readable, debug JSON remains explicit and S07 is `PASS`.

## Handoff to workflow execute

Promote #151 after I145-S07, execute S01–S07 serially and begin #153 only
after the independent audit passes.

