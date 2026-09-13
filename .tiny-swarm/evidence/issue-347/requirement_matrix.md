# Requirement Matrix — #347 / ARCH-03.04

Parent: #313 — EPIC 03

| ID | Requirement from issue | Type | Implementation evidence | Verification evidence | Status |
|---|---|---|---|---|---|
| REQ-001 | Preflight can run independently of deployment mutation. | architecture / functional | Explicit platform preflight port; platform and setup orchestration depend on the port rather than deployment adapters. | Port and workflow unit tests; architecture gate. | DONE |
| REQ-002 | Preflight results are represented explicitly and testable. | functional / quality | Existing typed `PreflightResult` is exposed through the port contract. | Port contract and preflight workflow tests. | DONE |
| REQ-003 | Pure preflight validation has no deployment side effects. | safety / functional | Preflight port is read-only and is invoked before mutating platform steps. | Guard-order test with recording mutation step; focused tests. | DONE |
| REQ-004 | Existing WSL2 and native-Linux safety behavior is preserved. | operating constraint / resilience | Existing `PreflightService` and host probe remain the concrete composition implementation. | Existing preflight regression suite and full quality gate. | DONE |
| REQ-005 | Failure messages remain actionable and deterministic. | functional / observability | Existing typed result/check/remediation contract is retained unchanged. | Existing failure/remediation tests and focused regression tests. | DONE |
