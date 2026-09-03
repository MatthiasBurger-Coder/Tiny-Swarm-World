# Acceptance Checklist: #285 / CRED-07

- [ ] WSL2 fresh install reaches a real terminal result.
- [ ] WSL2 checkout under `/mnt/*` succeeds on the standard internal-test path.
- [ ] Native Linux fresh install reaches a real terminal result.
- [ ] Portainer authentication succeeds in both applicable environments.
- [ ] Infisical bootstrap/login succeeds in both applicable environments.
- [ ] Feasible other catalog human-facing services are checked.
- [ ] Post-install service/UI/API acceptance is recorded.
- [ ] Rerun/reconcile shows no credential drift.
- [ ] Recreated standard environment resolves documented deterministic defaults.
- [ ] A supported custom/Infisical override replaces the catalog default.
- [ ] Restart/recovery relevant to credential consumption is verified.
- [ ] Update is tested only if a canonical update workflow exists.
- [ ] Evidence is redacted and contains no raw credentials or authorization headers.
- [ ] No blocked, skipped, partial, or degraded result is reported as PASS.
- [ ] Final candidate passes the full local quality gate.
- [ ] Final matrix maps every parent EPIC criterion to observed evidence.

Current decision: `BLOCKED` before live mutation pending scoped operator
approval and a native-Linux target. This checklist must not be converted to
checkmarks from static tests or command availability.
