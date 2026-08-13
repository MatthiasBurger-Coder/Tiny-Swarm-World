# Issue #128 Requirement Matrix

Workflow: `issue-128-branch-ci-governance-20260812`
Issue: #128
Parent roadmap: #120
Predecessor context: #121 audit evidence, #122 QMS-light and #123 ISMS-light

Matrix owner: Senior Requirement Engineer
Reviewers: Branch CI Governance Expert, QMS-light Governance Expert, Senior
System Architect, Senior Tester and Senior Documentation Engineer

## Status and interpretation

`VERIFIED_LOCAL` means that the repository policy and its evidence mapping are
verified. It does not prove that GitHub branch settings, hosted checks,
SonarCloud, or any other external service currently has that configuration.
Actual external state is explicitly classified as `UNKNOWN` unless observable
evidence exists. Failed, skipped, unavailable and unverifiable required checks
block merge and are never treated as green.

The issue requires `git diff --check` and
`python3 tools/quality_gate.py quality`. Both are local evidence only.

## Requirement-to-evidence matrix

| ID | Requirement | Type | Implementation/evidence | Verification | Status |
| --- | --- | --- | --- | --- | --- |
| REQ-128-001 | Create branch-protection.md, ci-quality-gates.md and pr-review-policy.md. | Required files | S128-02 documents | File/content review | VERIFIED_LOCAL |
| REQ-128-002 | Prohibit direct pushes to main. | Branch protection | branch-protection.md | Policy review | VERIFIED_LOCAL |
| REQ-128-003 | Require a pull request before main merge. | Branch protection | branch-protection.md | Policy review | VERIFIED_LOCAL |
| REQ-128-004 | Require configured status checks before merge. | Branch protection | branch-protection.md | Actual/target table | VERIFIED_LOCAL |
| REQ-128-005 | Block force pushes to main. | Branch protection | branch-protection.md | Policy review | VERIFIED_LOCAL |
| REQ-128-006 | Restrict branch deletion. | Branch protection | branch-protection.md | Policy review | VERIFIED_LOCAL |
| REQ-128-007 | Decide and justify linear-history protection. | Branch protection | branch-protection.md | Decision review | VERIFIED_LOCAL |
| REQ-128-008 | Decide and justify signed-commit protection. | Branch protection | branch-protection.md | Decision review | VERIFIED_LOCAL |
| REQ-128-009 | Classify code scanning as target state where unavailable. | Branch protection | branch-protection.md | Actual/target review | VERIFIED_LOCAL |
| REQ-128-010 | Classify code quality and local-gate relation. | Branch protection | branch-protection.md | QUALITY.md cross-check | VERIFIED_LOCAL |
| REQ-128-011 | Limit bypass permissions and require an auditable reason. | Branch protection | branch-protection.md | Policy review | VERIFIED_LOCAL |
| REQ-128-012 | Keep #122 QMS change/review/CAPA governance as the process relation. | Traceability | branch and PR policies | Link review | VERIFIED_LOCAL |
| REQ-128-013 | Carry #123 security, secret and no-live expectations into review. | Traceability | PR policy | Link/review check | VERIFIED_LOCAL |
| REQ-128-014 | Use python3 tools/quality_gate.py quality as canonical local gate. | CI | ci-quality-gates.md and QUALITY.md | Command check | VERIFIED_LOCAL |
| REQ-128-015 | Map verification-policy, lint, arch-lint, arch-tests, typecheck and test stages. | CI | ci-quality-gates.md and QUALITY.md | Stage comparison | VERIFIED_LOCAL |
| REQ-128-016 | Keep security gate separate unless separately accepted. | CI | ci-quality-gates.md | Policy review | VERIFIED_LOCAL |
| REQ-128-017 | Do not run live infrastructure in default CI. | CI safety | ci-quality-gates.md | No-live review | VERIFIED_LOCAL |
| REQ-128-018 | Gate live smoke validation behind manual/explicit environment consent. | CI safety | ci-quality-gates.md | Policy review | VERIFIED_LOCAL |
| REQ-128-019 | Link CI/quality evidence from PRs. | Evidence | ci-quality-gates.md and PR policy | Field review | VERIFIED_LOCAL |
| REQ-128-020 | Failed, unavailable or unverifiable required gates block merge. | Merge safety | all three documents | Cross-document review | VERIFIED_LOCAL |
| REQ-128-021 | Classify dependency audit, SBOM, image scan, SonarQube and docs checks as current/target/deferred. | CI roadmap | ci-quality-gates.md | Status-table review | VERIFIED_LOCAL |
| REQ-128-022 | Require PR summary, changed files, scope/non-goals and validation. | PR evidence | pr-review-policy.md | Required-field review | VERIFIED_LOCAL |
| REQ-128-023 | Require quality commands/results, live-command statement and blockers in PR body. | PR evidence | pr-review-policy.md | Required-field review | VERIFIED_LOCAL |
| REQ-128-024 | Require security and documentation impact statements. | PR evidence | pr-review-policy.md | Required-field review | VERIFIED_LOCAL |
| REQ-128-025 | Define reviewer triggers by runtime, architecture, security and governance impact. | Review | pr-review-policy.md | Trigger review | VERIFIED_LOCAL |
| REQ-128-026 | Require Three Amigos, architecture or security review when applicable. | Review | pr-review-policy.md | Trigger review | VERIFIED_LOCAL |
| REQ-128-027 | Prohibit overclaiming local, live, browser, SonarQube or external success. | Evidence integrity | pr-review-policy.md | Policy review | VERIFIED_LOCAL |
| REQ-128-028 | Define skipped-gate handling with explicit reason and non-pass state. | Review/quality | pr-review-policy.md | Policy review | VERIFIED_LOCAL |
| REQ-128-029 | Define merge approval, required review and post-merge cleanup expectations. | Merge | pr-review-policy.md | Policy review | VERIFIED_LOCAL |
| REQ-128-030 | Cross-link MAJ-05 and QMS evidence from #121/#122. | Audit | S128-02 and evidence package | Link review | VERIFIED_LOCAL |
| REQ-128-031 | Do not mutate GitHub settings or add unscoped CI jobs. | Scope/safety | Workflow and changed-file audit | Scope check | VERIFIED_LOCAL |
| REQ-128-032 | Use dedicated issue branch/worktree and serial S128-01 -> S128-02 execution. | Process | Workflow/context/evidence | Branch/order check | VERIFIED_LOCAL |
| REQ-128-033 | Provide distribution and consolidation evidence for each slice. | Process evidence | .codex/evidence/issue-128 | File check | VERIFIED_LOCAL |
| REQ-128-034 | Run required local validation and record exact result. | Quality | test_results.md | Command review | VERIFIED_LOCAL |
| REQ-128-035 | Provide six issue evidence files and independent completion audit before DONE. | Completion | .tiny-swarm/evidence/issue-128 | Required-file/audit review | VERIFIED_LOCAL |

## Actual-vs-target baseline

| Control/status | Repository evidence | Classification |
| --- | --- | --- |
| Local quality gate | `QUALITY.md` and `tools/quality_gate.py` | Current/local |
| SonarCloud workflow | `.github/workflows/sonar_check.yml` exists; token/result availability is not verified here | Repository-configured, external result unknown |
| GitHub main protection | No API/settings mutation or authoritative settings evidence in this workflow | Unknown; target policy documented |
| Required status checks | Policy requires configured checks; actual GitHub required-check list is not verified | Unknown; target policy documented |
| Code scanning, SBOM, dependency and image scans | Policies/evidence exist in repository where applicable; hosted enforcement is not established | Current policy / target enforcement |
| Live smoke validation | Not part of default CI | Explicit/manual environment-gated target |

## Boundary decisions

- This issue documents governance and does not configure GitHub.
- `QUALITY.md` and the verification-state policy remain authoritative.
- The existing SonarCloud workflow is evidence of repository configuration only;
  it is not evidence of a successful external scan.
- #126 receives the review/merge/security evidence contract before the admin
  surface work; #150 remains later in the ordered route.
