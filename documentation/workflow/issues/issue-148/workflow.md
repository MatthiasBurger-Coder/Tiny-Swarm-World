# Workflow: Issue #148 — Lean Installer Bootstrap Probes

Workflow ID: `issue-148-20260809`

Workflow version: `issue-148-v1.0.0`

Status: `READY_FOR_WORKFLOW`

Authoring branch: `feature/workflow-issue-chain-163-156-197-152-144-146-147-148-145-151-153-20260809`

Source: [GitHub Issue #148](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/148)

## Executive Summary

Reduce redundant installer bootstrap file reads and subprocess probes while
preserving export parsing, required/optional failure behavior, deterministic
evidence and Linux/WSL scope. Bootstrap timing is measured separately from the
governed live workflow.

## Target Picture

One invocation-local parsed env representation feeds normalization and
duplicate checks. Related Git/worktree, identity/group and evidence-context
metadata probes are batched or reused where safe. Required probes fail loudly;
optional probes become `unknown`; no host identity or Git/group state is
persisted across runs.

## Clarification, Baseline and Scope

Upstream dependency: `I147-S06`. The named installer regions are verified in
`src/tiny_swarm_world/installer.py`; behavior is protected by
`tests/test_installer.py`. Requirements are in the [matrix](requirement-matrix.md).
Non-goals are governed live workflow changes, broad Windows behavior and
silent probe failures. Confidence 92%, `READY_FOR_WORKFLOW`.

## Shared #152 performance evidence handoff

Use `documentation/process/performance-evidence-contract.md` and write
consumer evidence below `.tiny-swarm/evidence/issue-148/`. The stable segment
ID is `installer-bootstrap`; record file-read, subprocess-probe and related
bootstrap-duration counters with explicit baseline/new comparison limits.
Bootstrap timing remains separate from governed live workflow timing, and
redacted safe context must be used.

## Ordered Slices

### Slice 01 — Bootstrap inventory and measurement plan

Purpose: map file scans, subprocess calls, data dependencies, required vs
optional probes and #152 bootstrap evidence segments.

```yaml
slice_id: I148-S01
profile: FULL_PATH
owner: Senior Requirement Engineer
secondary_reviewers: [Senior System Architect, Senior Python Automation Developer, Senior Tester]
affected_files: [src/tiny_swarm_world/installer.py, tests/test_installer.py]
affected_modules: [installer bootstrap]
affected_contracts: [probe inventory, env behavior, evidence boundaries]
dependencies: [I147-S06]
parallel_group: SERIAL-BASELINE
file_locks: [.tiny-swarm/evidence/issue-148/**]
contract_locks: [I148-bootstrap-inventory]
architecture_locks: [Linux/WSL-only-baseline]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: review deployment/bootstrap risk sections
  adr: none
stop_conditions: [unknown probe owner, governed workflow scope leakage, required/optional status unclear]
```

Done criteria: every issue-listed region and probe is mapped to S148-S02–S148-S06.

### Slice 02 — Single-pass env-file parsing and normalization

Purpose: eliminate repeated reads while preserving quoting, comments,
duplicates, empty values, whitespace and malformed-line behavior.

```yaml
slice_id: I148-S02
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Tester, Senior System Architect]
affected_files: [src/tiny_swarm_world/installer.py, tests/test_installer.py]
affected_modules: [installer env export parsing]
affected_contracts: [shell-export compatibility, invocation-local cache]
dependencies: [I148-S01]
parallel_group: SERIAL-ENV
file_locks: [src/tiny_swarm_world/installer.py, tests/test_installer.py]
contract_locks: [I148-env-parser]
architecture_locks: [no-persistent-host-state]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.test_installer]
  required: []
documentation:
  arc42: no change
  adr: none
stop_conditions: [quoted/comment behavior changes, duplicate detection lost, file read persists across runs]
```

Done criteria: parser/normalizer uses one representation and all legacy fixture
semantics remain covered.

### Slice 03 — Batch Git/worktree/ignore probes

Purpose: reduce separate Git/worktree/ignore subprocess calls without changing
branch detection or safety decisions.

```yaml
slice_id: I148-S03
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior System Architect, Senior Tester]
affected_files: [src/tiny_swarm_world/installer.py, tests/test_installer.py]
affected_modules: [installer Git/worktree checks]
affected_contracts: [probe call-count, failure classification, existing safety gate]
dependencies: [I148-S02]
parallel_group: SERIAL-PROBES
file_locks: [src/tiny_swarm_world/installer.py, tests/test_installer.py]
contract_locks: [I148-git-probes]
architecture_locks: [no-unsafe-worktree-bypass]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.test_installer]
  required: []
documentation:
  arc42: no change
  adr: none
stop_conditions: [required safety check bypassed, output semantics change, probe error hidden]
```

Done criteria: call count is reduced/batched with deterministic mocked tests;
required failures remain loud.

### Slice 04 — Batch identity/group probes

Purpose: coalesce `id -nG`, `id -un` and `getent group lxd` where safe while
preserving native Linux/WSL prerequisite classification.

```yaml
slice_id: I148-S04
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior System Architect, Senior Tester, Linux Host Preparation]
affected_files: [src/tiny_swarm_world/installer.py, tests/test_installer.py]
affected_modules: [native group/identity prerequisite probes]
affected_contracts: [required-vs-optional probe classification]
dependencies: [I148-S03]
parallel_group: SERIAL-PROBES
file_locks: [src/tiny_swarm_world/installer.py, tests/test_installer.py]
contract_locks: [I148-identity-probes]
architecture_locks: [Linux/WSL-only-no-new-Windows-mode]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.test_installer]
  required: []
documentation:
  arc42: review host prerequisite wording only if verified
  adr: none
stop_conditions: [membership state cached across runs, required probe degrades silently, host behavior broadened]
```

Done criteria: group/identity behavior and diagnostics remain compatible.

### Slice 05 — Coalesce evidence-context system probes

Purpose: reduce branch/revision/kernel metadata probe overhead while keeping
deterministic support evidence and redaction.

```yaml
slice_id: I148-S05
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior System Architect, Senior Tester]
affected_files: [src/tiny_swarm_world/installer.py, tests/test_installer.py]
affected_modules: [installer evidence context]
affected_contracts: [deterministic bootstrap evidence, optional unknown state]
dependencies: [I148-S04]
parallel_group: SERIAL-EVIDENCE
file_locks: [src/tiny_swarm_world/installer.py, tests/test_installer.py]
contract_locks: [I148-evidence-context]
architecture_locks: [redacted-local-evidence]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.test_installer]
  required: []
documentation:
  arc42: quality/evidence wording checked
  adr: none
stop_conditions: [nondeterministic evidence, raw sensitive output, required probe hidden]
```

Done criteria: metadata probes are reduced/batched and output remains stable.

### Slice 06 — Regression and bootstrap performance evidence

Purpose: cover normalization/probe behavior, required/optional failures and
record separate bootstrap timing evidence using #152.

```yaml
slice_id: I148-S06
profile: FULL_PATH
owner: Senior Tester
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Senior Python Automation Developer]
affected_files: [tests/test_installer.py, .tiny-swarm/evidence/issue-148/**]
affected_modules: [installer regression/performance tests]
affected_contracts: [REQ-148-02 through REQ-148-09]
dependencies: [I148-S05]
parallel_group: SERIAL-QUALITY
file_locks: [tests/test_installer.py, .tiny-swarm/evidence/issue-148/**]
contract_locks: [I148-quality-evidence]
architecture_locks: [no-live-installer-run]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.test_installer]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: final bootstrap evidence check
  adr: none
stop_conditions: [test fixture gap, timing treated as universal, live setup required, quality failure unclassified]
```

Done criteria: all parser/probe cases pass and bootstrap evidence is explicitly
separate from live workflow evidence.

### Slice 07 — Evidence package and independent completion audit

Purpose: audit all nine requirements and release #145.

```yaml
slice_id: I148-S07
profile: FULL_PATH
owner: Issue Completion Auditor
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Senior Tester]
affected_files: [.tiny-swarm/evidence/issue-148/**]
affected_modules: [issue completion evidence]
affected_contracts: [I148-completion-decision]
dependencies: [I148-S06]
parallel_group: SERIAL-AUDIT
file_locks: [.tiny-swarm/evidence/issue-148/**]
contract_locks: [I148-completion-decision]
architecture_locks: [auditor-independent-from-implementer]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: final reviewed status
  adr: final status
stop_conditions: [open requirement, probe behavior changed, persisted host state, missing evidence]
```

Done criteria: S07 is `PASS`; otherwise #145 is blocked.

## Dependency Graph

```text
I147-S06 -> I148-S01 -> I148-S02 -> I148-S03 -> I148-S04 -> I148-S05 -> I148-S06 -> I148-S07
```

## Parallel Execution

- Can this workflow run in parallel? No; parser and probe results share one
  invocation-local bootstrap contract.
- Conflicting workflows: installer/bootstrap, host preparation or Windows/WSL
  bridge workflows touching `installer.py`.
- Shared files: `installer.py`, `tests/test_installer.py` and #152 evidence.
- Shared infrastructure: mocked subprocesses only.
- Requires isolated worktree: yes for every slice.
- Requires serialized live validation: live installation is not applicable by default.
- Merge-order constraints: S07 precedes #145.

## Automatic Work Distribution Policy

Analyze backend/runtime/tests/docs/quality/architecture/security streams; use
subagents or explicit fallback with required distribution/consolidation
evidence. Never parallelize `installer.py` slices, generated evidence,
unclear required/optional semantics, secrets or safety checks. Codex integrates.

## Git Worktree Execution Rule

Every slice is isolated and lock-verified; workers do not run `install.sh` live
or merge directly.

## Issue Completion Discipline

- Requirement matrix path: `documentation/workflow/issues/issue-148/requirement-matrix.md`; execution copy `.tiny-swarm/evidence/issue-148/requirement_matrix.md`.
- Required evidence path: `.tiny-swarm/evidence/issue-148/`.
- Required evidence files: standard six plus probe inventory, call-count and bootstrap timing evidence.
- Requirement Lead review: S01/S07.
- System Architect Reviewer review: S01/S03/S04/S07.
- Test / Evidence Reviewer review: S06/S07.
- Issue Completion Auditor review: S07.
- DONE blocking rule: open or unverified requirements force `INCOMPLETE`, `BLOCKED` or `FAILED`.

## Quality-Gate Expectations

Use focused installer tests, full `python3 tools/quality_gate.py quality` and
`git diff --check`; no live install evidence is implied.

## Documentation Synchronization and Arc42 Check Status

Arc42 deployment/bootstrap and risk sections were reviewed. Update only
verified evidence/probe semantics; do not expand Windows-specific behavior.

## Stop Conditions and Uncertainty Escalation

Stop for parser compatibility drift, hidden required failures, persistent host
state, sensitive evidence or timing ambiguity. Escalate host semantics to
Linux Host Preparation/System Architect and tests to Senior Tester.

## Definition of Done

All nine requirements are covered, bootstrap behavior is preserved, evidence
is deterministic and S07 is `PASS`.

## Handoff to workflow execute

Promote #148 after I147-S06, execute S01–S07 serially, then start #145 only
after the independent audit passes.
