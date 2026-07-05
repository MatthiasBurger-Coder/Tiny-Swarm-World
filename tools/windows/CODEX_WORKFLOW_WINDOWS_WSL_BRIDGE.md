# Codex Workflow: Windows <-> WSL Missing Link Pre-Installation Mechanism

## Context

Tiny Swarm World runs under WSL, but Windows must be able to access services through a browser before and after installation. WSL is treated as the guest system. Windows must explicitly bridge traffic to the current WSL IP.

The missing link must be implemented under:

```text
tools/windows
```

## Goal

Create a Windows-side pre-installation mechanism that prepares and refreshes the network bridge between Windows and WSL before `./install.sh` is allowed to run.

## Required files

```text
tools/windows/
  tws-wsl-bridge.ps1
  tws-wsl-bridge.config.json
  README.windows-wsl-bridge.md
  optional/
    tws_dns_resolver.py
```

## Functional requirements

### 1. Admin boundary

The PowerShell bridge script must fail fast unless it runs elevated for actions that mutate Windows state:

- install
- refresh
- uninstall

The verify/status actions may run non-elevated where possible.

### 2. WSL IP detection

The script must read the current WSL IP with:

```powershell
wsl.exe hostname -I
```

or with an explicit distro:

```powershell
wsl.exe -d <distro> -e hostname -I
```

The distro must be configurable.

### 3. Portproxy reconciliation

The script must delete and recreate Tiny Swarm managed TCP portproxy rules using the current WSL IP.

Required default ports are every TCP entry with an `external_port` in:

```text
infra/config/ports.yaml
```

Each port maps listenPort -> connectPort unless explicitly configured otherwise.

### 4. Firewall reconciliation

The script must create Windows Firewall inbound allow rules for each configured listen port.

Firewall rules must be identifiable and removable by a Tiny Swarm prefix.

### 5. Hostname reconciliation

The script must add a managed block to the Windows hosts file:

```text
# >>> Tiny Swarm World WSL Bridge >>>
127.0.0.1 tws.local gateway.tws.local service-access.tws.local ...
# <<< Tiny Swarm World WSL Bridge <<<
```

It must preserve all unrelated hosts-file entries.

### 6. Scheduled Task

The install action must register a Scheduled Task named:

```text
TinySwarmWorld-WslBridge
```

The task must run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/windows/tws-wsl-bridge.ps1 -Action refresh
```

It must run with highest privileges and be triggerable manually.

### 7. Installer integration

Before live infrastructure installation, `install.sh` must verify that the Windows bridge has either:

- a recent `.tws-wsl-bridge.state.json`, or
- the platform is not WSL, or
- Windows exposure was explicitly disabled.

If WSL is detected and Windows exposure is required, the installer must stop before mutating platform state with a precise message:

```text
Windows <-> WSL bridge is not prepared.
Run PowerShell as Administrator:
  tools/windows/tws-wsl-bridge.ps1 -Action install
```

### 8. Verification layering

The installer must distinguish:

- deployment readiness
- WSL host exposure readiness
- Windows exposure readiness

A Windows exposure failure must not be reported as a Docker Swarm deployment failure.

## Acceptance criteria

1. Running the bridge once as Administrator creates:
   - portproxy rules
   - firewall rules
   - hosts-file managed block
   - scheduled task
   - `.tws-wsl-bridge.state.json`

2. Running the bridge repeatedly is idempotent.

3. `uninstall` removes only Tiny Swarm managed entries.

4. After WSL IP changes, `Start-ScheduledTask -TaskName TinySwarmWorld-WslBridge` refreshes the portproxy connect address.

5. Tiny Swarm installation fails early if WSL is used and the bridge is missing.

6. Tiny Swarm installation does not fail deployment verification merely because Windows exposure is broken.

7. No hard-coded Windows port list is maintained outside `infra/config/ports.yaml`.

## Evidence required

Codex must provide evidence files or command output for:

```powershell
netsh interface portproxy show v4tov4
Get-NetFirewallRule | Where-Object DisplayName -like "Tiny Swarm World TCP *"
Get-Content C:\Windows\System32\drivers\etc\hosts
Get-ScheduledTask -TaskName TinySwarmWorld-WslBridge
```

and from WSL:

```bash
powershell.exe -NoProfile -Command "Start-ScheduledTask -TaskName TinySwarmWorld-WslBridge"
```
