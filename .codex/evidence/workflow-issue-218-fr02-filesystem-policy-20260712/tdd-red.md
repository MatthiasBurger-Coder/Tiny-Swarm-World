# FR-2 TDD RED Checkpoint

Date: `2026-07-12`
Baseline publication head: `529ae16677edefa6fe5f0543b8adadbfda586db6`
Live infrastructure: `NOT_RUN`
Decision: `EXPECTED_RED_CONFIRMED`

## Command

```bash
PYTHONPATH=src python3 -m unittest \
  tests.domain.preflight.test_project_filesystem \
  tests.application.services.platform.host.test_evaluate_project_filesystem \
  tests.application.services.platform.host.test_authorize_project_filesystem \
  tests.infrastructure.adapters.host.test_project_filesystem_inspector \
  tests.infrastructure.adapters.repositories.test_project_filesystem_evidence_local_repository \
  tests.application.services.platform.test_preflight_service \
  tests.infrastructure.test_composition \
  tests.integration.test_host_platform_paths \
  tests.architecture.test_host_detection_boundaries \
  tests.test_installer \
  tests.test_install_script \
  tests.test_package_entrypoint
```

## Result

Expected `FAIL`: 211 tests ran in 8.241 seconds with 3 failures and 41 errors.

Root failure groups are exactly the unimplemented FR-2 contracts:

- missing `domain.project_filesystem` and inspector/evidence ports/services;
- missing mountinfo inspector and protected evidence repository modules;
- `PreflightService` lacks evaluator/authorizer/project-path integration;
- composition builders lack `allow_wsl_windows_filesystem` propagation;
- installer options, authorization checkpoint, and bootstrap closure are absent;
- CLI parser and setup/platform/preflight propagation lack the exact flag;
- install-script fixture cannot copy the deliberately declared new bootstrap
  modules until production implementation creates them;
- current mock-call failures show the expected missing propagation keyword.

The RED did not run Incus, Docker, Docker Swarm, Windows commands, networking,
deployment, or services. Product implementation is now authorized only within
the Slice-01 allowlist and locks.
