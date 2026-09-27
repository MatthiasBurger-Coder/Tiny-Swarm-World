# Test results

- `PYTHONPATH=src python3 -m unittest tests.application.services.platform.host.test_prepare_host tests.infrastructure.test_host_preparation_composition`: PASS, 8 tests on final tree.
- `python3 tools/quality_gate.py quality` (first run): PASS, 2270 tests, 18 skipped. A focused test was added while this run was active, so it is not the final-tree authority.
- `python3 tools/quality_gate.py quality` (settled-tree run): FAIL, 2271 tests, 18 skipped, one unrelated setup timeout assertion in `tests.application.services.setup.test_operation_result_integration.OperationResultIntegrationTests.test_timeouts_retain_prior_confirmed_work`. Verification policy, lint, import contracts, architecture tests, and typecheck passed. The failing test passed immediately in isolation with the same code (1 test, 0.408 seconds), indicating timing sensitivity under the full suite.
- `python3 tools/quality_gate.py quality` (settled-tree retry): PASS, 2271 tests, 18 skipped; verification policy, Ruff lint, 6 import contracts, 30 architecture tests, mypy, and full unit suite passed.
- `python3 tools/quality_gate.py lint`: PASS after final focused test edit.
- `python3 tools/quality_gate.py typecheck`: PASS after final focused test edit, 705 source files.
- `git diff --check`: PASS.

Live infrastructure: LIVE_NOT_APPLICABLE for this adapter selection refactor; no live host preparation was run. External SonarQube: EXTERNAL_GATE_NOT_APPLICABLE to local implementation verification; no external result is claimed.
