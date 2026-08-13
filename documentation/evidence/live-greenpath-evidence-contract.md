# Live Green-Path Evidence Handoff

This handoff is the admin-surface input for the canonical live evidence
contract in Issue #125. It records what a future explicit live run must prove
for the secure Traefik dashboard; it does not claim that the run occurred.

## Required facts

- the selected Linux or WSL2 host and consent record;
- the effective `TSW_TRAEFIK_GUI_USERS_SECRET_NAME` reference, without its
  value;
- TLS certificate identity and validation result, without private material;
- resolution of `traefik.tsw.local` to the intended manager ingress;
- HTTPS response and authentication behavior for the dashboard route;
- rejection of unauthenticated access and absence of `api.insecure` exposure;
- preservation of Service Access routes;
- redacted evidence for fresh install, reconcile/re-run, and update where the
  route participates in the run;
- rollback or failure classification if the external TLS or users secret is
  missing.

## Current state

Static compose/configuration tests pass for the desired route, TLS entry point,
BasicAuth users-file reference, secret-name contract, and forbidden insecure
mode. No live deployment, DNS mutation, browser check, or credential test was
run by this workflow. The live fields above therefore remain `NOT_VERIFIED`
until an explicitly consented operator run supplies redacted evidence.
