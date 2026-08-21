# Issue #252 — S252-07 Consolidation

- Workflow: `issue-252-classic-public-beta-rc1-20260818`
- Slice: `S252-07` — WSL2 failure, recovery and restart resilience
- Branch: `feature/classic-public-beta-rc1-stabilization`
- Commit under final test: `25b9d79077f0ba49b17d75c003feb25e74b25d3e`
- Host: WSL2 / Ubuntu / systemd / Incus / Docker Swarm
- Source fix: `src/tiny_swarm_world/infrastructure/adapters/network/host_network_repair.py`
- Regression test: `tests/infrastructure/adapters/network/test_host_network_repair.py`
- Composition wiring: unchanged; `composition.py` was not the defect location.

## Scenario results

### Missing configuration — fail closed

- Command: `unset TSW_INFISICAL_LOGIN_EMAIL && ./tsw --json --preflight --service-profile service-access --allow-wsl-windows-filesystem`
- Environment: required live variables sourced from the ignored local env file;
  `TSW_INFISICAL_LOGIN_EMAIL` was removed in-process only.
- Start: `2026-08-21T22:49:26+02:00`
- End: `2026-08-21T22:49:39+02:00`
- Duration: 13 seconds
- Exit code: `1`
- Result: `FAILED` before mutation; the missing mandatory secret was reported
  with remediation. No live state was changed.

### Deterministic partial/ambiguous-state contract

- Command: `PYTHONPATH=src .venv/bin/python -m unittest tests.e2e.classic.test_lifecycle_contract`
- Start: `2026-08-21T22:49:25+02:00`
- End: `2026-08-21T22:49:28+02:00`
- Duration: 3 seconds
- Exit code: `0`
- Result: 12 lifecycle tests passed; fail-closed and same-identity recovery
  semantics remain covered.

### First restart observation and reproduced defect

- Host command: `wsl.exe --shutdown`
- The first post-restart diagnostics at `2026-08-21T22:50:09+02:00` showed
  WSL2/systemd available, but `tsw-incus-forwarding.service` had failed during
  boot because `incusbr0` did not yet exist. The three Incus nodes were stopped.
- Classification: `RC1_BLOCKER` — restart resilience required manual recovery
  because the persistence unit remained failed.
- Canonical recovery command:
  `./tsw --live --approve-live --json --service-profile service-access --allow-wsl-windows-filesystem platform reconcile`
- Recovery start: `2026-08-21T22:51:09+02:00`
- Recovery end: `2026-08-21T22:51:17+02:00`
- Duration: 8 seconds
- Exit code: `0`
- Result: `no_op` / `verified`; all three existing nodes were reused and
  returned to `RUNNING`. The forwarding unit still showed failed, proving the
  boot race rather than a missing platform resource.

### Root-cause fix

The generated forwarding script now waits for `ip link show dev "$BRIDGE"`
for at most 30 attempts with a two-second delay, then exits explicitly with a
bounded failure message. The systemd oneshot has `TimeoutStartSec=75s`. This
keeps the repair idempotent and fail-closed while allowing Incus time to create
the bridge after systemd starts the unit.

Focused regression command:
`PYTHONPATH=src .venv/bin/python -m unittest tests.infrastructure.adapters.network.test_host_network_repair tests.e2e.classic.test_lifecycle_contract`

Result: 27 tests passed; `git diff --check` passed.

### Installation of the fix and committed second restart

- Privileged canonical repair command was executed in WSL as root because the
  non-root sudo path timed out while installing the unit file:
  `PYTHONPATH=src .venv/bin/python -m tiny_swarm_world --live --approve-live --json --service-profile service-access --allow-wsl-windows-filesystem network repair --linux-forwarding --apply`
- Start: `2026-08-21T22:57:45+02:00`
- End: `2026-08-21T22:57:53+02:00`
- Duration: 8 seconds
- Exit code: `0`
- Result: forwarding script and systemd unit installed; rules applied;
  Incus egress verified.

- The same committed fix was installed once more at
  `2026-08-21T23:06:25+02:00` and completed at
  `2026-08-21T23:06:33+02:00` (8 seconds, exit code `0`).

- Host command: `wsl.exe --shutdown`
- Start: `2026-08-21T23:06:42+02:00`
- End: `2026-08-21T23:07:08+02:00`
- Duration: 26 seconds
- Exit code: `0`
- Post-restart diagnostics command:
  `python3 tools/install_debugger.py --live`
- Diagnostics: `2026-08-21T23:07:12+02:00` to approximately
  `2026-08-21T23:07:23+02:00`, exit code `0`.
- Result: systemd became ready; the forwarding service was initially
  `activating` while the bridge came up, then `active` at
  `2026-08-21T23:07:53+02:00`; `systemctl --failed` was empty.

- Canonical recovery command:
  `PYTHONPATH=src .venv/bin/python -m tiny_swarm_world --live --approve-live --json --service-profile service-access --allow-wsl-windows-filesystem platform reconcile`
- Start: `2026-08-21T23:07:58+02:00`
- End: `2026-08-21T23:08:08+02:00`
- Duration: 10 seconds
- Exit code: `0`
- Result: `no_op` / `verified`; all three existing Incus nodes were reused.

### Post-restart acceptance

- Service state: `tsw-incus-forwarding.service` active; no failed systemd
  units.
- Incus: three expected nodes `RUNNING`.
- Docker Swarm: one leader and two Ready/Active workers.
- Stacks: nine expected stacks present.
- Services: expected services ready; the Pulsar bootstrap one-shot remained
  the expected completed `0/1` service.
- Platform verify command:
  `PYTHONPATH=src .venv/bin/python -m tiny_swarm_world --json --service-profile service-access --allow-wsl-windows-filesystem platform verify`
- Start: `2026-08-21T23:08:13+02:00`
- End: `2026-08-21T23:08:29+02:00`
- Duration: 16 seconds
- Exit code: `0`
- Result: 26 checks verified; all nodes verified; 18 proxy devices present with
  zero drift/missing/unknown; Portainer endpoint registered and ready.

- Classic acceptance command:
  `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests/e2e/classic -t .`
- Start: `2026-08-21T23:08:34+02:00`
- End: `2026-08-21T23:08:42+02:00`
- Duration: 8 seconds
- Exit code: `0`
- Result: 92 tests ran, 17 expected skips, 0 failures.

## Defect disposition

- Defect: boot ordering race between systemd and asynchronous Incus bridge
  creation.
- Severity: `RC1_BLOCKER` when first reproduced.
- Smallest fix: bounded bridge readiness wait plus aligned systemd timeout in
  the existing forwarding adapter.
- Regression: source contract assertions plus the full deterministic lifecycle
  suite; live second-restart acceptance passed.
- Current status: fixed and reverified live.

## Evidence and redaction

- Evidence files: this consolidation record and
  `.codex/evidence/slice-S252-07-distribution.md`.
- Live command output was inspected only for statuses, counts, identities and
  readiness. Secret values, tokens, auth headers and the local env-file
  contents were not printed or copied.
- The repository-local live env file remains private and ignored.
- The historical Fresh Install failure remains an open S252-04/S252-03
  lifecycle limitation; this slice does not relabel it as a fresh-install
  success.
