# Slice 02 Consolidation: Issue 78 Python Packaging

Workflow id: `issue-78-python-packaging-20260614`
Slice id: `S02`
Slice title: Package metadata and CLI entry point

## Stream Results

- backend: accepted. Added a synchronous console-script wrapper around the
  existing async CLI entry point.
- tests: accepted. Added package metadata regression tests for `pyproject.toml`
  and legacy `setup.py` compatibility.

## Subagent Review

Real subagent review completed for packaging and test adequacy.

Result: no blocking findings.

Residual risks accepted or mitigated:

- `cli()` direct unit coverage: accepted. The editable-install gate invokes the
  installed `tiny-swarm-world` script and covers the console-script integration
  path.
- package version parity: mitigated by adding a regression test that compares
  `pyproject.toml` and `setup.py`.
- `requests==2.32.0` yanked warning: accepted as inherited dependency risk
  from the existing `requirements.txt` pin.

## Accepted Findings

- `tiny-swarm-world` must resolve to a synchronous callable because setuptools
  console scripts cannot await an async coroutine directly.
- `pyproject.toml` dependencies must match `requirements.txt` so package
  installs and source-checkout execution remain aligned.
- `pyproject.toml` and `setup.py` package versions must remain aligned while
  both metadata surfaces exist.

## Rejected Findings

None.

## Files Changed Per Stream

- backend: `src/tiny_swarm_world/__main__.py`
- packaging: `pyproject.toml`, `setup.py`
- tests: `tests/test_package_metadata.py`
- evidence: `.codex/evidence/issue-78/slice-02-distribution.md`,
  `.codex/evidence/issue-78/slice-02-consolidation.md`

## Conflicts

No file conflicts detected. Issue-specific evidence path is used so Issue #4
root-level slice evidence remains intact.

## Tests Executed

```text
PYTHONPATH=src python3 -m unittest tests.test_package_metadata tests.test_package_entrypoint
```

Result: passed, 33 tests.

```text
python3 -m pip install -e . && tiny-swarm-world --list-workflows
```

Result: passed in a temporary WSL virtual environment.

Note: pip reported that the existing `requests==2.32.0` pin is yanked. The
slice mirrors the existing repository requirement and does not change the
dependency version.

## SonarQube Findings

Not run locally for this slice. Remote PR checks remain the SonarQube decision
point during `push auto`.

## Documentation Updates

Documentation changes are intentionally deferred to Slice 03.

## Final Integration Decision

Accepted for Slice 02 checkpoint commit after subagent review, focused tests,
editable-install verification, and diff checks.
