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
# Compatibility entry point; implementation and registration belong to the module.
$tswImplementationPath=Join-Path $PSScriptRoot "../../modules/tsw_windows_wsl/bootstrap/windows/tws-wsl-bridge-service.ps1"
if($MyInvocation.InvocationName -eq '.') {
    . $tswImplementationPath @PSBoundParameters
} else {
    $ErrorActionPreference='Stop'
    $global:LASTEXITCODE=0
    & $tswImplementationPath @PSBoundParameters
    exit $LASTEXITCODE
}
