# S252-R03 Distribution Decision

- Workflow: `issue-252-classic-public-beta-rc1-remediation-20260823`
- Version: `2026-08-23-remediation-r1`
- Slice: `S252-R03 — Incus provider readiness and restart classification`
- Baseline: `70eef782`
- Execution: sequential, isolated worktree; no live provider mutation.
- Owner: Senior DevOps; implementation stream limited to the declared provider
  preflight adapter and its focused test.
- Review streams: Senior Python Automation Developer and Senior Tester.
- Required behavior: bounded `admin waitready` before `version` and `info`,
  typed/redacted timeout, unavailable, permission and unknown outcomes.
- Verification: exact targeted test, lint, typecheck, full local quality,
  independent reviews and one checkpoint commit/push.
