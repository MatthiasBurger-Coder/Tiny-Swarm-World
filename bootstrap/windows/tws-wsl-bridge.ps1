#requires -Version 5.1
<#
.SYNOPSIS
  Tiny Swarm World Windows <-> WSL bridge.

.DESCRIPTION
  Prepares the Windows side before a Tiny Swarm World installation in WSL.
  It reconciles:
    - Windows portproxy rules -> current WSL IP
    - Windows Firewall inbound rules
    - Windows hosts-file entries for known tsw.local names
    - Automatic Windows discovery/reconcile service at a fixed interval

  Check Windows and WSL prerequisites without changing state:
    .\bootstrap\windows\tws-wsl-bridge.ps1 -Action prerequisites

  Run from an elevated PowerShell once:
    .\bootstrap\windows\tws-wsl-bridge.ps1 -Action install

  Trigger discovery/reconcile manually:
    Restart-Service -Name TinySwarmWorldWslBridge
#>

[CmdletBinding()]
param(
    [ValidateSet("prerequisites", "inventory", "discover", "install", "reconcile", "refresh", "verify", "status", "uninstall")]
    [string]$Action = "refresh",

    [string]$ConfigPath = "",

    [string]$TaskName = "TinySwarmWorld-WslBridge",

    [string]$PortRegistryPath = "",

    [string]$Distro = "",

    [string]$ObservedAddress = "",

    [int]$ConnectTimeoutMs = 1500
)
# Compatibility entry point; implementation and registration belong to the module.
$tswImplementationPath=Join-Path $PSScriptRoot "../../modules/tsw_windows_wsl/bootstrap/windows/tws-wsl-bridge.ps1"
if($MyInvocation.InvocationName -eq '.') {
    . $tswImplementationPath @PSBoundParameters
} else {
    $ErrorActionPreference='Stop'
    $global:LASTEXITCODE=0
    & $tswImplementationPath @PSBoundParameters
}
