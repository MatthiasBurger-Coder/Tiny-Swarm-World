# Issue #201 Live Validation Report

Date: 2026-08-05

## Runs

| Run | Command | State | Result |
|---|---|---|---|
| 1 | `./install.sh --headless --confirm-reset --non-interactive-live-approval` | `LIVE_BLOCKED_BEFORE_MUTATION` | Checkout filesystem guard rejected the Windows-mounted `/mnt/d` path. |
| 2 | `./install.sh --headless --confirm-reset --non-interactive-live-approval --allow-wsl-windows-filesystem` | `LIVE_FAILED_AFTER_MUTATION` | Fresh reset passed and three Incus nodes were created/verified; Docker installation failed because LXC APT/HTTP egress was unavailable. |
| 3 | `./tsw network repair --linux-forwarding --apply` | `LIVE_VERIFIED` | Targeted Incus forwarding repair applied; LXC HTTP egress was verified. |
| 4 | `./tsw --live --approve-live --allow-wsl-windows-filesystem --lxc-backend incus --service-profile service-access setup run` | `LIVE_VERIFIED` | All setup phases completed, including deployment and platform verification. |

## Redacted evidence

- Failed-run evidence directory: `.tiny-swarm-world/evidence/installation-tests/wsl2/20260805T045023Z/`
- Final setup result: `completed` (recorded in the governed workflow progress log).
- Runtime: `wsl2`
- Service profile: `service-access`
- Provider: `lxc_native` / Incus
- Intermediate failure: `docker_install_failed` / `apt_repository_unreachable` on all three nodes.
- Repair result: `LIVE_VERIFIED`; `incusbr0` forwarding persistence installed and manager HTTP egress verified.
- Final setup phases: preflight, host prepare/verify, platform init/reconcile/expose,
  deployment bootstrap/apply/verify, artifacts prepare/verify, and platform verify
  all completed.
- Final platform verification: 26 preflight checks passed; three nodes are Ready,
  Docker is present on all nodes, Swarm membership is verified, 18 proxy devices are
  present, and the Portainer local endpoint is registered.
- Service state: 18 long-running services are healthy; the Pulsar manager bootstrap
  job completed successfully.
- Browser/Selenium: not required by Issue #201; not run.
- External SonarQube quality gate: not applicable to this governance-only issue;
  service deployment was completed and verified by the platform workflow.
- Windows-side localhost HTTP smoke: not independently verified because the
  elevated PowerShell portproxy check is a separate external gate.
- Documented `doctor-portproxy.ps1` check: blocked before inspection because the
  current PowerShell session is not elevated.

No secret values, raw logs, credentials, or tokens are included here. The
attached `live-installation.env` SHA-256 was unchanged by the run.

## Decision

`LIVE_VERIFIED` for the authorized installation and platform verification.
`EXTERNAL_GATE_UNAVAILABLE` remains only for the separate elevated Windows
portproxy/localhost smoke check; it does not invalidate Issue #201 completion.
