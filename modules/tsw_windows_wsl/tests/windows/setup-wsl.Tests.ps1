param([Parameter(Mandatory=$true)][string]$RepositoryRoot)
$ErrorActionPreference='Stop'
Import-Module (Join-Path $RepositoryRoot 'modules/tsw_windows_wsl/bootstrap/preparation/Preparation.psm1') -Force -DisableNameChecking
$script:count=0
function Assert($value,$name){if(!$value){throw "FAIL: $name"};$script:count++}
function Options {
    return @{Mode='Apply';Distro='Ubuntu-26.04';UbuntuRelease='26.04';LinuxCheckout='/home/operator/checkout'
        ServiceProfile='service-access';Services='';Json=$false;Resume=$false}
}
function Plan {
    return @{schema_version=1;mode='preflight';read_only=$true;actions=@();plan_fingerprint='same';target=@{user='operator'}
        handoff=@{status='LINUX_PREPARATION_REQUIRED';distro='Ubuntu-26.04';account='operator';checkout='/home/operator/checkout'}
        result=@{outcome='READY';exit_code=0;changed=$false;uncertain_actions=@()};blockers=@()}
}
function Reset {
    $script:prepares=0;$script:installs=0;$script:consents=0;$script:selects=0
    $script:code=0;$script:consent=$true;$script:drift=$false;$script:stageCode=0;$script:actions=$false
    $script:account='operator';$script:path='/home/operator/checkout';$script:registration='Ubuntu-26.04'
}
$ports=@{
    Prepare={param($options)
        $script:prepares++;$plan=Plan
        $plan.handoff.account=$script:account;$plan.handoff.checkout=$script:path;$plan.handoff.distro=$script:registration
        if($script:drift -and $script:prepares -gt 1){$plan.plan_fingerprint='changed'}
        if($script:actions){$plan.actions=@(@{id='enable_systemd'})}
        if($options.Mode -eq 'Apply' -or $script:stageCode -ne 0){$plan.result.exit_code=$script:stageCode;$plan.result.outcome='RESTART_REQUIRED'}
        return $plan
    }
    Install={param($handoff,$profile)
        $script:installs++
        Assert ($handoff.distro -ceq 'Ubuntu-26.04' -and $handoff.account -ceq 'operator') 'explicit selected target'
        Assert ($profile -ceq 'service-access') 'profile forwarded'
        return $script:code
    }
    Consent={param($plan) $script:consents++;return $script:consent}
    SelectDistro={$script:selects++;return 'Ubuntu-26.04'}
}
foreach($mode in @('Check','Plan')){
    Reset;$o=Options;$o.Mode=$mode;$r=Invoke-GuidedWindowsSetup $o $ports
    Assert ($script:prepares -eq 1 -and $script:installs -eq 0 -and $script:consents -eq 0) 'read-only delegates inventory only'
    Assert ($r.result.next_command -like './setup_wsl.ps1 * -Resume') 'same entrypoint resume'
}
foreach($testExit in @(0,1,2,3,4,124,130)){
    Reset;$script:code=$testExit;$r=Invoke-GuidedWindowsSetup (Options) $ports
    Assert ($r.result.exit_code -eq $testExit -and $r.result.child_exit_code -eq $testExit) "unmodified child exit $testExit"
    Assert ($r.result.installation_complete -eq ($testExit -eq 0)) 'installation success only on zero'
    Assert ($r.mode -eq 'apply' -and !$r.read_only -and $null -eq $r.result.changed -and $r.result.execution_started) 'live delegation never reported read-only or unchanged'
    Assert ($script:prepares -eq 2 -and $script:consents -eq 1 -and $script:installs -eq 1) 'fresh inventory after consent'
}
foreach($testExit in @(2,3,4,124,130)){
    Reset;$script:actions=$true;$script:stageCode=$testExit;$r=Invoke-GuidedWindowsSetup (Options) $ports
    Assert ($r.result.exit_code -eq $testExit -and $script:installs -eq 0) 'guarded preparation stops dependent stages'
}
Reset;$script:stageCode=3;$r=Invoke-GuidedWindowsSetup (Options) $ports
Assert ($r.result.exit_code -eq 3 -and $script:installs -eq 0) 'observed restart propagates'
Reset;$script:drift=$true;$r=Invoke-GuidedWindowsSetup (Options) $ports
Assert ($r.blockers[0].code -eq 'handoff_drift' -and $script:installs -eq 0) 'consent drift blocks'
Reset;$script:consent=$false;$r=Invoke-GuidedWindowsSetup (Options) $ports
Assert ($r.result.exit_code -eq 2 -and $script:installs -eq 0) 'declined consent blocks'
Reset;$o=Options;$o.Json=$true;$r=Invoke-GuidedWindowsSetup $o $ports
Assert ($script:prepares -eq 0 -and $script:consents -eq 0 -and $script:installs -eq 0) 'JSON apply no prompts or actions'
foreach($profile in @('minimal','custom','classic','invalid')){
    Reset;$o=Options;$o.ServiceProfile=$profile;$r=Invoke-GuidedWindowsSetup $o $ports
    Assert ($r.result.exit_code -eq 2 -and $script:prepares -eq 0) 'unsupported selection no inventory'
}
foreach($testAccount in @('root','operator;id','another')){
    Reset;$script:account=$testAccount;$r=Invoke-GuidedWindowsSetup (Options) $ports
    Assert ($r.result.exit_code -eq 2 -and $script:installs -eq 0) 'invalid or changed account blocks'
}
Reset;$script:registration='unrelated';$r=Invoke-GuidedWindowsSetup (Options) $ports
Assert ($r.result.exit_code -eq 2 -and $script:installs -eq 0) 'unrelated registration never used'
foreach($testPath in @('/mnt/c/checkout',"/home/operator/checkout'; touch /tmp/unsafe")){
    Reset;$script:path=$testPath;$r=Invoke-GuidedWindowsSetup (Options) $ports
    Assert ($r.result.exit_code -eq 2 -and $script:installs -eq 0) 'unsafe handoff blocks'
}
Reset;$o=Options;$o.Resume=$true;$r=Invoke-GuidedWindowsSetup $o $ports
Assert ($script:prepares -eq 2 -and $script:consents -eq 1) 'resume reobserves and never replays consent'
Reset;$o=Options;$o.Distro='';$o.Mode='Check';$r=Invoke-GuidedWindowsSetup $o $ports
Assert ($script:selects -eq 0 -and $script:prepares -eq 0 -and $r.result.exit_code -eq 2) 'read-only ambiguity never prompts'
Reset;$o=Options;$o.Distro='';$r=Invoke-GuidedWindowsSetup $o $ports
Assert ($script:selects -eq 1 -and $script:installs -eq 1) 'interactive explicit selection'
# Check the actual adapter's Windows argv construction without creating a process.
$module=Get-Module Preparation
$encoded=& $module {ConvertTo-PreparationProcessArguments @('--distribution','Ubuntu-26.04','--exec','/bin/bash','-lc','cd -- "$1"','setup-wsl','/home/operator/checkout with spaces')}
Assert ($encoded.Contains('\"$1\"') -and $encoded.EndsWith('"/home/operator/checkout with spaces"')) 'interactive argv retains bash quoting and path spaces'
Write-Output "PASS: $script:count guided setup assertions"
