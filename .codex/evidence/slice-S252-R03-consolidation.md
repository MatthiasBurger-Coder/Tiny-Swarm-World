# S252-R03 Consolidation Evidence

- Workflow: `issue-252-classic-public-beta-rc1-remediation-20260823`
- Version: `2026-08-23-remediation-r1`
- Slice: `S252-R03 — Incus provider readiness and restart classification`
- Rollback baseline: `70eef782`
- Result: PASS for local, non-mutating R03 verification.

The selected Incus/LXC backend now executes bounded `admin waitready` before
`version` and `info`; the first failure stops inspection. Timeout, daemon
unavailable, permission denied, executable missing and unknown failures map to
stable typed states. Subprocess launch exceptions are converted at the adapter
boundary without retaining exception text; evidence contains only constant
classification sources and summary fields.

Verification:

- Focused R03 test: PASS, 21 tests.
- Lint and typecheck: PASS, 634 files.
- Full quality: PASS; 1,810 tests, 18 skipped; verification policy, three import
  contracts and 18 architecture tests also passed.
- `git diff --check`: PASS.
- Independent Python review: PASS.
- Independent tester review: PASS.
- Live Incus/LXC and restart scenarios: not executed and not claimed.

The live restart matrix remains an evidence activity after all dependent
product remediation; local fake-runner results do not establish daemon or host
restart success.
