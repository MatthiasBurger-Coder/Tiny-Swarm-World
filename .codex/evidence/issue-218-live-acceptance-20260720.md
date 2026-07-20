# Issue #218 Live Acceptance Evidence

Date: 2026-07-20
Environment: WSL2, non-production local environment

## Passed checks

- Live installation completed successfully with generated non-production
  secrets.
- External Docker Desktop container `tiny-swarm-nexus-cache` was used as the
  Nexus instance. Its published ports are 8081 (Nexus HTTP) and 5000 (Docker
  Registry).
- Reachable repository endpoints from the Incus nodes:
  - `http://10.85.194.1:8081/repository/ubuntu-apt-proxy`
  - `http://10.85.194.1:8081/repository/ubuntu-security-apt-proxy`
  - `http://10.85.194.1:8081/repository/docker-apt-proxy`
  - `http://10.85.194.1:5000`
- Docker Engine 28.5.2 installed on manager and both workers.
- Docker Swarm reports three Ready nodes and the manager is Leader.
- DNS resolves `service-access.tsw.local` and `nexus.tsw.local` to
  `127.0.0.1` inside WSL.
- WSL HTTPS requests to `service-access.tsw.local` and `nexus.tsw.local`
  returned HTTP 200.
- Windows DNS resolution and HTTPS requests to both hosts returned HTTP 200.
- TCP connectivity checks passed for ports 80, 443, 5000 and 8081.
- Nexus and Service Access services report `1/1` replicas.
- Read-only Docker node/service inspection completed without mutation.
- Direct fail-closed validation was reproduced for an invalid TCP port:
  `New-BridgeCleanupPlan` rejects `connectPort=70000` before any mutation.

## Still required

- Repeat the checks after a WSL IP change and prove network preparation is
  idempotent across that change.
- Capture explicit Windows firewall and portproxy state before and after the
  repeat run.
- Execute the intentionally insufficient-resource scenario and retain its
  blocking evidence.
- Complete the independent Issue Completion Auditor and final acceptance
  checklist decision before closing Issue #218.

## Verification limitation

The Windows bridge suite is executed with Windows PowerShell Pester 3.4.0.
Its exception assertions are not reliably selectable/executed in this
environment, although the underlying `Assert-ValidTcpPort` and
`New-BridgeCleanupPlan` behavior was reproduced directly and failed closed.

No issue-closing claim is made by this evidence file.
