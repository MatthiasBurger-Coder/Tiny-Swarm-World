# Acceptance Checklist — #347 / ARCH-03.04

- [x] Preflight is exposed through an explicit application port independent of deployment mutation.
- [x] Results remain typed as `PreflightResult` and are testable with a fake port implementation.
- [x] Platform preflight is executed before mutating platform steps.
- [x] Existing WSL2/native-Linux safety behavior remains in the existing concrete service and adapters.
- [x] Existing actionable check/remediation messages remain unchanged.
- [x] Focused tests and the repository quality gate pass.
- [x] No live infrastructure command was run.
