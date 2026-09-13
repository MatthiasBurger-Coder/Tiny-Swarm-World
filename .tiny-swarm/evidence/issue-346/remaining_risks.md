# Remaining Risks — #346 / ARCH-03.03

- The inventory is a ranking baseline, not a refactor. The HIGH and CRITICAL
  surfaces remain in place until ARC-02 through ARC-05 implementation work.
- AST branching is a repeatable complexity indicator, not exact McCabe
  complexity; future ranking runs must use the same definition or document a
  metric-version change.
- Test friction is a reviewed proxy based on concrete dependencies, direct
  effects, compatibility seams, and existing tests. It is not a runtime timing
  measurement.
- Change frequency is limited to repository history since 2026-06-01 and may
  change as subsequent commits land.
- Follow-up issue references were checked against the open ARCH-03 backlog on
  2026-09-13; their implementation remains outside this issue.
- No live infrastructure, browser, SonarQube, Incus, or Docker evidence is
  claimed.
