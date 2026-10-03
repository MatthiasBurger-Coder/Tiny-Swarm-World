# Issue #361 test results

Final integrated candidate on `issue-361-complexity-guardrails`:

| Command or check | Result |
| --- | --- |
| `PYTHONPATH=src python3 -m unittest tests.tools.test_check_complexity_guardrails tests.architecture.test_skill_registry_integrity` | PASS: 17 focused tests |
| `python3 -m ruff check tools/check_complexity_guardrails.py tests/tools/test_check_complexity_guardrails.py` | PASS |
| `python3 tools/quality_gate.py complexity` | PASS: 259 modules checked |
| `python3 tools/quality_gate.py quality` | PASS: verification policy, complexity, lint, import-linter (6 kept/0 broken), architecture tests (30), mypy (725 source files), unit suite (2,335 tests; 18 skipped) |
| `git diff --check` | PASS |

The first full gate attempt failed only at the skill-registry integrity test
because `QUALITY.md` changed without its governing SHA-256 cache entry. The
cache was refreshed and the focused integrity test passed. Subsequent full
gate runs passed; the final run used the settled checker and baseline.

No live infrastructure command or external quality check was executed.
