# Pre-Linux application boundary. Existing preparation owns inventory and state;
# Linux preparation and installation retain their own consent and verification.
function Get-GuidedSetupNextCommand($Options) {
    $command="./setup_wsl.ps1 -Distro '$($Options.Distro)' -Profile '$($Options.ServiceProfile)'"
    if($Options.UbuntuRelease){$command+=" -UbuntuRelease '$($Options.UbuntuRelease)'"}
    if($Options.LinuxCheckout){$command+=" -LinuxCheckout '$($Options.LinuxCheckout)'"}
    return $command+' -Resume'
}

function New-GuidedSetupBlocked($Code,$Remedy) {
    return @{schema_version=1;blockers=@(@{code=$Code;remedy=$Remedy})
        result=@{outcome='BLOCKED';exit_code=2;changed=$false;preparation_ready=$false;services_verified=$false}}
}

function Invoke-GuidedWindowsSetup($Options,$Ports) {
    # Validate before any inventory, including module-level callers and JSON.
    if($Options.Mode -notin @('Check','Plan','Apply') -or
        $Options.ServiceProfile -cnotin @('default','service-access') -or $Options.Services){
        return New-GuidedSetupBlocked 'selection_unavailable' 'Use default/service-access; selective profiles require the shared setup boundary.'
    }
    if($Options.LinuxCheckout -and ($Options.LinuxCheckout -cnotmatch '\A/[A-Za-z0-9_./ -]+\z' -or $Options.LinuxCheckout -match '^/mnt/[a-z](?:/|$)')){
        return New-GuidedSetupBlocked 'unsafe_checkout' 'Select an owned Linux-native checkout with a safe absolute path.'
    }
    if($Options.Json -and $Options.Mode -eq 'Apply'){
        return New-GuidedSetupBlocked 'interactive_consent_required' 'Rerun without -Json to review each stage and supply fresh consent.'
    }
    if(!$Options.Distro -and $Options.Mode -eq 'Apply'){
        $Options.Distro=& $Ports.SelectDistro
    }
    if(!$Options.Distro -or $Options.Distro -cnotmatch '\A[A-Za-z0-9._-]+\z' -or
        ($Options.UbuntuRelease -and $Options.UbuntuRelease -cnotin @('24.04','26.04'))){
        return New-GuidedSetupBlocked 'explicit_distro_required' 'Rerun with -Distro exact_registration; custom names also need -UbuntuRelease.'
    }
    $next=Get-GuidedSetupNextCommand $Options
    $inventoryOptions=$Options.Clone()
    $inventoryOptions.Mode=$(if($Options.Mode -eq 'Plan'){'Plan'}else{'Check'})
    $plan=& $Ports.Prepare $inventoryOptions
    $plan.result.next_command=$next
    if($Options.Mode -ne 'Apply'){return $plan}

    # Missing prerequisites go through the original guarded preparation owner.
    # No qualification flags or saved approval are synthesized by this entrypoint.
    if(@($plan.actions).Count -gt 0){
        $apply=& $Ports.Prepare $Options
        $apply.result.next_command=$next
        return $apply # Every effect requires fresh inventory/consent on resume.
    }
    if($plan.result.exit_code -ne 0){return $plan}

    $handoff=$plan.handoff
    if(!$handoff -or $handoff.status -cne 'LINUX_PREPARATION_REQUIRED' -or
        $handoff.distro -cne $Options.Distro -or $handoff.account -cnotmatch '\A[a-z_][a-z0-9_-]{0,31}\z' -or
        $handoff.account -eq 'root' -or $handoff.account -cne $plan.target.user -or
        $handoff.checkout -cnotmatch '\A/[A-Za-z0-9_./ -]+\z' -or
        $handoff.checkout -match '^/mnt/[a-z](?:/|$)' -or !$plan.plan_fingerprint){
        return New-GuidedSetupBlocked 'unverified_handoff' 'Reobserve the selected ordinary account and matching Linux checkout with -Preflight.'
    }
    if(!(& $Ports.Consent $plan)){
        return New-GuidedSetupBlocked 'installation_consent_required' $next
    }
    # Bind consent to fresh source/account/checkout/plan observations. No shell
    # command from a report or checkpoint is ever evaluated.
    $fresh=& $Ports.Prepare $inventoryOptions
    if($fresh.result.exit_code -ne 0 -or @($fresh.actions).Count -ne 0 -or
        $fresh.plan_fingerprint -cne $plan.plan_fingerprint -or
        $fresh.handoff.account -cne $handoff.account -or $fresh.handoff.checkout -cne $handoff.checkout -or
        $fresh.handoff.distro -cne $handoff.distro){
        return New-GuidedSetupBlocked 'handoff_drift' $next
    }
    $plan.mode='apply'
    $plan.read_only=$false
    $plan.result.host_prepared=$true
    # Console-based legacy owners expose an exit, not a structured change list.
    # Do not claim either no effects or confirmed changes from the exit alone.
    $plan.result.changed=$null
    $plan.result.execution_started=$true
    try {$exitCode=& $Ports.Install $handoff $Options.ServiceProfile}
    catch [Management.Automation.PipelineStoppedException] {$exitCode=130}
    catch {$exitCode=1}
    $plan.result.child_exit_code=$exitCode
    $plan.result.exit_code=$exitCode
    $plan.result.outcome=$(switch($exitCode){0{'INSTALLATION_COMPLETE'}2{'BLOCKED'}3{'RESTART_REQUIRED'}4{'PARTIAL'}124{'TIMEOUT'}130{'INTERRUPTED'}default{'FAILED'}})
    if($exitCode -ne 0){$plan.result.uncertain_actions+= 'linux_preparation_or_installation'}
    if($exitCode -eq 3){$plan.restart=@{scope='unknown';operator_command=$next;remedy='Follow the Linux stage restart/login instructions, then resume.'}}
    # The delegated installer owns installation verification; configured service
    # URLs are not evidence of live service health.
    $plan.result.installation_complete=($exitCode -eq 0)
    $plan.result.services_verified=$false
    $plan.result.stage='install'
    return $plan
}

function New-GuidedWindowsSetupPorts {
    $preparationPorts=New-PreparationPorts
    return @{
        Prepare={param($options) Invoke-WindowsPreparation $options $preparationPorts}.GetNewClosure()
        SelectDistro={try {Read-Host 'Exact Ubuntu WSL2 registration (for example Ubuntu-26.04)'}catch{return ''}}
        Consent={param($plan)
            Write-Host ('Selected distro: '+$plan.handoff.distro+'; ordinary account: '+$plan.handoff.account)
            Write-Host ('Linux checkout: '+$plan.handoff.checkout)
            Write-Host 'Next: Linux preparation, then installation only on success. Each owner requests its own consent.'
            try {return (Read-Host 'Type exact yes to enter this selected Linux installation stage') -ceq 'yes'}catch{return $false}
        }
        Install=${function:Invoke-GuidedLinuxInstallation}
    }
}
