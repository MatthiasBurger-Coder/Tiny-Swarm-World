# Issue #218 — Real WSL2 acceptance

Date: 2026-08-04 (current run; earlier 2026-08-02 observations remain historical)
Environment: Windows 11 host, Ubuntu WSL2, kernel `6.18.33.2-microsoft-standard-WSL2`, systemd/Incus/Docker Swarm active. The repository was on `/mnt/d`; the explicit filesystem override was used only after the default policy rejected that path.

## Current focused acceptance run

- `artifacts verify`: **PASS**, all 15 image contracts available; Nexus
  admin access, Docker-hosted, Docker-Hub proxy and Maven proxy repositories
  reported active.
- `deployment apply`: **PASS**, exit `0`; nine stacks registered and all
  persistent services reached their desired replicas. The Pulsar manager
  bootstrap job completed as a one-shot task.
- Separate `deployment verify`: **PASS**, exit `0`; Portainer, Traefik, Nexus,
  Jenkins, Pulsar, SonarQube, Swagger, Infisical and Service Access endpoint
  checks all verified with expected HTTP statuses.
- Separate `platform verify`: **PASS**, exit `0`; 26 preflight checks, all three
  Docker runtimes, Swarm membership, 18 LXC proxy devices and the Portainer
  endpoint verified with `mutation.executed=false`.
- Windows-side checks: **PASS** for all nine active `*.tsw.local` names. DNS,
  TCP/443 and HTTPS returned expected statuses (`200`, `301`, `302`, `403` or
  `404`). The installed bridge bundle matches the patched source hash.
- Read-only snapshot: **PASS**. With the bridge service heartbeat paused,
  deployment/platform verify both exited `0` and portproxy, managed firewall,
  managed hosts, bridge-state hash and Incus/Docker metadata were equal before
  and after.
- `wsl.exe --shutdown` restart retained `172.25.81.206`; the required changed
  address behavior was therefore validated by the controlled live
  adapter/Pester simulation, which passed stale-tuple reconciliation.
- Bridge cleanup: **PASS**. The final elevated uninstall exited `0`, removed
  the 25 managed `0.0.0.0` mappings, managed Firewall rules, managed Hosts
  block, service and protected ProgramData; foreign legacy tuples remained.
  The final install then restored the bridge and returned Discovery READY.
- Opt-in Selenium browser tests: **SKIPPED**, 9 routes because Selenium and a
  Linux Firefox driver are absent. The project documents these browser checks
  as opt-in; Windows-side external HTTPS checks independently passed for all
  nine active routes.

## Historical 2026-08-02 sequence

1. Real host detection reported WSL2 and Windows interop.
2. Default WSL-mounted filesystem policy rejected the project path.
3. The explicit `--allow-wsl-windows-filesystem` override was supplied and
   recorded in preflight evidence.
4. Resource and artifact-source preflight passed. The selected profile was
   `service-access` and direct internet was the active source mode because the
   optional Nexus cache was not ready.
5. Incus nodes `swarm-manager`, `swarm-worker-1` and `swarm-worker-2` were
   available; Docker Swarm and all regular profile services became ready.
6. Installer run `20260802T183134Z` completed preflight, platform init,
   reconcile/expose, artifact preparation/verification, deployment apply,
   deployment verify and platform verify with exit code `0`.
7. A fresh direct `setup run` on the current source also completed every
   phase with exit code `0`, including artifact preparation/verification,
   deployment apply/verify and platform verify. The full `service-access`
   profile reported readiness for Traefik, Infisical, Service Access,
   Portainer, Nexus, Jenkins, Pulsar, SonarQube and Swagger.
8. Separate `deployment verify` and `platform verify` commands each exited
   `0`, proving the workflows are independently invocable.
9. Windows-side DNS, all configured TCP ports, and HTTPS routes were checked
   while the WSL address was stable. Service responses included expected
   `200`, `301`, `302`, `403` and `404` application statuses.
10. Two separate `host prepare` calls returned `SUCCESS`, `verified=true` and
   `preparation_path=verified_noop`.
11. A separate read-only `host verify` collected process, Docker, Incus,
   cgroup and network diagnostics and exited `0`.
12. A controlled live resource-gate run placed the preflight process in a
   nested cgroup-v2 scope limited to 8 GiB. It reported the nested limit,
   returned `INSUFFICIENT`/`RESOURCE_GATED` with exit code `1`, and entered no
   platform phase. Incus instance/profile and Docker stack/service snapshots
   were identical before and after the run.
13. After the cgroup inspector correction, a normal real WSL2 `setup run`
    was repeated and again completed every configured phase with exit code `0`.

### Historical acceptance that did not pass

The WSL interface was deliberately changed from `172.25.81.206` to
`172.25.81.207`. The Windows portproxy target remained on the old address and
the installed bridge service refused reconciliation with:

```text
Portproxy reconcile refused a listener owned by a different tuple: 0.0.0.0:80
```

The source tree now contains the stale-target fix and Pester covers it, but the
installed ProgramData bundle still contained the pre-fix implementation. The
current PowerShell token was not elevated, so the protected service/bundle and
portproxy state could not be updated safely. The WSL address was restored and
Incus/Swarm was recovered; no completion claim is made for the IP-change test.

## Evidence locations

- Installer context/log/exit evidence: `.tiny-swarm-world/evidence/installation-tests/wsl2/20260802T183134Z/`
- Live preflight and verification JSON: `.tiny-swarm-world/evidence/`
- Windows Pester result: `.tiny-swarm-world/local/pester-issue-218.xml`
- Host preparation second result: `.tiny-swarm-world/local/host-prepare-second.json`

Final live WSL2 status: **PASS**. The live acceptance was followed by green
PR checks, merge to `main` at `4e8eff8f41c3f28dda240003f4fb24317d834a42`,
green post-merge main verification and Issue #218 closure.
