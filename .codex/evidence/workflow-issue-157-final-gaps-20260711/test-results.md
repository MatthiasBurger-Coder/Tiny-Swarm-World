# Test Results

Status: `TARGETED_AND_ALL_REQUIRED_LOCAL_GATES_PASS`

All recorded tests were static or mocked and ran without live infrastructure
or reading the referenced local environment file.

## Slice 01: Model And Optional Routes

```text
tests.domain.ingress.test_desired_state
PASS - 10 tests

tests.integration.test_optional_service_routing
PASS - 9 tests

tests.integration.test_service_access_routing
PASS - 4 tests

tests.architecture.test_hexagonal_imports
PASS - 18 tests
```

Coverage includes Prometheus, Grafana, app, and API enabled/disabled cases,
exact Traefik labels, shared app/API upstream behavior, routed links, effective
health targets, skip semantics, and temporary fixture isolation.

## Slice 02: Productive Routing Evidence

```text
tests.application.services.deployment.test_write_effective_access_model_evidence
PASS - 3 tests

tests.infrastructure.adapters.repositories.test_routing_evidence_local_repository
PASS - 3 tests

tests.infrastructure.test_composition
PASS - 87 tests
```

Coverage includes the exact allowlist, credential-value redaction,
deterministic sorting, UTC injection, parent creation, private modes where
supported, atomic replacement, old-target preservation, temporary cleanup,
selected-profile reuse, and failure before stack apply.

## Slice 03: Dashboard Renderer

```text
tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml
tests.integration.test_service_access_routing
PASS - 50 tests
```

Coverage includes default and optional renderer output, model link equality,
row count, no preferred `10080`/`10443`, secret sentinels absent, labels and
Infisical item references present, core-route stability, and the committed
default fallback drift test.

## Slice 04: Dynamic Browser Matrix

```text
tests.live.browser_e2e_contract
PASS - 9 tests

tests.live.test_post_install_browser_live.StaticPostInstallLiveSuiteTest
PASS - 17 tests

tests.live.test_observability_browser_e2e
tests.live.test_tiny_swarm_app_browser_e2e
PASS - 4 tests
```

Coverage includes dynamic membership, enabled optionals, disabled/non-profile
and stale exclusion, all four route states, explicit missing failure,
deterministic suite result, opt-in guards, and static prerequisite skips.

## Integrated G2 Regression

```text
python3 tools/quality_gate.py quality
PASS
- Ruff: pass
- Import Linter: 3 contracts kept, 0 broken; 290 files, 657 dependencies
- Architecture tests: 18 passed
- Mypy: no issues in 471 source files
- Unittest: 1,361 run; 1,333 passed; 28 skipped
```

## Slice 05 Final Commands

```text
lint: PASS
arch-lint: PASS - 290 files, 657 dependencies, 3 kept, 0 broken
arch-tests: PASS - 18 tests
typecheck: PASS - no issues in 471 source files
test: PASS - 1,361 run; 1,333 passed; 28 skipped
quality: PASS - all sub-gates green; 1,361 run; 1,333 passed; 28 skipped
```

Each command ran independently in WSL on 2026-07-11. Live Selenium remained
not run because current consent and approved prerequisites were not supplied.
