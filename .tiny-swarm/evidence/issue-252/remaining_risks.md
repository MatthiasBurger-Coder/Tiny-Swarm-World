# Issue #252 Remediation Remaining Risks

- Exact R08 local candidate:
  `36ba799738ffb8db4175b7347a6aa8a7f907fa05`.
- R08 targeted and full local acceptance passed on that exact clean candidate;
  its evidence-only commit and final guarded PR/CI lifecycle necessarily
  follow the frozen SHA.
- WSL2 Fresh/Reconcile/Update, recovery and restart reruns have not executed on
  the remediation candidate. Historical live evidence is not transferred.
- Native Linux lifecycle evidence remains open. Local procfs fixtures verify
  only the read-only kernel-control contract.
- CI, SonarQube and protected self-hosted Classic runner evidence remains open
  for the remediation candidate.
- Browser/DNS/host-trust and live Docker secret-store convergence remain
  opt-in checks requiring explicit consent and prerequisites.
- Bcrypt is the recommended Traefik dashboard htpasswd format. Recognized
  legacy algorithms remain accepted compatibility surface and residual
  hardening work.

Until all mandatory issue requirements are verified, Issue #252 remains
`INCOMPLETE` and RC1 cannot be reported as accepted.
