# Issue #252 Remediation Test Results

Implementation baseline: `60d5d09f`

| Slice | Focused result | Full local quality result | Live result |
|---|---|---|---|
| R01 | PASS, 222 tests | PASS, 1,792 tests / 18 skipped | NOT_RUN |
| R02 | PASS, 249 tests | PASS, 1,804 tests / 18 skipped | NOT_RUN |
| R03 | PASS, 21 tests | PASS, 1,810 tests / 18 skipped | NOT_RUN |
| R04 | PASS, 13 tests | PASS, 1,819 tests / 18 skipped | NOT_RUN |
| R05 | PASS, 8 tests | PASS, 1,823 tests / 18 skipped | NOT_RUN |
| R06 | PASS, 136 tests / 8 expected live skips | PASS, 1,833 tests / 18 skipped | NOT_RUN |
| R07 | PASS, documentation/hash/redaction checks | PASS, 1,833 tests / 18 skipped | NOT_RUN |

Each full result includes verification policy, lint, three import contracts,
18 architecture tests, type checking and unit tests as recorded in the
corresponding `.codex/evidence/slice-S252-R0*-consolidation.md` file.

R07 documentation checks ran on the final post-`15c543eb` working tree. The
R08 exact-candidate gates remain open until the R07 commit SHA is frozen and
verified. Skipped live tests are non-success states.
