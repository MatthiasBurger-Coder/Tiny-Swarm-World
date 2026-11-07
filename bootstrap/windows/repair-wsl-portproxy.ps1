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

foreach ($port in $ports) {
    $ruleName = "Tiny-Swarm-World WSL Bridge $port"

    netsh interface portproxy delete v4tov4 `
        listenaddress=127.0.0.1 `
        listenport=$port 2>$null | Out-Null

    netsh interface portproxy add v4tov4 `
        listenaddress=127.0.0.1 `
        listenport=$port `
        connectaddress=$wslIp `
        connectport=$port | Out-Null

    $existing = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue

    if (-not $existing) {
        New-NetFirewallRule `
            -DisplayName $ruleName `
            -Direction Inbound `
            -Action Allow `
            -Protocol TCP `
            -LocalAddress 127.0.0.1 `
            -LocalPort $port `
            -Profile Private | Out-Null
    }
}

$entries = Get-PortProxyEntries
$rows = foreach ($port in $ports) {
    $entry = $entries | Where-Object {
        $_.ListenAddress -eq "127.0.0.1" -and
        $_.ListenPort -eq $port -and
        $_.ConnectAddress -eq $wslIp -and
        $_.ConnectPort -eq $port
    } | Select-Object -First 1
    $firewall = Get-NetFirewallRule `
        -DisplayName "Tiny-Swarm-World WSL Bridge $port" `
        -ErrorAction SilentlyContinue

    [PSCustomObject]@{
        Port = $port
        WslIp = $wslIp
        Portproxy = if ($entry) { "OK" } else { "FAILED" }
        Firewall = if ($firewall) { "OK" } else { "MISSING" }
    }
}

Write-Host "Configured Tiny-Swarm-World Windows -> WSL bridge"
Write-Host "WSL IP: $wslIp"
$rows | Format-Table -AutoSize
netsh interface portproxy show v4tov4
