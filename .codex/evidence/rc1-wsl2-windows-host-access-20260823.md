# RC1-09 WSL2 Windows host access / routing

## Scenario record

- Scenario: `RC1-09 WSL2 WINDOWS -> WSL HOST ACCESS / ROUTING`
- Result: `PASS`
- Commit SHA: `27ce3960da98a9ba124fd3f9ff5e003b13e89c60`
- Branch: `feature/classic-public-beta-rc1-stabilization`
- Host: Windows 11 Pro build `26200`, WSL2 NAT
- WSL distribution: Ubuntu 26.04 LTS
- Start: `2026-08-23T14:04:53.3114012Z`
- End: `2026-08-23T14:07:39.4331161Z`
- Duration: approximately `166.1 s`
- Live consent: previously recorded for Issue #252 RC1 execution

## Executed checks

The checks were executed from the Windows host and from the running WSL2
distribution. They were read-only and did not alter bridge, firewall, hosts,
Incus, Docker, Swarm, or service state.

1. Windows bridge service and protected state:

   - `TinySwarmWorldWslBridge`: `Running`
   - `agentStatus`: `ready`
   - `driftReasons`: empty
   - protected state mapping count: `24`
   - bridge mappings: `80`, `443`, `8086`, `10000`, `10001`, `10080`,
     `10443`, `11050`, `11080`, `12000`, `13081`, `13500`, `13501`, `14001`,
     `14080`, `14081`, `15090`, `15300`, `16080`, `16081`, `17080`, `18080`,
     `18081`, `18082`

2. WSL address and routing:

   - current WSL IPv4: `172.25.81.206`
   - protected bridge WSL IPv4: `172.25.81.206`
   - WSL default route: `172.25.80.1` via `eth0`
   - Incus bridge route: `10.85.194.0/24` via `incusbr0`
   - Docker bridge route: `172.17.0.0/16` via `docker0`

3. Windows portproxy:

   - `netsh interface portproxy show v4tov4` showed all required mappings
     targeting `172.25.81.206`.
   - Sampled public ingress and operator ports: `80`, `443`, `10000`,
     `10080`, `10443`.
   - The complete bridge state contained all registry-derived mappings.

4. Windows hosts/DNS resolution:

   - `15` managed `*.tsw.local` host entries were present.
   - `tsw.local`, `gateway.tsw.local`, `service-access.tsw.local`,
     `portainer.tsw.local`, `jenkins.tsw.local`, `sonarqube.tsw.local`,
     `nexus.tsw.local`, `pulsar.tsw.local`, and `infisical.tsw.local` resolved
     from Windows to `127.0.0.1` through the managed hosts surface.

5. Windows-side HTTP/HTTPS route verification using `curl.exe`:

   - `http://localhost:10000`: `200`
   - `http://service-access.tsw.local`: `301` (HTTP to HTTPS)
   - `https://infisical.tsw.local`: `200`
   - `https://jenkins.tsw.local`: `403` (expected protected route)
   - `https://nexus.tsw.local`: `200`
   - `https://portainer.tsw.local`: `200`
   - `https://pulsar-api.tsw.local/admin/v2/clusters`: `401` (expected
     unauthenticated API response)
   - `https://pulsar.tsw.local`: `200`
   - `https://service-access.tsw.local`: `200`
   - `https://sonarqube.tsw.local`: `200`
   - `https://swagger.tsw.local`: `302` (expected dashboard redirect)

6. Windows firewall/listener checks:

   - `22` Tiny Swarm World bridge firewall rules were found.
   - All `22` were enabled inbound allow rules.
   - Required Windows listeners were present for the published service
     surfaces.

7. Canonical WSL network diagnosis:

   - Command: `./tsw doctor network`
   - Exit code: `0`
   - Final diagnosis: `OK`
   - WSL egress, Incus bridge, LXC egress, forwarding, and service registry:
     `OK`.
   - The diagnostic itself reports that Windows portproxy verification needs
     elevated PowerShell; the equivalent elevated-state facts were verified
     directly from Windows in this scenario. The separate
     `tools/windows/doctor-portproxy.ps1` was not run in the non-elevated
     session and is therefore not used as evidence of the result.

## Restart and dynamic-IP evidence

RC1-08 executed a fresh `wsl.exe --shutdown` recovery before this scenario.
After that restart, the bridge agent rediscovered the current WSL address,
reported `ready`, and the Windows route matrix above passed. The address was
stable across the observed restart in this environment (`172.25.81.206`), so
no actual IP transition occurred during this run. The current-IP equality,
protected agent contract, portproxy targets, hosts resolution, and Windows
route probes were all verified after restart. The bridge implementation's
changed-IP reconciliation is additionally covered by its existing Windows
behavior regression tests; no synthetic state was accepted as live RC1
evidence.

## Preflight, runtime, and evidence state

- Preflight: `PASS`
- Incus/LXC nodes: previously verified ready in RC1-08; no node drift observed
- Docker/Swarm: previously verified ready in RC1-08; no mutation performed
- Stacks/services: previously verified ready in RC1-08; Windows route matrix
  reached the active service surfaces
- Routing: `PASS`
- Browser/API transport result: `PASS` for all active Windows route checks;
  protected endpoints returned their expected unauthenticated status
- Live verification state: `PASS`
- Defects discovered: none in RC1-09
- Manual repair: none
- Evidence files: this file; RC1-08 restart evidence; current protected
  bridge state outside the repository; command output retained in the live
  execution record
- Redaction: `PASS`; no passwords, tokens, hashes, credentials, or private
  keys recorded

## Final scenario result

`PASS` — Windows operator access through hosts resolution, Windows portproxy,
WSL2 NAT, Incus/LXC, Docker/Swarm, TLS ingress, and active service routes was
verified after the fresh WSL restart.
