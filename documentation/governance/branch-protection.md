# Main Branch Protection Policy

## Purpose and status vocabulary

This document defines the repository target for protecting `main` and the
evidence needed to review changes. It does not mutate GitHub settings. A
repository policy is not evidence that the corresponding external setting is
currently enabled.

Use these statuses:

- **Required now** — a merge must not proceed without the control or an
  explicitly recorded non-pass/blocker state.
- **Recommended** — the control is the preferred target, but adoption needs an
  explicit repository decision or prerequisite.
- **Target state** — planned enforcement that is not verified as active.
- **Not applicable** — the control does not fit this repository scope.
- **Deferred** — intentionally postponed to a named workflow or decision.

## Required protection model for `main`

| Control | Policy status | Repository evidence now | Decision/rationale |
| --- | --- | --- | --- |
| No direct pushes | Required now | Branch/workflow governance and protected-workflow policy | All changes use a dedicated branch and PR. GitHub setting remains externally unknown. |
| Pull request required | Required now | This policy and PR policy | Review and quality evidence must be present before merge. |
| Required status checks | Required now | CI policy maps the canonical local gate and configured checks | Unknown checks block merge; no missing/unverifiable check is treated as green. |
| Force pushes blocked | Required now | This policy | Protects audit history and review references. External setting is unverified. |
| Branch deletion restricted | Required now | This policy and post-merge cleanup rule | Delete only the verified merged task branch through the governed cleanup flow. |
| Linear history | Recommended | Current repository uses merge commits for workflow integration | Prefer linear history for product branches when the team adopts it; do not silently rewrite existing audit history. |
| Signed commits | Recommended | No repository-wide signing configuration is verified here | Adopt when signer availability and verification policy are agreed; missing signature is not represented as currently enforced. |
| Code scanning | Target state | Existing repository policies/workflows are reviewed separately | Require an observable configured check before making it a blocking GitHub rule. |
| Code quality | Required now | `QUALITY.md` and `tools/quality_gate.py quality` | Local quality evidence is mandatory; hosted enforcement remains an external setting to verify. |
| Bypass permissions | Required now | This policy and PR review policy | Limit bypass to named administrators for documented emergencies; require issue, reason, evidence and follow-up review. |

## Merge relationship and evidence

The canonical local gate is:

```text
python3 tools/quality_gate.py quality
```

It runs verification-policy consistency, lint, architecture lint, architecture
tests, type checking and tests. The local result is evidence for the PR, not a
claim about GitHub checks, SonarCloud or deployed infrastructure.

Changes follow #122 QMS-light change/review/CAPA rules and #123 ISMS-light
secret, redaction, security-review and no-live rules. A failed, skipped,
unavailable or unverifiable required check blocks merge.

## Settings boundary

This policy intentionally leaves GitHub branch-protection settings unchanged.
An authorized future settings workflow must record the observed rule set,
required-check names, bypass actors, branch-deletion behavior and verification
date without copying tokens or private configuration.
