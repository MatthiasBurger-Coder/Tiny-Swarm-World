# Issue #218 — Test results

Date: 2026-08-04. All Python commands were executed inside WSL as required by
the repository operating model.

## Full local quality gate

Command:

```text
wsl.exe bash -lc 'cd /mnt/d/Projects/Tiny-Swarm-World && python3 tools/quality_gate.py quality'
```

Result: **PASS**

- lint: PASS
- architecture lint: PASS (`3` contracts kept, `0` broken)
- architecture tests: PASS
- typecheck: PASS (`526` source files, no issues)
- complete Python suite: PASS (`1576` tests, `28` skipped; 124.501 seconds)

## Targeted native/host regression

Command:

```text
PYTHONPATH=src python3 -m unittest \
  tests.domain.preflight.test_host_environment \
  tests.domain.preflight.test_resources \
  tests.application.services.platform.host.test_detect_host_environment \
  tests.application.services.platform.host.test_prepare_host \
  tests.application.services.platform.test_preflight_service \
  tests.infrastructure.adapters.host.test_host_environment_detector \
  tests.infrastructure.adapters.host.test_host_preparation \
  tests.infrastructure.adapters.host.test_windows_command_runner \
  tests.infrastructure.adapters.network.test_host_network_probe \
  tests.infrastructure.adapters.network.test_host_network_repair \
  tests.infrastructure.adapters.preflight.test_host_preflight_probe \
  tests.infrastructure.adapters.preflight.test_windows_wsl_bridge_state \
  tests.integration.test_host_platform_paths \
  tests.architecture.test_host_detection_boundaries
```

Result on the actual Ubuntu 24.04.4 native Linux VM: **PASS**, `202` tests,
`0` errors, `0` failures, `0.356s`, `OK`.

The native host detector and composed native host-preparation service also
returned `SUCCESS` for `prepare`, `verify` and `cleanup`; evidence recorded
`windows_command_runner=not_selected` and `mutation=none`.

## Windows bridge contract tests

Pester command:

```text
Invoke-Pester -Path tests/windows/tws-wsl-bridge.Tests.ps1
```

Result: **PASS**, `43` passed, `0` failed, `0` skipped. The suite includes the
changed-WSL-IP stale-tuple test and read-only service-drift rejection test.

## Live installer and workflow tests

- Focused current-source WSL2 `artifacts verify`: **PASS**, exit `0`; all 15
  image contracts were available and Nexus Docker/Maven repositories were
  reachable.
- Current-source WSL2 `deployment apply`: **PASS**, exit `0`; all nine profile
  stacks were registered and all persistent services reached their desired
  replicas. The `pulsar-manager-bootstrap` one-shot job reached `Complete` and
  is intentionally shown by Docker as `0/1` after completion.
- Current-source WSL2 `deployment verify`: **PASS**, exit `0`; all nine service
  endpoint groups returned expected application statuses.
- Current-source WSL2 `platform verify`: **PASS**, exit `0`; 26 preflight checks,
  three Docker runtimes, Swarm membership, 18 proxy devices and Portainer local
  endpoint were verified read-only.
- Controlled live 8-GiB cgroup preflight: **PASS as a blocking test**;
  `effective_memory_bytes=8589934592`, `RESOURCE-STRUCTURED=INSUFFICIENT`,
  overall `RESOURCE_GATED`, expected exit `1`, and unchanged Incus/Docker
  snapshots before and after.
- Separate `deployment verify` and `platform verify`: **PASS**, independent
  invocations with independent exit codes.
- Explicit deployment-verify timeout test: **PASS**; a configured 3-second
  budget returned typed `timed_out` status with partial evidence and did not
  start later workflows.
- Windows-side stable DNS/HTTPS: **PASS** for all nine active `*.tsw.local`
  routes; TCP/443 and expected HTTP statuses were observed from Windows.
- Read-only snapshot: **PASS**; with the bridge heartbeat paused, the strict
  elevated before/after snapshot showed equal Incus/Swarm, Docker
  stack/service/config/secret metadata, portproxy, managed firewall rules,
  managed hosts block and protected bridge-state hash.
- Controlled `wsl --shutdown` IP exercise: the real address remained
  `172.25.81.206`, while the controlled live changed-IP adapter/Pester scenario
  passed the required stale-tuple reconciliation.
- Opt-in Selenium browser contract: **SKIPPED**, 9 route checks because the WSL
  test environment has neither Selenium nor a Linux Firefox driver. The project
  documents this suite as opt-in; Windows-side HTTPS checks were performed
  independently and passed for all nine active routes.
- `host verify`: **PASS**, exit `0`, bounded read-only diagnostics collected.
- `host prepare` first and second run: **PASS**, both verified no-op after the
  bridge was stable.

The latest test run also covers explicit `nproc`/`free -b` resource signals,
lazy native/WSL adapter construction, static-preflight no-write behavior, and
the configurable bridge-state path.

## Release lifecycle gates still pending

- SonarCloud is a GitHub Action requiring a configured remote token/check;
  `sonar-scanner` is not installed in WSL and neither `SONAR_TOKEN` nor
  `SONAR_CLOUD_TOKEN` is configured. No green check is available for this
  unmerged branch.
- A real WSL restart did not produce a changed address; changed-IP migration is
  therefore evidenced by the controlled live adapter/Pester simulation.
- Native Linux host-platform regression is complete; the disposable VM did not
  run a full Docker/Incus deployment because its required runtime, network and
  resource capacity were absent.
- SonarCloud and post-merge/main verification require the remote publication
  lifecycle and are not locally reproducible.
