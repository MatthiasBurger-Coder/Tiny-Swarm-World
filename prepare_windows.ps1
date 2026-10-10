# Windows pre-Linux preparation boundary; product Python remains Linux-only.
[CmdletBinding()]
param(
    [switch]$Help,[switch]$Preflight,[switch]$DryRun,[switch]$Json,[switch]$ApproveApply,
    [string]$Distro='',[string]$UbuntuRelease='',[string]$ServiceProfile='service-access',
    [switch]$QualificationRun,[string]$ApprovedPlan,
    [string]$QualificationHost,[string]$QualificationDistro,[string]$QualificationRevision,[string]$RecoveryReference,
    [Nullable[int]]$WslMemoryGiB,[Nullable[int]]$WslProcessors,[Nullable[int]]$WslSwapGiB,
    [int]$ProbeTimeoutSeconds=15,[int]$ActionTimeoutSeconds=900
)
$ErrorActionPreference='Stop'
$requiredAssets=@('Preparation.psm1','Policy.ps1','Application.ps1','Adapters.ps1','SourceProof.ps1','Download.ps1','linux-config.sh','Resources.ps1','ResourceAdapters.ps1','ResourceHost.ps1','linux-resources.sh','resource-projection.json','Bridge.ps1')
foreach($asset in $requiredAssets) {
    $path=Join-Path $PSScriptRoot ('tools/windows/preparation/'+$asset)
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
Import-Module (Join-Path $PSScriptRoot 'tools/windows/preparation/Preparation.psm1') -Force -DisableNameChecking
$mode='Apply'
if($Help){$mode='Help'}elseif($Preflight){$mode='Check'}elseif($DryRun){$mode='Plan'}
$invalid=([int]$Help.IsPresent+[int]$Preflight.IsPresent+[int]$DryRun.IsPresent -gt 1) -or ($ServiceProfile -notin @('default','service-access'))
$options=@{Mode=$mode
Invalid=$invalid
RepositoryRoot=$PSScriptRoot
Distro=$Distro
UbuntuRelease=$UbuntuRelease
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
