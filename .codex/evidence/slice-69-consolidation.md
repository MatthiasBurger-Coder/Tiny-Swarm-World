# Slice 69 Consolidation

- workflow id: issue-69-host-evidence-directories-20260614
- slice id: issue-69
- slice title: Use host-specific evidence directories

## Stream Results

- runtime: `install.sh` now resolves `wsl2` or `native_linux` before creating installation evidence.
- tests: focused wrapper and debugger tests cover native Linux and WSL2 evidence directory selection.
- documentation: README, installation guide, and troubleshooting guide document the host-runtime evidence naming rule.

## Review Results

- accepted findings: the fixed WSL2 path lived in `install.sh`, `tools/install_debugger.py`, and matching tests/docs.
- rejected findings: none.
- files changed per stream:
  - runtime: `install.sh`, `tools/install_debugger.py`
  - tests: `tests/test_install_script.py`, `tests/test_install_debugger.py`
  - documentation: `README.md`, `documentation/user_guide/installation.adoc`, `documentation/user_guide/troubleshooting.adoc`
- conflicts found: none.
- conflicts resolved: none.
- SonarQube findings and fixes: pending CI; local slice contains no secret values or live infrastructure calls.
- documentation updates: completed.
- final integration decision: accepted pending full quality gate and push auto lifecycle.

## Tests Executed

- `wsl.exe bash -lc "cd /mnt/d/Projects/Tiny-Swarm-World && python3 -m unittest tests.test_install_script tests.test_install_debugger"`: passed, 23 tests.
- `wsl.exe bash -lc "cd /mnt/d/Projects/Tiny-Swarm-World && git diff --check"`: passed, with existing CRLF warnings for unrelated files.
- `wsl.exe bash -lc "cd /mnt/d/Projects/Tiny-Swarm-World && python3 tools/quality_gate.py quality"`: passed; lint, arch-lint, arch-tests, typecheck, and 848 tests passed with 17 skipped.
