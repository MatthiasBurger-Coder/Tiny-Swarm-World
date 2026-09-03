# Acceptance Checklist: #285 / CRED-07

- [x] WSL2 fresh install reaches a real terminal result: reset/setup exit 0.
- [x] WSL2 checkout under `/mnt/*` succeeds on the standard internal-test path.
- [ ] Native Linux fresh install reaches a real terminal result.
- [x] Portainer authentication/access succeeds on WSL2; native counterpart is open.
- [x] Infisical bootstrap/login acceptance succeeds on WSL2; native counterpart is open.
- [x] Feasible other catalog services have WSL2 readiness/API checks.
- [x] WSL2 post-install service/API acceptance is recorded.
- [ ] Reconcile/rerun proves no credential drift.
- [x] WSL2 environment recreation resolves the documented default source model.
- [ ] A supported custom/Infisical override replaces the default.
- [x] WSL2 Portainer restart/recovery relevant to credential consumption is verified.
- [x] Update remains not applicable because no canonical update workflow exists.
- [x] Protected evidence and installer output contain no raw credentials or authorization headers.
- [x] No blocked, skipped, partial, or degraded result is reported as PASS.
- [x] Final candidate passes the full local quality gate.
- [ ] Final matrix is fully observed for native Linux and override scopes.

Current decision: `BLOCKED`. WSL2 is green for the standard catalog path; the
issue is not complete without native-Linux, override and remaining lifecycle
evidence.
