# Workflow: SonarCloud S3415 assertion order repair

Version: `workflow-sonar-s3415-v1.0.0`
Workflow ID: `workflow-sonar-s3415-20260718`
Branch: `fix/workflow-sonar-s3415-20260718`
Baseline: `main@e91ca5824e823fbd2ae547c23080e8847ef55ccb`
Status: `READY_FOR_EXECUTION`

## Executive Summary

Repair every current SonarCloud `python:S3415` finding: unittest assertions
must pass the actual value before the expected value. The 18 July 2026
SonarCloud profile update reports 1,580 such findings, all in `tests/`.

## Requirement Clarification Gate

| Field | Decision |
|---|---|
| Original request | Fix all 1,580 `python:S3415` findings. |
| Interpreted intent | Correct only the ordered assertion arguments reported by SonarCloud. |
| Change type | Test-maintenance repair. |
| Explicit requirement | Every current S3415 issue is removed without changing assertion semantics. |
| Non-goals | Product code, quality-profile changes, suppressions, test exclusions, live infrastructure, unrelated Sonar rules. |
| Risks | A blind textual swap can alter a non-reported assertion or a multi-line call. |
| Decision | `READY_FOR_WORKFLOW` — use Sonar issue locations plus Python AST positions. |

## Target Picture

- The queried S3415 count is zero after the next SonarCloud analysis.
- Every altered assertion preserves its compared expressions and message.
- No source module or runtime configuration is changed.

## Scope and Architecture

Only test assertion-call argument order changes. Hexagonal production boundaries,
public behavior, live-infrastructure safety, and arc42 architecture are
unaffected; no arc42 or ADR update is required.

## Test Strategy

1. Fetch all current S3415 issues from the public SonarCloud API.
2. Map each issue's Expected/Actual flow locations to AST call arguments.
3. Produce and review a unified patch; apply only that patch.
4. Run the changed test modules, `python3 tools/quality_gate.py quality`, and
   `git diff --check` through WSL.
5. Re-query SonarCloud after CI uploads the branch analysis; local verification
   cannot claim the remote count is zero before that upload.

## Ordered Slices

### Slice 01: Deterministic S3415 repair

```yaml
slice_id: "01"
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers:
  - Senior Requirement Engineer
  - Senior System Architect
  - Senior Tester
affected_files:
  - tests/**/*.py (only files named by current SonarCloud python:S3415 issues)
  - documentation/workflow/**
affected_modules: []
affected_contracts:
  - unittest actual-before-expected assertion convention
dependencies: []
parallel_group: serial-01
file_locks:
  - tests/**/*.py
  - documentation/workflow/**
contract_locks:
  - assertion expressions and optional messages must be preserved
architecture_locks:
  - no changes outside tests and workflow evidence
quality_gates:
  targeted:
    - changed unittest modules
    - git diff --check
  required:
    - python3 tools/quality_gate.py quality
    - SonarCloud branch analysis
documentation:
  arc42: not required; no architecture or runtime behavior changes
  adr: not required
stop_conditions:
  - a Sonar location cannot be mapped unambiguously to two assertion arguments
  - an edit changes an assertion expression, message, or non-test file
  - a required local gate fails
```

## Parallel Execution

- Can this workflow run in parallel? No. The same test files may contain
  several findings and require one consolidated deterministic patch.
- Requires isolated worktree: yes.
- Requires serialized live validation: no live validation is allowed.
- Merge-order constraint: the branch analysis follows the local quality gate.

## Automatic Work Distribution Policy

The slice is not safely divisible by file because issue-location mapping and a
single generated patch share every test file. Codex performs the required
role-based requirement, architecture, and test review in this worktree; no
parallel stream is assigned.

## Git Worktree Execution Rule

Only `fix/workflow-sonar-s3415-20260718` may be changed. Codex remains the
integration owner and must run required checks before declaring the slice done.

## Definition of Done

- All API-returned S3415 issue locations were either repaired or explicitly
  reported as unmappable.
- The reviewed patch changes only the two targeted arguments in test calls.
- Targeted tests, full local quality, and diff check pass.
- SonarCloud branch analysis confirms no open S3415 findings.
