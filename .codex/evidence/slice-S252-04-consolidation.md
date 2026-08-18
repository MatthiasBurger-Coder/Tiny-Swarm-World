# Issue #252 — S252-04 Consolidation

- Workflow: `issue-252-classic-public-beta-rc1-20260814`
- Slice: `S252-04` — WSL2 diagnostics and Fresh Install
- Branch: `docs/workflow-issue-252-classic-public-beta-20260814`
- Result: `S252-04_RECOVERED_LIVE_VERIFIED`
- Implementation: live recovery and post-install acceptance completed; the
  earlier missing-secret failure remains recorded below as historical evidence.

## Historical pre-authorization gate decision

Before the later explicit user authorization, the required WSL2 commands were
mutating and correctly blocked:

- `python3 tools/install_debugger.py --live`
- `./install.sh --headless --confirm-reset --non-interactive-live-approval`

At that point the workflow had no explicit user consent for live
infrastructure. Root governance also requires all Python commands to run
through WSL/Linux and does not authorize Administrator PowerShell access. The
absence of authorization applied only to that earlier gate and is superseded
for the recovery run by the explicit authorization recorded below.

## Historical review

The required Senior DevOps live-safety review was assigned as a real review-only
stream but did not return a report before shutdown. The main-thread fallback
review verified the active workflow's explicit-consent, target-ownership,
prerequisite, redaction, rollback and stop conditions. This is recorded as a
gate block, not as a live failure or pass.

## Handoff status

S252-05 through S252-12 remain not started in the formal workflow and still
require their own S3/S3D preflight. Native-Linux slices remain separately
gated and cannot use WSL2 evidence as a substitute.

## Historical live execution result — 2026-08-15

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

## Live recovery and acceptance result — 2026-08-18

- Host: WSL2/Linux userspace
- Consent: explicit user authorization to generate a new random Traefik admin
  secret and store it privately
- Secret recovery: Docker Swarm secret `tsw_traefik_gui_users` was created in
  the manager's secret store. The generated value, hash and credentials were
  not printed, persisted in the repository, or included in evidence.
- Idempotent setup command: `./tsw setup run --live --approve-live
  --service-profile service-access --allow-wsl-windows-filesystem`
- Idempotent setup exit code: `0`
- Setup result: all 18 phases completed, including host verification, Incus,
  Docker/Swarm, routing, artifact readiness, deployment verification and
  platform verification.
- Initial post-install E2E: `90/92`; the two failures were HTTPS trust
  failures caused by a stale local CA bundle after the reset, not service
  readiness failures.
- Recovery action: generated the current public Traefik CA bundle locally at
  `.tiny-swarm-world/local/traefik-live-ca-recovery-20260818.pem` and reran
  the complete Classic suite with `TSW_LIVE_TLS_CA_BUNDLE` set to that bundle.
  No private key or secret was stored.
- Final browser/API/E2E command: `PYTHONPATH=src .venv/bin/python -m
  unittest discover -s tests/e2e/classic -t .`
- Final E2E exit code: `0`; `92/92` tests passed in `39.809s`.
- Redacted evidence:
  `.tiny-swarm-world/evidence/classic-public-beta-rc1/20260818-traefik-secret-recovery-rerun/20260818T110826Z/summary.json`
- Final cluster state: three Incus/Swarm nodes `Ready` and `Active`; nine
  expected stacks present; all long-running services ready. The
  `pulsar-manager-bootstrap` one-shot service is `0/1` after completion, as
  expected.
- Redaction: confirmed; no raw secret, password, hash or private key appears
  in the generated evidence or tracked consolidation.
- Recovery status: `LIVE_VERIFIED` for the idempotent setup and
  post-install Acceptance/E2E path. This does not claim completion of the
  later reconcile, update, restart-resilience or Native-Linux slices.
