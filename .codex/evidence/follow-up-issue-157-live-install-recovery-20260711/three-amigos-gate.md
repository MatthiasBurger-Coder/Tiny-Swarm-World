# Three Amigos Gate

- Issue: #157 follow-up for live installation and verification recovery
- Branch: `fix/live-install-recovery-20260711`
- Gate result: ACCEPT
- Scope decision: preserve the merged Issue #157 routing architecture and close only runtime, recovery, observability, and verification blockers exposed by the approved live run.

## Requirement Lead

ACCEPT. The original Issue #157 requirements remain satisfied by merged PR #215. The follow-up is limited to reliable Windows-to-WSL exposure, redacted live evidence, bounded verification, deployment recovery, and defects directly exposed by the approved installation and Selenium runs. RabbitMQ, legacy messaging, Kubernetes, DNS-server mutation, certificate lifecycle, and unrelated refactoring remain out of scope.

## System Architect

ACCEPT. The effective access model remains the sole routing source for Traefik routes, service-access links, health targets, routing evidence, and browser expectations. Windows bridge behavior is isolated behind application preflight ports and infrastructure adapters. The protected Windows service design is recorded in the new ADR. Domain code performs no filesystem I/O.

## Test Lead

ACCEPT. Coverage includes static and live paths: transactional PowerShell/Pester recovery, Python adapter tests, all six quality gates, separate deployment/platform verification, redacted routing evidence checks, one deliberately retained failed Selenium record, and a final clean live Selenium pass derived from the effective access model.

## Runtime decisions from observed evidence

- The manager memory increase to 10 GiB is justified by a measured cgroup OOM at 4 GiB; CPU remains at the declared value 2 because CPU was not proven causal.
- The secret scanner prunes ignored trees before traversal because the previous implementation spent about 9.5 minutes walking excluded DrvFS state.
- Pulsar Manager bootstrap uses bounded `on-failure` retries because the initial one-shot task was externally interrupted with exit 137 while Worker 1 recorded no OOM.

No unresolved requirement contradiction remains.
