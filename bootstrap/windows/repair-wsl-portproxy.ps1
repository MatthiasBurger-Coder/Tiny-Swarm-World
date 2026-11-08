#Requires -RunAsAdministrator

[CmdletBinding()]
param()
# Compatibility entry point; implementation and registration belong to the module.
$tswImplementationPath=Join-Path $PSScriptRoot "../../modules/tsw_windows_wsl/bootstrap/windows/repair-wsl-portproxy.ps1"
if($MyInvocation.InvocationName -eq '.') {
    . $tswImplementationPath @PSBoundParameters
} else {
    $ErrorActionPreference='Stop'
    $global:LASTEXITCODE=0
    & $tswImplementationPath @PSBoundParameters
}
