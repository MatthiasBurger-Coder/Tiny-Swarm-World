# RC1 WSL2 Update and Post-Update Acceptance

## Scenario records

| Field | RC1-05 WSL2 UPDATE | RC1-06 WSL2 POST-UPDATE ACCEPTANCE |
|---|---|---|
| Scenario ID | RC1-05 | RC1-06 |
| Commit SHA | `27ce3960da98a9ba124fd3f9ff5e003b13e89c60` | `27ce3960da98a9ba124fd3f9ff5e003b13e89c60` |
| Branch | `feature/classic-public-beta-rc1-stabilization` | `feature/classic-public-beta-rc1-stabilization` |
| Host type | WSL2 / Incus / LXC-native Docker Swarm | WSL2 / Incus / LXC-native Docker Swarm |
| Operating system | Ubuntu on WSL2, kernel `6.18.33.2-microsoft-standard-WSL2` | Ubuntu on WSL2, kernel `6.18.33.2-microsoft-standard-WSL2` |
| Start (UTC) | `2026-08-23T13:29:53.687809Z` | After RC1-05 completion |
| End (UTC) | `2026-08-23T13:31:09.043040Z` | `2026-08-23T13:31:21Z` evidence generated |
| Duration | `75.355231 s` | `28 tests / 2.064 s` |
| Exit code | `0` | `0` |
| Final result | `PASS` | `PASS` |

## Executed commands

RC1-05 used the existing supported setup path with the evidence-defined,
process-local Traefik image update input:

```text
TSW_TRAEFIK_IMAGE=traefik@sha256:fcdef599e6259359833dd2e1d49f9e964f66825d69bd3dd468f51102ce013d03 \
PYTHONPATH=src python3 -m tiny_swarm_world setup run --live --approve-live --json \
  --service-profile service-access --allow-wsl-windows-filesystem
```

RC1-06 used the existing live post-install acceptance suite:

```text
TSW_RUN_POST_INSTALL_BROWSER_LIVE=1 PYTHONPATH=src \
python3 -m unittest tests.e2e.classic.test_post_install_browser_live
```

## Verification

- Preflight: `PASSED`; live consent, configuration, supported WSL2 host, and
  artifact contract checks were verified.
- Incus/LXC nodes: `swarm-manager`, `swarm-worker-1`, and `swarm-worker-2`
  verified as present and healthy.
- Docker/Swarm: all required replicated services healthy; expected one-shot
  `pulsar-manager-bootstrap` remains `0/1` after completion.
- Traefik: service updated from `traefik:v3.7.4` to the requested immutable
  digest and reached `1/1 Running`.
- Traefik secrets: the operator-provisioned htpasswd secret and TLS
  certificate/key secrets remained attached to the running service; no secret
  values were recorded.
- Deployment apply, deployment verify, and platform verify: `completed` /
  `verified`, with zero managed-config blockers and all required stack
  services discovered.
- Post-update live acceptance: 28 tests passed. HTTP, DNS, HTTPS/TLS route
  verification, service access, Infisical management, and credential checks
  were green. Evidence: `.tiny-swarm-world/evidence/classic-public-beta-rc1/20260823T133119Z/summary.json`.

## Defects and evidence

- New RC1 defect: none.
- Previously active Traefik TLS evidence blocker: closed by the corrected
  local certificate generation and CA-bundle propagation fix; no workaround or
  manual repair was used during this update.
- Runtime evidence is redacted. Passwords, hashes, tokens, private keys, and
  secret contents are not stored in this record.

**Final scenario result: RC1-05 PASS; RC1-06 PASS.**
