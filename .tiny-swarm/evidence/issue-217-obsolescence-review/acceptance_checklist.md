# Acceptance Checklist — Issue #217

| Requirement | Evidence | Current status |
|---|---|---|
| Current `main` baseline and all four issue snapshots captured | `baseline.md`, `issue-snapshots.md` | `VERIFIED_LOCAL` |
| Three-Amigos perspectives recorded for all candidates | `three-amigos.md` and three issue reviews | `VERIFIED_LOCAL` |
| Exactly one allowed decision per candidate | `decision-record.md` | `VERIFIED_LOCAL` |
| Implementation, tests, gaps and recommended action recorded | three `issue-*-review.md` files and test results | `VERIFIED_LOCAL` |
| #156 central port checks traced | #156 review/test evidence | `VERIFIED_LOCAL` with residual checks `BLOCKED` |
| #163 three literals, test intent, test result and Sonar state traced | #163 review/test evidence | `VERIFIED_LOCAL` with external Sonar `UNVERIFIED` |
| #197 ownership, consent and six behavior cases traced | #197 review/test evidence | `VERIFIED_LOCAL` with residual cases `UNVERIFIED`/`BLOCKED` |
| Scope and live-command safety preserved | distribution and test evidence | `VERIFIED_LOCAL` |
| Duplicate-work guard and action compare-and-set policy recorded | `deduplication-guard.md` | `VERIFIED_LOCAL`; remote actions pending |
| Full repository quality gate | Required by S217-05 | `PASS` — 1,697 tests, 28 skipped; verification policy, lint, architecture lint/tests and typecheck passed |
| Final issue actions and post-action snapshots | S217-06 | `PENDING` |

The workflow must not claim final `DONE` while guarded actions or the
post-action audit remain pending, or while an external state is described as
passed without observable evidence.
