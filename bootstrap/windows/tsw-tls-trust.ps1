#requires -Version 5.1
[CmdletBinding()]
param(
    [ValidateSet('inspect', 'install', 'remove')][string]$Action = 'inspect',
    [string]$CertificatePath,
    [string]$ExpectedSha256,
    [switch]$Approve
)
# Compatibility entry point; implementation and registration belong to the module.
$tswImplementationPath=Join-Path $PSScriptRoot "../../modules/tsw_windows_wsl/bootstrap/windows/tsw-tls-trust.ps1"
if($MyInvocation.InvocationName -eq '.') {
    . $tswImplementationPath @PSBoundParameters
} else {
    $ErrorActionPreference='Stop'
    $global:LASTEXITCODE=0
    & $tswImplementationPath @PSBoundParameters
    exit $LASTEXITCODE
}
