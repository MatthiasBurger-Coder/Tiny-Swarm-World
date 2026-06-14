# Slice 67 Consolidation Evidence

- Workflow id: `issue-67-python-installer-20260614`
- Slice id: `67`
- Slice title: Move install logic from shell to Python

## Stream Results

- Runtime installer: `install.sh` reduced to a Linux/WSL bootstrap wrapper that validates repository shape and delegates to `python3 -m tiny_swarm_world.installer`.
- Python installer: new `src/tiny_swarm_world/installer.py` owns argument parsing, secret handling, host-runtime detection, native Linux dependency bootstrap, reset confirmation, evidence context, terminal-recorder/headless execution, and exit-code preservation.
- Tests: installer script tests execute the real Python installer module in a temp repository while faking downstream CLI and recorder commands; new direct Python installer tests cover parsing, host detection, export parsing, and EOF reset handling.
- Documentation: README, installation guide, troubleshooting guide, and arc42 runtime view now identify the Python installer as authoritative.
- Quality: targeted tests and supplemental checks passed before final full quality gate.

## Subagent Review

- Boyle reviewed the branch read-only.
- Accepted findings:
  - Update tests that still expected the old shell implementation.
  - Update install debugger contract away from shell-owned reset/setup strings.
  - Resolve `cwd` and injected environment isolation gaps in the Python installer.
  - Update documentation to state Python installer authority.
- Rejected findings: none.

## Files Changed Per Stream

- Runtime: `install.sh`, `src/tiny_swarm_world/installer.py`, `tools/install_debugger.py`
- Tests: `tests/test_install_script.py`, `tests/test_install_debugger.py`, `tests/test_installer.py`
- Documentation: `README.md`, `documentation/user_guide/installation.adoc`, `documentation/user_guide/troubleshooting.adoc`, `documentation/arc42/06_runtime_view.adoc`
- Evidence: `.codex/evidence/slice-67-distribution.md`, `.codex/evidence/slice-67-consolidation.md`

## Conflicts

- Conflicts found: none.
- Conflicts resolved: not applicable.

## Tests Executed

- `PYTHONPATH=src python3 -m unittest tests.test_installer tests.test_install_script tests.test_install_debugger` - passed.
- `python3 tools/quality_gate.py lint` - passed.
- `python3 tools/quality_gate.py typecheck` - passed.
- `python3 tools/quality_gate.py quality` - passed, including lint, arch-lint, arch-tests, typecheck, and 859 tests with 17 skipped.
- `python3 -m ruff check src/tiny_swarm_world/installer.py tests/test_installer.py` - passed.
- `PYTHONPATH=src python3 -m py_compile src/tiny_swarm_world/installer.py` - passed.
- `PYTHONPATH=src python3 -m tiny_swarm_world.installer --help` - passed.

## SonarQube

- No local SonarQube run was executed. The push-auto lifecycle must verify or explicitly skip the remote SonarCloud check according to the repository's current CI behavior.

## Final Integration Decision

- Accepted for final full quality gate and `push auto` lifecycle.
