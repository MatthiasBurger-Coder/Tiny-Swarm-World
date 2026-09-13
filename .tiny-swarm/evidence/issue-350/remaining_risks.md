# Remaining Risks — ARCH-03.07

- The planner is additive and is not yet the executor of the existing Classic
  reconcile workflow; this preserves behavior and keeps integration scope
  bounded.
- Current-state comparison intentionally uses the fields available in the
  observed inventory. More detailed drift dimensions require a separate
  requirement and evidence slice.
- No live infrastructure was used; planning is verified with pure unit tests.
