# Test Results — #345 / ARCH-03.02

Verification date: 2026-09-13
Verification state: local, Linux/WSL, no live infrastructure

| Command | Result | Evidence |
|---|---|---|
| `git diff --check` | PASS | No whitespace errors. |
| `python3 tools/quality_gate.py arch-lint` | PASS | 5 contracts kept, 0 broken; 370 files and 858 dependencies analyzed. |
| `python3 tools/quality_gate.py arch-tests` | PASS | 22 architecture tests passed. |
| `python3 tools/quality_gate.py quality` | PASS | Verification policy, lint, arch-lint, arch-tests, typecheck, and test completed successfully. |
| Full test phase within quality gate | PASS | 2070 tests passed, 18 skipped. |

The full gate emitted existing mocked negative-path diagnostics and mypy
annotation notes but exited successfully. No Incus, Docker Swarm, compose,
bootstrap, or external-service command was run.
