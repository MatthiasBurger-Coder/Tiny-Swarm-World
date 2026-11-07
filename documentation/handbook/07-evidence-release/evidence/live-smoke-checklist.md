# Live Green-Path Smoke Checklist

This checklist is executed only after explicit live consent and a guarded
preflight. Mark unavailable or unexecuted items with the exact policy state;
do not use a checkmark for a planned action.

## Consent and host

- [ ] Consent record is present and scoped to the target and scenario.
- [ ] Host is classified as native Linux or WSL2.
- [ ] Target is disposable or has a documented rollback/recovery path.
- [ ] Evidence root is local, ignored and permission-restricted.

## A/B/C scenarios

- [ ] A — fresh install completed with phase evidence.
- [ ] B — reconcile/re-run completed without unplanned drift.
- [ ] C — existing-install update completed with rollback classification.
- [ ] Native Linux result recorded.
- [ ] WSL2 result recorded.

## Platform and services

- [ ] Preflight, LXC/Incus node readiness and Docker Engine state recorded.
- [ ] Docker Swarm, ingress network and Traefik readiness recorded.
- [ ] Secret references and external-secret readiness recorded without values.
- [ ] Nexus/artifacts, Jenkins, SonarQube, Pulsar and Swagger readiness
      recorded with applicable external states.
- [ ] Service Access route and browser/readiness result recorded.

## Secure Traefik admin surface

- [ ] `traefik.tsw.local` resolves to the intended manager ingress.
- [ ] TLS summary and chain result are recorded without private material.
- [ ] Authenticated dashboard access is recorded without credentials.
- [ ] Unauthenticated access is rejected.
- [ ] `api.insecure` exposure and extra dashboard ports are absent.
- [ ] Existing Service Access routes remain reachable.
- [ ] Missing TLS/users secret behavior is classified fail-closed if tested.

## Evidence closeout

- [ ] All phase results use policy states and dependent phases stopped after
      blocking failure.
- [ ] Raw output and sensitive material were redacted or excluded.
- [ ] SHA-256 checksums were generated after redaction and verified.
- [ ] Cleanup/rollback result is recorded.
- [ ] Independent reviewer recorded decision and findings.

Current repository status: this checklist is `PLANNED`; no live run was
executed by Issue #125 authoring.
