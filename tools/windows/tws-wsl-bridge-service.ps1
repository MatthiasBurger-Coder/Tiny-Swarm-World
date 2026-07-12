#requires -Version 5.1

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$BridgeScriptPath,

    [Parameter(Mandatory = $true)]
    [string]$ConfigPath,

    [Parameter(Mandatory = $true)]
    [string]$PortRegistryPath,

    [ValidateRange(1, 1440)]
    [int]$IntervalMinutes = 1
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-BridgeReconcileProcess {
    $powerShellPath = Join-Path $env:windir "System32\WindowsPowerShell\v1.0\powershell.exe"
    try {
        & $powerShellPath `
            -NoProfile `
            -NonInteractive `
            -ExecutionPolicy Bypass `
            -File $BridgeScriptPath `
            -Action refresh `
            -ConfigPath $ConfigPath `
            -PortRegistryPath $PortRegistryPath

        if ($LASTEXITCODE -ne 0) {
            Write-Error "Bridge reconcile exited with code $LASTEXITCODE." -ErrorAction Continue
        }
        return $LASTEXITCODE
    } catch {
        Write-Error ("Bridge reconcile failed: {0}" -f $_.Exception.Message) -ErrorAction Continue
        return 1
    }
}

function Invoke-BridgeServiceLoop {
    $consecutiveFailures = 0
    while ($true) {
        $startedAt = Get-Date
        $exitCode = Invoke-BridgeReconcileProcess

        if ($exitCode -eq 0) {
            $consecutiveFailures = 0
        } else {
            $consecutiveFailures++
            if ($consecutiveFailures -ge 3) {
                Write-Error "Bridge reconcile failed three consecutive times; exiting for Windows service recovery." -ErrorAction Continue
                return 1
            }
        }

        $elapsedSeconds = ((Get-Date) - $startedAt).TotalSeconds
        $delaySeconds = [Math]::Max(1, ($IntervalMinutes * 60) - [int][Math]::Ceiling($elapsedSeconds))
        Start-Sleep -Seconds $delaySeconds
    }
}

if ($MyInvocation.InvocationName -ne ".") {
    exit (Invoke-BridgeServiceLoop)
}
