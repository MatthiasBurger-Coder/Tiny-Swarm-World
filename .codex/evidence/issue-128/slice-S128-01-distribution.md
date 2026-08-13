# S128-01 Distribution Evidence

Workflow: `issue-128-branch-ci-governance-20260812`
Slice: S128-01 — Requirement matrix and actual-vs-target baseline

## Distribution decision

- Affected areas: branch protection, CI quality, PR review, QMS/security
  traceability, quality authority and audit evidence.
- Execution mode: sequential; shared status vocabulary and QUALITY.md lock.
- Selected streams: requirement engineering, branch/CI governance, quality,
  architecture, QMS/security traceability and evidence review.
- No parallel write worktrees: the matrix and actual-vs-target decisions are
  shared contracts.
- Forbidden: GitHub settings mutation, new CI jobs, live commands, secret
  values and unverifiable hosted-check claims.

## Quality and evidence

Targeted: `git diff --check`.
Required: `python3 tools/quality_gate.py quality` in WSL/Linux, as required by
the issue. The result remains local repository evidence only.

S128-01 establishes every issue bullet as a stable requirement and records
unknown external settings as unknown rather than as implemented controls.
