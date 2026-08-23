# S252-R05 Consolidation Evidence

- Workflow/version: `issue-252-classic-public-beta-rc1-remediation-20260823` / `2026-08-23-remediation-r1`
- Slice: `S252-R05 — Native-Linux kernel prerequisite verification`
- Rollback baseline: `6da94de6`
- Result: PASS for local read-only verification.

Native Linux preparation now reads the required bridge-netfilter and IPv4
forwarding controls only. Active, missing, disabled and read-error states are
reported with stable control names and summary statuses; missing or non-active
state fails closed without persisting observed values or procfs paths. Cleanup
explicitly leaves operator-owned state unchanged. Installation guidance clearly
separates direct inspection, temporary activation and operator-owned sysctl.d
persistence; only a separately authorized live setup may recheck after mutation.

Verification:

- Focused R05 tests: PASS, 8 tests.
- Lint/typecheck: PASS, 634 files.
- Full quality: PASS, 1,823 tests with 18 skipped; verification policy, three
  import contracts and 18 architecture tests passed.
- `git diff --check`: PASS.
- Independent Python/safety, tester and documentation reviews: PASS.
- Live sysctl, modprobe or host mutation: not executed and not claimed.

README alignment remains an R07 documentation-sync item. Generic prepare/live
consent behavior is unchanged; the adapter itself introduces no mutation.
