# Issue #252 — S252-04 Distribution Decision

- Workflow ID: `issue-252-classic-public-beta-rc1-20260814`
- Slice ID: `S252-04`
- Slice title: WSL2 diagnostics and Fresh Install
- Execution mode: `sequential`
- Dependency: `S252-03` checkpoint `97cf7c4e`; local deterministic gates pass.
- Owner stream: Senior DevOps / WSL2 live evidence.
- Review streams: Senior System Architect, Senior Tester, Live Evidence
  Validation Expert and real Senior DevOps review-only subagent.
- Parallelization: forbidden. This slice owns one WSL2 target, one evidence
  root, one runtime state and one rollback boundary.
- Expected live commands (currently blocked): `python3
  tools/install_debugger.py --live` and `./install.sh --headless
  --confirm-reset --non-interactive-live-approval`.
- Missing authorization: explicit live consent, target ownership,
  disposable/recoverable WSL2 target, prerequisite confirmation, redaction
  readiness and cleanup/rollback plan.
- Current state: `LIVE_CONSENT_MISSING` / `BLOCKED_BEFORE_MUTATION`.
- Stop condition triggered: the root governance forbids Incus, Docker, Swarm,
  installer, network, service and browser operations without explicit live
  authorization. Administrator PowerShell access is not granted by this
  workflow and is not a substitute for Linux/WSL consent.
- No worktree or implementation stream was started; no live command was run.
- Resume condition: the user explicitly authorizes the WSL2 live slice and
  provides or confirms the required target, prerequisites, redaction path and
  rollback/cleanup plan. Then rerun S3/S3D and this gate before execution.

## Resume gate — 2026-08-15

- Explicit live authorization: `GRANTED` by the user in the current turn,
  including reset-capable WSL2 installation authority.
- Target: user-controlled local WSL2 instance at the current checkout; live
  validation remains serialized because it shares Incus, Docker, ports,
  credentials and evidence paths.
- Redaction: protected local evidence paths are used; raw secrets and raw
  service output are not copied into public evidence.
- Preflight: `python3 tools/install_debugger.py --live` exit `0`;
  `python3 -m tiny_swarm_world --preflight
  --allow-wsl-windows-filesystem` with the ignored local environment loaded
  exit `0` (`PASSED`). The wrapper `tools/preflight.py` cannot forward the
  filesystem override and therefore remains blocked by design.
- Stream review: Senior DevOps, Senior System Architect and Senior Tester
  review-only agents returned their findings. The reviews are now superseded
  for consent by the explicit user authorization; their safety findings remain
  applicable.
- Execution mode remains `sequential`; no parallel live stream or worktree is
  allowed for this target.
- Branch note: the prescribed hierarchical branch cannot be created because
  the repository already owns the local `release` ref. No branch ref was
  renamed or deleted; the live run is being kept on the clean issue workflow
  branch and no product source changes are made.
- Next mutating command, if the live gate is still green:
  `./install.sh --headless --confirm-reset --non-interactive-live-approval
  --allow-wsl-windows-filesystem`.
