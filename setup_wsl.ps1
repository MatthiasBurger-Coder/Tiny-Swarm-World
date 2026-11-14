# Windows entrypoint only; product execution stays in the selected Linux account.
[CmdletBinding()]
param(
    [switch]$Help, [switch]$Preflight, [switch]$DryRun, [switch]$Json, [switch]$Resume,
    [string]$Distro='', [string]$UbuntuRelease='', [string]$LinuxCheckout='',
    [string]$Profile='service-access', [string]$Services='',
    [Parameter(ValueFromRemainingArguments=$true)][string[]]$UnsupportedArguments
)
$ErrorActionPreference='Stop'
$invalid=($UnsupportedArguments.Count -gt 0) -or ([int]$Help.IsPresent+[int]$Preflight.IsPresent+[int]$DryRun.IsPresent -gt 1) -or
    ($Resume -and ($Help -or $Preflight -or $DryRun)) -or
    ($Profile -cnotin @('default','service-access','minimal','custom')) -or
    ($Services -and $Profile -cne 'custom') -or ($Profile -ceq 'custom' -and !$Services) -or
    ($Distro -and $Distro -cnotmatch '\A[A-Za-z0-9._-]+\z') -or
    ($UbuntuRelease -and $UbuntuRelease -cnotin @('24.04','26.04'))
if($invalid){
    @{schema_version=1;result=@{outcome='BLOCKED';exit_code=2;changed=$false};blockers=@(@{code='invalid_arguments';remedy='Use ./setup_wsl.ps1 -Help.'})} | ConvertTo-Json -Depth 5 -Compress
    exit 2
}
if($Help){
    $usage=@'
./setup_wsl.ps1 [-Distro registration] [-UbuntuRelease 24.04|26.04]
    [-LinuxCheckout /absolute/Linux/path] [-Profile default|service-access]
    [-Preflight | -DryRun] [-Json] [-Resume] [-Verbose]
Guided apply is the default. Select an exact Ubuntu WSL2 registration and review
the ordinary Linux account and checkout. Custom registrations need UbuntuRelease.
Preflight/dry-run do not start a stopped distro, install dependencies or write state.
Minimal/custom profiles remain blocked until the shared selective setup boundary
is available. JSON apply never prompts and is blocked. No reset/force is exposed.
Elevation, account creation and restart are explicit operator steps. Rerun the
same command with -Resume; existing protected preparation state is reobserved,
and consent is requested afresh. No automatic shutdown or reboot occurs.
Windows preparation retains its qualification guard. An unqualified preparation
stage blocks installation. An already prepared target can delegate Linux
preparation and installation, with their own plans, consent and verification.
Child exits and restart-required status are preserved. No new clean-host release
qualification is claimed. Product Python runs only inside the selected WSL user.
'@
    if($Json){@{schema_version=1;help=$usage;result=@{outcome='HELP';exit_code=0;changed=$false}} | ConvertTo-Json -Depth 5 -Compress}else{$usage}
    exit 0
}
try {
    Import-Module (Join-Path $PSScriptRoot 'modules/tsw_windows_wsl/bootstrap/preparation/Preparation.psm1') -Force -DisableNameChecking
    $mode='Apply'
    if($Preflight){$mode='Check'}elseif($DryRun){$mode='Plan'}
    $options=@{Mode=$mode;RepositoryRoot=$PSScriptRoot;Distro=$Distro;UbuntuRelease=$UbuntuRelease
        LinuxCheckout=$LinuxCheckout;ServiceProfile=$Profile;Services=$Services;Resume=$Resume.IsPresent
        Json=$Json.IsPresent;ProbeTimeoutSeconds=15;ActionTimeoutSeconds=900
        Invalid=$false;ApproveApply=$false;QualificationRun=$false;ApprovedPlan=$null}
    $result=Invoke-GuidedWindowsSetup $options (New-GuidedWindowsSetupPorts)
} catch [Management.Automation.PipelineStoppedException] {
    $result=@{schema_version=1;result=@{outcome='INTERRUPTED';exit_code=130;changed=$false;uncertain_actions=@('active_stage')};blockers=@()}
} catch {
    # Do not serialize exceptions, native output or environment details.
    $result=@{schema_version=1;result=@{outcome='FAILED';exit_code=1;changed=$false}
        blockers=@(@{code='setup_boundary_failed';remedy='Inspect the trusted checkout and rerun -Preflight.'})}
}
if($Json){$result | ConvertTo-Json -Depth 30 -Compress}else{
    $result | ConvertTo-Json -Depth 30
}
exit $result.result.exit_code
