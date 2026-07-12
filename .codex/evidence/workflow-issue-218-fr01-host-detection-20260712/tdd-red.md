# Slice 01 TDD Red Checkpoint

Date: `2026-07-12`

Command:

```bash
PYTHONPATH=src "$TSW_QUALITY_PYTHON" -m unittest \
  tests.domain.preflight.test_host_environment \
  tests.application.services.platform.host.test_detect_host_environment \
  tests.infrastructure.adapters.host.test_host_environment_detector
```

Result: expected `FAIL` before production implementation.

- `HostEnvironmentSignals` was not yet exported.
- `application.services.platform.host` did not yet exist.
- `infrastructure.adapters.host` did not yet exist.

The failures prove that the new FR-1 contract tests preceded their production
types and adapters. No live command or infrastructure mutation was executed.

## Legacy-consumer and CLI red checkpoint

The exact expanded regression-first command was:

```bash
PYTHONPATH=src "$TSW_QUALITY_PYTHON" -m unittest \
  tests.domain.preflight.test_host_environment \
  tests.application.services.platform.host.test_detect_host_environment \
  tests.application.services.platform.test_preflight_service \
  tests.application.services.network.test_host_integration \
  tests.infrastructure.adapters.host.test_host_environment_detector \
  tests.infrastructure.adapters.preflight.test_host_preflight_probe \
  tests.infrastructure.adapters.network.test_host_network_probe \
  tests.infrastructure.test_os_types \
  tests.infrastructure.test_composition \
  tests.architecture.test_host_detection_boundaries \
  tests.integration.test_host_platform_paths \
  tests.test_installer \
  tests.test_package_entrypoint
```

For both checkpoints, `TSW_QUALITY_PYTHON` resolved to the pre-existing shared
WSL virtual-environment interpreter. Its host-specific absolute location is
intentionally omitted from general evidence.

Result: expected `FAIL` — 288 tests ran, with 5 assertion failures and 28
errors. The named failing groups were the new classifier table and report
schema tests, `DetectHostEnvironment` and detector-reader tests, typed
preflight fallback tests, `OsTypes.detect_current` WSL1/ambiguous rejection,
unsupported network short-circuit tests, composition builder/injection tests,
installer stop-before-bootstrap tests, host CLI stdout/exit/no-mutation tests,
the host-boundary architecture test, and native/WSL simulated integration
tests. These failures identified the not-yet-implemented detector injection,
fail-closed legacy mapping, structured preflight fields, early host CLI,
composition builders, unsupported network result, and removal of duplicate WSL
classifiers. Existing unrelated tests continued to run; no live command was
executed.
