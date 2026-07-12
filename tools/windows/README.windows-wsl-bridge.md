# Tiny Swarm World Windows <-> WSL Bridge

This directory contains the Windows-side preparation mechanism for Tiny Swarm World when WSL is treated as the guest system.

The bridge is intentionally a **one-time pre-installation step**. It prepares
Windows before `./install.sh` runs in WSL and registers a Windows service that
keeps the bridge aligned with the current WSL address afterwards.

## Why this exists

Tiny Swarm World runs services inside WSL, then inside Incus/LXC and Docker Swarm. Windows does not reliably discover that nested network path by itself.

This bridge reconciles:

1. Windows `netsh interface portproxy` rules
2. Windows Firewall inbound rules
3. Windows `hosts` entries for stable `*.tsw.local` names
4. An automatic Windows service that discovers and reconciles drift at the
   configured interval

The installer downloads the pinned WinSW 2.12.0 service wrapper from its
official GitHub release and verifies its SHA-256 checksum before installation.

TCP ports and route hostnames are read from `infra/config/ports.yaml`.
`tws-wsl-bridge.config.json` contains only Windows-side settings such as the
WSL distro, listen address, hosts address, firewall prefix and extra hostname
aliases.

## Prerequisites

The supported bridge path requires:

1. Windows 10 or Windows 11 with WSL 2 installed
2. A running WSL 2 distribution; the default distribution is used unless
   `distro` is set in `tws-wsl-bridge.config.json`
3. `systemd` as PID 1 inside that distribution
4. Windows PowerShell 5.1 or newer, opened as Administrator
5. The Windows IP Helper service (`iphlpsvc`) running
6. Windows Firewall and Service cmdlets
7. The tracked bridge config and `infra/config/ports.yaml`

Check all prerequisites without changing portproxy, Firewall, hosts, service, or
state-file data:

```powershell
cd D:\Projects\Tiny-Swarm-World
Set-ExecutionPolicy -Scope Process Bypass
.\tools\windows\tws-wsl-bridge.ps1 -Action prerequisites
```

The check is ready only when every line reports `PREREQUISITE OK`. A normal,
non-elevated PowerShell deliberately reports `administrator` as failed because
the subsequent install needs elevation.

### Reach the prerequisite state

Install or update WSL and make WSL 2 the default from elevated PowerShell:

```powershell
wsl --install
wsl --update
wsl --set-default-version 2
wsl --list --verbose
```

If the selected distribution is still version 1, convert it explicitly:

```powershell
wsl --set-version <DistributionName> 2
```

Enable systemd inside the selected WSL distribution by adding this content to
`/etc/wsl.conf`:

```ini
[boot]
systemd=true
```

Then restart WSL from Windows and verify PID 1:

```powershell
wsl --shutdown
wsl -d <DistributionName> --exec sh -lc "ps -p 1 -o comm="
```

The result must be `systemd`. If IP Helper is stopped, start it from elevated
PowerShell:

```powershell
Start-Service iphlpsvc
Set-Service iphlpsvc -StartupType Automatic
```

Re-run `-Action prerequisites` after each repair. Installing WSL or converting
a distribution can require a reboot; the bridge script does not hide that
host-level lifecycle.

## One-time install

Open **PowerShell as Administrator**:

```powershell
cd D:\Projects\Tiny-Swarm-World

Set-ExecutionPolicy -Scope Process Bypass

.\tools\windows\tws-wsl-bridge.ps1 -Action install
```

`install` repeats the prerequisite gate before making changes. It registers the
automatic Windows service and then reconciles only Tiny Swarm World's
registry-defined TCP mappings and managed Windows artifacts. Re-running it is
the supported repair and agent-upgrade path.

The first installation opens a Windows credential dialog. Enter the Windows
account that owns the WSL distribution. The password is handed directly to the
Windows Service Control Manager and is not written to the repository or bridge
configuration.

Repair compares Windows account SIDs, so equivalent local-account forms such
as `.\user` and `COMPUTER\user` do not trigger a replacement or another
credential prompt. A later prompt occurs only when the service registration is
missing. A registration with a different path or account is classified as a
collision and is not stopped, deleted, or repaired automatically.

The elevated install action copies the reviewed bridge script, runner,
configuration, and port registry into a hardened bundle below
`%ProgramData%\TinySwarmWorld\WslBridge`. The service executes only that bundle;
later checkout edits are not picked up by a periodic refresh or service restart.
Run the elevated `install` action again to publish a reviewed update. The bundle
removes inherited write access, grants only SYSTEM and Administrators full
control, and gives the WSL-owner account read/execute access. WinSW is stored in
the same protected directory and is accepted only after its pinned SHA-256
checksum matches immediately before service start.

ACL changes use no-follow Windows handles and one atomic owner/DACL update per
path. The namespace parent is part of ownership verification; reparse points,
hard-linked files, unexpected ACEs, and path-identity changes fail closed.
Upgrading an older bridge ACL is permitted only by the explicit `install`
action after the SCM path and account SID match. The script then hardens the
namespace under the reconciliation mutex and repeats the complete ownership
check before staging or stopping the service.

WinSW log files are not executable input or cleanup/state authority. Their
directory remains exactly protected; direct log files may use its safe inherited
ACL but are still rejected if they are directories, reparse points, or hard
links.

An upgrade is prepared in a same-volume staging directory and validated before
the owned service is stopped. Bundle, wrapper, XML, and installation manifest
are switched under a protected per-item journal. The update is committed only
after a fresh `ready` heartbeat reports the staged bundle identity. A failed or
interrupted update restores the fingerprinted previous payload and restarts the
previously running service; an unrecognized file or registration fails closed.

If your WSL distro is not the default distro, edit:

```json
{
  "distro": "auto"
}
```

in `tools/windows/tws-wsl-bridge.config.json`.

`discoveryIntervalMinutes` controls the periodic reconcile interval and must be
between 1 and 60. The default is one minute.

Examples:

```json
"distro": "Ubuntu-24.04"
```

or:

```json
"distro": "Debian"
```

## Automatic discovery after WSL restart

The Windows service starts automatically, reconciles immediately, and then runs
once per configured interval. It reads the current WSL IPv4 address and its
installed port-registry snapshot, compares them with Windows portproxy, Firewall and
hosts-file state, and changes only drifted resources. An unchanged run is a
no-op apart from renewing the prepared-state heartbeat.

If immediate recovery is needed before the next interval, trigger the agent
from Windows:

```powershell
Restart-Service -Name TinySwarmWorldWslBridge
```

Or from WSL:

```bash
powershell.exe -NoProfile -Command "Restart-Service -Name TinySwarmWorldWslBridge"
```

## Verify

From Windows PowerShell:

```powershell
.\tools\windows\tws-wsl-bridge.ps1 -Action status
.\tools\windows\tws-wsl-bridge.ps1 -Action verify
```

Use the actions for different evidence:

- `prerequisites` proves that Windows and WSL can support the bridge.
- `discover` is read-only and reports `READY` or the detected drift reasons.
- `reconcile` is the idempotent action used by the Windows service.
- `status` shows configured ports, the current WSL IP, portproxy state, the
  Windows service, and the managed hosts block.
- `verify` performs live TCP connections to every registry-defined Windows
  localhost port.

`verify` may fail before Tiny Swarm services are actually running. That is
expected and does not invalidate a successful prerequisite or bridge install.
After the Tiny Swarm installation, all ports belonging to deployed services
must be checked again as live service evidence.

## Prepared-state contract

The Windows/WSL bridge is prepared for `install.sh` when:

- `prerequisites` passes;
- the managed portproxy rules target the current WSL IPv4 address;
- matching Tiny Swarm World Firewall rules exist;
- the managed `*.tsw.local` hosts block exists;
- `TinySwarmWorldWslBridge` is registered as an automatic Windows service;
- the service definition references only the hardened ProgramData bundle and
  the pinned WinSW wrapper still has the expected SHA-256 hash;
- `%ProgramData%\TinySwarmWorld\WslBridge\bridge-state.json` exists, is recent,
  records the current WSL IP and verified bundle identity, and contains every
  external TCP port from
  `infra/config/ports.yaml`;
- the state reports contract version 2, agent mode `windows-service`, and
  agent status `ready`.

Run `-Action install` once to create this complete state and service agent.
`refresh` remains a compatibility alias for `reconcile`. The protected state is
outside the repository and is never mirrored into the checkout by the
privileged service.

Legacy Scheduled Tasks are removed after the service reaches its verified
running state. They are never accepted as a prepared-agent fallback.

## Tiny Swarm installer preflight

When WSL2 live setup requires Windows exposure, `./install.sh` checks for:

- `/mnt/c/ProgramData/TinySwarmWorld/WslBridge/bridge-state.json`
- the owned Windows-service agent contract, verified bundle identity, and
  `ready` status
- a discovery heartbeat no older than five minutes
- a current WSL IP matching the state file
- all external TCP ports from `infra/config/ports.yaml` in the state file

During a reconcile, the agent first writes the exact transient marker
`agentStatus=degraded` with `driftReasons=["reconcile_in_progress"]`. Only after
observing that trusted marker may preflight reread a temporarily missing or
partially written state file. The default bound is 180 retries at 0.5 seconds,
or at most 90 seconds. A persistent invalid/missing state fails closed at the
bound; any other real drift fails immediately without consuming the grace
period.

If this check fails, setup stops before platform mutation with
`WINDOWS-WSL-BRIDGE`. To run WSL2 without Windows localhost/browser exposure,
set `TSW_WINDOWS_EXPOSURE=disabled` explicitly before setup.

Consequently, a successful WSL installation with Windows exposure enabled has
already passed a current automatic-bridge contract. The agent continues to
repair later WSL address changes without modifying the native Linux install
path.

## Run Tiny Swarm installation after bridge preparation

Inside WSL:

```bash
cd /mnt/d/Projects/Tiny-Swarm-World

./install.sh --headless --confirm-reset --non-interactive-live-approval
```

## Browser entry points

After installation:

```text
https://gateway.tsw.local
https://service-access.tsw.local
http://localhost:10000
http://localhost:10080
https://localhost:10443
http://localhost:10001
http://localhost:11080
http://localhost:12000
http://localhost:13081
http://localhost:14080
http://localhost:15090
http://localhost:15300
http://localhost:16080
http://localhost:17080
http://localhost:18080
```

The `*.tsw.local` entries are not wildcard DNS entries. The default mechanism
uses the Windows hosts file. Canonical hostnames come from `route_host` values
in `infra/config/ports.yaml`; `tws-wsl-bridge.config.json` contains an empty
`hostNames` extension list by default so it does not create a parallel route
namespace. The managed block writes one hostname per line so Windows name
resolution does not drop aliases because of a long hosts-file line.

## Uninstall

Open PowerShell as Administrator:

```powershell
.\tools\windows\tws-wsl-bridge.ps1 -Action uninstall
```

This first validates a complete cleanup plan from protected ProgramData state,
then removes only exact Tiny Swarm portproxy tuples, exact firewall rule names,
the hosts block, the owned Windows service, and the legacy scheduled task. A
missing protected state or ownership collision stops uninstall before mutation.
`SeServiceLogonRight` is removed only when the protected installation manifest
proves Tiny Swarm World added it and no other Windows service uses the account.

## Optional DNS resolver

`optional\tws_dns_resolver.py` is included only for experiments with a real `tsw.local` zone. It is **not** the default path because binding DNS on Windows port 53 and integrating it into Windows name resolution is more fragile than using explicit hosts entries.

Default recommendation:

```text
Use hosts-file entries for known Tiny Swarm service names.
Use portproxy for TCP access.
Use the Windows service discovery agent for automatic reconcile.
```
