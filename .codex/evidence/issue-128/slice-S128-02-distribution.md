# S128-02 Distribution Evidence

Workflow: `issue-128-branch-ci-governance-20260812`
Slice: S128-02 — Branch, CI and PR policy documents

## Distribution decision

- Affected areas: branch protection, CI quality policy, PR review, QMS/ISMS
  traceability, documentation navigation and quality authority.
- Execution mode: sequential; the three policies share status vocabulary,
  gate semantics and merge-blocking rules.
- Selected streams: Branch CI Governance Expert, QMS-light review,
  documentation, architecture, quality/test and audit evidence.
- Forbidden: GitHub settings mutation, unscoped CI jobs, live commands, raw
  secrets, guessed hosted-check status and merge bypasses.

## Quality and evidence

Targeted: `git diff --check`.
Required: `python3 tools/quality_gate.py quality` in WSL/Linux because the
issue explicitly requires the full gate and `QUALITY.md` was synchronized.
Both results remain local repository evidence only.

The three documents classify current versus target state, retain failed or
unknown checks as merge blockers and link #121/#122/#123 evidence.
