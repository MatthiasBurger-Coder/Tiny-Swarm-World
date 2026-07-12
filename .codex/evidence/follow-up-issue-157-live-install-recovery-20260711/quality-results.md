# Quality Results

| Gate | Result | Evidence |
| --- | --- | --- |
| `python3 tools/quality_gate.py lint` | PASS | `quality-20260712T104400Z/lint.log` |
| `python3 tools/quality_gate.py arch-lint` | PASS | 290 files, 658 dependencies, 3 contracts kept |
| `python3 tools/quality_gate.py arch-tests` | PASS | 18/18 |
| `python3 tools/quality_gate.py typecheck` | PASS | 472 files, 0 errors |
| `python3 tools/quality_gate.py test` | PASS | 1410 tests, 28 skipped |
| `python3 tools/quality_gate.py quality` | PASS | aggregate green; 1410 tests, 28 skipped |

Commands were executed through WSL with `.venv/bin/python`, unbuffered output, independent outer timeouts, and separate ignored logs. A first system-Python lint bootstrap attempt was rejected before lint because Ruff was absent; that environment error is retained separately and was not treated as a code result.

`git diff --check`: PASS.
