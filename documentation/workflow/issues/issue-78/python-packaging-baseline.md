# Issue 78 Python Packaging Baseline

## Decision

Issue #78 should add standard `pyproject.toml` metadata while preserving the
existing `setup.py` compatibility surface.

The selected implementation path is:

- add `pyproject.toml` with setuptools build metadata, Python 3.12 support,
  runtime dependencies, package discovery under `src`, and a console script;
- add a synchronous CLI wrapper in `tiny_swarm_world.__main__` for console
  script execution while preserving `python -m tiny_swarm_world`;
- keep `setup.py` compatible with the same console script for legacy editable
  installs;
- add package metadata tests that do not require live infrastructure;
- update README and user guide command examples to prefer the installed CLI
  while keeping direct module execution documented for source checkout work.

## Repository Evidence

- `setup.py` already exists and reads runtime dependencies from
  `requirements.txt`.
- No `pyproject.toml` exists at workflow start.
- `src/tiny_swarm_world/__main__.py` exposes async `main(...)` and currently
  calls `asyncio.run(main())` only under the module guard.
- README and user-guide command examples mostly use
  `PYTHONPATH=src python3 -m tiny_swarm_world`.

## Non-Goals

- No live infrastructure execution.
- No packaging backend switch away from setuptools.
- No removal of `python -m tiny_swarm_world`.
- No change to repository quality gate behavior.

## Next Slice

Slice 02 should add `pyproject.toml`, add the console script wrapper, keep
`setup.py` compatible, and add package metadata tests.
