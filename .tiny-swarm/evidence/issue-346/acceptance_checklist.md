# Acceptance Checklist — #346 / ARCH-03.03

- [x] The current orchestration edge is scoped completely: three entrypoints and all `composition*.py` modules.
- [x] Ranking criteria are documented with repeatable thresholds and weights.
- [x] Complexity, module/function size, fan-out, side effects, responsibilities, infrastructure coupling, test friction, and change frequency are represented.
- [x] Every scoped surface is classified LOW, MEDIUM, HIGH, or CRITICAL.
- [x] Every HIGH/CRITICAL hotspot has a proposed decomposition target.
- [x] File size is explicitly treated as context, not the deciding metric.
- [x] Results feed a P0–P4 ARC-02 through ARC-06 implementation order.
- [x] Requirement matrix and all required issue evidence files exist.
- [x] `git diff --check` passes.
- [x] No live infrastructure verification is claimed.
