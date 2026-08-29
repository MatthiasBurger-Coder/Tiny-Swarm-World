# RC1_BLOCKER-003 — Incus Readiness Fix

## Root cause

The provider preflight treated successful `incus version` and `incus info`
responses as sufficient readiness. Immediately after WSL restart, Incus could
respond while its early-start tasks and automatic managed-container startup
were still in progress. Reconcile then attempted the selected node lifecycle
transition too early and returned `failed_to_apply`.

## Smallest fix

`LxcProviderPreflightProbe` now executes the existing read-only
`<backend> admin waitready --timeout <bounded-seconds>` command before
`version` and `info`. The default provider readiness budget is bounded at 30
seconds, which covers the observed WSL2/Incus startup interval without an
unbounded wait or lifecycle retry.

## Regression and local verification

- Regression test: `tests.infrastructure.adapters.preflight.test_lxc_provider_preflight`
  — 15 tests passed.
- Full quality gate: `python3 tools/quality_gate.py quality` — passed.
  - verification policy: PASS
  - lint: PASS
  - arch-lint: 3 contracts kept
  - arch-tests: 18 passed
  - mypy: no issues in 627 files
  - full test discovery: 1,782 passed, 18 skipped

## Real re-run

The affected scenario was rerun from a fresh `wsl.exe --shutdown` boundary:

- Restart diagnostics: `2026-08-23T13:58:40Z`–`13:58:52Z`, exit code `0`.
- `platform reconcile`: `2026-08-23T13:58:58Z`, structured `completed`,
  `no_op`, `verified`, exit code `0`; all three node identities were verified.
- `platform verify`: `completed`, `verified`; 26 platform checks and 18 proxy
  devices passed with zero drift, missing, unknown, or failed entries.
- Post-restart live acceptance: 29 tests passed, exit code `0`.
- Readiness evidence: 22 bounded attempts, 71.436 seconds elapsed, no pending
  services, 180-second maximum; evidence
  `.tiny-swarm-world/evidence/classic-public-beta-rc1/20260823T135937Z/summary.json`.

**Blocker status: CLOSED.**
