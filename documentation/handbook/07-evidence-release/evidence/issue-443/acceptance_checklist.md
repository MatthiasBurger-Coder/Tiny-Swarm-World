# Issue #443 acceptance checklist

- [x] AC1: unknown IDs, cycles and foundation removal fail before writes (SelectionPlanningTests and SelectionCliTests).
- [x] AC2: reordered equivalent selections have identical deterministic topological plans (SelectionPlanningTests).
- [x] AC3: dependency provenance and whole-resolved-set resource aggregation/unknowns verified with native and synthetic declarations (SelectionPlanningTests).
- [x] AC4: explicit removal and implicit deselection cannot persist/remove deployed state/data; reverse impact preview retains state (SelectionServiceTests).
- [x] CLI/config/persisted/preset precedence; approval, preview, no-op, CAS, stale/tampered plan, failed storage and preservation coverage.
- [x] Full local QUALITY.md gate completed: .venv/bin/python tools/quality_gate.py quality, exit 0; final amended run 2682 tests, 18 skips.
- [x] Independent issue-completion audit completed: PASS, all four perspectives, no open requirements. See completion_audit.md.

No live deployment or external success is part of this local acceptance.

- [x] Publication security amendment: config path containment and Python3.12 loop sanitizer verified; independent re-review approves. External Sonar result is required separately before merge.
