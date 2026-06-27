---
name: issue-completion-auditor
description: "Use after issue or workflow implementation to audit whether the branch fully satisfies the issue requirements, acceptance criteria, tests, evidence, documentation and completion discipline before any DONE claim."
---

# Skill: Issue Completion Auditor

## Mission

Verify whether a branch fully satisfies a GitHub issue, workflow issue or
issue-driven implementation request.

This skill is an audit gate. It does not implement code, repair tests or
approve its own implementation work.

## Required References

Read before auditing:

1. Root `AGENTS.md`.
2. Root `QUALITY.md`.
3. `documentation/process/issue-completion-discipline.md`.
4. The complete issue, workflow slice or user request under audit.
5. The requirement matrix for the issue or slice.
6. Changed files in the branch.
7. Test and quality-gate evidence.
8. Documentation and evidence files referenced by the issue.

## Audit Inputs

Compare:

- issue requirements and acceptance criteria;
- requirement matrix;
- changed files;
- tests and checks;
- evidence under `.tiny-swarm/evidence/<workflow-or-issue-id>/`;
- workflow evidence under `.codex/evidence/**` when applicable;
- documentation updates;
- architecture and safety rules from `AGENTS.md`;
- quality commands and failure policy from `QUALITY.md`.

## Audit Procedure

1. Confirm the branch is not `main`, `master`, `develop` or another shared
   branch for write-capable completion work.
2. Read the complete issue or workflow slice.
3. Verify that every explicit and implicit issue requirement is present in the
   requirement matrix.
4. Map every requirement to changed code, config, documentation or declared
   non-code evidence.
5. Map every requirement to a test, check, static validation, config diff,
   evidence file or manual verification result.
6. Verify that required evidence files exist:
   - `requirement_matrix.md`
   - `implementation_summary.md`
   - `changed_files.md`
   - `test_results.md`
   - `remaining_risks.md`
   - `acceptance_checklist.md`
7. Check for TODO-as-implementation, scaffolding-only completion, hidden scope
   reduction and unrelated behavior changes.
8. Verify that local validation was executed or that a documented blocker
   explains why it could not run.
9. Produce a final audit decision.

## Definition of Done

The audit may return `PASS` only when:

1. All requirements from the issue or workflow slice were explicitly
   extracted.
2. Every requirement has implementation evidence.
3. Every requirement has at least one relevant test, check or evidence
   artifact.
4. No acceptance criterion is open, silently ignored or partially implemented.
5. The change was locally validated with the relevant `QUALITY.md` gate or an
   explicitly justified narrower command.
6. Required evidence exists under the intended workflow or issue evidence path.
7. Non-implemented or unverifiable points are reported as blockers.

If any requirement is open or unverified, the audit result must not be `PASS`.

## No Silent Scope Reduction

Fail the audit when the branch:

- implements only the easy parts;
- leaves TODOs, placeholders or stubs as substitutes for required behavior;
- claims success with scaffolding only;
- skips tests or evidence without a recorded blocker;
- ignores acceptance criteria;
- changes unrelated behavior to make checks pass;
- bypasses architecture, safety or quality gates.

## Three Amigos Completion Review

Before a `PASS` decision, confirm the evidence includes three perspectives:

| Perspective | Required confirmation |
|---|---|
| Requirement Lead | Every issue requirement is captured and no hidden requirement was ignored. |
| System Architect Reviewer | The solution fits hexagonal architecture, provider model, reconciliation and workflow design without shortcuts or local hacks. |
| Test / Evidence Reviewer | Every requirement has test or evidence and quality gates were not bypassed. |

If one perspective fails or is missing without a justified blocker, return
`INCOMPLETE` or `BLOCKED`.

## Decision Contract

Return exactly one:

```text
PASS
INCOMPLETE
BLOCKED
REJECTED
```

Use `PASS` only for fully complete, verified and evidenced work.

Use `INCOMPLETE` when implementation exists but any requirement, test,
documentation update, validation command or evidence file is missing.

Use `BLOCKED` when external information, environment, permissions or an
architecture decision prevents completion and the blocker is explicit.

Use `REJECTED` when the branch silently reduced scope, used TODOs or
scaffolding as completion, changed unrelated behavior, bypassed gates, or
cannot map acceptance criteria to implementation.

## Stop Conditions

Stop and return `BLOCKED` when:

- the issue, workflow slice or acceptance criteria cannot be read completely;
- the requirement matrix is missing;
- the evidence path is unclear;
- changed files cannot be inspected;
- quality-gate authority is unclear;
- architecture ownership or source of truth would require guessing;
- the audit would require running live infrastructure commands without
  explicit approval.

## Required Final Report

```md
## Issue Completion Audit

Decision: PASS | INCOMPLETE | BLOCKED | REJECTED

Issue:
- <issue id/title>

Requirement matrix:
- REQ-001: ...
- REQ-002: ...

Implemented requirements:
- REQ-001: ...

Verified requirements:
- REQ-001: verified by ...

Open requirements:
- none

Rejected or unrelated changes:
- none

Changed files:
- ...

Tests / checks reviewed:
- command: ...
  result: PASS/FAIL/NOT RUN

Evidence reviewed:
- .tiny-swarm/evidence/.../requirement_matrix.md
- .tiny-swarm/evidence/.../test_results.md

Risks:
- ...

Final decision:
- ...
```

If `Open requirements` is not empty, `Decision` must not be `PASS`.
