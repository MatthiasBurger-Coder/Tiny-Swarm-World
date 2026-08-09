# Issue #190 — Test Results

Focused verification:

- Ruff on changed source/tests: PASS.
- Stack prerequisite, asset-transfer, runtime and architecture tests: PASS (66 tests).
- git diff --check: PASS.

Required local quality gate:

- verification-policy: PASS
- lint: PASS
- arch-lint: PASS (3 contracts kept, 0 broken)
- arch-tests: PASS
- typecheck: PASS (Success: no issues found in 599 source files)
- full test suite: PASS (1691 passed, 28 skipped)

Live Docker/Swarm, browser/Selenium and external quality-system checks were
not executed and are not claimed.
