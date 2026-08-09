# Issue #187 — S187-03 Consolidation Evidence

- Workflow: `issue-187-20260809` / `issue-187-v1.0.0`
- Slice: `S187-03` — Regression and completion audit
- Execution branch: `feature/preflight-service-probe-registry-solid`
- Decision: `PASS`
- Independent audit roles: requirement, system architecture, tester/evidence,
  documentation and security.

## Audit result

The after responsibility map confirms that HostPreflightProbe retains host and
low-level I/O responsibilities while the ordered service-probe registry owns
only service dispatch. The before/after contract preserves all 15 named
patterns, ordering, path/marker semantics, HTTPS/TCP selection and false
fallback for unsupported names.

The requirement matrix records REQ-187-001 through REQ-187-007 as
VERIFIED_LOCAL. Required issue evidence, Three-Amigos and responsibility maps
are present.

## Verification

- focused registry and preflight tests: PASS (44 tests)
- git diff --check: PASS
- local quality gate: PASS (1689 passed, 28 skipped)
- verification-policy, lint, architecture, typecheck and regression stages:
  PASS

Live host/network, browser/Selenium and external quality-system checks were not
run and are explicitly not claimed.

## Handoff

Issue #187 is locally complete and audited. The active chain can advance to
Issue #190.
