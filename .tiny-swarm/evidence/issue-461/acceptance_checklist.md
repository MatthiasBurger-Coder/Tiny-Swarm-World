# Acceptance checklist

- [ ] AC1: Both host families have actual fresh/rerun/recovery results.
  Fresh/rerun/recovery remain BLOCKED; native preflight exit 2 is recorded.
- [ ] AC2: Real ordinary WSL preservation and separately authorized reset
  isolation results. Sourceef7 preflight/dry-run preserves measured registration,
  configuration, hosts and bootstrap-state fingerprints. Separate reset consent
  exists only for Ubuntu in the secured owned VM. Current30 checkpoint actual restore and scoped Ubuntu unregister/empty
  inventory/restore were verified with primary WSL registration/config unchanged;
  ordinary full-apply preservation and remaining bootstrap scenarios remain open.
- [x] AC3: Each eligible release explicitly marked UNQUALIFIED in the release
  matrix; excluded target families identified. No new release is qualified.
- [x] AC4: Targeted regressions and applicable local quality/security checks
  pass for the integrated candidate. Current frozen source
  `ef7e88350ede68f7d4197265b2a272c4bd404a3c`: full Python3.12 gate PASS2555 tests,
  43 architecture tests, 7 import contracts, 799 typed files; final targeted19
  PASS and resource assertions77 PASS. Strict dependency audit PASS. Concrete
  architecture/security reviews approve R461-24. Historical storage trust was
  resolved in source806; current live blockers are bridge inventory, prior-source canonical state
  and missing live scenarios. Current30 resource and reset isolation cases pass.
- [ ] Exact target/source consent, observed versions, commands/exits and
  redacted per-scenario evidence with AC mapping.
- [ ] Independent completion audit permits DONE. Live blockers prevent PASS.

All scenario IDs map to requirements in requirement_matrix.md. Local checks
support AC4 and safety regression coverage only; they cannot close AC1/AC2.
