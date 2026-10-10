# Acceptance checklist

- [ ] AC1: Both host families have actual fresh/rerun/recovery results.
  Matrix records BLOCKED before execution; no live result exists.
- [ ] AC2: Real ordinary WSL preservation and separately authorized reset
  isolation results. Ordinary isolated-guest tests lack runtime prerequisites;
  explicit destructive reset remains LIVE_CONSENT_MISSING.
- [x] AC3: Each eligible release explicitly marked UNQUALIFIED in the release
  matrix; excluded target families identified. No new release is qualified.
- [ ] AC4: Targeted regressions and applicable local quality/security checks
  pass for the integrated candidate. Focused 35 tests PASS; original dependency audit FAIL, corrected lock audit
  PASS; full Python 3.12 quality PASS. Final source SHA awaits freeze.
- [ ] Exact target/source consent, observed versions, commands/exits and
  redacted per-scenario evidence with AC mapping.
- [ ] Independent completion audit permits DONE. Live blockers prevent PASS.

All scenario IDs map to requirements in requirement_matrix.md. Local checks
support AC4 and safety regression coverage only; they cannot close AC1/AC2.
