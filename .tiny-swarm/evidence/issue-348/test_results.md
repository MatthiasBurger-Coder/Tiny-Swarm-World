# Test Results — #348 / ARCH-03.05

Verification date: 2026-09-13

Verification state: local Linux/WSL; no live infrastructure

| Command / check | Result | Evidence |
|---|---|---|
| `PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_runtime_profile tests.application.services.platform.test_node_provider_selection tests.infrastructure.test_composition` | PASS | 125 tests passed. |
| `python3 -m ruff check src/tiny_swarm_world/application/services/platform/runtime_profile.py src/tiny_swarm_world/application/services/platform/__init__.py src/tiny_swarm_world/infrastructure/composition_runtime.py tests/application/services/platform/test_runtime_profile.py` | PASS | No lint findings. |
| `git diff --check` | PASS | No whitespace errors. |
| `python3 tools/quality_gate.py quality` | PASS | Verification policy, Ruff, import-linter, architecture tests, Mypy, and 2,076 tests passed; 18 skipped. |
| Live Incus, Docker Swarm, compose, browser, or external service checks | NOT APPLICABLE | Pure resolver and mocked/local composition verification. |
