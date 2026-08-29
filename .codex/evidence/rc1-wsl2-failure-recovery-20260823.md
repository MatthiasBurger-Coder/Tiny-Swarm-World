# RC1 WSL2 Failure / Recovery

## Scenario

| Field | Value |
|---|---|
| Scenario ID | RC1-07 WSL2 FAILURE / RECOVERY |
| Covered contracts | RC1-S07 missing prerequisite fail-closed; RC1-S08 partial-state recovery |
| Commit SHA | `27ce3960da98a9ba124fd3f9ff5e003b13e89c60` |
| Branch | `feature/classic-public-beta-rc1-stabilization` |
| Host type | WSL2 / Incus / LXC-native Docker Swarm |
| Operating system | Ubuntu on WSL2, kernel `6.18.33.2-microsoft-standard-WSL2` |
| Final result | `PASS` |

## RC1-S07 — missing prerequisite fail-closed

The existing local environment was sourced, then
`TSW_INFISICAL_LOGIN_EMAIL` was removed in-process only. The ignored local
environment file was not changed.

```text
./tsw --json --preflight --service-profile service-access \
  --allow-wsl-windows-filesystem
```

- Start: `2026-08-23T13:34:09Z`
- End: `2026-08-23T13:34:23Z`
- Observed command exit code: `1`
- Result: expected fail-closed behavior before live mutation.
- Evidence: the mandatory secret check reported `FAILED` with remediation to
  provide the value through the environment or ignored local file.
- No Incus, Docker, Swarm, stack, routing, or service mutation occurred.

This is a successful failure-semantic assertion; the blocked runtime state is
not treated as a service acceptance pass.

## RC1-S08 — partial-state recovery

The existing valid installation was then reconciled with the canonical
state-preserving command:

```text
./tsw --live --approve-live --json --service-profile service-access \
  --allow-wsl-windows-filesystem platform reconcile
```

- Start: `2026-08-23T13:34:32Z`
- End: `2026-08-23T13:34:39Z`
- Exit code: `0`
- Mutation: `no_op`; no reset, destroy, secret deletion, or broad cleanup.
- Verification: `verified`.
- Incus/LXC nodes: `swarm-manager`, `swarm-worker-1`, and `swarm-worker-2`
  all `already_present` and verified with the same identities.

## Post-recovery platform verification

```text
./tsw --json --service-profile service-access \
  --allow-wsl-windows-filesystem platform verify
```

- Start: `2026-08-23T13:34:58Z`
- End: `2026-08-23T13:35:13Z`
- Exit code: `0`
- Result: `completed`, `verification: verified`.
- Platform checks: 26 verified.
- Proxy devices: 18 present, zero missing, drifted, unknown, or failed.
- Portainer local Docker endpoint: registered and ready.

## Defects and redaction

- New RC1 blocker: none.
- Manual repair: not required.
- The previously fixed Traefik TLS blocker remained closed.
- No password, hash, token, private key, auth header, or local env-file
  content was recorded.

**Final scenario result: RC1-07 PASS.**
