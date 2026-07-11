# Tiny Swarm World Windows <-> WSL Bridge

This directory contains the Windows-side preparation mechanism for Tiny Swarm World when WSL is treated as the guest system.

The bridge is intentionally a **one-time pre-installation step**. It prepares
Windows before `./install.sh` runs in WSL and registers a scheduled discovery
agent that keeps the bridge aligned with the current WSL address afterwards.

## Why this exists

Tiny Swarm World runs services inside WSL, then inside Incus/LXC and Docker Swarm. Windows does not reliably discover that nested network path by itself.

This bridge reconciles:

1. Windows `netsh interface portproxy` rules
2. Windows Firewall inbound rules
3. Windows `hosts` entries for stable `*.tws.local` names
4. A Scheduled Task that discovers and reconciles drift after logon and every
   configured interval

No additional Windows software is required for the default mechanism.

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
6. Windows Firewall and Scheduled Task cmdlets
7. The tracked bridge config and `infra/config/ports.yaml`

Check all prerequisites without changing portproxy, Firewall, hosts, task, or
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
scheduled discovery agent and then reconciles only Tiny Swarm World's
registry-defined TCP mappings and managed Windows artifacts. Re-running it is
the supported repair and agent-upgrade path.

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

The scheduled discovery agent runs after Windows logon and once per configured
interval. It reads the current WSL IPv4 address and the repository port
registry, compares them with the observed Windows portproxy, Firewall and
hosts-file state, and changes only drifted resources. An unchanged run is a
no-op apart from renewing the prepared-state heartbeat.

If immediate recovery is needed before the next interval, trigger the agent
from Windows:

```powershell
Start-ScheduledTask -TaskName TinySwarmWorld-WslBridge
```

Or from WSL:

```bash
powershell.exe -NoProfile -Command "Start-ScheduledTask -TaskName TinySwarmWorld-WslBridge"
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
- `reconcile` is the idempotent action used by the scheduled discovery agent.
- `status` shows configured ports, the current WSL IP, portproxy state, the
  Scheduled Task, and the managed hosts block.
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
- `TinySwarmWorld-WslBridge` is registered for discovery/reconcile after logon
  and periodically;
- `tools/windows/.tws-wsl-bridge.state.json` exists, is recent, records the
  current WSL IP, and contains every external TCP port from
  `infra/config/ports.yaml`;
- the state reports contract version 2, agent mode `scheduled-discovery`, and
  agent status `ready`.

Run `-Action install` once to create this complete state and scheduled agent.
`refresh` remains a compatibility alias for `reconcile`. The generated state
file is ignored by Git and must not be committed.

## Tiny Swarm installer preflight

When WSL2 live setup requires Windows exposure, `./install.sh` checks for:

- `tools/windows/.tws-wsl-bridge.state.json`
- the scheduled-discovery agent contract and `ready` status
- a discovery heartbeat no older than five minutes
- a current WSL IP matching the state file
- all external TCP ports from `infra/config/ports.yaml` in the state file

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
http://gateway.tws.local
https://gateway.tws.local
http://service-access.tws.local
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

The `*.tws.local` entries are not wildcard DNS entries. The default mechanism
uses the Windows hosts file. Hostnames come from explicit aliases in
`tws-wsl-bridge.config.json` plus `route_host` values in
`infra/config/ports.yaml`.

## Uninstall

Open PowerShell as Administrator:

```powershell
.\tools\windows\tws-wsl-bridge.ps1 -Action uninstall
```

This removes only the managed Tiny Swarm portproxy rules, firewall rules, hosts block and scheduled task.

## Optional DNS resolver

`optional\tws_dns_resolver.py` is included only for experiments with a real `tws.local` zone. It is **not** the default path because binding DNS on Windows port 53 and integrating it into Windows name resolution is more fragile than using explicit hosts entries.

Default recommendation:

```text
Use hosts-file entries for known Tiny Swarm service names.
Use portproxy for TCP access.
Use the Scheduled Task discovery agent for automatic reconcile.
```
