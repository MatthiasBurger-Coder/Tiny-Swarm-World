# Issue #218 — Implementation summary

Date: 2026-08-04
Decision: **PASS — implementation, live acceptance, publication and main
verification complete**.

## Implemented and verified locally

- Dedicated host detection distinguishes native Linux, WSL1, WSL2 and
  unsupported/ambiguous signals.
- WSL filesystem policy blocks Windows-mounted project paths unless an explicit
  override is supplied and recorded.
- WSL resource inspection covers CPU, `/proc/meminfo`, `free -b`, cgroup
  memory current/max/high/events/stat, disk capacity and pressure assessment.
- cgroup-v2 inspection resolves the current process scope instead of assuming
  the filesystem root, so nested systemd memory limits are enforced.
- The resource adapter records whether CPU and memory values came from
  `nproc`/`free -b` or fixture-safe Linux fallbacks.
- Host-specific adapters are created lazily only after typed host selection;
  `setup run` orders `host prepare` and `host verify` before Incus phases.
- Static preflight returns its structured result without writing generic
  evidence; accepted live preflight retains the evidence write boundary.
- Service-profile and aggregate Incus-limit validation run before mutation and
  include the explicit 8 GiB host / 10 GiB manager guard test.
- Host preparation is separated into application ports, domain decisions and
  infrastructure adapters; native Linux uses a no-op adapter.
- Windows command execution remains behind a dedicated runner and the existing
  protected PowerShell bridge service owns portproxy, firewall and hosts-file
  mutation.
- Installer artifact readiness has direct-internet, configured-cache and
  fallback semantics with bounded probes; the fresh live run used direct
  internet because the optional Nexus cache was unavailable. Explicit offline
  mode now requires a checksum-verified local artifact manifest.
- Setup phases emit typed statuses and structured progress with bounded phase
  subprocesses; deployment apply, deployment verify and platform verify are
  separate invocations.
- Read-only hang diagnostics collect bounded process, Docker, Incus, cgroup and
  network state. Docker log collection now executes a bounded tail command.
- `host prepare` skips the installation-port gate after the platform is already
  installed, allowing a second idempotent preparation to report verified no-op.
- The source bridge script now identifies a changed WSL target tuple as stale,
  and read-only bridge verification rejects agent drift even when a TCP port is
  listening.
- Deployment verify has a central positive timeout configuration
  (`TSW_DEPLOYMENT_VERIFY_TIMEOUT_SECONDS`, default 300 seconds), bounded async
  endpoint probes and a typed `timed_out` result with partial evidence.
- Docker APT bootstrap uses bounded connect/total timeouts and configurable
  mirror settings; the live run verified all 15 image contracts against the
  prepared manager cache and active Nexus repositories.

## Live result

The current real WSL2 run completed artifact verification, deployment apply,
deployment verify and platform verify with exit code 0. Nine service stacks
were registered and all persistent services became ready; the Pulsar manager
bootstrap job completed as a one-shot task. The controlled 8-GiB cgroup preflight returned
`INSUFFICIENT`/`RESOURCE_GATED` before mutation with unchanged Incus/Docker
snapshots. Public-image preparation and verification now accept an already-
present manager cache without unnecessary registry access. DNS, Windows
TCP ports and HTTPS endpoints passed while the WSL address was stable. Two
explicit `host prepare` runs completed as verified no-ops.

The patched protected bridge bundle now matches source and stable Windows
DNS/TCP/HTTPS checks pass for all nine active routes. A controlled
`wsl.exe --shutdown` restart retained `172.25.81.206`; the adapter/Pester
changed-IP simulation passes the required stale-tuple migration. The final
elevated owned-only cleanup exited `0`, removed only managed resources and left
foreign legacy tuples unchanged; the final install restored Discovery READY.
The strict quiesced read-only snapshot also passed. The opt-in Selenium suite
recorded nine skips because WSL lacks Selenium and a Linux Firefox driver.

## Release decision

The source-level fix is covered by Pester 43/43, the full quality gate (1589
tests, 28 skips) and the native Linux host-platform regression on an actual
Ubuntu 24.04.4 VM with 202 targeted tests. PR #233 merged as
`4e8eff8f41c3f28dda240003f4fb24317d834a42`; PR checks, post-merge SonarCloud,
post-merge Quality Gate and Dependency Graph all passed. The independent
completion audit is PASS and Issue #218 is closed. The opt-in Selenium suite
is not a mandatory release gate under the project's documented live-test
contract.
