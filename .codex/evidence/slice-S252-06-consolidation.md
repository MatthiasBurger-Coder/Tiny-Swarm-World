# Issue #252 — S252-06 Consolidation

- Workflow: `issue-252-classic-public-beta-rc1-20260818`
- Slice: `S252-06` — WSL2 update and post-update acceptance
- Branch: `feature/classic-public-beta-rc1-stabilization`
- Host: WSL2/Linux userspace, commands executed through WSL
- Commit under test: `14cd01a391462aeec631d70640b4b490c560f955`
- Final slice result: `S252-06_LIVE_VERIFIED`

## Selected change

The setup workflow has no separate update command. The update used the
supported `TSW_TRAEFIK_IMAGE` Compose override for the existing Traefik stack:

- Before: `traefik:v3.7.4`
- Update input: `traefik@sha256:fcdef599e6259359833dd2e1d49f9e964f66825d69bd3dd468f51102ce013d03`
- Verified existing image ID: `sha256:f66893ac132535099f7ef6c40ca1636f6a89f2c373c0eef28dd84537928ec0b6`
- After: the requested digest reference
- Rollback: rerun the same setup command without the override, restoring the
  pinned tag reference; no rollback was needed because verification passed.

This was content-identical and did not change service membership, data
volumes, routes, secret names or unrelated image references.

## Commands and results

| Scenario | Command | Start | End | Duration | Exit |
|---|---|---|---|---:|---:|
| Controlled update | `./tsw setup run --live --approve-live --json --service-profile service-access --allow-wsl-windows-filesystem` with process-local `TSW_TRAEFIK_IMAGE` override | `2026-08-21T22:45:09+02:00` | `2026-08-21T22:46:29+02:00` | ~80 s | 0 |
| Post-update Classic acceptance | `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests/e2e/classic -t .` | `2026-08-21T22:46:53+02:00` | `2026-08-21T22:47:02+02:00` | ~9 s wall / 3.687 s test runtime | 0 |
| Post-update platform verification | `./tsw --json --service-profile service-access --allow-wsl-windows-filesystem platform verify` | `2026-08-21T22:47:06+02:00` | `2026-08-21T22:47:22+02:00` | ~16 s | 0 |

The operator env was loaded only inside the WSL process. The digest override
was process-local and no secret value or env-file content was emitted.

## Acceptance

- Setup update: all configured phases completed, including artifact readiness,
  deployment apply/verify and platform verify.
- Classic suite: `92` tests executed, `17` expected skips, `0` failures.
- Platform verification: `26` checks passed; all three managed Incus nodes
  were `already_present` and `verified`.
- Nodes before/after: `swarm-manager`, `swarm-worker-1`,
  `swarm-worker-2`; all remained `RUNNING` at the Incus layer and
  `Ready`/`Active` in Swarm, with the manager remaining `Leader`.
- Stacks before/after: the same nine stacks with the same service counts:
  `infisical(3)`, `jenkins(1)`, `nexus(1)`, `portainer(2)`, `pulsar(3)`,
  `service-access(2)`, `sonarqube(2)`, `swagger(4)`, `traefik(1)`.
- Services before/after: the same 19 services with the same replica states;
  all long-running services remained ready and
  `pulsar-manager-bootstrap` remained the expected completed `0/1` one-shot.
- Routing: all `18` expected LXC proxy devices remained present with zero
  drift, missing or unknown devices.
- Portainer: local endpoint remained registered and ready.
- Deployment readiness: all nine configured stack contracts reported verified
  endpoint readiness during the setup run.
- Secret evidence: only secret names were inspected; the Traefik secret names
  remained unchanged. No secret value, password, token, hash or private key
  was emitted.

## Findings and review

- Only the approved Traefik image reference changed.
- No unrelated healthy state was lost.
- No rollback was required.
- One transient `incus exec` child-PID lookup failure occurred during a
  read-only post-update node snapshot; the exact command succeeded on the
  bounded retry. It is recorded as an operational observation, not a product
  defect, because the update and verification workflows themselves completed
  successfully.
- No RC1 blocker or major defect was found in S252-06.
- Role-based fallback review was used because callable subagents were not
  available. The distribution record covers the required DevOps, tester,
  Python, architecture and live-evidence perspectives.

## Redaction and evidence

Redaction confirmed. This tracked consolidation contains no raw credentials,
join tokens, authorization headers, private keys, password values or full env
file. Runtime detail remains in ignored local evidence only. `composition.py`
was not changed.

Decision: S252-06 is live-verified. WSL2 failure/recovery/restart, Native Linux,
CI evidence and final audit remain open.
