# Acceptance Checklist: #282 / CRED-04

- [x] The KEEP/MIGRATE/DELETE matrix was committed before cleanup edits.
- [x] The normal installer has no random default-password generation.
- [x] Generated/bootstrap/fixed credential recovery persistence was removed.
- [x] One explicit operator override responsibility remains defined.
- [x] Credential-source mode selectors and dead branches were removed.
- [x] Catalog, manifest, and installer have distinct responsibilities.
- [x] Preflight no longer requires removed generated/fixed secret state.
- [x] Operator values, conflicts, and evidence remain redaction-safe.
- [x] Obsolete docs, examples, and behavior tests were rewritten or removed.
- [x] `python3 tools/quality_gate.py quality` passed.
- [x] The full repository test execution passed with 1,900 tests and 18 skips.
- [x] The affected-slice branch-aware test execution passed with 247 tests.
- [x] Added executable production lines and source branch arcs were covered by
      the branch-aware run; the reproducible change-specific result is above
      the 95% threshold.
- [x] No live infrastructure was run; live WSL2/native Linux proof remains
      explicitly assigned to #285 / CRED-07.
