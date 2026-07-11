# Quality Results

Status: `ALL_REQUIRED_LOCAL_GATES_PASS`

## Latest Integrated Product Gate

After Slices 02, 03, and 04 were consolidated on the workflow branch:

```text
python3 tools/quality_gate.py quality
PASS
- Ruff: pass
- Import Linter: 3 contracts kept, 0 broken
- Import analysis: 290 files, 657 dependencies
- Architecture tests: 18 passed
- Mypy: no issues in 471 source files
- Unittest: 1,361 run; 1,333 passed; 28 skipped
```

No live browser, DNS, Traefik, Docker, Swarm, or Incus dependency was used.

## Required Slice 05 Commands

Every requested command ran independently in WSL on 2026-07-11 against the
integrated branch:

| Command | Result |
|---|---|
| `git diff --check` | `PASS` after final audit and context-hash edits |
| `python3 tools/quality_gate.py lint` | `PASS`; Ruff all checks passed |
| `python3 tools/quality_gate.py arch-lint` | `PASS`; 290 files, 657 dependencies, 3 contracts kept, 0 broken |
| `python3 tools/quality_gate.py arch-tests` | `PASS`; 18 tests |
| `python3 tools/quality_gate.py typecheck` | `PASS`; no issues in 471 source files |
| `python3 tools/quality_gate.py test` | `PASS`; 1,361 run, 1,333 passed, 28 skipped |
| `python3 tools/quality_gate.py quality` | `PASS`; all sub-gates green, 1,361 run, 1,333 passed, 28 skipped |

The 28 skipped tests are existing opt-in/platform prerequisite paths; no live
browser or infrastructure dependency was introduced into the static gate.

## External Checks

- PR required checks: `PENDING_SLICE_06`.
- SonarCloud/SonarQube PR result: `PENDING_SLICE_06`.
- Review-comment closure: `PENDING_SLICE_06`.
