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
$RepositoryRoot=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
$requiredAssets=@(
    'bootstrap/windows/preparation/Preparation.psm1','bootstrap/windows/preparation/Policy.ps1',
    'bootstrap/windows/preparation/Application.ps1','bootstrap/windows/preparation/Adapters.ps1',
    'bootstrap/windows/preparation/SourceProof.ps1','bootstrap/windows/preparation/Download.ps1',
    'bootstrap/windows/preparation/linux-config.sh','bootstrap/windows/preparation/Resources.ps1',
    'bootstrap/windows/preparation/ResourceAdapters.ps1','bootstrap/windows/preparation/ResourceHost.ps1',
    'bootstrap/windows/preparation/linux-resources.sh','bootstrap/windows/preparation/resource-projection.json',
    'bootstrap/windows/preparation/Bridge.ps1','bootstrap/windows/preparation/Handoff.ps1',
    'bootstrap/windows/preparation/linux-handoff.sh'
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
Import-Module (Join-Path $RepositoryRoot 'bootstrap/windows/preparation/Preparation.psm1') -Force -DisableNameChecking
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
