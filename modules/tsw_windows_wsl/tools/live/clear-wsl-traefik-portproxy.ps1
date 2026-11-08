#Requires -RunAsAdministrator

[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string] $ListenAddress = "127.0.0.1",
    [int[]] $Ports = @(80, 443),
    [switch] $ShowOnly
)

$ErrorActionPreference = "Stop"

function Get-ListeningProcess {
    param(
        [string] $Address,
        [int[]] $PortList
    )

    foreach ($port in $PortList) {
        Get-NetTCPConnection `
            -State Listen `
            -LocalAddress $Address `
            -LocalPort $port `
            -ErrorAction SilentlyContinue |
            ForEach-Object {
                $process = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
                [PSCustomObject]@{
                    LocalAddress  = $_.LocalAddress
                    LocalPort     = $_.LocalPort
                    OwningProcess = $_.OwningProcess
                    ProcessName   = if ($process) { $process.ProcessName } else { "<unknown>" }
                }
            }
    }
}

function Show-CurrentState {
    param(
        [string] $Address,
        [int[]] $PortList
    )

    Write-Host ""
    Write-Host "Current v4tov4 portproxy rules:"
    netsh interface portproxy show v4tov4

    $listeners = @(Get-ListeningProcess -Address $Address -PortList $PortList)
    Write-Host ""
    if ($listeners.Count -eq 0) {
        Write-Host "No listeners remain on $Address ports $($PortList -join ', ')."
        return $true
    }

    Write-Warning "The following listeners still occupy the installer ports:"
    $listeners | Format-Table -AutoSize
    return $false
}

Write-Host "Tiny Swarm World WSL Traefik portproxy cleanup"
Write-Host "Target listener: $ListenAddress"
Write-Host "Target ports:    $($Ports -join ', ')"

if ($ShowOnly) {
    $isClear = Show-CurrentState -Address $ListenAddress -PortList $Ports
    if ($isClear) {
        exit 0
    }
    exit 2
}

foreach ($port in $Ports) {
    $target = "${ListenAddress}:$port"
    if ($PSCmdlet.ShouldProcess($target, "delete v4tov4 portproxy rule")) {
        Write-Host "Deleting v4tov4 portproxy rule for $target"
        $output = & netsh interface portproxy delete v4tov4 `
            listenaddress=$ListenAddress `
            listenport=$port 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Delete returned exit code $LASTEXITCODE for $target. Output: $output"
        }
    }
}

Start-Sleep -Milliseconds 500
$isClear = Show-CurrentState -Address $ListenAddress -PortList $Ports

if (-not $isClear) {
    Write-Error "Ports are still occupied. Stop the listed process or remove the matching forwarding rule before running ./install.sh."
    exit 2
}

Write-Host ""
Write-Host "OK: $ListenAddress ports $($Ports -join ', ') are clear for Tiny Swarm World preflight."
