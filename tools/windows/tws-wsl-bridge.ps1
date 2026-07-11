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
    - Scheduled discovery/reconcile task after logon and at a fixed interval

  Check Windows and WSL prerequisites without changing state:
    .\tools\windows\tws-wsl-bridge.ps1 -Action prerequisites

  Run from an elevated PowerShell once:
    .\tools\windows\tws-wsl-bridge.ps1 -Action install

  Trigger discovery/reconcile manually:
    Start-ScheduledTask -TaskName TinySwarmWorld-WslBridge
#>

[CmdletBinding()]
param(
    [ValidateSet("prerequisites", "discover", "install", "reconcile", "refresh", "verify", "status", "uninstall")]
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

function Get-ConfiguredDistro {
    param($Config)

    if ($Config.PSObject.Properties.Name -contains "distro") {
        return [string]$Config.distro
    }
    return "auto"
}

function Invoke-WslShellText {
    param(
        $Config,
        [string]$Command
    )

    $distro = Get-ConfiguredDistro $Config
    if ([string]::IsNullOrWhiteSpace($distro) -or $distro -eq "auto") {
        $raw = & wsl.exe sh -lc $Command 2>$null
    } else {
        $raw = & wsl.exe -d $distro -e sh -lc $Command 2>$null
    }

    if ($LASTEXITCODE -ne 0) {
        throw "WSL command failed for configured distro '$distro': $Command"
    }

    return ($raw -join "`n").Trim()
}

function New-BridgePrerequisiteResult {
    param(
        [string]$Name,
        [bool]$Passed,
        [string]$Message
    )

    return [pscustomobject]@{
        Name    = $Name
        Passed  = $Passed
        Message = $Message
    }
}

function Get-BridgePrerequisiteResults {
    param($Config)

    $results = [System.Collections.ArrayList]::new()
    $windowsDetected = [Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT
    [void]$results.Add((New-BridgePrerequisiteResult `
        -Name "windows" `
        -Passed $windowsDetected `
        -Message $(if ($windowsDetected) { "Windows host detected." } else { "Run this script from Windows PowerShell." })))

    $isAdministrator = Test-IsAdministrator
    [void]$results.Add((New-BridgePrerequisiteResult `
        -Name "administrator" `
        -Passed $isAdministrator `
        -Message $(if ($isAdministrator) { "PowerShell is elevated." } else { "Open PowerShell as Administrator." })))

    $wslAvailable = $null -ne (Get-Command wsl.exe -ErrorAction SilentlyContinue)
    [void]$results.Add((New-BridgePrerequisiteResult `
        -Name "wsl-command" `
        -Passed $wslAvailable `
        -Message $(if ($wslAvailable) { "wsl.exe is available." } else { "Install WSL 2 before preparing the bridge." })))

    $netshAvailable = $null -ne (Get-Command netsh.exe -ErrorAction SilentlyContinue)
    [void]$results.Add((New-BridgePrerequisiteResult `
        -Name "netsh-command" `
        -Passed $netshAvailable `
        -Message $(if ($netshAvailable) { "netsh.exe is available." } else { "netsh.exe is required for Windows portproxy rules." })))

    $firewallAvailable = $null -ne (Get-Command New-NetFirewallRule -ErrorAction SilentlyContinue)
    [void]$results.Add((New-BridgePrerequisiteResult `
        -Name "firewall-cmdlet" `
        -Passed $firewallAvailable `
        -Message $(if ($firewallAvailable) { "Windows Firewall cmdlets are available." } else { "New-NetFirewallRule is unavailable." })))

    $taskAvailable = $null -ne (Get-Command Register-ScheduledTask -ErrorAction SilentlyContinue)
    [void]$results.Add((New-BridgePrerequisiteResult `
        -Name "task-cmdlet" `
        -Passed $taskAvailable `
        -Message $(if ($taskAvailable) { "Scheduled Task cmdlets are available." } else { "Register-ScheduledTask is unavailable." })))

    $ipHelper = Get-Service -Name iphlpsvc -ErrorAction SilentlyContinue
    $ipHelperRunning = $null -ne $ipHelper -and $ipHelper.Status -eq "Running"
    [void]$results.Add((New-BridgePrerequisiteResult `
        -Name "ip-helper" `
        -Passed $ipHelperRunning `
        -Message $(if ($ipHelperRunning) { "IP Helper is running." } else { "Start the Windows IP Helper service (iphlpsvc)." })))

    if ($wslAvailable) {
        try {
            $kernelRelease = Invoke-WslShellText -Config $Config -Command "uname -r"
            $isWsl2 = $kernelRelease -match "(?i)(microsoft-standard-wsl2|wsl2)"
            [void]$results.Add((New-BridgePrerequisiteResult `
                -Name "wsl2-runtime" `
                -Passed $isWsl2 `
                -Message $(if ($isWsl2) { "Configured distro is running under WSL 2." } else { "Configured distro is not running under WSL 2." })))
        } catch {
            [void]$results.Add((New-BridgePrerequisiteResult `
                -Name "wsl2-runtime" `
                -Passed $false `
                -Message $_.Exception.Message))
        }

        try {
            $pidOne = Invoke-WslShellText -Config $Config -Command "ps -p 1 -o comm="
            $systemdRunning = $pidOne.Trim() -eq "systemd"
            [void]$results.Add((New-BridgePrerequisiteResult `
                -Name "wsl-systemd" `
                -Passed $systemdRunning `
                -Message $(if ($systemdRunning) { "systemd is PID 1 in the configured distro." } else { "Enable systemd in the configured WSL distro." })))
        } catch {
            [void]$results.Add((New-BridgePrerequisiteResult `
                -Name "wsl-systemd" `
                -Passed $false `
                -Message $_.Exception.Message))
        }

        try {
            $wslIp = Get-WslIp $Config
            [void]$results.Add((New-BridgePrerequisiteResult `
                -Name "wsl-ipv4" `
                -Passed $true `
                -Message "Current WSL IPv4 address resolved: $wslIp"))
        } catch {
            [void]$results.Add((New-BridgePrerequisiteResult `
                -Name "wsl-ipv4" `
                -Passed $false `
                -Message $_.Exception.Message))
        }
    }

    return @($results)
}

function Write-BridgePrerequisiteResults {
    param($Results)

    foreach ($result in $Results) {
        $status = if ($result.Passed) { "OK" } else { "FAIL" }
        $color = if ($result.Passed) { "Green" } else { "Yellow" }
        Write-Host ("PREREQUISITE {0,-4} {1}: {2}" -f $status, $result.Name, $result.Message) -ForegroundColor $color
    }
}

function Assert-BridgePrerequisites {
    param($Config)

    $results = @(Get-BridgePrerequisiteResults -Config $Config)
    Write-BridgePrerequisiteResults -Results $results
    $failed = @($results | Where-Object { -not $_.Passed })
    if ($failed.Count -gt 0) {
        $failedNames = $failed.Name -join ", "
        throw "Windows/WSL bridge prerequisites failed: $failedNames"
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

function Get-DiscoveryIntervalMinutes {
    param($Config)

    $interval = 1
    if ($Config.PSObject.Properties.Name -contains "discoveryIntervalMinutes") {
        $interval = [int]$Config.discoveryIntervalMinutes
    }
    if ($interval -lt 1 -or $interval -gt 60) {
        throw "discoveryIntervalMinutes must be between 1 and 60."
    }
    return $interval
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

function Get-PortProxyRecords {
    $records = [System.Collections.ArrayList]::new()
    $output = & netsh interface portproxy show v4tov4 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to inspect Windows portproxy state."
    }

    foreach ($line in $output) {
        if ($line -match '^\s*(\d{1,3}(?:\.\d{1,3}){3})\s+(\d+)\s+(\d{1,3}(?:\.\d{1,3}){3})\s+(\d+)\s*$') {
            [void]$records.Add([pscustomobject]@{
                ListenAddress  = $Matches[1]
                ListenPort     = [int]$Matches[2]
                ConnectAddress = $Matches[3]
                ConnectPort    = [int]$Matches[4]
            })
        }
    }
    return @($records)
}

function Get-PreviousBridgeState {
    if (-not (Test-Path -LiteralPath $StatePath)) {
        return $null
    }
    try {
        return Get-Content -LiteralPath $StatePath -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        return $null
    }
}

function Remove-StalePortProxyMappings {
    param(
        $Config,
        $Mappings
    )

    $previous = Get-PreviousBridgeState
    if ($null -eq $previous -or -not ($previous.PSObject.Properties.Name -contains "mappings")) {
        return
    }

    $listenAddress = Get-ListenAddress $Config
    $previousListenAddress = $listenAddress
    if ($previous.PSObject.Properties.Name -contains "listenAddress" -and -not [string]::IsNullOrWhiteSpace([string]$previous.listenAddress)) {
        $previousListenAddress = [string]$previous.listenAddress
    }
    $desiredPorts = [System.Collections.Generic.HashSet[int]]::new()
    foreach ($mapping in $Mappings) {
        [void]$desiredPorts.Add([int]$mapping.ListenPort)
    }

    foreach ($mapping in (Convert-ToArray $previous.mappings)) {
        $port = [int]$mapping.listenPort
        if ($previousListenAddress -ne $listenAddress -or -not $desiredPorts.Contains($port)) {
            Remove-PortProxy -ListenAddress $previousListenAddress -ListenPort $port
            Write-Host ("PORTPROXY stale mapping removed {0}:{1}" -f $previousListenAddress, $port)
        }
    }
}

function Test-PortProxyMappingsReady {
    param(
        $Config,
        [string]$WslIp,
        $Mappings
    )

    $listenAddress = Get-ListenAddress $Config
    $records = @(Get-PortProxyRecords)
    foreach ($mapping in $Mappings) {
        $matches = @($records | Where-Object {
            $_.ListenAddress -eq $listenAddress -and
            $_.ListenPort -eq [int]$mapping.ListenPort -and
            $_.ConnectAddress -eq $WslIp -and
            $_.ConnectPort -eq [int]$mapping.ConnectPort
        })
        if ($matches.Count -ne 1) {
            return $false
        }
    }
    return $true
}

function Reconcile-PortProxy {
    param(
        $Config,
        [string]$WslIp,
        $Mappings
    )

    Remove-StalePortProxyMappings -Config $Config -Mappings $Mappings
    $listenAddress = Get-ListenAddress $Config
    $records = @(Get-PortProxyRecords)

    foreach ($m in $Mappings) {
        $matches = @($records | Where-Object {
            $_.ListenAddress -eq $listenAddress -and
            $_.ListenPort -eq [int]$m.ListenPort -and
            $_.ConnectAddress -eq $WslIp -and
            $_.ConnectPort -eq [int]$m.ConnectPort
        })
        if ($matches.Count -eq 1) {
            Write-Host ("PORTPROXY unchanged {0}:{1} -> {2}:{3} ({4})" -f $listenAddress, $m.ListenPort, $WslIp, $m.ConnectPort, $m.Name)
            continue
        }
        Remove-PortProxy -ListenAddress $listenAddress -ListenPort $m.ListenPort
        Add-PortProxy -ListenAddress $listenAddress -ListenPort $m.ListenPort -ConnectAddress $WslIp -ConnectPort $m.ConnectPort
        Write-Host ("PORTPROXY {0}:{1} -> {2}:{3} ({4})" -f $listenAddress, $m.ListenPort, $WslIp, $m.ConnectPort, $m.Name)
    }
}

function Test-FirewallRuleReady {
    param(
        $Config,
        [int]$Port
    )

    $prefix = Get-FirewallRulePrefix $Config
    $ruleName = "$prefix TCP $Port"
    $rules = @(Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -eq $ruleName })
    if ($rules.Count -ne 1) {
        return $false
    }
    $rule = $rules[0]
    if ($rule.Enabled.ToString() -ne "True" -or $rule.Direction.ToString() -ne "Inbound" -or $rule.Action.ToString() -ne "Allow") {
        return $false
    }
    $filters = @($rule | Get-NetFirewallPortFilter -ErrorAction SilentlyContinue)
    $matchingFilters = @($filters | Where-Object {
        $_.LocalPort.ToString() -eq $Port.ToString() -and
        $_.Protocol.ToString() -in @("TCP", "6")
    })
    return $matchingFilters.Count -eq 1
}

function Test-FirewallRulesReady {
    param(
        $Config,
        $Mappings
    )

    $prefix = Get-FirewallRulePrefix $Config
    $desiredPorts = @(($Mappings | Select-Object -ExpandProperty ListenPort) | Sort-Object -Unique)
    $managedRules = @(Get-NetFirewallRule -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -like "$prefix TCP *" })
    if ($managedRules.Count -ne $desiredPorts.Count) {
        return $false
    }
    foreach ($port in $desiredPorts) {
        if (-not (Test-FirewallRuleReady -Config $Config -Port $port)) {
            return $false
        }
    }
    return $true
}

function Reconcile-FirewallRules {
    param(
        $Config,
        $Mappings
    )

    $prefix = Get-FirewallRulePrefix $Config

    $desiredPorts = @(($Mappings | Select-Object -ExpandProperty ListenPort) | Sort-Object -Unique)
    $desiredNames = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($port in $desiredPorts) {
        [void]$desiredNames.Add("$prefix TCP $port")
    }

    Get-NetFirewallRule -ErrorAction SilentlyContinue |
        Where-Object { $_.DisplayName -like "$prefix TCP *" -and -not $desiredNames.Contains($_.DisplayName) } |
        Remove-NetFirewallRule -ErrorAction SilentlyContinue

    foreach ($port in $desiredPorts) {
        $ruleName = "$prefix TCP $port"
        if (Test-FirewallRuleReady -Config $Config -Port $port) {
            Write-Host ("FIREWALL unchanged TCP {0}" -f $port)
            continue
        }
        Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue |
            Where-Object { $_.DisplayName -eq $ruleName } |
            Remove-NetFirewallRule -ErrorAction SilentlyContinue
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

function Get-ReconciledHostsContent {
    param(
        $Config,
        $HostNames
    )

    $hostNames = @(Convert-ToArray $HostNames)
    $content = Remove-ManagedHostsBlock
    if ($hostNames.Count -eq 0) {
        return $content.TrimEnd() + [Environment]::NewLine
    }

    $hostsAddress = Get-HostsAddress $Config
    $block = @(
        $HostsStart,
        "$hostsAddress`t$($hostNames -join ' ')",
        $HostsEnd
    ) -join [Environment]::NewLine
    $base = $content.TrimEnd()
    if ([string]::IsNullOrWhiteSpace($base)) {
        return $block + [Environment]::NewLine
    }
    return $base + [Environment]::NewLine + $block + [Environment]::NewLine
}

function Test-HostsFileReady {
    param(
        $Config,
        $HostNames
    )

    if (-not (Test-Path -LiteralPath $HostsPath)) {
        return $false
    }
    $current = Get-Content -LiteralPath $HostsPath -Raw -ErrorAction Stop
    $desired = Get-ReconciledHostsContent -Config $Config -HostNames $HostNames
    return $current -eq $desired
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
    $newContent = Get-ReconciledHostsContent -Config $Config -HostNames $hostNames
    if ((Test-Path -LiteralPath $HostsPath) -and (Test-HostsFileReady -Config $Config -HostNames $hostNames)) {
        Write-Host ("HOSTS unchanged {0} -> {1}" -f ($hostNames -join ", "), $hostsAddress)
        return
    }

    [System.IO.File]::WriteAllText($HostsPath, $newContent, [System.Text.Encoding]::ASCII)
    Write-Host ("HOSTS {0} -> {1}" -f ($hostNames -join ", "), $hostsAddress)
}

function Remove-HostsFileBlock {
    $content = Remove-ManagedHostsBlock
    Set-Content -LiteralPath $HostsPath -Value ($content.TrimEnd() + [Environment]::NewLine) -Encoding ASCII -Force
    Write-Host "HOSTS managed Tiny Swarm block removed"
}

function Register-BridgeTask {
    param(
        [string]$ResolvedConfigPath,
        $Config
    )

    $scriptPath = $PSCommandPath
    $intervalMinutes = Get-DiscoveryIntervalMinutes $Config
    $arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`" -Action reconcile -ConfigPath `"$ResolvedConfigPath`""

    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arguments
    $logonTrigger = New-ScheduledTaskTrigger -AtLogOn
    $periodicTrigger = New-ScheduledTaskTrigger `
        -Once `
        -At (Get-Date).AddMinutes($intervalMinutes) `
        -RepetitionInterval (New-TimeSpan -Minutes $intervalMinutes) `
        -RepetitionDuration (New-TimeSpan -Days 3650)
    $triggers = @($logonTrigger, $periodicTrigger)
    $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -StartWhenAvailable `
        -MultipleInstances IgnoreNew `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 5)

    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $triggers `
        -Principal $principal `
        -Settings $settings `
        -Description "Discover and reconcile the Tiny Swarm World Windows <-> WSL bridge after logon and every $intervalMinutes minute(s)." `
        -Force | Out-Null

    Write-Host "TASK registered: $TaskName (logon + every $intervalMinutes minute(s))"
}

function Test-BridgeTaskReady {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($null -eq $task) {
        return $false
    }
    $arguments = @($task.Actions | ForEach-Object { [string]$_.Arguments }) -join " "
    $triggers = @($task.Triggers)
    return $arguments -match '(?i)-Action\s+reconcile' -and $triggers.Count -ge 2
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

function Get-BridgeDiscovery {
    param(
        $Config,
        [string]$WslIp,
        $Mappings,
        $HostNames
    )

    $driftReasons = [System.Collections.ArrayList]::new()
    if (-not (Test-PortProxyMappingsReady -Config $Config -WslIp $WslIp -Mappings $Mappings)) {
        [void]$driftReasons.Add("portproxy_drift")
    }
    if (-not (Test-FirewallRulesReady -Config $Config -Mappings $Mappings)) {
        [void]$driftReasons.Add("firewall_drift")
    }
    if (-not (Test-HostsFileReady -Config $Config -HostNames $HostNames)) {
        [void]$driftReasons.Add("hosts_drift")
    }
    if (-not (Test-BridgeTaskReady)) {
        [void]$driftReasons.Add("scheduled_task_drift")
    }

    return [pscustomobject]@{
        Ready                    = $driftReasons.Count -eq 0
        WslIp                    = $WslIp
        DiscoveryIntervalMinutes = Get-DiscoveryIntervalMinutes $Config
        DriftReasons             = @($driftReasons)
    }
}

function Write-BridgeDiscovery {
    param($Discovery)

    $status = if ($Discovery.Ready) { "READY" } else { "DEGRADED" }
    $reasons = if ($Discovery.DriftReasons.Count -eq 0) { "none" } else { $Discovery.DriftReasons -join "," }
    Write-Host ("DISCOVERY {0} wslIp={1} intervalMinutes={2} drift={3}" -f $status, $Discovery.WslIp, $Discovery.DiscoveryIntervalMinutes, $reasons)
}

function Invoke-BridgeReconcile {
    param(
        $Config,
        $Mappings,
        $HostNames,
        [string]$RegistryPath
    )

    $wslIp = Get-WslIp $Config
    $pendingDiscovery = [pscustomobject]@{
        Ready                    = $false
        WslIp                    = $wslIp
        DiscoveryIntervalMinutes = Get-DiscoveryIntervalMinutes $Config
        DriftReasons             = @("reconcile_in_progress")
    }
    Write-StateFile `
        -Config $Config `
        -WslIp $wslIp `
        -Mappings $Mappings `
        -HostNames $HostNames `
        -RegistryPath $RegistryPath `
        -Discovery $pendingDiscovery
    Reconcile-PortProxy -Config $Config -WslIp $wslIp -Mappings $Mappings
    Reconcile-FirewallRules -Config $Config -Mappings $Mappings
    Reconcile-HostsFile -Config $Config -HostNames $HostNames
    $discovery = Get-BridgeDiscovery -Config $Config -WslIp $wslIp -Mappings $Mappings -HostNames $HostNames
    Write-StateFile `
        -Config $Config `
        -WslIp $wslIp `
        -Mappings $Mappings `
        -HostNames $HostNames `
        -RegistryPath $RegistryPath `
        -Discovery $discovery
    Write-BridgeDiscovery -Discovery $discovery
    if (-not $discovery.Ready) {
        throw "Windows/WSL bridge reconcile finished with drift: $($discovery.DriftReasons -join ', ')"
    }
}

function Write-StateFile {
    param(
        $Config,
        [string]$WslIp,
        $Mappings,
        $HostNames,
        [string]$RegistryPath,
        $Discovery
    )

    $state = [ordered]@{
        contractVersion    = 2
        agentMode          = "scheduled-discovery"
        agentStatus        = $(if ($Discovery.Ready) { "ready" } else { "degraded" })
        generatedAt        = (Get-Date).ToString("o")
        action             = $Action
        wslIp              = $WslIp
        taskName           = $TaskName
        discoveryIntervalMinutes = $Discovery.DiscoveryIntervalMinutes
        driftReasons       = @($Discovery.DriftReasons)
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

    $wslIp = ""
    try {
        $wslIp = Get-WslIp $Config
        Write-Host ("WSL IP: {0}" -f $wslIp)
    } catch {
        Write-Host ("WSL IP: unavailable - {0}" -f $_.Exception.Message) -ForegroundColor Yellow
    }

    if (-not [string]::IsNullOrWhiteSpace($wslIp)) {
        try {
            $discovery = Get-BridgeDiscovery -Config $Config -WslIp $wslIp -Mappings $Mappings -HostNames $HostNames
            Write-BridgeDiscovery -Discovery $discovery
        } catch {
            Write-Host ("DISCOVERY unavailable - {0}" -f $_.Exception.Message) -ForegroundColor Yellow
        }
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
    "prerequisites" {
        Assert-BridgePrerequisites -Config $config
        Write-Host "Windows/WSL bridge prerequisites are ready. No bridge state was changed."
    }

    "discover" {
        Assert-BridgePrerequisites -Config $config
        $wslIp = Get-WslIp $config
        $discovery = Get-BridgeDiscovery -Config $config -WslIp $wslIp -Mappings $mappings -HostNames $hostNames
        Write-BridgeDiscovery -Discovery $discovery
        $discovery | ConvertTo-Json -Depth 4
        if (-not $discovery.Ready) {
            throw "Windows/WSL bridge discovery found drift: $($discovery.DriftReasons -join ', ')"
        }
    }

    "install" {
        Assert-BridgePrerequisites -Config $config
        $resolvedConfig = (Resolve-Path -LiteralPath $ConfigPath).Path
        Register-BridgeTask -ResolvedConfigPath $resolvedConfig -Config $config
        Invoke-BridgeReconcile -Config $config -Mappings $mappings -HostNames $hostNames -RegistryPath $registryPath
        Write-Host ""
        Write-Host "Installed. Discovery/reconcile now runs automatically. Trigger it manually with:"
        Write-Host "  Start-ScheduledTask -TaskName $TaskName"
    }

    "reconcile" {
        Assert-BridgePrerequisites -Config $config
        Invoke-BridgeReconcile -Config $config -Mappings $mappings -HostNames $hostNames -RegistryPath $registryPath
        Write-Host "Reconcile completed."
    }

    "refresh" {
        Assert-BridgePrerequisites -Config $config
        Invoke-BridgeReconcile -Config $config -Mappings $mappings -HostNames $hostNames -RegistryPath $registryPath
        Write-Host "Reconcile completed."
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
