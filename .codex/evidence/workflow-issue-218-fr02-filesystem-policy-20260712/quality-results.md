# FR-2 Local Quality Results

All commands ran in WSL from the isolated FR-2 worktree. No live infrastructure
command was run.

| Check | Result |
| --- | --- |
| Focused FR-2 suite | PASS — 343 tests |
| Focused FR-2 suite with `CI=1` | PASS — 343 tests |
| Focused remediation suite | PASS — 195 tests |
| `quality_gate.py lint` | PASS |
| `quality_gate.py arch-lint` | PASS — 3 contracts, 307 files, 716 dependencies |
| `quality_gate.py arch-tests` | PASS — 18 tests |
| `quality_gate.py typecheck` | PASS — 500 source files |
| `quality_gate.py test` | PASS — 1,495 tests, 28 expected skips |
| `quality_gate.py quality` | PASS |
| `git diff --check` | PASS before final evidence reconciliation |

The initial lint invocation with the WSL system interpreter could not start
because Ruff was absent. It was retried unchanged with the repository WSL
virtual environment, where Ruff is installed. This is a tooling-environment
repair and no quality check was skipped or weakened.

Live Selenium, Incus, Docker, Swarm, DNS, and service checks are `NOT_RUN`:
they are outside this static filesystem-policy slice and were not authorized.
