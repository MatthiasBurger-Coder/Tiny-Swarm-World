# Test Results

Status: `BASELINE_VERIFIED_IMPLEMENTATION_NOT_RUN`

## Baseline

Command:

```bash
PYTHONPATH=src python3 -m unittest \
  tests.domain.ingress.test_desired_state \
  tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml \
  tests.integration.test_service_access_routing \
  tests.integration.test_observability_routing \
  tests.integration.test_tiny_swarm_app_routing \
  tests.live.browser_e2e_contract \
  tests.live.test_post_install_browser_live.StaticPostInstallLiveSuiteTest
```

Result: `PASS`

- 77 tests
- 6.247 seconds
- no live infrastructure
- no local env-file read

## Implementation

Not run. `workflow execute` must replace this section with exact targeted test
commands, counts and results for every slice.

## Authoring Full Regression

Command:

```bash
python3 tools/quality_gate.py quality
```

Result: `PASS`

- lint: pass
- arch-lint: 3 contracts kept
- arch-tests: pass
- typecheck: no issues in 463 source files
- test: 1,336 tests passed, 28 skipped
- no live infrastructure was invoked
- `python3` used the existing WSL virtual-environment toolchain; its
  host-specific absolute path is intentionally omitted
