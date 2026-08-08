# Issue #232 test and quality results

All commands were run from WSL/Linux with the repository `PYTHONPATH` or the
quality-gate wrapper as required by project governance.

## Latest completed results

| Check | Result | Evidence |
|---|---|---|
| Focused Slice 07 domain/inventory/readiness/gate/adapter tests | PASS | 28 tests, `OK` |
| Slice 07 full test gate | PASS | 1,623 tests, 28 skipped, `OK` |
| Focused Slice 06 artifact/setup/adapter tests | PASS | 44 tests, `OK` |
| Lint | PASS | `python3 tools/quality_gate.py lint` |
| Architecture lint | PASS | 3 contracts kept, 0 broken |
| Architecture tests | PASS | 18 tests, `OK` |
| Typecheck | PASS | no issues in 538 source files |
| Full quality gate after Slice 07 state/evidence changes | PASS | 1,623 tests, 28 skipped, `OK` |
| Slice 08 required quality-gate rerun | PASS | 1,623 tests, 28 skipped, `OK`; completed after extended wrapper timeout |
| Slice 09 documentation consistency | PASS | `git diff --check`; documentation claims reviewed against source, tests and verification-state policy |
| Slice 09 final quality-gate rerun | PASS | 1,623 tests, 28 skipped, `OK` |

The final Slice 09 full quality result is the authoritative local result for
the completed implementation and documentation package.

An intermediate Slice 09 quality run detected a stale governing hash for the
changed Arc42 file. The registry hash was refreshed from the file content, the
targeted registry-integrity test passed 5/5, and the final full quality run
then passed.

## Safety classification

No live infrastructure command was run. Live installation and external quality
checks remain non-success states until separately applicable, explicitly
authorized and backed by redacted evidence. Slice 08 therefore records
`LIVE_CONSENT_MISSING` in `live_acceptance.md`; it produced no live process,
exit code or runtime result.
