# Nightly Classic Live recovery — 2026-10-18

Final result: `LIVE_VERIFIED` for the existing protected WSL2 test target at
commit `5389646b18bab1d77fcb99d369427a7d710321e7`.

## Failure and repair

- [Original run](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/actions/runs/38699450369):
  no runner assigned; GitHub cancelled after 24 hours waiting for a runner.
- The local runner had no persistent service. Reconnection reported that
  GitHub had deleted its inactive registration. Registered `tsw-protected-wsl2`
  again with its existing labels and enabled the systemd user service
  `actions.runner.tsw-classic.service`, with user lingering enabled.
- [First validation](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/actions/runs/39106569349):
  setup, readiness, authenticated acceptance and reconcile passed. Update failed
  because `jenkins:rc1-proof-b-20260913` was absent from the target registry.
  Canonical recovery restored and verified the original image. Changed the
  GitHub repository variable `TSW_CLASSIC_UPDATE_TO_IMAGE` to the available
  `127.0.0.1:13500/jenkins:compat363-bdd73f58` compatibility image.
- Cancelled the intervening scheduled run
  [39107074224](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/actions/runs/39107074224)
  during authenticated tests because it started with the old configuration.
- [Second validation](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/actions/runs/39107132668):
  update and its acceptance tests passed. Recovery observation failed when an
  Incus command returned 255. The Incus journal recorded
  `Failed to retrieve PID of executing child process` at 07:24:00 UTC.
  Swarm subsequently completed the rollout; another canonical recovery check
  verified convergence with `mutation=not_needed`. Repeated the complete chain
  once after verifying this state. No product retry behavior was changed.

## Successful verification

[Run 39107610200](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/actions/runs/39107610200)
completed successfully on runner `tsw-protected-wsl2` (registration ID 25).
Both GitHub jobs passed. The live chain ran from 07:25:50 to 07:31:25 UTC.
All 14 operations returned exit code zero, including setup, verification,
reconcile, update, recovery and their readiness/authenticated checks.
Each authenticated phase passed 25 live tests and seven API checks with no
errors, failures or skips. Recovery restored Jenkins to
`127.0.0.1:13500/jenkins:0.2.0`. The runner service remained active afterward.

GitHub artifact: `classic-live-evidence-39107610200` (ID `12129640586`,
14-day retention). Its current-run summary is
`20261018T072550.876822Z/run-summary.json`, status `LIVE_VERIFIED`, SHA-256
`7d94c4a01ad573b3b88f3e2e55fce77abf360aac8cbaaec7f32c9f862d6430d7`.

This verifies the configured existing-installation chain and a distinct
packaging-image update, not a clean installation or Jenkins binary-version
upgrade. The earlier Incus failure remains recorded; this successful retry
does not establish that the Incus process-creation issue is fixed. Automatic
runner startup requires the WSL distribution and host to be running.

## Publication verification

`.venv/bin/python tools/quality_gate.py quality` passed, including 43
architecture tests and the 2,631-test suite (18 optional checks skipped).
The initial system-Python invocation failed three installer tests because
their isolated `HOME` hid user-site runtime dependencies. All three passed
when run explicitly with the project Venv, followed by the successful complete
gate in that Venv. No product or test files were changed to resolve this local
environment problem. `git diff --check` also passed.
