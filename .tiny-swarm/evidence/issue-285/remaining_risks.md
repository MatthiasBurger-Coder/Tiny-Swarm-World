# Remaining Risks and Scope Boundaries: #285 / CRED-07

- No separate native-Linux host or VM was available. Incus containers managed
  from WSL2 cannot substitute for native-Linux host evidence.
- The custom/Infisical override scenario was not run. It requires an
  operator-owned WSL-native `0600` credential file and a non-secret
  credential-rotation reference; neither was supplied.
- The separate reconcile run passed, but a before/after credential-source or
  value-equivalence comparison was not captured, so credential-drift
  acceptance remains open.
- Browser acceptance was not run. Installer/API readiness and service access
  are not browser evidence.
- Historical failed attempts are retained only as redacted diagnostic history;
  they are not passes. The final WSL2 run is the protected candidate.
- The authorized Incus test environment is still running after the successful
  proof. No production environment was targeted.

These gaps keep the issue and PR in `BLOCKED` state. No merge or branch cleanup
is authorized until the missing required evidence is supplied and reviewed.
