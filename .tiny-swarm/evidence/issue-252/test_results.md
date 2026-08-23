# Issue #252 Remediation Test Results

Implementation baseline: `60d5d09f`

Exact R08 local candidate: `36ba799738ffb8db4175b7347a6aa8a7f907fa05`

| Slice | Focused result | Full local quality result | Live result |
|---|---|---|---|
| R01 | PASS, 222 tests | PASS, 1,792 tests / 18 skipped | NOT_RUN |
| R02 | PASS, 249 tests | PASS, 1,804 tests / 18 skipped | NOT_RUN |
| R03 | PASS, 21 tests | PASS, 1,810 tests / 18 skipped | NOT_RUN |
| R04 | PASS, 13 tests | PASS, 1,819 tests / 18 skipped | NOT_RUN |
| R05 | PASS, 8 tests | PASS, 1,823 tests / 18 skipped | NOT_RUN |
| R06 | PASS, 136 tests / 8 expected live skips | PASS, 1,833 tests / 18 skipped | NOT_RUN |
| R07 | PASS, documentation/hash/redaction checks | PASS, 1,833 tests / 18 skipped | NOT_RUN |
| R08 | PASS, all declared targeted gates | PASS, 1,833 tests / 18 skipped | NOT_RUN |

Each full result includes verification policy, lint, three import contracts,
18 architecture tests, type checking and unit tests as recorded in the
corresponding `.codex/evidence/slice-S252-R0*-consolidation.md` file.

R07 documentation checks ran on the final post-`15c543eb` working tree. R08
exact-candidate local gates passed on the clean SHA above. The executed
commands were `git diff --check` plus the `lint`, `arch-lint`, `arch-tests`,
`typecheck`, `test` and `quality` quality-gate modes. Skipped live tests are
non-success states; no WSL2, Native Linux, CI, SonarQube or runner execution is
reported as successful.
