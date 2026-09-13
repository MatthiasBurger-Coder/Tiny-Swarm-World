# CRED-09 issue #296 requirement matrix

Reconstructed issue-local entrypoint, 2026-09-13. The authoritative executed
completion report and ten stable IDs were already published. Actual tested
revision remains 81443e80; current applicability is separately reviewed in
[the R06 comparison](../issue-302/credential-applicability.json).


| Stable requirement | Implementation and verification | State |
|---|---|---|
| CRED-09-REQ-001 — sources/lifecycle | Canonical resolver and current contract; distinct-source, source-identity and bootstrap regressions | VERIFIED |
| CRED-09-REQ-002 — defaults/operator/secure on both hosts | Current catalog baselines and independent Vault cases; explicit distinct operator cases plus applicable historical matching-override results below | VERIFIED |
| CRED-09-REQ-003 — conflicting-source winner | Both conflict runs consumed Vault, authenticated it and rejected the distinct operator value | VERIFIED |
| CRED-09-REQ-004 — non-effective input/session semantics | HTTP 401 rejection and observed cookie invalidation in all four runs, with explicit session scope | VERIFIED |
| CRED-09-REQ-005 — rerun/restart comparisons | Reconcile, redeployment, exact task replacement, actual source provenance and protected value/specification equality in all runs | VERIFIED |
| CRED-09-REQ-006 — isolated intended transition | Only Jenkins service/key changed; unrelated Vault values and full service specifications compared | VERIFIED |
| CRED-09-REQ-007 — bootstrap/external guards | Resolver lifecycle/identity regressions and `test_infisical_provider_mode_rejects_unsupported_external_mixing`; guards retained | VERIFIED |
| CRED-09-REQ-008 — protected evidence | Values compared in memory or private rollback; published labels, booleans and operation outcomes only | VERIFIED |
| CRED-09-REQ-009 — restoration/cleanup | Four verified restorations, zero remaining rotation records on either host; deliberate retained migration recovery material | VERIFIED |
| CRED-09-REQ-010 — traceability/no blanket claims | This report, JSON evidence, historical records and explicit linked scope below | VERIFIED |
