# RC1 WSL2 Restart Resilience

## Scenario record

| Field | Value |
|---|---|
| Scenario ID | RC1-08 WSL2 RESTART RESILIENCE |
| Commit SHA | `27ce3960da98a9ba124fd3f9ff5e003b13e89c60` |
| Branch | `feature/classic-public-beta-rc1-stabilization` |
| Host type | WSL2 / Incus / LXC-native Docker Swarm |
| Operating system | Ubuntu on WSL2, kernel `6.18.33.2-microsoft-standard-WSL2` |
| Restart boundary | `wsl.exe --shutdown` |
| Final result | `PASS` |

## Executed recovery sequence

1. `wsl.exe --shutdown` completed successfully.
2. Fresh `PYTHONPATH=src python3 tools/install_debugger.py --live` ran from
   `2026-08-23T13:58:40Z` to `13:58:52Z`, exit code `0`.
3. Existing `platform reconcile` ran from `2026-08-23T13:58:58Z`; it waited
   for Incus readiness through the new `admin waitready` probe and returned
   `completed`, `mutation: no_op`, `verification: verified`, exit code `0`.
4. Existing `platform verify` returned `completed`, `verification: verified`,
   with 26 checks, all three nodes, 18 proxy devices, zero drift/missing/
   unknown/failed devices, and a ready Portainer endpoint.
5. Existing live post-install acceptance ran with
   `TSW_RUN_POST_INSTALL_BROWSER_LIVE=1` and completed 29 tests with exit code
   `0`.

## Application readiness evidence

The live acceptance runner observed application warm-up explicitly before its
assertions. It used 22 bounded attempts over 71.436 seconds with a 180-second
maximum and 2-second polling interval. The final readiness record has no
pending services and `result: passed`:

`.tiny-swarm-world/evidence/classic-public-beta-rc1/20260823T135937Z/summary.json`

The final live evidence contains passing HTTP routes, DNS resolution, HTTPS/TLS
verification, Infisical management, SonarQube credential checks, Pulsar API
authentication, and Pulsar Manager login checks. No secret value was recorded.

## Defect loop

The first post-fix restart attempt exposed a second RC1 blocker: the platform
was back, but application services were still warming up when the one-shot
acceptance started. The existing platform verification checked node/proxy
readiness but did not establish application-level readiness for the live
acceptance suite.

Smallest fix: add a bounded, redaction-safe application readiness gate to the
existing live acceptance runner. It polls the actual configured service/TLS
routes and the Pulsar Manager login readiness, records attempts and elapsed
time, and fails explicitly on timeout. It does not redeploy stacks, manually
repair services, skip checks, or turn an incomplete state into PASS.

Local regression and quality evidence is recorded in
`.codex/evidence/rc1-blocker-003-fix.md`.

**Final scenario result: RC1-08 PASS.**
