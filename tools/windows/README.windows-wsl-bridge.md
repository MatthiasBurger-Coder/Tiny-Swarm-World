# Tiny Swarm World Windows <-> WSL Bridge

This directory contains the Windows-side preparation mechanism for Tiny Swarm World when WSL is treated as the guest system.

The bridge is intentionally a **pre-installation step**. It prepares Windows before `./install.sh` runs in WSL.

## Why this exists

Tiny Swarm World runs services inside WSL, then inside Incus/LXC and Docker Swarm. Windows does not reliably discover that nested network path by itself.

This bridge reconciles:

1. Windows `netsh interface portproxy` rules
2. Windows Firewall inbound rules
3. Windows `hosts` entries for stable `*.tws.local` names
4. A Scheduled Task that refreshes the bridge after logon or WSL IP changes

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

`install` repeats the prerequisite gate before making changes. It then
reconciles only Tiny Swarm World's registry-defined TCP mappings and managed
Windows artifacts. Re-running it is the supported repair path.

If your WSL distro is not the default distro, edit:

```json
{
  "distro": "auto"
}
```

in `tools/windows/tws-wsl-bridge.config.json`.

Examples:

```json
"distro": "Ubuntu-24.04"
```

or:

```json
"distro": "Debian"
```

## Refresh after WSL restart

If WSL was shut down, the WSL IP can change. Refresh the bridge from Windows:

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
- `TinySwarmWorld-WslBridge` is registered for refresh after logon;
- `tools/windows/.tws-wsl-bridge.state.json` exists, is recent, records the
  current WSL IP, and contains every external TCP port from
  `infra/config/ports.yaml`.

Run `-Action install` to create this complete state. Run `-Action refresh`
after a WSL address change. The generated state file is ignored by Git and
must not be committed.

## Tiny Swarm installer preflight

When WSL2 live setup requires Windows exposure, `./install.sh` checks for:

- `tools/windows/.tws-wsl-bridge.state.json`
- a current WSL IP matching the state file
- all external TCP ports from `infra/config/ports.yaml` in the state file

If this check fails, setup stops before platform mutation with
`WINDOWS-WSL-BRIDGE`. To run WSL2 without Windows localhost/browser exposure,
set `TSW_WINDOWS_EXPOSURE=disabled` explicitly before setup.

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
Use Scheduled Task for automatic refresh.
```
