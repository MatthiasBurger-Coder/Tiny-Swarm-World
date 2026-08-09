# Issue #191 — Test Results

Focused verification:

- Ruff on changed source/tests: PASS.
- Builder, boundary, preflight and node-provider regression tests: PASS (67 tests).
- git diff --check: PASS.

Required local quality gate: python3 tools/quality_gate.py quality

- verification-policy: PASS
- lint: PASS
- arch-lint: PASS (3 contracts kept, 0 broken)
- arch-tests: PASS
- typecheck: PASS (Success: no issues found in 595 source files)
- full test suite: PASS (1685 passed, 28 skipped)

Verification state is local only. Live Incus/LXC, Docker/Swarm, browser/
Selenium and SonarQube/external quality checks were not executed.
