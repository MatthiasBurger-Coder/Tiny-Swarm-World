# Issue #252 Execution Requirement Matrix

Source: `documentation/workflow/requirement-matrix.md`

Implementation baseline: `60d5d09f`

No requirement from the canonical matrix is removed here. Requirements
REQ-252-001 through REQ-252-050 retain their canonical wording and are grouped
only by unchanged verification state; their live/release/external evidence is
not replaced by remediation unit tests.

| Requirement IDs | Implementation/evidence state | Status |
|---|---|---|
| REQ-252-001, REQ-252-041, REQ-252-042, REQ-252-043 | Final RC1 qualification, gates and decision remain dependent on all mandatory matrices and the independent final audit. | OPEN |
| REQ-252-002, REQ-252-003, REQ-252-012, REQ-252-013, REQ-252-014, REQ-252-015, REQ-252-044 | Scope and repository-layout constraints remain represented by the workflow and changed-file history; final audit remains open. | OPEN |
| REQ-252-004, REQ-252-005, REQ-252-006, REQ-252-007, REQ-252-008, REQ-252-009 | Fresh, post-install, reconcile, update and dependent acceptance require exact-candidate live reruns. Historical runs are not transferred. | OPEN |
| REQ-252-010, REQ-252-011, REQ-252-020, REQ-252-029, REQ-252-030, REQ-252-037, REQ-252-038 | Failure/recovery, restart, convergence and defect rerun evidence remains open on the remediation candidate. | OPEN |
| REQ-252-016, REQ-252-017 | Three-Amigos workflow records exist, but issue-level completion remains pending final audit and dependent execution. | OPEN |
| REQ-252-018, REQ-252-019, REQ-252-021, REQ-252-022, REQ-252-023, REQ-252-024, REQ-252-025, REQ-252-027, REQ-252-028 | Service/prerequisite/topology readiness requires exact-host observed evidence; local contract tests are not live proof. | OPEN |
| REQ-252-026, REQ-252-031, REQ-252-032, REQ-252-039, REQ-252-040, REQ-252-049, REQ-252-050 | Redaction and non-success semantics are locally exercised, but complete scenario and CI/live evidence audits remain open. | OPEN |
| REQ-252-033 | Exact-candidate local baseline executed honestly on `36ba799738ffb8db4175b7347a6aa8a7f907fa05`; targeted gates and full quality PASS, with 1,833 tests and 18 expected skips. | LOCAL_VERIFIED |
| REQ-252-034, REQ-252-035 | WSL2 diagnostics and lifecycle evidence must be rerun or retain an explicit non-success state for the remediation candidate. | OPEN |
| REQ-252-036 | Native Linux Fresh/Reconcile/Update and acceptance have not executed. | OPEN |
| REQ-252-045, REQ-252-046, REQ-252-047, REQ-252-048 | PR/push quality, Conda, SonarQube and protected self-hosted Classic-live runner evidence remains external and open. | OPEN |

## Authorized remediation requirements

| ID | Implementation evidence | Verification evidence | Status |
|---|---|---|---|
| REQ-252-051 | R01 canonical resolver, domain contract, port and composition at `b88255f1` | R01 focused 222 tests; full quality 1,792/18 skipped; independent reviews | LOCAL_VERIFIED |
| REQ-252-052 | R01 incomplete/conflicting external configuration fails before managed mutation | Negative resolver/configuration regressions in R01 evidence | LOCAL_VERIFIED |
| REQ-252-053 | R01 managed CA plus separately signed ingress leaf with strict SAN/chain/expiry checks | Synthetic PKI regressions in R01 evidence | LOCAL_VERIFIED |
| REQ-252-054 | R01 valid-state byte reuse and protected private-key modes | Fingerprint, replacement, file-type and permission regressions | LOCAL_VERIFIED |
| REQ-252-055 | R01 composition plus R06 canonical E2E resolver/trust-bundle wiring | R01/R06 focused tests and composition join | LOCAL_VERIFIED |
| REQ-252-056 | R02 owned/fingerprinted logical Docker secret pair with ID-scoped rollback | Partial-state, mismatch, rollback and retry regressions; focused 249 tests | LOCAL_VERIFIED |
| REQ-252-057 | R02 validated operator htpasswd and verify-before-apply ordering without value retention | Validation, ordering, blocked-apply and redaction regressions | LOCAL_VERIFIED |
| REQ-252-058 | R03 bounded Incus/LXC `admin waitready` before inspection and typed failures | Focused 21 tests; full quality 1,810/18 skipped | LOCAL_VERIFIED |
| REQ-252-059 | R04 manager-container Docker/storage probes with fail-closed backend and timeout mapping | Focused 13 tests; full quality 1,819/18 skipped | LOCAL_VERIFIED |
| REQ-252-060 | R05 read-only procfs verification of bridge netfilter and IPv4 forwarding | Focused 8 tests; documentation review; full quality 1,823/18 skipped | LOCAL_VERIFIED |
| REQ-252-061 | R06 one monotonic deadline, capped requests and explicit late-ready/error failures | Focused 136/8 expected live skips; full quality 1,833/18 skipped | LOCAL_VERIFIED |
| REQ-252-062 | R07 Arc42/config/ADR alignment plus six issue evidence files reference baseline `60d5d09f` and reject historical transfer | `git diff --check`, sensitive-marker and governing-hash reviews passed; final quality passed 1,833 tests with 18 expected skips; independent R07 reviews passed | LOCAL_VERIFIED |
| REQ-252-063 | R08 exact-candidate targeted and full local quality evidence | Clean candidate `36ba799738ffb8db4175b7347a6aa8a7f907fa05`; diff, lint, three import contracts, 18 architecture tests, typecheck, 1,833 tests / 18 skips and full quality PASS | LOCAL_VERIFIED |

`LOCAL_VERIFIED` never means live, Native Linux host, browser, CI, SonarQube or
runner success. The issue remains `INCOMPLETE` while any mandatory row is open.
