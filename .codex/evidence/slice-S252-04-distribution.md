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
