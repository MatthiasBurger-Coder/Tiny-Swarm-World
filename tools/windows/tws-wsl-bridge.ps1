#requires -Version 5.1
<#
.SYNOPSIS
  Tiny Swarm World Windows <-> WSL bridge.

.DESCRIPTION
  Prepares the Windows side before a Tiny Swarm World installation in WSL.
  It reconciles:
    - Windows portproxy rules -> current WSL IP
    - Windows Firewall inbound rules
    - Windows hosts-file entries for known tws.local names
    - Optional Scheduled Task for refresh after logon / WSL IP changes

  Run from an elevated PowerShell once:
    .\tools\windows\tws-wsl-bridge.ps1 -Action install

  Refresh later:
    Start-ScheduledTask -TaskName TinySwarmWorld-WslBridge
#>

[CmdletBinding()]
param(
    [ValidateSet("install", "refresh", "verify", "status", "uninstall")]
    [string]$Action = "refresh",

    [string]$ConfigPath = (Join-Path $PSScriptRoot "tws-wsl-bridge.config.json"),

    [string]$TaskName = "TinySwarmWorld-WslBridge",

    [int]$ConnectTimeoutMs = 1500
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$HostsPath = Join-Path $env:windir "System32\drivers\etc\hosts"
$HostsStart = "# >>> Tiny Swarm World WSL Bridge >>>"
$HostsEnd = "# <<< Tiny Swarm World WSL Bridge <<<"
$StatePath = Join-Path $PSScriptRoot ".tws-wsl-bridge.state.json"

function Get-TswRepositoryRoot {
    return (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")).Path
}

function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Assert-Administrator {
    if (-not (Test-IsAdministrator)) {
        throw "This action needs an elevated PowerShell. Start PowerShell as Administrator and run the command again."
    }
}

function Read-BridgeConfig {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Config file not found: $Path"
    }

    return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
}

function Convert-ToArray {
    param($Value)
    if ($null -eq $Value) { return @() }
    if ($Value -is [System.Array]) { return @($Value) }
    return @($Value)
}

function Get-WslIp {
    param($Config)

    $distro = ""
    if ($Config.PSObject.Properties.Name -contains "distro") {
        $distro = [string]$Config.distro
    }

    if ([string]::IsNullOrWhiteSpace($distro) -or $distro -eq "auto") {
        $raw = & wsl.exe hostname -I 2>$null
    } else {
        $raw = & wsl.exe -d $distro -e hostname -I 2>$null
    }

    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace(($raw -join " "))) {
        throw "Could not determine WSL IP. Check that WSL is installed and the configured distro is running. Configured distro: '$distro'"
    }

    $ip = (($raw -join " ").Trim().Split(" ", [System.StringSplitOptions]::RemoveEmptyEntries))[0]

    if ($ip -notmatch '^\d{1,3}(\.\d{1,3}){3}$') {
        throw "Invalid WSL IPv4 address returned by WSL: '$ip'"
    }

    return $ip
}

function Get-ListenAddress {
    param($Config)
    if ($Config.PSObject.Properties.Name -contains "listenAddress" -and -not [string]::IsNullOrWhiteSpace([string]$Config.listenAddress)) {
        return [string]$Config.listenAddress
    }
    return "0.0.0.0"
}

function Get-HostsAddress {
    param($Config)
    if ($Config.PSObject.Properties.Name -contains "hostsAddress" -and -not [string]::IsNullOrWhiteSpace([string]$Config.hostsAddress)) {
        return [string]$Config.hostsAddress
    }
    return "127.0.0.1"
}

function Get-FirewallRulePrefix {
    param($Config)
    if ($Config.PSObject.Properties.Name -contains "firewallRulePrefix" -and -not [string]::IsNullOrWhiteSpace([string]$Config.firewallRulePrefix)) {
        return [string]$Config.firewallRulePrefix
    }
    return "Tiny Swarm World"
}

function Add-TswRegistryPortMapping {
    param(
        [System.Collections.ArrayList] $Mappings,
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

    $port = [int] $Entry["external_port"]
    $name = "port-$port"
    if ($Entry.ContainsKey("id") -and -not [string]::IsNullOrWhiteSpace([string] $Entry["id"])) {
        $name = [string] $Entry["id"]
    }

    [void] $Mappings.Add([pscustomobject]@{
        Name        = $name
        ListenPort  = $port
        ConnectPort = $port
    })
}

function Add-TswRegistryHostName {
    param(
        [System.Collections.ArrayList] $HostNames,
        [hashtable] $Entry
    )

    if (-not $Entry.ContainsKey("route_host")) {
        return
    }

    $hostName = [string] $Entry["route_host"]
    if (-not [string]::IsNullOrWhiteSpace($hostName)) {
        [void] $HostNames.Add($hostName)
    }
}

function Read-TswPortRegistry {
    param([string] $RegistryPath)

    $mappings = [System.Collections.ArrayList]::new()
    $hostNames = [System.Collections.ArrayList]::new()
    if (-not (Test-Path -LiteralPath $RegistryPath)) {
        return [pscustomobject]@{ Mappings = @(); HostNames = @() }
    }

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
                Add-TswRegistryPortMapping -Mappings $mappings -Entry $current
                Add-TswRegistryHostName -HostNames $hostNames -Entry $current
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
        if ($line -match "^\s+route_host:\s*(\S+)\s*$") {
            $current["route_host"] = $Matches[1].Trim().Trim('"').Trim("'")
            continue
        }
    }

    if ($null -ne $current) {
        Add-TswRegistryPortMapping -Mappings $mappings -Entry $current
        Add-TswRegistryHostName -HostNames $hostNames -Entry $current
    }

    return [pscustomobject]@{
        Mappings = @($mappings | Sort-Object ListenPort -Unique)
        HostNames = @($hostNames | Sort-Object -Unique)
    }
}

function Get-ConfigPortMappings {
    param($Config)

    $result = @()
    $propertyNames = $Config.PSObject.Properties.Name
    $mappingProperties = @("additionalPortMappings", "portMappings")

    foreach ($propertyName in $mappingProperties) {
        if (-not ($propertyNames -contains $propertyName)) {
            continue
        }
        foreach ($m in (Convert-ToArray $Config.$propertyName)) {
            $name = "port-$($m.listenPort)"
            if ($m.PSObject.Properties.Name -contains "name" -and -not [string]::IsNullOrWhiteSpace([string]$m.name)) {
                $name = [string]$m.name
            }

            $result += [pscustomobject]@{
                Name        = $name
                ListenPort  = [int]$m.listenPort
                ConnectPort = [int]$m.connectPort
            }
        }
    }

    if ($propertyNames -contains "ports") {
        foreach ($p in (Convert-ToArray $Config.ports)) {
            $port = [int]$p
            $result += [pscustomobject]@{
                Name        = "port-$port"
                ListenPort  = $port
                ConnectPort = $port
            }
        }
    }

    return $result
}

function Get-PortMappings {
    param(
        $Config,
        $RegistryMappings
    )

    $result = @()
    $seenPorts = [System.Collections.Generic.HashSet[int]]::new()

    foreach ($m in (Convert-ToArray $RegistryMappings)) {
        if ($seenPorts.Add([int] $m.ListenPort)) {
            $result += $m
        }
    }

    foreach ($m in (Get-ConfigPortMappings $Config)) {
        if ($seenPorts.Add([int] $m.ListenPort)) {
            $result += $m
        }
    }

    if ($result.Count -eq 0) {
        throw "No ports configured. Add external TCP ports to infra\config\ports.yaml or provide additionalPortMappings in $ConfigPath."
    }

    return $result | Sort-Object ListenPort -Unique
}

function Remove-PortProxy {
    param(
        [string]$ListenAddress,
        [int]$ListenPort
    )

    $null = & netsh interface portproxy delete v4tov4 "listenaddress=$ListenAddress" "listenport=$ListenPort" protocol=tcp 2>$null
}

function Add-PortProxy {
    param(
        [string]$ListenAddress,
        [int]$ListenPort,
        [string]$ConnectAddress,
        [int]$ConnectPort
    )

    $output = & netsh interface portproxy add v4tov4 "listenaddress=$ListenAddress" "listenport=$ListenPort" "connectaddress=$ConnectAddress" "connectport=$ConnectPort" protocol=tcp 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to add portproxy $ListenAddress`:$ListenPort -> $ConnectAddress`:$ConnectPort. Output: $($output -join ' ')"
    }
}

function Reconcile-PortProxy {
    param(
        $Config,
        [string]$WslIp,
        $Mappings
    )

    $listenAddress = Get-ListenAddress $Config

    foreach ($m in $Mappings) {
        Remove-PortProxy -ListenAddress $listenAddress -ListenPort $m.ListenPort
        Add-PortProxy -ListenAddress $listenAddress -ListenPort $m.ListenPort -ConnectAddress $WslIp -ConnectPort $m.ConnectPort
        Write-Host ("PORTPROXY {0}:{1} -> {2}:{3} ({4})" -f $listenAddress, $m.ListenPort, $WslIp, $m.ConnectPort, $m.Name)
    }
}

function Reconcile-FirewallRules {
    param(
        $Config,
        $Mappings
    )

    $prefix = Get-FirewallRulePrefix $Config

    Get-NetFirewallRule -ErrorAction SilentlyContinue |
        Where-Object { $_.DisplayName -like "$prefix TCP *" } |
        Remove-NetFirewallRule -ErrorAction SilentlyContinue

    foreach ($port in (($Mappings | Select-Object -ExpandProperty ListenPort) | Sort-Object -Unique)) {
        $ruleName = "$prefix TCP $port"
        New-NetFirewallRule `
            -DisplayName $ruleName `
            -Direction Inbound `
            -Action Allow `
            -Protocol TCP `
            -LocalPort $port `
            -Profile Any | Out-Null

        Write-Host ("FIREWALL allow TCP {0}" -f $port)
    }
}

function Remove-ManagedHostsBlock {
    if (-not (Test-Path -LiteralPath $HostsPath)) {
        return ""
    }

    $content = Get-Content -LiteralPath $HostsPath -Raw -ErrorAction Stop
    $startEsc = [regex]::Escape($HostsStart)
    $endEsc = [regex]::Escape($HostsEnd)
    $pattern = "(?ms)^[ \t]*$startEsc.*?^[ \t]*$endEsc[ \t]*(\r?\n)?"
    return [regex]::Replace($content, $pattern, "")
}

function Get-BridgeHostNames {
    param(
        $Config,
        $RegistryHostNames
    )

    $hostNames = @()
    if (-not ($Config.PSObject.Properties.Name -contains "hostNames")) {
        $hostNames = @()
    } else {
        $hostNames = @(Convert-ToArray $Config.hostNames | ForEach-Object { [string]$_ })
    }

    $hostNames += @(Convert-ToArray $RegistryHostNames | ForEach-Object { [string]$_ })
    return @($hostNames | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Sort-Object -Unique)
}

function Reconcile-HostsFile {
    param(
        $Config,
        $HostNames
    )

    $hostNames = @(Convert-ToArray $HostNames)
    if ($hostNames.Count -eq 0) {
        return
    }

    $hostsAddress = Get-HostsAddress $Config
    $content = Remove-ManagedHostsBlock

    $block = @()
    $block += $HostsStart

    $line = "$hostsAddress`t$($hostNames -join ' ')"
    $block += $line

    $block += $HostsEnd

    $newContent = $content.TrimEnd() + [Environment]::NewLine + ($block -join [Environment]::NewLine) + [Environment]::NewLine

    Set-Content -LiteralPath $HostsPath -Value $newContent -Encoding ASCII -Force
    Write-Host ("HOSTS {0} -> {1}" -f ($hostNames -join ", "), $hostsAddress)
}

function Remove-HostsFileBlock {
    $content = Remove-ManagedHostsBlock
    Set-Content -LiteralPath $HostsPath -Value ($content.TrimEnd() + [Environment]::NewLine) -Encoding ASCII -Force
    Write-Host "HOSTS managed Tiny Swarm block removed"
}

function Register-BridgeTask {
    param([string]$ResolvedConfigPath)

    $scriptPath = $PSCommandPath
    $arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`" -Action refresh -ConfigPath `"$ResolvedConfigPath`""

    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arguments
    $trigger = New-ScheduledTaskTrigger -AtLogOn
    $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew

    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Principal $principal `
        -Settings $settings `
        -Description "Refresh Tiny Swarm World Windows <-> WSL bridge after WSL IP changes." `
        -Force | Out-Null

    Write-Host "TASK registered: $TaskName"
}

function Unregister-BridgeTask {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($null -ne $task) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "TASK removed: $TaskName"
    }
}

function Remove-BridgeFirewallRules {
    param($Config)

    $prefix = Get-FirewallRulePrefix $Config

    Get-NetFirewallRule -ErrorAction SilentlyContinue |
        Where-Object { $_.DisplayName -like "$prefix TCP *" } |
        Remove-NetFirewallRule -ErrorAction SilentlyContinue

    Write-Host "FIREWALL managed Tiny Swarm rules removed"
}

function Remove-BridgePortProxy {
    param(
        $Config,
        $Mappings
    )

    $listenAddress = Get-ListenAddress $Config
    foreach ($m in $Mappings) {
        Remove-PortProxy -ListenAddress $listenAddress -ListenPort $m.ListenPort
        Write-Host ("PORTPROXY removed {0}:{1}" -f $listenAddress, $m.ListenPort)
    }
}

function Test-TcpPort {
    param(
        [string]$HostName,
        [int]$Port,
        [int]$TimeoutMs
    )

    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $async = $client.BeginConnect($HostName, $Port, $null, $null)
        $ok = $async.AsyncWaitHandle.WaitOne($TimeoutMs, $false)
        if ($ok) {
            $client.EndConnect($async)
            return $true
        }
        return $false
    } catch {
        return $false
    } finally {
        $client.Close()
    }
}

function Verify-Bridge {
    param(
        $Config,
        $Mappings
    )

    $failed = @()

    foreach ($m in $Mappings) {
        $ok = Test-TcpPort -HostName "127.0.0.1" -Port $m.ListenPort -TimeoutMs $ConnectTimeoutMs
        if ($ok) {
            Write-Host ("VERIFY OK   127.0.0.1:{0} ({1})" -f $m.ListenPort, $m.Name)
        } else {
            Write-Host ("VERIFY FAIL 127.0.0.1:{0} ({1})" -f $m.ListenPort, $m.Name) -ForegroundColor Yellow
            $failed += $m
        }
    }

    if ($failed.Count -gt 0) {
        throw "Windows bridge verification failed for $($failed.Count) port(s). This can also mean the Tiny Swarm services are not running yet."
    }
}

function Write-StateFile {
    param(
        $Config,
        [string]$WslIp,
        $Mappings,
        $HostNames,
        [string]$RegistryPath
    )

    $state = [ordered]@{
        generatedAt        = (Get-Date).ToString("o")
        action             = $Action
        wslIp              = $WslIp
        listenAddress      = (Get-ListenAddress $Config)
        hostsAddress       = (Get-HostsAddress $Config)
        configPath         = (Resolve-Path -LiteralPath $ConfigPath).Path
        registryPath       = $RegistryPath
        hostNames          = @($HostNames)
        mappings           = @($Mappings | ForEach-Object {
            [ordered]@{
                name        = $_.Name
                listenPort  = $_.ListenPort
                connectPort = $_.ConnectPort
            }
        })
    }

    $state | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $StatePath -Encoding UTF8
    Write-Host "STATE written: $StatePath"
}

function Show-Status {
    param(
        $Config,
        $Mappings,
        $HostNames
    )

    Write-Host "Tiny Swarm World Windows <-> WSL bridge status"
    Write-Host ("Config: {0}" -f (Resolve-Path -LiteralPath $ConfigPath).Path)
    Write-Host ("Ports: {0}" -f (($Mappings | Select-Object -ExpandProperty ListenPort) -join ", "))
    Write-Host ("Hosts: {0}" -f ($HostNames -join ", "))

    try {
        $wslIp = Get-WslIp $Config
        Write-Host ("WSL IP: {0}" -f $wslIp)
    } catch {
        Write-Host ("WSL IP: unavailable - {0}" -f $_.Exception.Message) -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "Portproxy:"
    & netsh interface portproxy show v4tov4

    Write-Host ""
    Write-Host "Scheduled task:"
    Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue | Format-List TaskName, State, TaskPath

    Write-Host ""
    Write-Host "Managed hosts block present:"
    if ((Test-Path -LiteralPath $HostsPath) -and ((Get-Content -LiteralPath $HostsPath -Raw) -like "*$HostsStart*")) {
        Write-Host "yes"
    } else {
        Write-Host "no"
    }
}

$config = Read-BridgeConfig -Path $ConfigPath
$registryPath = Join-Path (Get-TswRepositoryRoot) "infra\config\ports.yaml"
$registry = Read-TswPortRegistry -RegistryPath $registryPath
$mappings = @(Get-PortMappings $config $registry.Mappings)
$hostNames = @(Get-BridgeHostNames $config $registry.HostNames)

switch ($Action) {
    "install" {
        Assert-Administrator
        $resolvedConfig = (Resolve-Path -LiteralPath $ConfigPath).Path
        $wslIp = Get-WslIp $config
        Reconcile-PortProxy -Config $config -WslIp $wslIp -Mappings $mappings
        Reconcile-FirewallRules -Config $config -Mappings $mappings
        Reconcile-HostsFile -Config $config -HostNames $hostNames
        Register-BridgeTask -ResolvedConfigPath $resolvedConfig
        Write-StateFile -Config $config -WslIp $wslIp -Mappings $mappings -HostNames $hostNames -RegistryPath $registryPath
        Write-Host ""
        Write-Host "Installed. You can refresh later with:"
        Write-Host "  Start-ScheduledTask -TaskName $TaskName"
    }

    "refresh" {
        Assert-Administrator
        $wslIp = Get-WslIp $config
        Reconcile-PortProxy -Config $config -WslIp $wslIp -Mappings $mappings
        Reconcile-FirewallRules -Config $config -Mappings $mappings
        Reconcile-HostsFile -Config $config -HostNames $hostNames
        Write-StateFile -Config $config -WslIp $wslIp -Mappings $mappings -HostNames $hostNames -RegistryPath $registryPath
        Write-Host "Refresh completed."
    }

    "verify" {
        Verify-Bridge -Config $config -Mappings $mappings
    }

    "status" {
        Show-Status -Config $config -Mappings $mappings -HostNames $hostNames
    }

    "uninstall" {
        Assert-Administrator
        Remove-BridgePortProxy -Config $config -Mappings $mappings
        Remove-BridgeFirewallRules -Config $config
        Remove-HostsFileBlock
        Unregister-BridgeTask
        if (Test-Path -LiteralPath $StatePath) {
            Remove-Item -LiteralPath $StatePath -Force
        }
        Write-Host "Uninstalled."
    }
}
