# Pure plan policy: no host or filesystem calls.
function Get-PreparationSelection($Options) {
    if($Options.LinuxCheckout -and ($Options.LinuxCheckout -isnot [string] -or $Options.LinuxCheckout -cnotmatch '\A/[A-Za-z0-9_./ -]+\z' -or $Options.LinuxCheckout -match '^/mnt/[a-z](?:/|$)')){return @{valid=$false}}
    if($Options.Distro -isnot [string] -or $Options.Distro -cnotmatch '\A[A-Za-z0-9][A-Za-z0-9._-]{0,63}\z'){return @{valid=$false}}
    $canonical=$null
    if($Options.Distro -ceq 'Ubuntu-24.04'){$canonical='24.04'}
    elseif($Options.Distro -ceq 'Ubuntu-26.04'){$canonical='26.04'}
    $release=$Options.UbuntuRelease
    if(!$release){$release=$canonical}
    if($release -cnotin @('24.04','26.04') -or ($canonical -and $release -cne $canonical)){return @{valid=$false}}
    return @{valid=$true;release=$release;install_artifact=$(if($canonical){$Options.Distro}else{$null})}
}
function Get-PreparationVirtualization($HostFacts) {
    $firmware=@($HostFacts.firmware_values)
    $known=$HostFacts.hypervisor_present -is [bool] -and $firmware.Count -gt 0 -and @($firmware | Where-Object{$_ -isnot [bool]}).Count -eq 0
    $enabled=$null
    $available=$null
    if($known){$enabled=@($firmware | Where-Object{$_ -eq $false}).Count -eq 0
    $available=$HostFacts.hypervisor_present -or $enabled}
    return @{known=$known;firmware_enabled=$enabled;hypervisor_present=$HostFacts.hypervisor_present;available=$available}
}
function Test-PreparationInstallCapabilities($HelpResult) {
    if($HelpResult.exit_code -isnot [int] -or $HelpResult.exit_code -notin @(0,-1) -or $HelpResult.stdout -isnot [string] -or $HelpResult.stderr -isnot [string] -or $HelpResult.stderr.Length -ne 0){return $false}
    $text=$HelpResult.stdout -replace "`0",''
    foreach($flag in @('--install','--from-file','--name','--no-launch')){
        if($text -cnotmatch ('(?m)(?:\A|[\s,])'+[regex]::Escape($flag)+'(?=\z|[\s,])')){return $false}
    }
    return $true
}
function Get-PreparationDigest($Value) {
    $bytes = [Text.Encoding]::UTF8.GetBytes(($Value | ConvertTo-Json -Depth 30 -Compress))
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant() } finally { $sha.Dispose() }
}
function New-PreparationPlan($Options, $Facts, $Source) {
    $blockers = New-Object Collections.ArrayList
    $actions = New-Object Collections.ArrayList
    $restart = @{scope='none'
    operator_command=$null}
    function Block($Code, $Remedy) { [void]$blockers.Add(@{code=$Code
    stage='windows_wsl'
    remedy=$Remedy}) }
    function Action($Id, $Before, $After, $Scope) {
        [void]$actions.Add(@{id=$Id
        owner='W04'
        target=$Options.Distro
        operation='update'
        before=$Before
        after=$After
        prerequisites=@('candidate_eligibility','fresh_consent','protected_evidence')
        privilege='administrator'
        timeout_seconds=$Options.ActionTimeoutSeconds
        restart_scope=$Scope
        preservation_rule='preserve unrelated distributions and configuration'
        verification_probe='fresh_inventory'
        retry_budget=0})
    }
    if ($Facts.platform -ne 'Windows' -or $Facts.product_type -ne 1 -or $Facts.build -lt 22000 -or $Facts.architecture -ne 'AMD64') { Block 'unsupported_host' 'Use Windows 11 client x64 build 22000 or newer.' }
    if($Facts.evidence_storage_safe -ne $true){Block 'unsafe_evidence_storage' 'Resolve protected local evidence owner/ACL/reparse safety before candidate mutation.'}
    if ($null -eq $Facts.virtualization) { Block 'virtualization_unknown' 'Inspect typed host hypervisor and firmware virtualization facts, then rerun preflight.' }
    elseif ($Facts.virtualization -ne $true) { Block 'virtualization_unavailable' 'Enable hardware virtualization in firmware, then rerun preflight.' }
    if ($Facts.elevated -ne $true) { Block 'elevation_required' 'Open elevated Windows PowerShell and rerun preflight.' }
    if ($Facts.reboot_pending) { $restart=@{scope='Windows'
    operator_command='Restart-Computer'}
    Block 'reboot_pending' 'Restart Windows yourself, then rerun preflight.' }
    if(!$Options.InstallArtifact -and $Facts.distro_present -ne $true){Block $(if($Facts.distro_present -eq $false){'custom_registration_missing'}else{'custom_registration_unknown'}) 'Select an observed existing registration with its explicit UbuntuRelease; missing custom registrations never install prerequisites.'}
    elseif ($Facts.features_known -ne $true) { Block 'features_unknown' 'Inspect required Windows optional feature states.' }
    elseif ($Facts.features_missing.Count -gt 0) { Action 'enable_features' @($Facts.features_missing) 'Enabled' 'Windows' }
    elseif ($Facts.wsl_present -eq $false) { Action 'install_wsl' 'absent' '3.0.1' 'Windows' }
    elseif ($Facts.wsl_present -ne $true -or !$Facts.wsl_version -or ([version]$Facts.wsl_version -lt [version]'2.4.10')) { Block 'wsl_version_unsupported' 'Install a reviewed WSL release >=2.4.10; no automatic upgrade of existing WSL.' }
    elseif ($Facts.distro_inventory_known -ne $true) { Block 'distro_inventory_unknown' 'Inspect authoritative distribution names, generations and defaults; no replacement/install is allowed from ambiguous enumeration.' }
    elseif ($Facts.distro_present -eq $false) {
        if($Facts.install_capable -ne $true){Block 'wsl_capabilities_unknown' 'Verify WSL --install --from-file --name --no-launch capabilities before installation.'}
        else{Action 'install_distro' 'absent' $Options.Distro 'distro'}
    }
    elseif ($Facts.distro_present -ne $true) { Block 'distro_unknown' 'Inspect WSL distribution registration.' }
    elseif ($Facts.wsl_generation -ne 2) { Block 'wsl1_unsupported' 'Select an existing WSL2 target; automatic conversion is forbidden.' }
    elseif ($Facts.running -ne $true) { Block 'distro_stopped' ('Start the selected distro interactively: wsl.exe --distribution '+$Options.Distro+'. Complete its account setup, then rerun preflight.') }
    elseif ($Facts.linux_known -ne $true) { Block 'linux_unknown' 'Inspect the selected running distro release, account and configuration.' }
    elseif ($Facts.linux_id -ne 'ubuntu' -or $Facts.release -ne $Options.ExpectedRelease -or $Facts.linux_architecture -ne 'x86_64') { Block 'linux_unsupported' 'Select the matching supported Ubuntu x86_64 release.' }
    elseif ($Facts.uid -lt 1000 -or $Facts.uid -ge 65534 -or !$Facts.user -or $Facts.user -eq 'root') { Block 'ordinary_account_required' ('In '+$Options.Distro+', create an ordinary account with adduser, then select it using wsl.exe --manage '+$Options.Distro+' --set-default-user <existing-account>; log in and rerun.') }
    elseif ($Facts.config_safe -ne $true) { Block 'unsafe_wsl_conf' 'Resolve duplicate INI sections/keys, symlink or unsafe /etc/wsl.conf ownership/mode.' }
    elseif ($Facts.systemd_packages -ne $true) { Block 'systemd_packages_missing' 'In the selected Ubuntu distro run sudo apt-get update and sudo apt-get install systemd systemd-sysv after separately reviewing and approving those commands.' }
    elseif ($Facts.systemd_configured -ne $true) { Action 'enable_systemd' $Facts.config_hash 'boot.systemd=true' 'distro' }
    elseif ($Facts.pid1 -ne 'systemd') { $restart=@{scope='distro'
    operator_command=('wsl.exe --terminate '+$Options.Distro+'; wsl.exe --distribution '+$Options.Distro)}
    Block 'systemd_restart_required' 'Terminate/relaunch only the selected distro yourself, then rerun preflight.' }
    $resources=@{state='LIFECYCLE_PREREQUISITES_REQUIRED'}
    if($blockers.Count -eq 0 -and $actions.Count -eq 0){
        $resources=Get-PreparationResourceAssessment $Options $Facts
        foreach($blocker in $resources.blockers){[void]$blockers.Add($blocker)}
        if($resources.change_required){
            Action 'adapt_wsl_resources' @{settings=$resources.current_settings;snapshot=$resources.config_snapshot} $resources.allocation 'WSL-wide'
            $actions[$actions.Count-1].owner='W05'
            $actions[$actions.Count-1].target='global .wslconfig'
            $actions[$actions.Count-1].preservation_rule='Preserve unrelated entries, encoding, newlines and metadata; protected unique backup and final approved snapshot comparison.'
        }
        if(@($resources.blockers | Where-Object{$_.code -eq 'effective_resources_mismatch'}).Count -gt 0){$restart=@{scope='WSL-wide';operator_command=('wsl.exe --shutdown; wsl.exe --distribution '+$Options.Distro)}}
    }
    if($blockers.Count -eq 0 -and $actions.Count -eq 0){Add-PreparationBridgePlan $Options $Facts $blockers $actions}
    $candidateEligible=$blockers.Count -eq 0
    if($Options.Mode -ne 'Apply' -and $actions.Count -gt 0){Block 'prerequisite_missing' 'Review this staged plan, then authorize the exact candidate qualification stage.'}
    $ready = $blockers.Count -eq 0 -and $actions.Count -eq 0
    $outcome='BLOCKED'
    $exit=2
    if ($ready) { $outcome='READY'
    $exit=0 }
    elseif ($restart.scope -ne 'none') { $outcome='RESTART_REQUIRED'
    $exit=3 }
    $nextCommand='./prepare_windows.ps1 -Distro '+$Options.Distro+' -UbuntuRelease '+$Options.ExpectedRelease+' -ServiceProfile '+$Options.ServiceProfile+' -Preflight'
    foreach($key in @('WslMemoryGiB','WslProcessors','WslSwapGiB')){if($null -ne $Options[$key]){$nextCommand+=' -'+$key+' '+$Options[$key]}}
    $handoff=Get-PreparationHandoff $Options $Facts
    if(!$ready){$handoff=@{status='WINDOWS_PREREQUISITES_REQUIRED';preparation_ready=$false;services_verified=$false}}
    elseif($handoff.operator_command){$nextCommand=$handoff.operator_command}
    else {Block 'linux_checkout_required' $handoff.remedy; $outcome='BLOCKED'; $exit=2}
    $plan = [ordered]@{schema_version=1
    mode=$(switch($Options.Mode){'Check'{'preflight'}
    'Plan'{'dry_run'}
    default{'apply'}})
    read_only=($Options.Mode -ne 'Apply')
    target=$Facts
    source=$Source
    selection=@{profile=$Options.ServiceProfile
    distro=$Options.Distro
    ubuntu_release=$Options.ExpectedRelease
    catalog_source='canonical fixed WSL profile and provider resource projection'}
    observations=@{host=$Facts
    source=$Source}
    actions=@($actions.ToArray())
    handoff=$handoff
    resources=$resources
    blockers=@($blockers.ToArray())
    restart=$restart
    result=@{outcome=$outcome
    exit_code=$exit
    changed=$false
    completed_actions=@()
    uncertain_actions=@()
    capability_ready=$ready
    preparation_ready=$false
    services_verified=$false
    candidate_eligible=$candidateEligible
    qualified=$false
    live_state='LIVE_CONSENT_MISSING'
    next_command=$nextCommand
    evidence_path=$null}
    artifacts=(Get-PreparationArtifacts)}
    $boundFacts=ConvertTo-PreparationHashtable ($Facts | ConvertTo-Json -Depth 30 -Compress | ConvertFrom-Json)
    if($boundFacts.resource_facts){foreach($key in @('distro_free_bytes','swap_free_bytes','effective_disk_bytes')){$boundFacts.resource_facts.Remove($key)}}
    $plan['plan_fingerprint']=Get-PreparationDigest @($boundFacts,$Source,$plan.selection,$plan.resources,$plan.actions,@($plan.blockers | Where-Object{$_.code -ne 'prerequisite_missing'}),$plan.artifacts)
    return $plan
}
function Get-PreparationArtifacts {
    return @{
        wsl=@{version='3.0.1'
        url='https://github.com/microsoft/WSL/releases/download/3.0.1/wsl.3.0.1.0.x64.msi'
        sha256='28b1a0d013640a2ac95898ea705fa186e5b4ff767a1c1b49257161bc106599c6'}
        'Ubuntu-24.04'=@{version='24.04.5'
        url='https://releases.ubuntu.com/noble/ubuntu-24.04.5-wsl-amd64.wsl'
        sha256='bb415d824822c4b878125729af451a5d18fb13d1cf5cbed9a7393ad64ac6039e'}
        'Ubuntu-26.04'=@{version='26.04.1'
        url='https://releases.ubuntu.com/resolute/ubuntu-26.04.1-wsl-amd64.wsl'
        sha256='48d56724b5c8e60f24893e83e73bbb58c60b3ca22fba3da977075420acd54104'}
    }
}

function Get-PreparationEvidenceFacts($Facts) {
    return @{build=$Facts.build
    architecture=$Facts.architecture
    wsl_version=$Facts.wsl_version
    wsl_generation=$Facts.wsl_generation
    release=$Facts.release
    linux_architecture=$Facts.linux_architecture
    config_hash=$Facts.config_hash
    config_metadata=$Facts.config_metadata
    systemd_configured=$Facts.systemd_configured
    pid1=$Facts.pid1}
}
