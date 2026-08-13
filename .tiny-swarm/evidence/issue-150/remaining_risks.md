# Issue #150 Remaining Risks

1. The external Docker users secret and operator CA material are prerequisites
   for a live dashboard. The repository intentionally does not create or log
   their values.
2. `traefik.tsw.local` resolution, TLS chain validation, authentication
   behavior and route convergence have not been executed against a live Swarm.
3. Fresh install, reconcile/re-run and update behavior remain live evidence
   scenarios for the Public-Beta Green-Path and Issue #125.
4. SonarQube and other external gates were not accessed by the local quality
   run; no external green claim is made.

Risk treatment is documented in the ADR, ASVS/admin-surface model, secret
policy and live evidence handoff. The live risks block Public-Beta acceptance,
not the local static implementation.
