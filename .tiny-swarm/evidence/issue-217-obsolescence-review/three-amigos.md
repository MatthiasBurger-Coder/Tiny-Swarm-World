# Three-Amigos Review — Issue #217

Baseline: `main` at `ecdc71d94a72530905ecb0a41d2845921ad6debb`.
The requirement, implementation/architecture and test/quality perspectives
were recorded before any remote issue mutation.

## Issue #156

| Perspective | Current conclusion | Evidence |
|---|---|---|
| Requirement Lead | The central direct-published-port requirement remains valid; the issue is not complete. | Issue body and acceptance criteria re-read; `issue-156-review.md`. |
| Developer / System Architect | Registry loading and effective-access projection exist, but service-access direct publishers and several direct URL/readiness producers bypass the effective map. | `ports.yaml`, `compose_file_repository_yaml.py`, `desired_state.py`, `service_stack_contract.py`, `installer.py`, `composition.py`, `service-access/nginx/default.conf`. |
| Test / Quality Lead | Targeted repository/routing tests pass; they do not prove every direct publisher is centrally resolved. Full quality state is not claimed in the candidate audit. | `issue-156-test-results.md`; 58 targeted tests passed. |
| Decision | `KEEP_OPEN` | Residual central-resolution and end-to-end propagation work remains. |

## Issue #163

| Perspective | Current conclusion | Evidence |
|---|---|---|
| Requirement Lead | The single focused correction remains valid; #159 and #160 are historical closed duplicates. | Issue body, original keys and duplicate note re-read; `issue-163-review.md`. |
| Developer / System Architect | No runtime change is needed; the test fixture still contains the three raw address literals and an existing safe-literal helper is unused by this target test. | Current lines 165, 166 and 194; `tests/support/sonar_safe_literals.py:4-5`. |
| Test / Quality Lead | Targeted test passes, literal scan still finds all three values, and external Sonar/CI state is explicitly `UNVERIFIED`. | `issue-163-test-results.md`; 15 tests passed. |
| Decision | `KEEP_OPEN` | Test-only hygiene remains incomplete. |

## Issue #197

| Perspective | Current conclusion | Evidence |
|---|---|---|
| Requirement Lead | The extraction acceptance criteria remain valid and are not satisfied. | Issue body and six behavior cases re-read; `issue-197-review.md`. |
| Developer / System Architect | Socat process inspection/startup remains in `composition.py`; `SocatManager` remains application-owned and no focused infrastructure adapter exists. | Composition ownership scan and source references in `issue-197-review.md`. |
| Test / Quality Lead | Composition and architecture tests pass, but dedicated consent, existing-process, success and failure coverage is not evidenced. | `issue-197-test-results.md`; 95 + 24 tests passed. |
| Decision | `KEEP_OPEN` | Architecture extraction and safety regression coverage remain incomplete. |

## Governance result

All three role perspectives are recorded, each issue has exactly one allowed
decision, and no issue was closed, reopened or rewritten during this review.

