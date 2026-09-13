# Test Results — #346 / ARCH-03.03

Verification date: 2026-09-13

Verification state: local Linux/WSL; no live infrastructure

| Command / check | Result | Evidence |
|---|---|---|
| AST metric inventory from `arch-03-03-orchestration-hotspot-ranking.md` | PASS | All three entrypoints and all 12 `composition*.py` modules produced metrics. |
| `git diff --check` | PASS | No whitespace errors in the documentation/evidence changes. |
| `python3 tools/quality_gate.py quality` | PASS | Verification policy, lint, arch-lint, arch-tests, typecheck, and test completed; 2,070 tests passed and 18 skipped. |
| Live Incus, Docker Swarm, compose, bootstrap, or external service checks | NOT APPLICABLE | This is a source-level architecture audit. |

The metric command uses Python AST parsing and `git rev-list`; it does not
import or execute Tiny Swarm World product modules.
