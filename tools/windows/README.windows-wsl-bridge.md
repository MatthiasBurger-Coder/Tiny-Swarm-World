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

## One-time install

Open **PowerShell as Administrator**:

```powershell
cd D:\Projects\Tiny-Swarm-World

Set-ExecutionPolicy -Scope Process Bypass

.\tools\windows\tws-wsl-bridge.ps1 -Action install
```

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

`verify` may fail before Tiny Swarm services are actually running. That is expected. The bridge can exist before the services listen.

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
