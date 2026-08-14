# Issue #252 — S252-03 Consolidation

- Workflow: `issue-252-classic-public-beta-rc1-20260814`
- Slice: `S252-03` — Deterministic lifecycle, fail-closed and recovery coverage
- Branch: `docs/workflow-issue-252-classic-public-beta-20260814`
- Result: `S252-03_READY_FOR_S252-04`
- Live execution: not applicable to this local test slice; no live command ran.

## Review outcome

The Quality Reviewer initially returned `INCOMPLETE` because the candidate
contract lacked explicit prerequisite, failed-after-mutation, empty-scenario,
full-evidence and serialized-writer checks, and did not exercise a production
workflow. Codex incorporated those findings before consolidation:

- added `LIVE_PREREQUISITE_MISSING`, `LIVE_PARTIAL`, `LIVE_DEGRADED` and
  `LIVE_FAILED_AFTER_MUTATION` assertions;
- made empty required-scenario sets and raw redaction status fail closed;
- expanded the evidence model with scenario, readiness/transition, retry,
  remediation, rollback/cleanup, checksum and reviewer fields;
- exercised the production `PlatformReconcileWorkflow` with a synthetic step,
  including failed verification after apply;
- exercised the existing browser evidence writer with a temporary redacted
  evidence root.

The remaining reconcile/update/restart identity comparisons are deliberately
synthetic policy fixtures in test support. They are not live results and do
not claim runtime execution.

## Checks

- Focused `test_lifecycle_contract` — PASS; 12 tests.
- `python3 tools/quality_gate.py lint` — PASS.
- `python3 tools/quality_gate.py arch-tests` — PASS; 18 tests.
- `python3 tools/quality_gate.py test` — PASS; 1,768 tests, 18 skipped.
- `python3 tools/quality_gate.py quality` — PASS; policy, lint, arch-lint,
  arch-tests, mypy and full unittest gate all passed.
- `git diff --check` — PASS after staging.
- Live/Incus/Docker/Swarm/browser/SonarQube checks — NOT RUN; no live consent.

## Handoff

S252-03 now provides deterministic local coverage for prerequisite blocking,
partial/ambiguous/failure states, stable identity and state preservation,
restart verification, evidence completeness, redaction and exact final
decision values. S252-04 may begin only through the explicit live-consent gate.
