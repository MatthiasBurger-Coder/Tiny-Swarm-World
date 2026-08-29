# Issue #252 — S252-06 Distribution Decision

- Workflow: `issue-252-classic-public-beta-rc1-20260818`
- Slice: `S252-06` — WSL2 update and post-update acceptance
- Branch: `feature/classic-public-beta-rc1-stabilization`
- Affected areas: runtime, deployment, tests, live evidence
- Execution mode: sequential
- Selected streams: runtime, tests, live-evidence validation
- Real subagents: unavailable in this execution context
- Fallback review: explicit role-based review by Senior DevOps, Senior Tester,
  Senior Python Automation Developer, Senior System Architect and Live Evidence
  Validation Expert
- Git worktrees: not used; the live target and rollback boundary are shared

## Approved reversible update

The repository exposes no separate update CLI. The controlled update input is
the supported Compose image override:

```text
TSW_TRAEFIK_IMAGE=traefik@sha256:fcdef599e6259359833dd2e1d49f9e964f66825d69bd3dd468f51102ce013d03
```

The current service uses `traefik:v3.7.4`; the manager already has the digest
and both references resolve to image ID
`sha256:f66893ac132535099f7ef6c40ca1636f6a89f2c373c0eef28dd84537928ec0b6`.
The update is therefore content-identical, reversible by omitting the override,
and does not require a new image pull or secret change. No service profile,
stack membership, data volume, route, credential or unrelated image is
changed.

## Scope and locks

- Expected ignored evidence path: `.tiny-swarm-world/evidence/classic-public-beta-rc1/wsl2/RC1-S06/`
- Tracked governance evidence path:
  `.codex/evidence/slice-S252-06-consolidation.md`
- File lock: `.tiny-swarm-world/evidence/classic-public-beta-rc1/wsl2/`
- Contract locks: safe update, preservation, rollback evidence
- Architecture locks: non-destructive reconcile, verify-after-apply

Parallel execution is rejected because the update, rollback boundary and
post-update acceptance share the same WSL2 Incus/Docker/Swarm state.

## Update contract

- Load the existing operator env only inside WSL.
- Add the digest override only to the setup process; do not edit or print the
  local secret env file.
- Execute `setup run --live --approve-live` with the existing service-access
  profile and WSL filesystem override.
- Compare before/after service image, node, stack, service, route and secret
  identities.
- Rerun the complete Classic suite and platform verification.
- Rollback reference: repeat the same setup command without
  `TSW_TRAEFIK_IMAGE`; do not perform rollback unless the update changes
  unrelated state or fails verification.

## Stop conditions

Stop on any image mismatch, unexpected stack/service change, readiness failure,
secret change, unrelated state loss, unverified update or evidence/redaction
failure.
