# S252-R04 Consolidation Evidence

- Workflow/version: `issue-252-classic-public-beta-rc1-remediation-20260823` / `2026-08-23-remediation-r1`
- Slice: `S252-R04 — Managed-LXC artifact readiness and timeout semantics`
- Rollback baseline: `2f107bf8`
- Result: PASS for local non-mutating verification.

Managed LXC Docker and manager-storage probes execute as bounded, read-only
`incus|lxc exec swarm-manager -- ...` commands with output discarded. Local
build-input ownership remains on the host. Timeout, missing CLI/runtime,
non-zero and unknown outcomes remain typed and summary-only. An unresolved or
ambiguous LXC backend now fails closed with unavailable probes and can never
substitute host Docker/storage checks; only an explicitly non-managed provider
uses local probes.

Verification:

- Focused R04 tests: PASS, 13 tests.
- Lint/typecheck: PASS, 634 files.
- Full quality: PASS, 1,819 tests with 18 skipped; verification policy, three
  import contracts and 18 architecture tests also passed.
- `git diff --check`: PASS.
- Independent DevOps review: PASS after unresolved-backend remediation.
- Independent tester review: PASS.
- Live Incus/LXD/Docker commands: not executed and not claimed.

Live manager-node readiness remains serialized follow-up evidence; local mocks
prove command construction, classification and redaction, not host availability.
