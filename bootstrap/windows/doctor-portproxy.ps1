#Requires -RunAsAdministrator

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

function Get-TswRepositoryRoot {
    return (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")).Path
}

function Add-TswPortEntry {
    param(
        [System.Collections.ArrayList] $Ports,
        [hashtable] $Entry
    )

    if (-not $Entry.ContainsKey("external_port")) {
        return
    }

    $protocol = "tcp"
    if ($Entry.ContainsKey("protocol")) {
        $protocol = [string] $Entry["protocol"]
    }

    if ($protocol.ToLowerInvariant() -ne "tcp") {
        return
    }

    if ($Entry.ContainsKey("exposure") -and [string] $Entry["exposure"] -eq "public_ingress") {
        return
    }

    [void] $Ports.Add([int] $Entry["external_port"])
}

function Get-TswBridgePorts {
    param([string] $RegistryPath)

    $ports = [System.Collections.ArrayList]::new()
    $inPorts = $false
    $current = $null

    foreach ($line in Get-Content -LiteralPath $RegistryPath) {
        if ($line -match "^ports:\s*$") {
            $inPorts = $true
            continue
        }
        if (-not $inPorts) {
            continue
        }
        if ($line -match "^\S" -and $line -notmatch "^ports:\s*$") {
            break
        }
        if ($line -match "^\s*-\s+id:\s*(.+?)\s*$") {
            if ($null -ne $current) {
                Add-TswPortEntry -Ports $ports -Entry $current
            }
            $current = @{ id = $Matches[1].Trim().Trim('"').Trim("'") }
            continue
        }
        if ($null -eq $current) {
            continue
        }
        if ($line -match "^\s+external_port:\s*(\d+)\s*$") {
            $current["external_port"] = [int] $Matches[1]
            continue
        }
        if ($line -match "^\s+protocol:\s*(\S+)\s*$") {
            $current["protocol"] = $Matches[1].Trim().Trim('"').Trim("'")
            continue
        }
        if ($line -match "^\s+exposure:\s*(\S+)\s*$") {
            $current["exposure"] = $Matches[1].Trim().Trim('"').Trim("'")
            continue
        }
    }

    if ($null -ne $current) {
        Add-TswPortEntry -Ports $ports -Entry $current
    }

    return @($ports | Select-Object -Unique)
}

function Get-WslEth0IPv4 {
    $line = (wsl.exe bash -lc "ip -4 -o addr show dev eth0 scope global")
    $match = [regex]::Match($line, "inet\s+(\d+\.\d+\.\d+\.\d+)/")

    if (-not $match.Success) {
        throw "Could not determine WSL eth0 IPv4 from: $line"
    }

    return $match.Groups[1].Value
}

function Get-PortProxyEntries {
    $raw = netsh interface portproxy show v4tov4 | Out-String
    $entries = @()
    foreach ($line in $raw -split "`r?`n") {
        $match = [regex]::Match(
            $line,
            "^\s*(\d+\.\d+\.\d+\.\d+)\s+(\d+)\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+)\s*$"
        )
        if ($match.Success) {
            $entries += [PSCustomObject]@{
                ListenAddress = $match.Groups[1].Value
                ListenPort = [int] $match.Groups[2].Value
                ConnectAddress = $match.Groups[3].Value
                ConnectPort = [int] $match.Groups[4].Value
            }
        }
    }
    return $entries
}

$repoRoot = Get-TswRepositoryRoot
$registryPath = Join-Path $repoRoot "infra\config\ports.yaml"
$wslIp = Get-WslEth0IPv4
$ports = Get-TswBridgePorts -RegistryPath $registryPath
$portproxyEntries = Get-PortProxyEntries
$listeners = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue

$rows = foreach ($port in $ports) {
    $ruleName = "Tiny-Swarm-World WSL Bridge $port"
    $entry = $portproxyEntries | Where-Object {
        $_.ListenAddress -eq "127.0.0.1" -and $_.ListenPort -eq $port
    } | Select-Object -First 1
    $listener = $listeners | Where-Object {
        $_.LocalAddress -in @("127.0.0.1", "0.0.0.0", "::") -and $_.LocalPort -eq $port
    } | Select-Object -First 1
    $firewall = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue

    $diagnoses = [System.Collections.Generic.List[string]]::new()
    if (-not $entry) {
        $diagnoses.Add("WINDOWS_PORTPROXY_MISSING")
    }
    elseif ($entry.ConnectAddress -ne $wslIp) {
        $diagnoses.Add("WINDOWS_PORTPROXY_STALE_WSL_IP")
    }
    if ($listener -and -not $entry) {
        $diagnoses.Add("WINDOWS_PORT_OCCUPIED")
    }
    if (-not $firewall) {
        $diagnoses.Add("WINDOWS_FIREWALL_RULE_MISSING")
    }
    if ($diagnoses.Count -eq 0) {
        $diagnoses.Add("WINDOWS_PORTPROXY_OK")
    }

    [PSCustomObject]@{
        Port = $port
        WslIp = $wslIp
        ConnectAddress = if ($entry) { $entry.ConnectAddress } else { "" }
        Listener = if ($listener) { "yes" } else { "no" }
        Firewall = if ($firewall) { "yes" } else { "no" }
        Diagnosis = ($diagnoses -join ",")
    }
}

Write-Host "[Windows Portproxy]"
Write-Host "Registry: $registryPath"
Write-Host "WSL IP: $wslIp"
$rows | Format-Table -AutoSize
Write-Host ""
Write-Host "Raw v4tov4 rules:"
netsh interface portproxy show all
