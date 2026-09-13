# Test Results — #344 / ARCH-03.01

Verification date: 2026-09-13
Verification state: local, Linux/WSL, no live infrastructure

| Command | Result | Evidence |
|---|---|---|
| `git diff --check` | PASS | No whitespace errors. |
| `python3 tools/quality_gate.py arch-lint` | PASS | Import-linter: 3 contracts kept, 0 broken; 370 files and 859 dependencies analyzed. |
| `python3 tools/quality_gate.py arch-tests` | PASS | 18 architecture tests passed. |
| `python3 tools/quality_gate.py quality` | PASS | Verification policy, lint, arch-lint, arch-tests, typecheck, and test all completed successfully. |
| Full test phase within quality gate | PASS | 2066 tests passed, 18 skipped. |
| AST package dependency inspection | PASS / recorded | Confirmed root mixed-import set and the composition strongly connected component documented in the audit. |

The full test run emitted expected mocked failure/status diagnostics and
non-blocking type-check notes, but ended with `OK (skipped=18)` and exit code
0. No live Incus, Docker Swarm, compose, SSH, bootstrap, or external service
command was run.
