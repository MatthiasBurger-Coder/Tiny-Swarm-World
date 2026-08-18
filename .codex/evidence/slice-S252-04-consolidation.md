# Issue #252 — S252-04 Consolidation

- Workflow: `issue-252-classic-public-beta-rc1-20260814`
- Slice: `S252-04` — WSL2 diagnostics and Fresh Install
- Branch: `docs/workflow-issue-252-classic-public-beta-20260814`
- Result: `S252-04_BLOCKED_LIVE_CONSENT_MISSING`
- Implementation: not started; no live command was executed.

## Gate decision

The required WSL2 commands are mutating and remain blocked:

- `python3 tools/install_debugger.py --live`
- `./install.sh --headless --confirm-reset --non-interactive-live-approval`

The workflow has no explicit user consent for live infrastructure, no confirmed
disposable/recoverable WSL2 target, no target-ownership record and no confirmed
rollback/cleanup plan for this run. Root governance also requires all Python
commands to run through WSL/Linux and does not authorize Administrator
PowerShell access. No Incus, Docker, Swarm, network, service, browser,
credential or PowerShell operation was attempted.

## Review

The required Senior DevOps live-safety review was assigned as a real review-only
stream but did not return a report before shutdown. The main-thread fallback
review verified the active workflow's explicit-consent, target-ownership,
prerequisite, redaction, rollback and stop conditions. This is recorded as a
gate block, not as a live failure or pass.

## Handoff

S252-05 through S252-12 are not started because they depend on the WSL2 live
evidence chain. Resume only after explicit WSL2 live authorization and a fresh
S3/S3D preflight. Native-Linux slices remain separately gated and cannot use
WSL2 evidence as a substitute.

## Live execution result — 2026-08-15

- Branch: `docs/workflow-issue-252-classic-public-beta-20260814` (clean issue
  workflow branch; the prescribed hierarchical branch could not be created
  because local ref `release` already exists and was not renamed or deleted).
- Commit: `fd4ad5cb9110e322f2ced90b5150f5d47f498619`
- Host: WSL2/Linux userspace
- Consent: explicit user authorization, including reset-capable live work
- `install_debugger.py --live`: exit `0`
- Final preflight with authorized filesystem override and loaded ignored local
  environment: exit `0`
- Fresh Install attempt 1: reset `0`, setup `1`; blocked by missing LXC APT
  egress. Targeted forwarding repair was applied and `doctor network` returned
  `NETWORK_OK`.
- Fresh Install attempt 2: reset `0`, setup `1`; cluster, Swarm, secrets
  bootstrap and artifacts completed, but Traefik deployment failed because
  required external Docker secret `tsw_traefik_gui_users` was absent.
- Final slice state: `S252-04_BLOCKED_RC1_BLOCKER` /
  `LIVE_FAILED_AFTER_MUTATION`.
- Redacted scenario evidence:
  `.tiny-swarm-world/evidence/classic-public-beta-rc1/wsl2/RC1-S02/summary.md`
  and `RC1-S03/summary.md`.
- No browser/API/E2E acceptance, reconcile, update, restart or native-Linux
  run was started; dependent slices remain blocked.
