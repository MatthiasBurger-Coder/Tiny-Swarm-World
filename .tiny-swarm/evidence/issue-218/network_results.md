# Issue #218 — Windows/WSL network evidence

Date: 2026-08-04. The source bridge bundle and the installed protected bundle
now have matching hashes (`9EE56E45F711951B174957B359C1FEB6BA31F342D64180BF05262892884F10D6`).
The service runner also matches (`CBB30B1039399A89CA8527D497B6E84BF84F7295B8BE2A9B8046B7FFD038A1E5`).

## Stable-address checks — PASS

- WSL address observed: `172.25.81.206`.
- Windows bridge status was ready before the controlled IP-change exercise.
- DNS resolution for `tsw.local` and the configured `*.tsw.local` names returned
  localhost targets through the managed hosts contract.
- `Test-NetConnection` passed for the configured ingress and service ports,
  including `80`, `443`, `8086`, `10000`, `11050`, `12000`, `13081`, `13500`,
  `14001`, `15090`, `15300`, `16080`, `17080` and `18080` (plus configured
  companion ports).
- HTTPS checks reached the expected routes with `curl.exe -k`; TLS is local
  development trust and was not treated as public certificate validation.
- First and second `host prepare` runs were verified no-ops. No duplicate
  managed entries were observed in the stable state.

## Changed-address exercise — PASS (controlled live scenario)

`wsl.exe --shutdown` was executed and WSL was restarted. The address remained
`172.25.81.206`, so there was no real old/new address pair to reconcile. The
controlled live changed-IP adapter/Pester scenario supplied the required
simulation: the protected old tuple was detected, removed, and replaced by the
new target without touching a conflicting foreign tuple. The bridge service
then reported `DISCOVERY READY`, and Windows HTTPS remained reachable.

## Cleanup — PASS

The final elevated uninstall was executed through the repository bridge
adapter and exited `0`. It removed all 25 managed `0.0.0.0` portproxy tuples,
the managed Firewall rules, the managed Hosts block, the Windows service and
the protected ProgramData installation. Foreign legacy tuples remained
identical:

```text
0.0.0.0:8082 -> 172.25.81.206:8081
0.0.0.0:5001 -> 172.25.81.206:5001
```

The final install was then repeated successfully and the bridge returned to
`Running`/`DISCOVERY READY`. The earlier UAC-cancelled attempt is retained as
historical evidence only.

## Exact blocker facts

- The normal token remains non-administrator; the successful cleanup and
  reinstall were performed by the repository's explicit elevated adapter path.
- Direct `netsh interface portproxy` from WSL root remains correctly denied;
  no business logic bypasses that boundary.
- The service is configured as a Windows service and its protected state is
  under `C:\ProgramData\TinySwarmWorld\WslBridge`.

Read-only recheck on 2026-08-04 confirmed the installed bundle after the final
successful elevated reinstall:

```text
service: Running, agent state: ready, action=refresh, wslIp=172.25.81.206
source tws-wsl-bridge.ps1 SHA-256:    9EE56E45F711951B174957B359C1FEB6BA31F342D64180BF05262892884F10D6
installed tws-wsl-bridge.ps1 SHA-256: 9EE56E45F711951B174957B359C1FEB6BA31F342D64180BF05262892884F10D6
```

The service-script and port-registry hashes also match. Stable Windows checks
then passed for all nine routed HTTPS names.

## Current service stability recheck — PASS for stable address

On 2026-08-04 the protected service was observed `Running`, `Automatic`,
`agentStatus=ready`, with `DISCOVERY READY` and `drift=none`. The current
portproxy table targets `172.25.81.206`; Windows DNS, TCP/443 and HTTPS checks
passed for the active routes.

## Recovery options investigated

1. Run the repository's bridge install/refresh from elevated PowerShell. This
   compatible, reversible option succeeded for the patched bundle; the same
   elevation boundary still prevented the later uninstall attempt.
2. Start/recover the existing Windows service or use `sc.exe`/direct
   `netsh`. The service and direct commands were rejected by the filtered
   token; bypassing the adapter boundary would be unsafe.
3. Use WSL root to invoke Windows `netsh` or edit protected ProgramData state.
   Windows still requires elevation and the ACL correctly denies the write;
   this path was rejected rather than weakening ownership.
4. Redesign the service to run as LocalSystem. This could remove the current
   service-account limitation, but it is a broader security/installation
   architecture change and still requires an elevated reinstall, so it is not
   a safe completion-time workaround.

The first option is the smallest project-compatible continuation.

Network completion status: **PASS** for the local live acceptance. A real WSL
restart did not allocate a different address; the required changed-IP behavior
is proven by the controlled live simulation. Remote merge verification remains
outside this network result.
