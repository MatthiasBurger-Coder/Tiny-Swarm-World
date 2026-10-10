# Acceptance checklist

- [ ] AC1: Both host families have actual fresh/rerun/recovery results.
  Fresh/rerun/recovery remain BLOCKED; native preflight exit 2 is recorded.
- [ ] AC2: Real ordinary WSL preservation and separately authorized reset
  isolation results. Ordinary isolated-guest preservation/resource/bootstrap tests remain open; manual WSL/Ubuntu prerequisites are now observed;
  explicit destructive reset remains LIVE_CONSENT_MISSING.
- [x] AC3: Each eligible release explicitly marked UNQUALIFIED in the release
  matrix; excluded target families identified. No new release is qualified.
- [x] AC4: Targeted regressions and applicable local quality/security checks
  pass for the integrated candidate. Focused 35 tests PASS; original dependency audit FAIL, corrected lock audit
  PASS; full Python 3.12 quality PASS. Original frozen runtime candidate `3da77f8908d598688ed46dd6eab74c5f32a7ac50` matches its tested source/lock. Narrow corrected Windows checkpoint adapter and final regression pass revised full Python3.12 quality retry and WindowsPowerShell5.1 filesystem contracts; corrected frozen source `bce63aafb6990e9157c8ddb3eb12e4aa9fd1f440`; source-bound actual disposable writer verification PASS. Revised full product apply remains BLOCKED on storage trust.
- [ ] Exact target/source consent, observed versions, commands/exits and
  redacted per-scenario evidence with AC mapping.
- [ ] Independent completion audit permits DONE. Live blockers prevent PASS.

All scenario IDs map to requirements in requirement_matrix.md. Local checks
support AC4 and safety regression coverage only; they cannot close AC1/AC2.
