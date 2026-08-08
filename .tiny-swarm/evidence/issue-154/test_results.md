# Issue #154 Test and Quality Results

Workflow: `issue-154-20260808`
Verification state: `VERIFIED_LOCAL`

All commands were run from the repository through WSL/Linux. No live
infrastructure command was executed.

## Final Slice 06 checks

| Check | Result |
|---|---|
| `git diff --check` | PASS |
| `wsl bash -lc 'cd /mnt/d/Projects/Tiny-Swarm-World && python3 tools/quality_gate.py test'` | PASS — 1,631 tests, 28 skipped |
| `wsl bash -lc 'cd /mnt/d/Projects/Tiny-Swarm-World && python3 tools/quality_gate.py quality'` | PASS |

The final `quality` gate passed verification-policy consistency, Ruff,
import-linter architecture contracts (3 kept, 0 broken), architecture tests
(18), mypy (`Success: no issues found in 538 source files`), and the full test
suite (1,631 tests, 28 skipped).

## Issue regression evidence

The Slice 05 focused #154/#218/#232 regression suite passed 286 tests. It
covers setup ordering and downstream `not_run`, Docker verification for every
expected node, manager-before-worker bootstrap, unavailable worker
credentials, structured Ready/Active/manager-state checks, domain/YAML parity,
and preserved host-preflight and artifact-readiness behavior.

Slices 01–04 also recorded focused results of 142, 100, 54, and 125 tests
respectively, with their required gates green. Their distribution and
consolidation records are under `.codex/evidence/issue-154/`.

The test output contains expected fake failure-path diagnostics, redacted
command diagnostics, ResourceWarnings, dependency-environment setup messages,
and 28 policy-governed skips. These did not cause a test or quality-gate
failure.
