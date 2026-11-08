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
$ErrorActionPreference='Stop'
$RepositoryRoot=[IO.Path]::GetFullPath((Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../..')).ProviderPath)
$requiredAssets=@(
    'modules/tsw_windows_wsl/bootstrap/preparation/Preparation.psm1','modules/tsw_windows_wsl/bootstrap/preparation/Policy.ps1',
    'modules/tsw_windows_wsl/bootstrap/preparation/Application.ps1','modules/tsw_windows_wsl/bootstrap/preparation/Adapters.ps1',
    'modules/tsw_windows_wsl/bootstrap/preparation/SourceProof.ps1','modules/tsw_windows_wsl/bootstrap/preparation/Download.ps1',
    'modules/tsw_windows_wsl/bootstrap/preparation/linux-config.sh','modules/tsw_windows_wsl/bootstrap/preparation/Resources.ps1',
    'modules/tsw_windows_wsl/bootstrap/preparation/ResourceAdapters.ps1','modules/tsw_windows_wsl/bootstrap/preparation/ResourceHost.ps1',
    'modules/tsw_windows_wsl/bootstrap/preparation/linux-resources.sh','modules/tsw_windows_wsl/bootstrap/preparation/resource-projection.json',
    'modules/tsw_windows_wsl/bootstrap/preparation/Bridge.ps1','modules/tsw_windows_wsl/bootstrap/preparation/Handoff.ps1',
    'modules/tsw_windows_wsl/bootstrap/preparation/linux-handoff.sh'
)
foreach($asset in $requiredAssets) {
    $path=Join-Path $RepositoryRoot $asset
    if(!(Test-Path -LiteralPath $path -PathType Leaf)) {
        $failure=@{schema_version=1
        blockers=@(@{code='missing_asset'
        asset=$asset
        remedy='Extract the complete reviewed release including preparation assets.'})
        result=@{status='BLOCKED';outcome='BLOCKED'
        exit_code=2
        changed=$false
        preparation_ready=$false
        services_verified=$false}}
        $failure | ConvertTo-Json -Depth 10 -Compress
        exit 2
    }
}
Import-Module (Join-Path $RepositoryRoot 'modules/tsw_windows_wsl/bootstrap/preparation/Preparation.psm1') -Force -DisableNameChecking
$mode='Apply'
if($Help){$mode='Help'}elseif($Preflight){$mode='Check'}elseif($DryRun){$mode='Plan'}
$invalid=([int]$Help.IsPresent+[int]$Preflight.IsPresent+[int]$DryRun.IsPresent -gt 1) -or ($ServiceProfile -notin @('default','service-access'))
$options=@{Mode=$mode
Invalid=$invalid
RepositoryRoot=$RepositoryRoot
Distro=$Distro
UbuntuRelease=$UbuntuRelease
LinuxCheckout=$LinuxCheckout
ServiceProfile=$ServiceProfile
Json=$Json.IsPresent
ApproveApply=$ApproveApply.IsPresent
QualificationRun=$QualificationRun.IsPresent
ApprovedPlan=$ApprovedPlan
QualificationHost=$QualificationHost
QualificationDistro=$QualificationDistro
QualificationRevision=$QualificationRevision
RecoveryReference=$RecoveryReference
WslMemoryGiB=$WslMemoryGiB
WslProcessors=$WslProcessors
WslSwapGiB=$WslSwapGiB
ProbeTimeoutSeconds=$ProbeTimeoutSeconds
ActionTimeoutSeconds=$ActionTimeoutSeconds}
$result=Invoke-WindowsPreparation -Options $options -Ports (New-PreparationPorts)
$result.result.status=$result.result.outcome
if($result.restart){$result.restart.command=$result.restart.operator_command}
if($Json){$result | ConvertTo-Json -Depth 30 -Compress}else{$result | ConvertTo-Json -Depth 30}
exit $result.result.exit_code
