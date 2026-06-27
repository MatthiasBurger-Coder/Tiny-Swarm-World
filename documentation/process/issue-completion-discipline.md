# Issue Completion Discipline

Tiny Swarm World skills are execution gates, not advisory expert personas. A
skill may contribute implementation work, review work or governance decisions,
but an issue is complete only when every requirement is implemented, verified
and evidenced.

This discipline applies to issue-driven work, `workflow execute`, slice
execution, implementation skills, reviewer skills and completion audits.

## Mandatory Completion Loop

```text
Issue
  -> Requirement Lead extracts a requirement matrix
  -> System Architect Reviewer validates architecture fit
  -> Implementation Agent implements the complete mapped scope
  -> Test / Evidence Reviewer verifies every requirement
  -> Issue Completion Auditor decides PASS, INCOMPLETE, BLOCKED or REJECTED
```

The implementer does not decide alone that the issue is done. The final
completion decision must be made from the requirement matrix, changed files,
tests, evidence and documented risks.

## Required First Step: Issue Decomposition

Before implementation, create a requirement matrix:

| ID | Requirement from issue | Type | Files likely affected | Implementation evidence | Test evidence | Status |
|----|------------------------|------|------------------------|--------------------------|---------------|--------|

Rules:

- Every sentence that describes expected behavior must become a requirement.
- Every bullet point in the issue must become at least one requirement.
- Every mentioned file, service, port, command, workflow or evidence path must
  be considered.
- If a requirement is ambiguous, mark it `BLOCKED` instead of guessing
  silently.
- Implementation may not start before the matrix exists.
- Requirement IDs must be stable for the branch or workflow slice.

## Definition of Done

An issue, workflow slice or skill task may be marked `DONE` only when:

1. All requirements from the issue or slice were explicitly extracted.
2. Every requirement has implementation evidence.
3. Every requirement has at least one test, check or evidence artifact.
4. No acceptance criterion is open, implicitly ignored or partially
   implemented.
5. The change was locally validated with the relevant `QUALITY.md` command or
   a documented narrower gate.
6. Evidence was created under the intended workflow or issue evidence path.
7. Non-implemented or unverifiable points are reported as blockers, not hidden.

If any requirement is open or unverified, the status must not be `DONE`.

## No Silent Scope Reduction

The scope must not be reduced silently.

If a requirement cannot be implemented because information is missing, existing
architecture is unclear, tests fail, dependencies are unavailable, the change
would be too large, or the issue conflicts with existing code, stop and report
`BLOCKED` with exact reasons.

Do not:

- implement only the easy parts;
- leave TODOs as a substitute for implementation;
- claim success when only scaffolding was added;
- skip tests because they are inconvenient;
- ignore evidence requirements;
- change unrelated behavior to make checks pass.

## Evidence Requirements

For every completed issue or workflow slice, create evidence under:

```text
.tiny-swarm/evidence/<workflow-or-issue-id>/
```

Required files:

- `requirement_matrix.md`
- `implementation_summary.md`
- `changed_files.md`
- `test_results.md`
- `remaining_risks.md`
- `acceptance_checklist.md`

The issue is not `DONE` unless all required evidence files exist and are
consistent with the implemented changes. If no evidence was created, the
implementation status is `FAILED` even if code was changed.

For workflow slices that already require `.codex/evidence/**`, keep that slice
evidence and also maintain the issue-level `.tiny-swarm/evidence/**` package
when the work is issue-driven.

## Acceptance Verification

For each requirement, provide one of:

- automated test name;
- command output;
- static validation;
- config diff;
- created evidence file;
- manual verification step with result.

A requirement without verification remains `OPEN`. A workflow with `OPEN`
requirements must not be marked `DONE`.

## Three Amigos Completion Gate

Before `DONE`, the implementation must pass three independent perspectives:

| Perspective | Required decision |
|---|---|
| Requirement Lead | Confirms every issue requirement is captured and no hidden requirement was ignored. |
| System Architect Reviewer | Confirms the solution fits hexagonal architecture, provider model, reconciliation and workflow design without local hacks. |
| Test / Evidence Reviewer | Confirms every requirement has test or evidence and quality gates were not bypassed. |

If one perspective fails, the issue is `INCOMPLETE` or `BLOCKED`, not `DONE`.

## Stop Conditions

Stop and report `BLOCKED` when:

- issue requirements contradict current architecture;
- required files or modules are missing;
- existing tests fail before the change and impact cannot be isolated;
- required runtime checks cannot be executed;
- the evidence path is unclear;
- the issue needs a design decision not present in the issue;
- implementation would require disabling guards or validations.

Do not stop for ordinary implementation errors. Fix compile errors, test
failures and lint findings inside the branch when the fix is in scope and does
not weaken guards.

## No Scaffolding-Only Completion

Creating interfaces, empty classes, TODOs, placeholder implementations, config
stubs or documentation is not sufficient.

If scaffolding is created, it must be connected to executable behavior and
verified by tests or evidence. A branch that only prepares structure without
implementing behavior is `INCOMPLETE` unless the issue explicitly asks only for
scaffolding.

## Status Rules

Use `DONE` only if all requirements are implemented and verified.

Use `INCOMPLETE` if implementation exists but one or more requirements are
missing or unverified.

Use `BLOCKED` if external information, environment, permissions or architecture
decisions prevent completion.

Use `FAILED` if attempted changes break existing behavior or validation.

The `issue-completion-auditor` skill maps these implementation statuses to
audit outcomes:

- `PASS` for fully complete, verified work;
- `INCOMPLETE` for missing implementation, missing verification or open
  requirements;
- `BLOCKED` for true external, architectural or requirement blockers;
- `REJECTED` for scope reduction, TODO-as-implementation, scaffolding-only
  completion, unrelated behavior changes or bypassed gates.

## Final Completion Report

Every issue-driven skill result must include:

```md
## Final Completion Report

Status: DONE | INCOMPLETE | BLOCKED | FAILED

Issue:
- <issue id/title>

Requirement matrix:
- REQ-001: ...
- REQ-002: ...

Implemented requirements:
- REQ-001: ...
- REQ-002: ...

Verified requirements:
- REQ-001: verified by ...
- REQ-002: verified by ...

Open requirements:
- none

Changed files:
- ...

Tests / checks executed:
- command: ...
  result: PASS/FAIL

Evidence:
- .tiny-swarm/evidence/.../requirement_matrix.md
- .tiny-swarm/evidence/.../test_results.md

Risks:
- ...

Decision:
- The issue is fully complete because ...
```

If `Open requirements` is not empty, `Status` must not be `DONE`.
