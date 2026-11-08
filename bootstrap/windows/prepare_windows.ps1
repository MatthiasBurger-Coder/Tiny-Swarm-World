# Windows pre-Linux preparation boundary; product Python remains Linux-only.
[CmdletBinding()]
param(
    [switch]$Help,[switch]$Preflight,[switch]$DryRun,[switch]$Json,[switch]$ApproveApply,
    [string]$Distro='',[string]$UbuntuRelease='',[string]$LinuxCheckout='',[string]$ServiceProfile='service-access',
    [switch]$QualificationRun,[string]$ApprovedPlan,
    [string]$QualificationHost,[string]$QualificationDistro,[string]$QualificationRevision,[string]$RecoveryReference,
    [Nullable[int]]$WslMemoryGiB,[Nullable[int]]$WslProcessors,[Nullable[int]]$WslSwapGiB,
    [int]$ProbeTimeoutSeconds=15,[int]$ActionTimeoutSeconds=900
)
# Compatibility entry point; implementation and registration belong to the module.
$tswImplementationPath=Join-Path $PSScriptRoot "../../modules/tsw_windows_wsl/bootstrap/windows/prepare_windows.ps1"
if($MyInvocation.InvocationName -eq '.') {
    . $tswImplementationPath @PSBoundParameters
} else {
    $ErrorActionPreference='Stop'
    $global:LASTEXITCODE=0
    & $tswImplementationPath @PSBoundParameters
    exit $LASTEXITCODE
}
