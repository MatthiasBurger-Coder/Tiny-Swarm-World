# S252-R04 Distribution Decision

- Workflow/version: `issue-252-classic-public-beta-rc1-remediation-20260823` / `2026-08-23-remediation-r1`
- Slice: `S252-R04 — Managed-LXC artifact readiness and timeout translation`
- Baseline: `2f107bf8`
- Mode: sequential isolated execution; no live provider or Docker mutation.
- Owner: Senior Python Automation Developer; reviews by Senior DevOps and
  Senior Tester.
- Locks: artifact-source readiness adapter, setup composition and their focused
  tests only, as declared in the workflow.
- Acceptance: provider-aware manager-container probes, host-local build-input
  checks, bounded timeouts, typed missing CLI/node/non-zero/timeout states and
  summary-only evidence.
- Gates: exact focused tests, lint, typecheck, full quality, independent review,
  single checkpoint commit and push.
