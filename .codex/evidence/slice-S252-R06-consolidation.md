# S252-R06 Consolidation Evidence

- Workflow/version: `issue-252-classic-public-beta-rc1-remediation-20260823` / `2026-08-23-remediation-r1`
- Slice: `S252-R06 — Bounded E2E readiness and composition integration`
- Rollback baseline: `aad6ab53`
- Result: PASS for deterministic local verification; no live success claimed.

The single canonical Classic post-install suite now uses one monotonic global
deadline and caps every request by the remaining budget. Timeouts, probe
exceptions, TLS failures and even a late-ready response remain explicit
failures with attempts, bounded duration and pending service names recorded in
redacted evidence. Empty readiness matrices return immediately. The suite
constructs/injects the existing canonical TLS resolver and consumes its trust
bundle instead of maintaining an independent path contract. Composition tests
join the same selected Incus request through preflight, artifact readiness,
platform, artifact, deployment and host-preparation wiring.

Verification:

- Focused R06 command: PASS, 136 tests with 8 expected live skips.
- Lint/typecheck: PASS, 634 files.
- Full quality: PASS, 1,833 tests with 18 skipped; verification policy, three
  import contracts and 18 architecture tests passed.
- `git diff --check`: PASS.
- Independent Python, system architecture and live-evidence reviews: PASS.
- Live Classic browser suite: not executed; opt-in skips are not success evidence.

The live rerun remains a serialized R08 handoff and must use the exact final
candidate commit and explicit consent/prerequisites.
